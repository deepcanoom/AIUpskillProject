"""Complete multi-agent pipeline with MCP."""

import argparse
import sys
from pathlib import Path

# Make 'src' importable when run as a script (python src/complete_pipeline.py)
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import asyncio
from src.orchestrator import FetchOrchestrator
from src.agents.news_filter_agent import NewsFilterAgent
from src.agents.summarizer_agent import SummarizerAgent
from src.agents.writer_agent import WriterAgent
from src.database.db_manager import DatabaseManager
from src.factories.fetcher_factory import FetcherFactory
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


async def run_complete_pipeline(limit: int = 0):
    """
    Run complete pipeline:
    1. Fetch articles (Milestone 1)
    2. Save to database
    3. Filter with AI (Milestone 3)
    4. Summarize (Milestone 4)
    5. Write newsletter (Milestone 4)

    Args:
        limit: Max articles to feed to the AI filter stage (0 = all).
               Useful for a fast smoke test, since the filter makes one
               LLM call per article.
    """
    print("=" * 70)
    print("  Complete AI Agent Pipeline with MCP")
    print("=" * 70)

    # Step 1: Fetch
    print("\n📰 Step 1: Fetching articles from sources...")
    storage = MarkdownStorage("data/articles")
    transformer = ArticleTransformer()

    fetchers = []
    for source_type in FetcherFactory.get_available_types():
        try:
            fetcher = FetcherFactory.create(
                source_type,
                transformer=transformer,
                storage=storage,
                feed_url=(
                    "https://hnrss.org/frontpage" if source_type == "rss" else None
                ),
            )
            fetchers.append((source_type, fetcher))
        except Exception as e:
            print(f"   ⚠️ Skipping {source_type}: {e}")

    orchestrator = FetchOrchestrator(
        fetchers=fetchers,
        storage=storage,
        transformer=transformer,
    )
    articles = await orchestrator.fetch_all()
    fetch_output = Path("data/articles/all_articles.md")
    print(f"✅ Fetched {len(articles)} articles → {fetch_output}")

    # Step 2: Save to database
    print("\n💾 Step 2: Saving to database...")
    db = DatabaseManager()
    await db.initialize()
    for article in articles:
        await db.insert_article(
            {
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "published_at": article.published_at.isoformat(),
                "summary": article.summary,
                "score": getattr(article, "score", 0),
            }
        )
    db_articles = await db.query_articles(limit=1000)
    print(f"✅ Database has {len(db_articles)} articles")

    # Step 3: Filter
    print("\n🤖 Step 3: Filtering with AI agent...")
    # The filter makes one LLM call per article, so `limit` is passed to the
    # agent (it re-parses the markdown file, so slicing here would not help).
    filter_agent = NewsFilterAgent(max_articles=limit or None)
    filter_output = Path("data/context/filtered_articles.md")
    await filter_agent.execute(
        input_path=str(fetch_output), output_path=str(filter_output)
    )
    print(f"✅ Filtered articles → {filter_output}")

    # Step 4: Summarize
    print("\n📝 Step 4: Summarizing with AI agent...")
    summarizer = SummarizerAgent()
    summary_output = Path("data/context/summary.md")
    await summarizer.execute(
        input_path=str(filter_output), output_path=str(summary_output)
    )
    print(f"✅ Summary → {summary_output}")

    # Step 5: Write
    print("\n✍️  Step 5: Writing newsletter...")
    writer = WriterAgent()
    newsletter_output = Path("data/output/newsletter.md")
    await writer.execute(
        input_path=str(summary_output), output_path=str(newsletter_output)
    )
    print(f"✅ Newsletter → {newsletter_output}")

    print("\n" + "=" * 70)
    print("🎉 Complete Pipeline Success!")
    print("=" * 70)
    print(f"\n📊 Pipeline Summary:")
    print(f"   1. Fetched: {len(articles)} articles")
    print(f"   2. Database: {len(db_articles)} total articles")
    print(f"   3. Filtered: {filter_output}")
    print(f"   4. Summarized: {summary_output}")
    print(f"   5. Newsletter: {newsletter_output}")
    print(f"\n📖 Read your newsletter:")
    print(f"   cat {newsletter_output}")
    print("=" * 70)


if __name__ == "__main__":
    # Windows console (cp1252) can't encode emojis in print output;
    # line_buffering=True flushes every print so logs appear instantly
    # even when stdout is piped/redirected.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

    parser = argparse.ArgumentParser(
        description="Run the complete multi-agent AI news pipeline."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help=(
            "Max articles to send to the AI filter stage (0 = all). "
            "The filter makes one LLM call per article, so a small value "
            "gives a much faster smoke test."
        ),
    )
    args = parser.parse_args()

    asyncio.run(run_complete_pipeline(limit=args.limit))
