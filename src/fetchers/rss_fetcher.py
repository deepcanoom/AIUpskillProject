# src/fetchers/rss_fetcher.py

import asyncio
from typing import List

import aiohttp
import feedparser

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article


class FeedFetchError(Exception):
    """Raised when a feed cannot be retrieved or contains no entries."""


class RSSFetcher(BaseFetcher):
    """Fetch from RSS feed.

    Downloads with aiohttp rather than letting feedparser hit the network
    directly: feedparser.parse(url) is a *blocking* socket call, so calling it
    from an async method stalls the whole event loop (which serialises the
    orchestrator's "concurrent" fetches) and applies no timeout of its own.
    """

    REQUEST_TIMEOUT = 15.0
    MAX_ATTEMPTS = 3
    RETRY_BASE_DELAY = 1.0
    USER_AGENT = (
        "AIUpskillProject/1.0 (+https://github.com/HarwinValero/AIUpskillProject)"
    )

    def __init__(self, feed_url: str, transformer, storage):
        super().__init__(transformer, storage)
        self.feed_url = feed_url

    async def _download(self) -> bytes:
        """Fetch the raw feed body, honouring an explicit timeout."""
        timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                self.feed_url, headers={"User-Agent": self.USER_AGENT}
            ) as response:
                response.raise_for_status()
                return await response.read()

    async def fetch_articles(self) -> List[Article]:
        """Fetch from RSS feed.

        Retries transient failures (timeouts, 429s, 5xx). If every attempt
        fails this raises instead of returning an empty list, so callers can
        tell "the feed is unavailable" apart from "the feed had no articles".
        """
        last_error: Exception | None = None

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                feed = feedparser.parse(await self._download())

                # A malformed feed can still yield usable entries, so only an
                # empty entry list counts as a failure here.
                if not feed.entries:
                    raise FeedFetchError(
                        f"Feed returned no entries (status={feed.get('status')}, "
                        f"bozo={feed.get('bozo')}: {feed.get('bozo_exception')})"
                    )

                return self.transformer.transform_rss(feed.entries)

            except (aiohttp.ClientError, FeedFetchError, asyncio.TimeoutError) as exc:
                last_error = exc
                if attempt < self.MAX_ATTEMPTS:
                    delay = self.RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    # ASCII only: Windows consoles often run cp1252, where a
                    # character like "↻" raises UnicodeEncodeError.
                    print(
                        f"   [rss] attempt {attempt}/{self.MAX_ATTEMPTS} failed "
                        f"({type(exc).__name__}), retrying in {delay:.0f}s"
                    )
                    await asyncio.sleep(delay)

        raise FeedFetchError(
            f"Could not fetch RSS feed {self.feed_url} after "
            f"{self.MAX_ATTEMPTS} attempts: {last_error}"
        ) from last_error

    def get_source_name(self) -> str:
        """Return source name."""
        return "rss"
