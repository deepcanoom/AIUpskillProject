# tests/test_fetchers_integration.py
"""Integration tests for multiple fetchers."""

import pytest

from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


@pytest.mark.asyncio
async def test_both_fetchers():
    """Test both fetchers work."""
    # Create dependencies
    transformer = ArticleTransformer()
    storage = MarkdownStorage("data/articles")

    # HackerNews
    hn = HackerNewsFetcher(transformer, storage)
    hn_articles = await hn.fetch_articles()
    assert len(hn_articles) > 0

    # RSS
    rss = RSSFetcher("https://hnrss.org/frontpage", transformer, storage)
    rss_articles = await rss.fetch_articles()
    assert len(rss_articles) > 0

    print(f"✅ HN: {len(hn_articles)} articles")
    print(f"✅ RSS: {len(rss_articles)} articles")


@pytest.mark.asyncio
async def test_concurrent_fetching():
    """Test fetching from both sources concurrently."""
    import asyncio
    import time

    # Create dependencies
    transformer = ArticleTransformer()
    storage = MarkdownStorage("data/articles")

    hn = HackerNewsFetcher(transformer, storage)
    rss = RSSFetcher("https://hnrss.org/frontpage", transformer, storage)

    start = time.time()

    # Fetch both at same time!
    hn_articles, rss_articles = await asyncio.gather(
        hn.fetch_articles(), rss.fetch_articles()
    )

    elapsed = time.time() - start

    total = len(hn_articles) + len(rss_articles)
    print(f"⚡ Fetched {total} articles in {elapsed:.2f}s")

    assert elapsed < 15.0  # Should be fast with concurrent

