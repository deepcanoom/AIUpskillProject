"""Base fetcher interface and specialized fetcher interfaces."""

from abc import ABC, abstractmethod
from typing import List

from src.models.article import Article
from src.storage.base_storage import ArticleStorage
from src.transformers.article_transformer import ArticleTransformer

class BaseFetcher(ABC):
    """
    Abstract base class for all news fetchers.
    Follows the Dependency Inversion Principle.
    """

    def __init__(self, transformer: ArticleTransformer, storage: ArticleStorage):
        """Initialize with transformer and storage dependencies."""
        self.transformer = transformer
        self.storage = storage

    @abstractmethod
    async def fetch_articles(self) -> List[Article]:
        """Fetch raw articles from the source. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Return the unique name of the source. Must be implemented by subclasses."""
        pass

    async def fetch_and_save(self) -> List[Article]:
        """Template method: fetch, save, and return articles."""
        articles = await self.fetch_articles()
        
        if articles:
            source_name = self.get_source_name()
            self.storage.save(articles, f"{source_name}_articles.md")
            
        return articles


class AuthenticatedFetcher(ABC):
    """Interface for fetchers that require authentication."""

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the source.

        Returns:
            True if authentication successful
        """
        pass


class PaginatedFetcher(ABC):
    """Interface for fetchers that support pagination."""

    @abstractmethod
    async def fetch_page(self, page: int) -> List[Article]:
        """
        Fetch specific page of results.

        Args:
            page: Page number (1-indexed)

        Returns:
            Articles from that page
        """
        pass