"""Agent that filters AI-relevant articles."""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.agents.base_agent import BaseAgent


class NewsFilterAgent(BaseAgent):
    """Filter articles for AI/ML relevance using an LLM."""

    def __init__(
        self,
        model: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
    ):
        super().__init__(model=model, tools=tools)
        self.relevance_threshold = 6

    async def _load_context(
        self,
        input_path: str,
    ) -> Dict[str, Any]:
        """Load articles from a markdown file."""
        print(f"📖 Loading articles from {input_path}")

        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        content = path.read_text(encoding="utf-8")
        articles = self._parse_markdown(content)

        print(f"   Found {len(articles)} articles")
        return {"articles": articles}

    def _parse_markdown(
        self,
        content: str,
    ) -> List[Dict]:
        """Extract articles from markdown."""
        articles = []
        sections = content.split("---")

        for section in sections:
            title_match = re.search(
                r"^##\s+(.+)$",
                section,
                re.MULTILINE,
            )
            if not title_match:
                continue

            title = title_match.group(1).strip()

            url_match = re.search(
                r"\*\*URL:\*\*\s*(.+)",
                section,
            )
            url = url_match.group(1).strip() if url_match else ""

            lines = [
                line.strip()
                for line in section.splitlines()
                if line.strip()
                and not line.strip().startswith("**")
                and not line.strip().startswith("##")
            ]
            summary = lines[-1] if lines else ""

            articles.append(
                {
                    "title": title,
                    "url": url,
                    "summary": summary,
                }
            )

        return articles

    async def _process(
        self,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate articles and keep relevant ones."""
        articles = context["articles"]
        print(f"🔍 Filtering {len(articles)} articles...")

        filtered = []

        for index, article in enumerate(articles, start=1):
            print(f"   [{index}/{len(articles)}] " f"{article['title'][:50]}...")

            judgment = self._judge_relevance(article)

            # A score of 0 means the article could not be evaluated.
            # Stop instead of reporting it as "not relevant".
            if judgment.get("relevance_score") == 0:
                raise RuntimeError(
                    f"No se pudo evaluar '{article['title']}': "
                    f"{judgment.get('reasoning', 'error desconocido')}"
                )

            relevant = judgment.get("relevant", False)
            relevance_score = judgment["relevance_score"]

            if relevant and relevance_score >= self.relevance_threshold:
                filtered.append(
                    {
                        **article,
                        "relevance_score": relevance_score,
                        "reasoning": judgment.get("reasoning", ""),
                        "key_topics": judgment.get("key_topics", []),
                    }
                )
                print(f"      ✅ Relevant " f"(score: {relevance_score})")
            else:
                print(f"      ❌ Not relevant " f"(score: {relevance_score})")

        print(f"\n📊 Filtered: " f"{len(filtered)}/{len(articles)} articles")

        return {
            "filtered_articles": filtered,
            "total_input": len(articles),
            "total_output": len(filtered),
        }

    def _judge_relevance(
        self,
        article: Dict,
    ) -> Dict:
        """Ask the LLM whether an article is relevant."""
        prompt = f"""
You are an expert AI/ML news analyst.

Judge whether this article is relevant to AI/ML.

Article:
Title: {article["title"]}
Summary: {article["summary"]}

Relevant topics include:
- Machine Learning
- Large Language Models
- Neural Networks
- Computer Vision
- Natural Language Processing
- AI Research
- AI Applications
- Deep Learning
- Transformers
- GPT
- Stable Diffusion
- AI Ethics
- AI Safety

Output ONLY valid JSON using this exact structure:

{{
    "relevant": true,
    "relevance_score": 1,
    "reasoning": "brief explanation",
    "key_topics": ["topic1", "topic2"]
}}

The relevance_score must be an integer from 1 to 10.

Example relevant article:

Title: "GPT-4 Released"

Response:

{{
    "relevant": true,
    "relevance_score": 10,
    "reasoning": "Major LLM release",
    "key_topics": ["LLM", "GPT"]
}}

Example non-relevant article:

Title: "New JavaScript Framework"

Response:

{{
    "relevant": false,
    "relevance_score": 1,
    "reasoning": "Web development topic, not AI",
    "key_topics": []
}}

Return only the JSON object.
"""

        try:
            response = self._call_llm(prompt)

            if not response:
                raise ValueError("LLM returned an empty response")

            json_text = response.strip()

            if "```json" in json_text:
                json_text = json_text.split("```json", 1)[1].split("```", 1)[0]
            elif "```" in json_text:
                json_text = json_text.split("```", 1)[1].split("```", 1)[0]

            judgment = json.loads(json_text.strip())

            for field in (
                "relevant",
                "relevance_score",
                "reasoning",
            ):
                if field not in judgment:
                    raise ValueError(f"Missing required field: {field}")

            if not isinstance(judgment["relevant"], bool):
                raise ValueError("relevant must be a boolean")

            score = judgment["relevance_score"]
            if isinstance(score, bool) or not isinstance(score, int):
                raise ValueError("relevance_score must be an integer")

            if not 1 <= score <= 10:
                raise ValueError("relevance_score must be between 1 and 10")

            judgment.setdefault("key_topics", [])
            return judgment

        except Exception as exc:
            print(f"      ⚠️ Failed to judge article: {exc}")
            return {
                "relevant": False,
                "relevance_score": 0,
                "reasoning": f"Failed to judge: {exc}",
                "key_topics": [],
            }

    async def _save_result(
        self,
        result: Dict[str, Any],
        output_path: str,
    ) -> None:
        """Save filtered articles to markdown."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        articles = result["filtered_articles"]
        total_input = result["total_input"]
        total_output = result["total_output"]

        if total_input > 0:
            filter_rate = total_output / total_input * 100
        else:
            filter_rate = 0.0

        with path.open("w", encoding="utf-8") as file:
            file.write("# Filtered AI/ML Articles\n\n")
            file.write(f"**Total Input:** {total_input}\n")
            file.write(f"**Total Output:** {total_output}\n")
            file.write(f"**Filter Rate:** {filter_rate:.1f}%\n\n")
            file.write("---\n\n")

            for article in articles:
                file.write(f"## {article['title']}\n\n")
                file.write(f"**URL:** {article['url']}\n")
                file.write("**Relevance Score:** " f"{article['relevance_score']}/10\n")
                file.write("**Reasoning:** " f"{article['reasoning']}\n")

                key_topics = ", ".join(article.get("key_topics", []))
                file.write(f"**Key Topics:** {key_topics}\n\n")
                file.write(f"{article['summary']}\n\n")
                file.write("---\n\n")

        print(f"💾 Saved {len(articles)} filtered " f"articles to {path}")
