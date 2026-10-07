"""Base storage interface for articles."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from src.models.article import Article


class ArticleStorage(ABC):
    """
    Abstract base class for article storage.

    Follows Interface Segregation and Dependency Inversion principles.
    Any storage implementation (Markdown, JSON, Database) must implement this.
    """

    @abstractmethod
    def save(self, articles: List[Article], filename: str = None) -> Path:
        """
        Save articles to storage.

        Args:
            articles: List of articles to save
            filename: Optional filename

        Returns:
            Path to saved file/resource
        """
        pass
