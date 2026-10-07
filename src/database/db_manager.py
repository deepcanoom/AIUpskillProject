"""SQLite database manager for articles."""

import os
import sqlite3
import sys
import aiosqlite
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Env var that overrides the default database location. The MCP server runs
# in a separate process, so this is how SearchSkill (and tests) point it at
# a specific database file.
DB_PATH_ENV_VAR = "NEWS_AGENT_DB"
DEFAULT_DB_PATH = "data/news_agent.db"


class DatabaseManager:
    """Manages SQLite database for articles."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv(DB_PATH_ENV_VAR, DEFAULT_DB_PATH)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    source TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    summary TEXT,
                    score INTEGER DEFAULT 0,
                    relevance_score INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_source ON articles(source)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_published ON articles(published_at)
            """)

            await db.commit()

        # stderr, not stdout: the MCP database server calls this, and on the
        # stdio transport stdout is the JSON-RPC channel — a stray print
        # there corrupts the protocol stream.
        print(f"Database initialized: {self.db_path}", file=sys.stderr)

    async def insert_article(self, article: Dict):
        """Insert article into database."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    """
                    INSERT INTO articles 
                    (title, url, source, published_at, summary, score, relevance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        article["title"],
                        article["url"],
                        article["source"],
                        article["published_at"],
                        article.get("summary", ""),
                        article.get("score", 0),
                        article.get("relevance_score", 0),
                    ),
                )
                await db.commit()
            except sqlite3.IntegrityError:
                # URL already exists, skip
                pass

    async def query_articles(self, source: str = None, limit: int = 50) -> List[Dict]:
        """Query articles from database."""
        query = "SELECT * FROM articles"
        params = []

        if source:
            query += " WHERE source = ?"
            params.append(source)

        query += " ORDER BY published_at DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def search_articles(self, query: str, limit: int = 10) -> List[Dict]:
        """Search articles by keyword in title, summary or source."""
        query_sql = """
            SELECT * FROM articles
            WHERE title LIKE ? OR summary LIKE ? OR source LIKE ?
            ORDER BY published_at DESC
            LIMIT ?
        """
        pattern = f"%{query}%"
        params = (pattern, pattern, pattern, limit)

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            async with db.execute(query_sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_sources(self) -> List[Dict]:
        """Return each source with its article count.

        Backs the `get_sources` MCP tool exposed by the database server.
        """
        query = """
            SELECT source, COUNT(*) AS article_count
            FROM articles
            GROUP BY source
            ORDER BY article_count DESC, source ASC
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]


# Test it
async def test_db():
    """Test database."""
    db = DatabaseManager()
    await db.initialize()

    # Insert test article
    await db.insert_article(
        {
            "title": "Test Article",
            "url": "https://test.com/article1",
            "source": "test",
            "published_at": datetime.now().isoformat(),
            "summary": "Test summary",
        }
    )

    # Query
    articles = await db.query_articles(limit=10)
    print(f"✅ Found {len(articles)} articles")
    for article in articles:
        print(f"  - {article['title']}")


if __name__ == "__main__":
    import sys
    import asyncio

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(test_db())
