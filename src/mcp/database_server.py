"""Database MCP server using the low-level MCP SDK.

Exposes the article database as three MCP tools over the stdio transport:

- ``get_sources``     -> each source with its article count (JSON)
- ``query_articles``  -> most recent articles, optionally per source (text)
- ``search_articles`` -> keyword search in title/summary/source (JSON)

Run it directly (``python src/mcp/database_server.py``) or let an MCP client
such as ``SearchSkill`` spawn it. Set ``NEWS_AGENT_DB`` to point the server at
a database other than ``data/news_agent.db``.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Make the project root importable so 'src' resolves when this file is run
# as a script by an MCP client (python src/mcp/database_server.py).
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from src.database.db_manager import DatabaseManager

server = Server("database-server")


# mcp==1.1.2 registers handlers through decorators. The decorators return the
# original coroutine, so `list_tools()` / `call_tool()` stay directly callable
# from tests without spinning up a subprocess.
@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools for database interaction."""
    return [
        Tool(
            name="get_sources",
            description="Get list of available article sources",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="query_articles",
            description="Query articles from the database with optional limit",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Only return articles from this source",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max articles to return",
                    },
                },
            },
        ),
        Tool(
            name="search_articles",
            description="Search articles by query string",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term"},
                    "limit": {"type": "integer", "description": "Max results"},
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Execute a database tool.

    Raising here is fine: the SDK turns the exception into a
    ``CallToolResult`` with ``isError=True`` instead of killing the server.
    """
    arguments = arguments or {}

    db = DatabaseManager()
    await db.initialize()

    if name == "get_sources":
        sources = await db.get_sources()
        payload = json.dumps({"total": len(sources), "sources": sources})
        return [TextContent(type="text", text=payload)]

    if name == "query_articles":
        limit = arguments.get("limit", 10)
        articles = await db.query_articles(source=arguments.get("source"), limit=limit)
        # Human-readable list: this tool is meant to be read by an LLM.
        formatted = "\n".join(
            f"- [{a.get('source')}] {a.get('title')} ({a.get('url')})" for a in articles
        )
        return [TextContent(type="text", text=formatted or "No articles found.")]

    if name == "search_articles":
        query = arguments.get("query", "")
        if not query:
            raise ValueError("search_articles requires a non-empty 'query'")
        limit = arguments.get("limit", 5)
        articles = await db.search_articles(query, limit=limit)
        payload = json.dumps({"total": len(articles), "articles": articles})
        return [TextContent(type="text", text=payload)]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the server via stdio transport."""
    # mcp 1.1.2 wraps sys.stdin/sys.stdout as they are. On Windows a pipe
    # defaults to cp1252, so any emoji or accented title in a response would
    # crash the writer and leave the client waiting forever.
    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
