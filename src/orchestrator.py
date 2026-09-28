"""Orchestrate multiple news fetchers."""

import asyncio
from typing import List, Tuple

from src.fetchers.base_fetcher import BaseFetcher
from src.storage.base_storage import ArticleStorage
from src.transformers.article_transformer import ArticleTransformer
from src.models.article import Article


class FetchOrchestrator:
    """
    Orchestrates fetching from multiple sources.

    Follows Dependency Inversion Principle:
    - Depends on abstractions (BaseFetcher, ArticleStorage)
    - Dependencies injected via constructor
    """

    def __init__(
        self,
        fetchers: List[Tuple[str, BaseFetcher]],
        storage: ArticleStorage,
        transformer: ArticleTransformer,
    ):
        """
        Initialize with injected dependencies.

        Args:
            fetchers: List of tuples containing (name, fetcher_instance)
            storage: Storage implementation (abstractions)
            transformer: Transformer instance
        """
        self.fetchers = fetchers
        self.storage = storage
        self.transformer = transformer

    async def fetch_all(self) -> List[Article]:
        """
        Fetch from all sources concurrently.

        Returns:
            Combined list of all articles
        """
        print("\n🚀 Starting fetch from all sources...")
        print(f"   Sources: {len(self.fetchers)}")

        # Create tasks for all fetchers
        tasks = []
        for name, fetcher in self.fetchers:
            if hasattr(fetcher, "fetch_and_save"):
                task = fetcher.fetch_and_save()
            else:
                task = fetcher.fetch()
            tasks.append(task)

        # Fetch all concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine articles
        all_articles = []
        for (name, _), result in zip(self.fetchers, results):
            if isinstance(result, Exception):
                print(f"⚠️  {name} failed: {result}")
            else:
                print(f"✅ {name}: {len(result)} articles")
                all_articles.extend(result)

        # Save combined results
        if all_articles:
            self.storage.save(all_articles, "all_articles.md")

        print(
            f"\n🎉 Total: {len(all_articles)} articles from {len(self.fetchers)} sources"
        )
        return all_articles
