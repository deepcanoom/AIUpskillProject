# src/main.py

import asyncio

from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.orchestrator import FetchOrchestrator
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


async def main():
    """Main entry point with dependency injection."""

    # 1. Crear las dependencias base
    transformer = ArticleTransformer()
    storage = MarkdownStorage("data/articles")

    # 2. Crear los fetchers inyectándoles el transformador y el almacenamiento
    fetchers = [
        ("HackerNews", HackerNewsFetcher(transformer, storage)),
        ("GitHub Trending", GitHubTrendingFetcher(transformer, storage)),
    ]

    # 3. Inyectar todo en el orquestador
    orchestrator = FetchOrchestrator(
        fetchers=fetchers, storage=storage, transformer=transformer
    )

    # 4. Ejecutar el proceso
    articles = await orchestrator.fetch_all()
    print(f"✅ Fetched {len(articles)} articles total")


if __name__ == "__main__":
    asyncio.run(main())
