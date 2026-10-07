"""Test polymorphic usage of fetchers."""

import pytest
from src.transformers.article_transformer import ArticleTransformer
from src.storage.markdown_storage import MarkdownStorage
from src.fetchers.base_fetcher import BaseFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher


@pytest.mark.asyncio
async def test_polymorphic_usage():
    """Test using fetchers polymorphically."""
    transformer = ArticleTransformer()
    storage = MarkdownStorage("data/test")

    def process_fetcher(fetcher: BaseFetcher):
        """This function accepts ANY fetcher."""
        # Should work with all fetchers
        source = fetcher.get_source_name()
        return source

    # All fetchers work with same function!
    hn = HackerNewsFetcher(transformer, storage)
    assert process_fetcher(hn) == "hackernews"

    gh = GitHubTrendingFetcher(transformer, storage)
    assert process_fetcher(gh) == "github_trending"

    print("✅ Polymorphism works!")
