"""Fetch top stories from the Hacker News API."""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional

import aiohttp

from src.models.article import Article
from src.storage.markdown_storage import MarkdownStorage
from src.utils.rate_limiter import RateLimiter


class HackerNewsFetcher:
    """
    Fetches top stories from the Hacker News API.

    API docs: https://github.com/HackerNews/API
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self) -> None:
        self.storage = MarkdownStorage()
        self.rate_limiter = RateLimiter(max_concurrent=10)

    async def fetch(self, limit: int = 30) -> List[Article]:
        """
        Fetch top stories from Hacker News.

        Args:
            limit: Number of stories to fetch.

        Returns:
            List of Article objects.
        """
        if limit <= 0:
            raise ValueError("limit must be greater than zero")

        print(f"📰 Fetching {limit} stories from Hacker News...")

        timeout = aiohttp.ClientTimeout(total=30)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            story_ids = await self._fetch_top_story_ids(session)
            articles = await self._fetch_stories(
                session,
                story_ids[:limit],
            )

        print(f"✅ Fetched {len(articles)} Hacker News stories")
        return articles

    async def fetch_and_save(self, limit: int = 30) -> List[Article]:
        """Fetch articles and save them to a Markdown file."""
        articles = await self.fetch(limit)

        if articles:
            self.storage.save(
                articles,
                "hackernews_articles.md",
            )

        return articles

    async def _fetch_top_story_ids(
        self,
        session: aiohttp.ClientSession,
    ) -> List[int]:
        """Fetch the list of top-story IDs."""
        url = f"{self.BASE_URL}/topstories.json"

        async with session.get(url) as response:
            response.raise_for_status()
            story_ids = await response.json()

        if not isinstance(story_ids, list):
            raise ValueError("Hacker News returned an invalid story list")

        return story_ids

    async def _fetch_stories(
        self,
        session: aiohttp.ClientSession,
        story_ids: List[int],
    ) -> List[Article]:
        """Fetch multiple stories concurrently."""
        tasks = [self._fetch_story(session, story_id) for story_id in story_ids]

        stories = await asyncio.gather(*tasks)
        return [story for story in stories if story is not None]

    async def _fetch_story(
        self,
        session: aiohttp.ClientSession,
        story_id: int,
    ) -> Optional[Article]:
        """Fetch a single story by its ID with rate limiting."""
        url = f"{self.BASE_URL}/item/{story_id}.json"

        try:
            # Envolvemos la llamada protegida con el rate limiter
            async with self.rate_limiter:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()

            if not data or data.get("deleted") or data.get("dead"):
                return None

            # Ask HN stories and some other items might not have an external URL.
            if not data.get("url"):
                return None

            return Article(
                title=data.get("title", "No Title"),
                url=data["url"],
                published_at=datetime.fromtimestamp(
                    data.get("time", 0),
                    tz=timezone.utc,
                ),
                source="hackernews",
                summary=data.get("text", "")[:200],
                score=data.get("score", 0),
            )

        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as error:
            print(f"⚠️ Failed to fetch story {story_id}: {error}")
            return None


async def test_fetch() -> List[Article]:
    """Run a quick test of the fetcher."""
    fetcher = HackerNewsFetcher()
    articles = await fetcher.fetch(limit=5)

    print("\n📊 Results:")

    for article in articles:
        print(f"  - {article.title[:50]}...")

    return articles


if __name__ == "__main__":
    asyncio.run(test_fetch())
