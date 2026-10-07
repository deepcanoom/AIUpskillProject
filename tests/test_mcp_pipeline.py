"""Milestone 4 delivery tests: MCP servers, SearchSkill and the agent pipeline.

Database layer: insert, URL de-duplication, query, search and source counts.
Every MCP tool handler, called in-process (fast, no subprocess).
End-to-end MCP over stdio: a real server process spawned by SearchSkill.
Pipeline smoke test: fetch -> store -> filter -> summarize -> write, offline.
Canned LLM responses stand in for the provider, so no API key is needed.
Agents (Summarizer, Writer) are checked on their parsing and file output.
No network: the fetch step is replaced by a fake orchestrator.
Outputs land in pytest's tmp dir; the repo's data/ folder is never touched.
One `pytest` run covers Milestones 1-4.
MCP servers log to stderr only: on stdio, stdout belongs to the protocol.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.agents.news_filter_agent import NewsFilterAgent
from src.agents.summarizer_agent import SummarizerAgent
from src.agents.writer_agent import WriterAgent
from src.database.db_manager import DatabaseManager
from src.mcp import database_server, hello_server
from src.models.article import Article
from src.skills.search_skill import SearchSkill

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SEED_ARTICLES = [
    {
        "title": "New LLM beats benchmarks",
        "url": "https://example.com/llm",
        "source": "hackernews",
        "published_at": "2026-10-01T10:00:00",
        "summary": "A large language model release.",
        "score": 120,
    },
    {
        "title": "Vision transformers in production",
        "url": "https://example.com/vit",
        "source": "rss",
        "published_at": "2026-10-02T10:00:00",
        "summary": "Computer vision at scale.",
        "score": 80,
    },
    {
        "title": "Rust 2.0 announced",
        "url": "https://example.com/rust",
        "source": "github",
        "published_at": "2026-10-03T10:00:00",
        "summary": "Systems programming news.",
        "score": 50,
    },
]


@pytest.fixture
def db_path(tmp_path, monkeypatch) -> Path:
    """Point every DatabaseManager (and the MCP server) at a temp database."""
    path = tmp_path / "news_agent.db"
    monkeypatch.setenv("NEWS_AGENT_DB", str(path))
    return path


@pytest.fixture
async def seeded_db(db_path) -> DatabaseManager:
    db = DatabaseManager()
    await db.initialize()
    for article in SEED_ARTICLES:
        await db.insert_article(article)
    return db


@pytest.fixture
def llm_env(monkeypatch):
    """A syntactically valid provider config; the LLM itself is always faked."""
    monkeypatch.setenv("LITELLM_MODEL", "gemini/test-model")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")


# --------------------------------------------------------------------------
# Database layer
# --------------------------------------------------------------------------


class TestDatabaseManager:
    async def test_uses_env_var_path(self, db_path):
        assert DatabaseManager().db_path == str(db_path)

    async def test_insert_and_query_newest_first(self, seeded_db):
        rows = await seeded_db.query_articles(limit=10)
        assert [r["title"] for r in rows] == [
            "Rust 2.0 announced",
            "Vision transformers in production",
            "New LLM beats benchmarks",
        ]

    async def test_duplicate_url_is_ignored(self, seeded_db):
        await seeded_db.insert_article({**SEED_ARTICLES[0], "title": "Duplicate"})
        rows = await seeded_db.query_articles(limit=10)
        assert len(rows) == 3
        assert "Duplicate" not in {r["title"] for r in rows}

    async def test_query_filters_by_source_and_limit(self, seeded_db):
        rows = await seeded_db.query_articles(source="rss")
        assert [r["source"] for r in rows] == ["rss"]
        assert len(await seeded_db.query_articles(limit=2)) == 2

    async def test_search_matches_title_summary_and_source(self, seeded_db):
        assert len(await seeded_db.search_articles("LLM")) == 1
        assert len(await seeded_db.search_articles("computer vision")) == 1
        assert len(await seeded_db.search_articles("github")) == 1
        assert await seeded_db.search_articles("quantum") == []

    async def test_get_sources_counts(self, seeded_db):
        await seeded_db.insert_article(
            {**SEED_ARTICLES[0], "url": "https://example.com/llm-2"}
        )
        sources = await seeded_db.get_sources()
        assert sources[0] == {"source": "hackernews", "article_count": 2}
        assert {s["source"] for s in sources} == {"hackernews", "rss", "github"}


# --------------------------------------------------------------------------
# MCP tool handlers (in-process)
# --------------------------------------------------------------------------


class TestDatabaseServerHandlers:
    async def test_lists_three_tools(self):
        tools = await database_server.list_tools()
        assert {t.name for t in tools} == {
            "get_sources",
            "query_articles",
            "search_articles",
        }
        search = next(t for t in tools if t.name == "search_articles")
        assert search.inputSchema["required"] == ["query"]

    async def test_get_sources_returns_json(self, seeded_db):
        [content] = await database_server.call_tool("get_sources", {})
        data = json.loads(content.text)
        assert data["total"] == 3

    async def test_search_articles_returns_json(self, seeded_db):
        [content] = await database_server.call_tool(
            "search_articles", {"query": "transformers", "limit": 5}
        )
        data = json.loads(content.text)
        assert data["total"] == 1
        assert data["articles"][0]["url"] == "https://example.com/vit"

    async def test_query_articles_returns_readable_list(self, seeded_db):
        [content] = await database_server.call_tool(
            "query_articles", {"source": "hackernews"}
        )
        assert content.text == (
            "- [hackernews] New LLM beats benchmarks (https://example.com/llm)"
        )

    async def test_query_articles_on_empty_db(self, db_path):
        [content] = await database_server.call_tool("query_articles", {})
        assert content.text == "No articles found."

    async def test_rejects_empty_query_and_unknown_tool(self, db_path):
        with pytest.raises(ValueError, match="non-empty"):
            await database_server.call_tool("search_articles", {"query": ""})
        with pytest.raises(ValueError, match="Unknown tool"):
            await database_server.call_tool("drop_table", {})


class TestHelloServerHandlers:
    async def test_lists_greet_and_add(self):
        assert {t.name for t in await hello_server.list_tools()} == {"greet", "add"}

    async def test_greet_and_add(self):
        [greeting] = await hello_server.call_tool("greet", {"name": "Alice"})
        assert greeting.text == "Hello, Alice! 👋"
        [total] = await hello_server.call_tool("add", {"a": 5, "b": 3})
        assert total.text == "5 + 3 = 8"


# --------------------------------------------------------------------------
# Real MCP protocol over stdio (spawns server subprocesses)
# --------------------------------------------------------------------------


class TestMcpOverStdio:
    async def test_hello_server_round_trip(self):
        params = StdioServerParameters(
            command=sys.executable,
            args=[str(PROJECT_ROOT / "src" / "mcp" / "hello_server.py")],
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert {t.name for t in tools.tools} == {"greet", "add"}
                result = await session.call_tool("add", {"a": 2, "b": 2})
                assert result.content[0].text == "2 + 2 = 4"
                # Non-ASCII must survive the pipe (Windows defaults to cp1252).
                result = await session.call_tool("greet", {"name": "Zoë"})
                assert result.content[0].text == "Hello, Zoë! 👋"

    async def test_search_skill_finds_articles(self, seeded_db, db_path):
        result = await SearchSkill(db_path=str(db_path)).search("LLM", limit=5)
        assert result["success"], result.get("error")
        assert result["total"] == 1
        assert result["articles"][0]["title"] == "New LLM beats benchmarks"

    async def test_search_skill_handles_unicode_titles(self, seeded_db, db_path):
        await seeded_db.insert_article(
            {
                **SEED_ARTICLES[0],
                "url": "https://example.com/es",
                "title": "Visión por computador — año 2026 🚀",
            }
        )
        result = await SearchSkill(db_path=str(db_path)).search("Visión")
        assert result["success"], result.get("error")
        assert result["articles"][0]["title"] == "Visión por computador — año 2026 🚀"

    async def test_search_skill_surfaces_tool_errors(self, seeded_db, db_path):
        result = await SearchSkill(db_path=str(db_path)).search("", limit=5)
        assert result["success"] is False
        assert "non-empty" in result["error"]
        assert result["articles"] == []


# --------------------------------------------------------------------------
# Agents with a faked LLM
# --------------------------------------------------------------------------

FILTERED_MD = """# Filtered AI/ML Articles

**Total Input:** 3
**Total Output:** 2

---

## New LLM beats benchmarks

**URL:** https://example.com/llm
**Relevance Score:** 9/10
**Reasoning:** Major model release
**Key Topics:** LLMs, Benchmarks

A large language model release.

---

## Vision transformers in production

**URL:** https://example.com/vit
**Relevance Score:** 7/10
**Reasoning:** Applied computer vision
**Key Topics:** Computer Vision

Computer vision at scale.

---
"""


def fake_filter_llm(self, prompt, system=None, max_tokens=None):
    """Judge Rust articles as off-topic, everything else as AI."""
    # Look only at the article's title: the prompt template itself already
    # lists topics such as "Computer Vision".
    title = prompt.split("Title: ", 1)[1].splitlines()[0]
    if "Rust" in title:
        return json.dumps(
            {
                "relevant": False,
                "relevance_score": 2,
                "reasoning": "Systems programming, not AI",
                "key_topics": [],
            }
        )
    topic = "Computer Vision" if "Vision" in title else "LLMs"
    return (
        "```json\n"
        + json.dumps(
            {
                "relevant": True,
                "relevance_score": 9,
                "reasoning": f"Core {topic} news",
                "key_topics": [topic],
            }
        )
        + "\n```"
    )


class TestSummarizerAndWriter:
    async def test_summarizer_groups_by_first_topic(
        self, tmp_path, llm_env, monkeypatch
    ):
        prompts = []

        def fake_llm(self, prompt, system=None, max_tokens=None):
            prompts.append(prompt)
            return f"  Summary #{len(prompts)}  "

        monkeypatch.setattr(SummarizerAgent, "_call_llm", fake_llm)

        source = tmp_path / "filtered.md"
        source.write_text(FILTERED_MD, encoding="utf-8")
        output = tmp_path / "summary.md"

        result = await SummarizerAgent().execute(str(source), str(output))

        assert result["success"]
        text = output.read_text(encoding="utf-8")
        assert "**Total Articles:** 2" in text
        assert "## LLMs (1 articles)" in text
        assert "## Computer Vision (1 articles)" in text
        assert "Summary #1\n" in text  # LLM output is stripped
        assert len(prompts) == 2

    def test_summarizer_parses_relevance_scores(self, llm_env):
        articles = SummarizerAgent()._parse_markdown(FILTERED_MD)
        assert [(a["title"], a["relevance"]) for a in articles] == [
            ("New LLM beats benchmarks", 9),
            ("Vision transformers in production", 7),
        ]

    async def test_writer_wraps_newsletter(self, tmp_path, llm_env, monkeypatch):
        monkeypatch.setattr(
            WriterAgent,
            "_call_llm",
            lambda self, prompt, system=None, max_tokens=None: "Hello readers!",
        )
        source = tmp_path / "summary.md"
        source.write_text("# Summary\n\nLLMs everywhere.", encoding="utf-8")
        output = tmp_path / "out" / "newsletter.md"

        await WriterAgent().execute(str(source), str(output))

        text = output.read_text(encoding="utf-8")
        assert text.startswith("# AI/ML Daily Newsletter - ")
        assert "Hello readers!" in text
        assert text.rstrip().endswith("*Generated by AI Agent Pipeline*")

    async def test_missing_api_key_fails_fast(self, tmp_path, monkeypatch):
        monkeypatch.setenv("LITELLM_MODEL", "gemini/test-model")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            await WriterAgent().execute(str(tmp_path / "x"), str(tmp_path / "y"))


# --------------------------------------------------------------------------
# Complete pipeline, fully offline
# --------------------------------------------------------------------------


async def test_complete_pipeline_end_to_end(tmp_path, monkeypatch, llm_env, db_path):
    from src import complete_pipeline

    # The pipeline writes to relative data/ paths: run it inside tmp_path.
    monkeypatch.chdir(tmp_path)

    fetched = [
        Article(
            title=a["title"],
            url=a["url"],
            published_at=datetime.fromisoformat(a["published_at"]),
            source=a["source"],
            summary=a["summary"],
            score=a["score"],
        )
        for a in SEED_ARTICLES
    ]

    async def fake_fetch_all(self):
        self.storage.save(fetched, "all_articles.md")
        return fetched

    monkeypatch.setattr(
        complete_pipeline.FetchOrchestrator, "fetch_all", fake_fetch_all
    )
    monkeypatch.setattr(NewsFilterAgent, "_call_llm", fake_filter_llm)
    monkeypatch.setattr(
        SummarizerAgent,
        "_call_llm",
        lambda self, prompt, system=None, max_tokens=None: "Topic summary.",
    )
    monkeypatch.setattr(
        WriterAgent,
        "_call_llm",
        lambda self, prompt, system=None, max_tokens=None: "Today in AI...",
    )

    await complete_pipeline.run_complete_pipeline()

    # Step 2: every fetched article reached the database.
    rows = await DatabaseManager().query_articles(limit=100)
    assert {r["url"] for r in rows} == {a["url"] for a in SEED_ARTICLES}

    # Step 3: the off-topic article was filtered out.
    filtered = (tmp_path / "data/context/filtered_articles.md").read_text("utf-8")
    assert "**Total Input:** 3" in filtered
    assert "**Total Output:** 2" in filtered
    assert "Rust 2.0" not in filtered

    # Step 4: one summary section per topic.
    summary = (tmp_path / "data/context/summary.md").read_text("utf-8")
    assert "## LLMs (1 articles)" in summary
    assert "## Computer Vision (1 articles)" in summary

    # Step 5: the newsletter is written.
    newsletter = (tmp_path / "data/output/newsletter.md").read_text("utf-8")
    assert "Today in AI..." in newsletter
