# test_github_manual.py
import asyncio
from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.transformers.article_transformer import ArticleTransformer
from src.storage.markdown_storage import MarkdownStorage

async def test_github():
    transformer = ArticleTransformer()
    storage = MarkdownStorage("data/articles") # O la ruta de almacenamiento configurada

    fetcher = GitHubTrendingFetcher(
        transformer=transformer, 
        storage=storage
    )
    articles = await fetcher.fetch_and_save()

    print(f"✅ Fetched {len(articles)} trending repos!")
    if articles:
        print(f"First: {articles[0].title}")

if __name__ == "__main__":
    asyncio.run(test_github())