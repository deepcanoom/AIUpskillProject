# AI Upskill Project — Project Documentation

**Multi-agent news aggregation system with MCP integration**

An AI agent pipeline that fetches, filters, summarizes, and writes AI/ML news
newsletters.

> **Note on scope.** This document describes the *implemented project*. The
> repository root [`README.md`](../README.md) is the Blend curriculum guide
> (the 5-week arc, PR checkpoints, milestone docs) and is intentionally left
> untouched. Read that one first if you are starting the course.

---

## Features

- **Async News Fetching** from multiple sources (HackerNews, RSS, GitHub Trending)
- **AI-Powered Filtering** via LiteLLM — provider-agnostic, swapped with one env var
- **MCP Integration** with a SQLite-backed database server
- **Multi-Agent Pipeline** (Filter → Summarize → Write)
- **SQLite Database** for article storage
- **Evaluation Framework** with accuracy / precision / recall / F1

---

## Quick Start

### Prerequisites

- Python 3.11+
- One LLM provider API key. Any
  [LiteLLM-supported provider](https://docs.litellm.ai/docs/providers) works —
  this project has been run against Groq, Gemini, and Anthropic.

### Installation

```bash
git clone https://github.com/BLEND360/AIUpskillProject.git
cd AIUpskillProject

python -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate            # Windows

pip install -r requirements.txt

cp .env.example .env
# Edit .env: set LITELLM_MODEL and the matching provider key
```

### Configuring the model

`.env` drives provider selection. Pick **one** `LITELLM_MODEL` line and set the
matching key:

```bash
LITELLM_MODEL=groq/qwen/qwen3.8-27b
GROQ_API_KEY=your-key-here
```

See [`.env.example`](../.env.example) for the Gemini and Anthropic variants.
`src/agents/base_agent.py` maps each provider prefix to the env vars that can
hold its key, and turns provider errors into actionable hints (rate limits,
rejected keys, retired model strings).

### Run the complete pipeline

```bash
python src/complete_pipeline.py

# Fewer articles (useful on free tiers with tight quotas):
python src/complete_pipeline.py --limit 5
```

Outputs:

| Path | Contents |
|------|----------|
| `data/output/newsletter.md` | Final newsletter |
| `data/context/filtered_articles.md` | FilterAgent output |
| `data/context/summary.md` | SummarizerAgent output |
| `data/news_agent.db` | Article database |

### Run individual components

```bash
python -m src.main               # fetch articles only
python src/pipeline.py                  # filter articles with AI
python src/evaluation/evaluator.py      # evaluate filtering quality
python -m scripts.run_evaluation        # evaluation with score-error metrics
```

---

## Architecture

```
┌──────────┐
@@DIAGRAM_START@@
└───────────┬────────────┘
            │
            ▼
        ┌────────────┐
        │ Fetch Orchestrator│
        │  (Milestones 1–2) │
        └──────────┬────────┘
            │
            ▼
            ┌──────────┐
            │ Database │ ← MCP Server
            │ (SQLite) │
            └─────┬────┘
           │
           ▼
        ┌────────────┐
        │    FilterAgent    │
        │   (LLM + Tools)   │
        └──────────┬────────┘
                   │
            ▼
        ┌────────────┐
        │  SummarizerAgent  │
        │  (+ SearchSkill)  │
        └──────────┬────────┘
                   │
            ▼
        ┌────────────┐
        │    WriterAgent    │
        │    (Newsletter)   │
        └──────────┬────────┘
                   │
@@DIAGRAM_END@@
```

Deeper design rationale: [`docs/architecture/overview.md`](architecture/overview.md)
and [`docs/design-decisions.md`](design-decisions.md).

---

## Project Structure

```
AIUpskillProject/
├── src/
│   ├── agents/              # AI agents
│   │   ├── base_agent.py
│   │   ├── news_filter_agent.py
│   │   ├── enhanced_filter_agent.py
│   │   ├── summarizer_agent.py
│   │   └─��� writer_agent.py
│   ├── fetchers/            # News fetchers (HN, RSS, GitHub Trending)
│   ├── factories/           # fetcher_factory.py
│   ├── strategies/          # rate_limit_strategy.py
│   ├── transformers/        # article_transformer.py
│   ├── storage/             # markdown_storage.py + base
│   ├── database/            # db_manager.py (SQLite)
│   ├── mcp/          # MCP servers and client
│   │   ├── database_server.py
│   │   ├── hello_server.py
│   │   └── simple_client.py
│   ├── skills/              # search_skill.py
│   ├── tools/               # LLM-callable tools (calculator, web_search)
│   ├── evaluation/          # Evaluation framework
│   │   └── evaluator.py
│   ├── orchestrator.py      # fetch orchestration
│   ├── pipeline.py
│   └── complete_pipeline.py
├── scripts/
│   ├── verify_setup.py
│   └── run_evaluation.py
├── tests/
├── data/
│   ├── articles/            # Fetched articles
│   ├── context/             # Agent outputs
│   ├── output/              # Final newsletter
│   └── evaluation/          # Golden dataset + reports
└── docs/
```

---

## Key Technologies

- **Python 3.11+** — core language, async/await throughout
- **aiohttp** — concurrent HTTP; **feedparser** — RSS parsing
- **LiteLLM** — LLM provider abstraction
- **MCP (Model Context Protocol)** — tool integration
- **aiosqlite / SQLite** — local database
- **pytest + pytest-asyncio** — testing
- **ruff** — formatting and linting

---

## Evaluation

The framework lives in [`src/evaluation/evaluator.py`](../src/evaluation/evaluator.py)
and ships two evaluators:

- **`FilterEvaluator`** — runs the agent against the golden dataset, applies a
  `relevance_threshold` of 6 (requires `relevant == True` **and** `score >= 6`),
  and writes a Markdown report including the LLM's reasoning per case.
- **`AgentEvaluator`** — the variant used by `scripts/run_evaluation.py`; adds
  `mean_score_error` to measure how far predicted scores drift from expected.

Golden dataset: [`data/evaluation/golden_dataset.json`](../data/evaluation/golden_dataset.json)
— 10 labelled cases (6 relevant, 4 not).

### Measured results

Last run on 2026-10-07 against `groq/qwen/qwen3.8-27b`:

| Metric | Result |
|--------|--------|
| Accuracy | 100.0% |
| Precision | 100.0% |
| Recall | 100.0% |
| F1 Score | 1.000 |
| Correct | 10/10 |
| Mean score error | 0.50 |

Report: [`data/evaluation/evaluation_report.md`](../data/evaluation/evaluation_report.md)

**Interpretation.** A perfect score here reflects an easy dataset more than a
flawless agent: the 10 cases are deliberately well-separated (*"Recipe for
Perfect Pizza Dough"* vs. *"Transformer Architecture Explained"* needs no
nuance). The only observed deviations were in the numeric score, never the
classification — e.g. AI Ethics scored 9 against an expected 7. To get a
meaningful quality signal the dataset needs borderline cases (GPU revenue
reports, SIMD intrinsics for tensor ops, recommendation-latency work), where
the threshold of 6 would actually bite.

### Reproducing

```bash
python src/evaluation/evaluator.py
cat data/evaluation/evaluation_report.md
```

---

## Testing

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=term-missing
```

Current state: **15 tests passing, 23% line coverage** across `src/`. Coverage
is concentrated in the Milestone 1–2 layers (fetchers, orchestrator,
transformers are 74–100%); the agent, MCP, skills, and tools modules are
largely uncovered because they are exercised manually through the pipeline
scripts at the repository root rather than by automated tests.

---

## Milestones

- Milestone 0: Setup
- Milestone 1: Async News Fetcher
- Milestone 2: SOLID Refactoring
- Milestone 3: First Agent with Tools
- Milestone 4: MCP-Powered Pipeline
- Milestone 5: Evaluation & Documentation

Milestone instructions: [`docs/milestones/`](milestones/)

---

## Known issues

- **Non-zero exit code after a successful evaluation.** `python
  src/evaluation/evaluator.py` prints `[OK] Evaluation complete!`, writes the
  report, then exits `1`. This is litellm/httpx cleanup noise as the event loop
  closes, not an evaluation failure. It matters if you chain the command in CI.
- **Pydantic serialization warnings** from litellm on some responses. Benign;
  does not affect results.
- **Console encoding on Windows.** Console output uses ASCII prefixes
  (`[OK]`, `[FAIL]`, `[DATA]`) instead of emoji because the default `cp1252`
  code page raises `UnicodeEncodeError` on them. All file writes pin
  `encoding="utf-8"` for the same reason.
- **`src/mcp_servers/` and `src/orchestration/` are empty packages.** The real
  implementations are `src/mcp/` and `src/orchestrator.py`.
- **`src/models/src/models/article.py`** is a stray nested duplicate of
  `src/models/article.py`; the latter is the one imported.
