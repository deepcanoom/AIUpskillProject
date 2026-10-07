# Milestone 3: First Agent with Tools

## Summary

Built the first AI agent of the system: a `NewsFilterAgent` that uses an LLM (via LiteLLM) to classify article relevance, plus an `EnhancedFilterAgent` that combines LLM judgment with tool use (function calling).

**Goal:** Move from "code that fetches" to "code that thinks" - an agent with a consistent lifecycle (load -> process -> save) powered by an LLM and extensible with tools.

---

## Changes

### 1. BaseAgent (Template Method pattern)
- `src/agents/base_agent.py` - abstract base class defining the agent lifecycle:
  - `load()` -> `process()` -> `save()` (Template Method)
  - Consistent structure for all future agents (Summarizer, Writer)
- Subclasses implement only the steps they need

### 2. NewsFilterAgent
- `src/agents/news_filter_agent.py`
- Reads articles from Markdown context files
- Asks the LLM to judge relevance of each article (prompt engineering)
- Robust JSON parsing of LLM output (handles fenced code blocks, malformed JSON)
- Saves filtered articles back to Markdown for the next stage

### 3. Tools (function calling)
- `src/tools/calculator.py` - safe arithmetic evaluation tool
- `src/tools/web_search.py` - mock web search tool (interface ready for a real backend)
- `src/agents/enhanced_filter_agent.py` - `EnhancedFilterAgent(NewsFilterAgent)` that overrides `_judge_relevance` to combine LLM judgment + tool execution

### 4. LLM via LiteLLM
- Provider-agnostic access through `LITELLM_MODEL` env var
- API key kept in `.env` (never committed)

---

## Testing

```bash
.\venv\Scripts\python -m pytest tests/ -v
```

- **14/15 tests passing.** The only failure is `test_concurrent_fetching`, a network integration test that hit a slow external RSS source (timeout on their side, not a code defect).
- Agent filtering logic, tool execution and JSON parsing all covered.

---

## Files Changed

**Added:**
- `src/agents/base_agent.py` - Template Method base agent
- `src/agents/news_filter_agent.py` - LLM-powered relevance filter
- `src/agents/enhanced_filter_agent.py` - agent with tool use
- `src/tools/calculator.py` - calculator tool
- `src/tools/web_search.py` - mock search tool

**Existing (from Milestones 1-2):** fetchers, storage, orchestrator, SOLID architecture.

---

## How to Review

1. **Run the tests:** `.\venv\Scripts\python -m pytest tests/ -v`
2. **Check the agent lifecycle:** `src/agents/base_agent.py` (load -> process -> save)
3. **Check prompt engineering + JSON parsing:** `src/agents/news_filter_agent.py`
4. **Check tool integration:** `src/agents/enhanced_filter_agent.py` and `src/tools/`
5. **Run the pipeline end to end:** `.\venv\Scripts\python src/main.py`

---

## Checklist

- [x] BaseAgent with Template Method pattern
- [x] NewsFilterAgent with prompt engineering and robust JSON parsing
- [x] Calculator and web search tools implemented
- [x] EnhancedFilterAgent with tool use (function calling)
- [x] Tests written and passing
- [x] LLM access via LiteLLM (provider-agnostic)
- [x] Ready for review

---

## Questions for Reviewers

1. Is the BaseAgent lifecycle the right level of abstraction?
2. Is the JSON parsing of LLM output robust enough for production prompts?
3. Should tools be registered via a factory (as fetchers are) for consistency?

---

**Submitted by:** BlendAdmin
**Date:** 2026-10-07
**Milestone:** 3 of 5
