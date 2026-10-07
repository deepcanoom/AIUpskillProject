"""Reusable search skill using MCP."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import get_default_environment, stdio_client

# Resolved from this file, not the CWD, so the skill works no matter where
# the pipeline is launched from.
DATABASE_SERVER_SCRIPT = (
    Path(__file__).resolve().parent.parent / "mcp" / "database_server.py"
)


class SearchSkill:
    """
    Reusable skill for searching articles.

    Uses MCP database server to search.
    Demonstrates skill pattern: higher-level abstraction over tools.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: SQLite file the MCP server should read. Defaults to
                     NEWS_AGENT_DB, then data/news_agent.db (resolved against
                     the current directory, as DatabaseManager does).
        """
        db_path = db_path or os.getenv("NEWS_AGENT_DB", "data/news_agent.db")

        # The MCP client only forwards a small allow-list of env vars to the
        # server process, so the DB location must be passed explicitly.
        env = get_default_environment()
        env["NEWS_AGENT_DB"] = str(Path(db_path).resolve())
        env["PYTHONIOENCODING"] = "utf-8"

        # sys.executable (not "python") so the server runs in the same
        # virtualenv as the client, with the same installed packages.
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(DATABASE_SERVER_SCRIPT)],
            env=env,
        )

    async def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for articles.

        Args:
            query: Search query
            limit: Max results

        Returns:
            Dict with results and metadata
        """
        print(f"🔍 SearchSkill: Searching for '{query}'...")

        try:
            # Connect to MCP server
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # Call search tool
                    result = await session.call_tool(
                        "search_articles", {"query": query, "limit": limit}
                    )

            # Inspect the result only after the MCP session has closed: an
            # exception raised inside stdio_client's task group would reach us
            # wrapped in an ExceptionGroup, hiding the server's message.
            text = result.content[0].text

            # Tool errors come back as a result, not an exception.
            if result.isError:
                raise RuntimeError(text)

            # Parse result
            data = json.loads(text)

            print(f"   Found {data['total']} matches")

            return {
                "success": True,
                "query": query,
                "total": data["total"],
                "articles": data["articles"],
            }

        except Exception as e:
            print(f"   ❌ Search failed: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "total": 0,
                "articles": [],
            }


# Test it
async def test_search_skill():
    """Test search skill."""
    skill = SearchSkill()

    result = await skill.search("machine learning", limit=5)

    print(f"\n✅ SearchSkill tested")
    print(f"   Success: {result['success']}")
    print(f"   Total: {result['total']}")
    print(f"   Articles: {len(result['articles'])}")

    if result["articles"]:
        print(f"\n   First result:")
        print(f"   - {result['articles'][0]['title']}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(test_search_skill())
