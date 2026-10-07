# tests/test_orchestrator.py
"""Tests for FetchOrchestrator using mocks (DIP in action!)"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.models.article import Article
from src.orchestrator import FetchOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_with_mocks():
    """
    Test orchestrator with mocked dependencies.

    DIP makes this easy - just inject mocks!
    """
    # Create mock fetcher
    mock_fetcher = Mock()
    mock_fetcher.fetch_and_save = AsyncMock(
        return_value=[
            Article(
                title="Test",
                url="http://test.com",
                published_at=datetime.now(),
                source="test",
                summary="Test",
            )
        ]
    )

    # Create mock storage
    mock_storage = Mock()

    # Create mock transformer
    mock_transformer = Mock()

    # Inject mocks into orchestrator
    orchestrator = FetchOrchestrator(
        fetchers=[("TestFetcher", mock_fetcher)],
        storage=mock_storage,
        transformer=mock_transformer,
    )

    # Test
    articles = await orchestrator.fetch_all()

    # Verify
    assert len(articles) == 1
    assert articles[0].title == "Test"
    assert mock_fetcher.fetch_and_save.called
    print("✅ Single mock fetcher works!")


@pytest.mark.asyncio
async def test_multiple_fetchers():
    """Test with multiple mock fetchers."""
    mock_fetcher1 = Mock()
    mock_fetcher1.fetch_and_save = AsyncMock(
        return_value=[
            Article(
                title="Article 1",
                url="http://1.com",
                published_at=datetime.now(),
                source="test",
                summary="Test",
            )
        ]
    )

    mock_fetcher2 = Mock()
    mock_fetcher2.fetch_and_save = AsyncMock(
        return_value=[
            Article(
                title="Article 2",
                url="http://2.com",
                published_at=datetime.now(),
                source="test",
                summary="Test",
            )
        ]
    )

    orchestrator = FetchOrchestrator(
        fetchers=[("Fetcher1", mock_fetcher1), ("Fetcher2", mock_fetcher2)],
        storage=Mock(),
        transformer=Mock(),
    )

    articles = await orchestrator.fetch_all()

    assert len(articles) == 2
    assert articles[0].title == "Article 1"
    assert articles[1].title == "Article 2"
    print("✅ Multiple fetchers work!")


@pytest.mark.asyncio
async def test_orchestrator_handles_fetcher_failure():
    """Test that orchestrator handles fetcher failures gracefully."""
    # Create one working fetcher
    working_fetcher = Mock()
    working_fetcher.fetch_and_save = AsyncMock(
        return_value=[
            Article(
                title="Success",
                url="http://success.com",
                published_at=datetime.now(),
                source="test",
                summary="Success",
            )
        ]
    )

    # Create one failing fetcher
    failing_fetcher = Mock()
    failing_fetcher.fetch_and_save = AsyncMock(side_effect=Exception("Network error"))

    orchestrator = FetchOrchestrator(
        fetchers=[
            ("WorkingFetcher", working_fetcher),
            ("FailingFetcher", failing_fetcher),
        ],
        storage=Mock(),
        transformer=Mock(),
    )

    # Should still get articles from working fetcher
    articles = await orchestrator.fetch_all()

    assert len(articles) == 1
    assert articles[0].title == "Success"
    print("✅ Error handling works!")


@pytest.mark.asyncio
async def test_orchestrator_saves_combined_results():
    """Test that orchestrator saves all articles together."""
    mock_fetcher1 = Mock()
    mock_fetcher1.fetch_and_save = AsyncMock(
        return_value=[
            Article(
                title="Article 1",
                url="http://1.com",
                published_at=datetime.now(),
                source="source1",
                summary="Test",
            )
        ]
    )

    mock_fetcher2 = Mock()
    mock_fetcher2.fetch_and_save = AsyncMock(
        return_value=[
            Article(
                title="Article 2",
                url="http://2.com",
                published_at=datetime.now(),
                source="source2",
                summary="Test",
            )
        ]
    )

    mock_storage = Mock()

    orchestrator = FetchOrchestrator(
        fetchers=[("Fetcher1", mock_fetcher1), ("Fetcher2", mock_fetcher2)],
        storage=mock_storage,
        transformer=Mock(),
    )

    await orchestrator.fetch_all()

    # Verify storage.save was called with combined articles
    assert mock_storage.save.called
    saved_articles = mock_storage.save.call_args[0][0]
    assert len(saved_articles) == 2
    print("✅ Combined save works!")
