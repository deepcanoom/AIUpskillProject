"""Quick workflow test to verify fetchers work."""

import asyncio

from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


async def main():
    """Test the workflow with proper DIP."""
    # Create dependencies
    transformer = ArticleTransformer()
    storage = MarkdownStorage("data/articles")

    # Create fetcher with dependencies
    fetcher = HackerNewsFetcher(transformer, storage)

    # Fetch and save
    articles = await fetcher.fetch_and_save()

    print(f"✅ Done! Fetched and saved {len(articles)} articles")


if __name__ == "__main__":
    asyncio.run(main())