"""Tests for HackerNews fetcher."""

import pytest

from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.models.article import Article
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


@pytest.mark.asyncio
async def test_fetch_returns_articles():
    """Test that fetch returns list of articles."""
    # Create dependencies
    transformer = ArticleTransformer()
    storage = MarkdownStorage("data/articles")

    # Create fetcher with DIP
    fetcher = HackerNewsFetcher(transformer, storage)
    articles = await fetcher.fetch_articles()

    # Should get some articles
    assert len(articles) > 0

    # Each should be an Article
    for article in articles:
        assert isinstance(article, Article)
        assert article.title
        assert article.url
        assert article.source == "hackernews"


@pytest.mark.asyncio
async def test_fetch_concurrent():
    """Test that fetch is fast (concurrent)."""
    import time

    # Create dependencies
    transformer = ArticleTransformer()
    storage = MarkdownStorage("data/articles")

    fetcher = HackerNewsFetcher(transformer, storage)

    start = time.time()
    articles = await fetcher.fetch_articles()
    elapsed = time.time() - start

    # Should be faster than sequential (< 10 seconds for 30 articles)
    assert elapsed < 10.0
    assert len(articles) > 0

    print(f"⚡ Fetched {len(articles)} articles in {elapsed:.2f}s")
