# AI Upskill Project

**Multi-agent news pipeline with MCP integration.**

An AI agent pipeline that fetches tech news, keeps what is relevant to AI/ML,
summarizes it by topic and writes a daily newsletter. Built milestone by
milestone as part of Blend's AI engineering onboarding curriculum.

## Features

- **Async news fetching** from HackerNews and GitHub Trending (an RSS fetcher
  is also included), with rate limiting and graceful degradation
- **AI-powered filtering** through LiteLLM. Provider-agnostic: change one env
  var to swap models (tested with Gemini and Anthropic Claude)
- **MCP integration**: a database MCP server with 3 tools (`query`, `search`,
  `get_sources`) and a reusable `SearchSkill` client
- **Three-agent pipeline**: Filter -> Summarize -> Write
- **SQLite database** for article storage
- **Evaluation framework**: golden dataset with accuracy, precision, recall
  and F1
- **Tests with pytest**: 15 passing, including substitutability (LSP) tests.
  LLM-backed tests call the real model first and fall back to mocks if the
  provider is unavailable

## Quick start

### Prerequisites

- Python 3.11+
- One LLM provider API key. Any LiteLLM-supported provider works; free
  options include Groq and Gemini

### Installation

```bash
git clone https://github.com/HarwinValero/AIUpskillProject.git
cd AIUpskillProject

python -m venv venv
source venv/bin/activate          # macOS/Linux
# venv\Scripts\activate           # Windows

pip install -r requirements.txt

cp .env.example .env              # then edit .env (see Configuration)
python scripts/verify_setup.py
```

### Configuration

Set these in `.env` (it is git-ignored, never commit keys):

| Variable | Required | Description |
|----------|----------|-------------|
| `LITELLM_MODEL` | yes | Model string, e.g. `gemini/gemini-2.0-flash`, `groq/openai/gpt-oss-120b` or `claude-haiku-4-5-20251001` |
| `<PROVIDER>_API_KEY` | yes | The key matching the model's provider: `GEMINI_API_KEY`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`... |
| `LLM_MIN_INTERVAL` | no | Seconds to wait between LLM calls (default 0). Use it on free tiers with tokens-per-minute limits |
| `LLM_NUM_RETRIES` | no | Retries on transient LLM errors (default 2) |

### Run the complete pipeline

```bash
python -X utf8 -m src.complete_pipeline
```

It fetches articles, stores them in SQLite, filters them with the LLM,
summarizes them by topic and writes the newsletter:

- `data/output/newsletter.md`: final newsletter
- `data/context/`: intermediate outputs (`filtered_articles.md`, `summary.md`)
- `data/articles/`: fetched articles (markdown)
- `data/news_agent.db`: article database

> **Windows:** run Python with `-X utf8` (or set `PYTHONUTF8=1`). The programs
> print emoji and read UTF-8 markdown, which the default Windows console
> encoding cannot handle. Always run modules from the project root with `-m`
> so that `src` is importable.

### Run individual components

```bash
python -X utf8 -m src.main                  # fetch articles only
python -X utf8 -m src.pipeline              # fetch + filter
python -X utf8 -m src.evaluation.evaluator  # evaluate the filter agent
python -X utf8 -m tests.test_enhanced_agent # filter agent with tool use (calculator, mock web_search)

python -X utf8 -m populate_db               # load data/articles/*.md into SQLite
python -X utf8 -m src.mcp.simple_client     # MCP hello world server + client
python -X utf8 -m test_db_server            # try the database MCP server
python -X utf8 -m src.skills.search_skill   # SearchSkill over the database server
```

## Architecture

```
+------------------------------------------+
|  News sources                            |
|  HackerNews | GitHub Trending | RSS      |
+--------------------+---------------------+
                     | async fetchers
                     v
          +---------------------+
          |  FetchOrchestrator  |--> data/articles/*.md
          +----------+----------+
                     |
         +-----------+-----------+
         v                       v
   +-----------+         +---------------+
   |  SQLite   |<--------| Database MCP  |  (query / search / get_sources,
   | articles  |         |    server     |   used through SearchSkill)
   +-----------+         +---------------+
                     |
                     v
          +---------------------+
          |   NewsFilterAgent   |  LLM relevance score per article
          +----------+----------+
                     v
          +---------------------+
          |   SummarizerAgent   |  groups by topic, summarizes
          +----------+----------+
                     v
          +---------------------+
          |    WriterAgent      |  writes the newsletter
          +----------+----------+
                     v
              newsletter.md
```

The database is filled by the pipeline and can be queried through the MCP
server; the three agents exchange data through markdown files in `data/`.

See `docs/design-decisions.md` for the design reasoning and
`docs/architecture/overview.md` for the curriculum orientation.

## Project structure

```
AIUpskillProject/
├── src/
│   ├── agents/          # BaseAgent, NewsFilterAgent, EnhancedFilterAgent, SummarizerAgent, WriterAgent
│   ├── fetchers/        # BaseFetcher, HackerNews, RSS, GitHub Trending
│   ├── factories/       # FetcherFactory
│   ├── strategies/      # rate limiting strategies
│   ├── transformers/    # raw data -> Article
│   ├── storage/         # ArticleStorage interface, MarkdownStorage
│   ├── orchestration/   # FetchOrchestrator
│   ├── database/        # SQLite manager
│   ├── mcp/             # MCP servers and client (hello world, database)
│   ├── skills/          # SearchSkill
│   ├── tools/           # LLM-callable tools (calculator, web_search)
│   ├── evaluation/      # FilterEvaluator
│   ├── models/          # Article
│   ├── main.py          # fetch only
│   ├── pipeline.py      # fetch + filter
│   └── complete_pipeline.py
├── tests/
├── scripts/             # verify_setup.py, examples
├── data/
│   ├── articles/        # fetched articles
│   ├── context/         # agent outputs
│   ├── output/          # final newsletter
│   └── evaluation/      # golden dataset and report
└── docs/
```

## Key technologies

- **Python 3.11+**: async/await throughout
- **aiohttp** and **feedparser**: HTTP and RSS
- **LiteLLM**: LLM provider abstraction
- **MCP (`mcp`)**: Model Context Protocol servers and clients
- **SQLite**: local article database
- **pytest, pytest-asyncio, pytest-cov**: testing
- **ruff**: formatting and linting

## Evaluation

The filter agent is evaluated against a hand-labeled golden dataset
(`data/evaluation/golden_dataset.json`, 10 cases):

```bash
python -X utf8 -m src.evaluation.evaluator   # writes data/evaluation/evaluation_report.md
```

Latest run: **10/10 correct** (accuracy, precision and recall 100%, F1 1.000).
Treat this with care: the dataset is small and easy, and two of its cases are
close to the examples in the agent's prompt. It is a regression check, not a
quality benchmark.

## Running tests

```bash
pytest tests/ -v

# with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

15 tests passing, including substitutability (LSP) and pattern (Factory,
Strategy) tests. The only known flaky one is `test_concurrent_fetching`, a
network integration test that depends on third-party RSS availability.

## Development

### Code style

```bash
ruff format src tests
ruff check src tests
```

### Adding a news source

1. Create a fetcher in `src/fetchers/` that inherits from `BaseFetcher`.
2. Implement `fetch_articles()` and `get_source_name()`. Return an empty list
   on errors instead of raising, so any fetcher can replace another.
3. Register it with `FetcherFactory`, or add an instance to the fetchers list
   you pass to `FetchOrchestrator`.

No existing fetcher needs to change.

## Known limitations

- Free LLM tiers rate-limit by requests and tokens per minute. Use
  `LLM_MIN_INTERVAL` and `LLM_NUM_RETRIES`. If the provider fails, the filter
  reports how many articles it could not judge instead of treating them as
  "not relevant".
- The database is populated by the pipeline but the agents read markdown
  files; `SummarizerAgent` creates a `SearchSkill` that it does not use yet.
- `EnhancedFilterAgent` can call tools (calculator, and a mocked
  `web_search`), but in full runs the model rarely chose to call one.
- The golden dataset is small (10 cases).

## Milestones

| Milestone | What was built |
|-----------|----------------|
| M0 — Setup | Dev environment, API key, verify script |
| M1 — Async News Fetcher | HackerNews and RSS fetchers, orchestrator, rate limiting |
| M2 — SOLID Refactoring | SOLID principles, Factory/Strategy/Template Method, GitHub Trending added without editing existing code |
| M3 — First Agent | NewsFilterAgent via LiteLLM, tool calling |
| M4 — MCP Pipeline | Database MCP server, SearchSkill, three-agent pipeline |
| M5 — Evaluation | Golden dataset, metrics, documentation |

## License

MIT

## About the curriculum

This repository is part of Blend's 5-week AI engineering onboarding
curriculum (about 38-54 hours). Each milestone ends with a PR checkpoint
reviewed by peers. The curriculum overview lives in
`docs/curriculum/overview.md`.

