"""Database MCP server using low-level MCP SDK."""

import asyncio
import sys
from pathlib import Path

# 1. Asegurar que la raíz del proyecto esté en el path (para resolver 'src')
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ListToolsResult, CallToolResult
from src.database.db_manager import DatabaseManager


# 2. Definir los manejadores de herramientas con la firma correcta
async def handle_list_tools(ctx, params) -> ListToolsResult:
    """List available tools for database interaction."""
    return ListToolsResult(
        tools=[
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
                        "limit": {
                            "type": "integer",
                            "description": "Max articles to return",
                        }
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
    )


async def handle_call_tool(ctx, params) -> CallToolResult:
    """Execute database tools."""
    name = params.name
    arguments = params.arguments or {}

    db = DatabaseManager()
    await db.initialize()

    if name == "get_sources":
        sources = await db.get_sources()
        import json as _json

        payload = _json.dumps({"total": len(sources), "sources": sources})
        return CallToolResult(content=[TextContent(type="text", text=payload)])

    elif name == "query_articles":
        limit = arguments.get("limit", 10)
        articles = await db.query_articles(limit=limit)
        # Formatear el resultado como texto legible
        formatted = "\n".join(
            [
                f"- [{a.get('source')}] {a.get('title')} ({a.get('url')})"
                for a in articles
            ]
        )
        return CallToolResult(content=[TextContent(type="text", text=formatted)])

    elif name == "search_articles":
        query = arguments.get("query", "")
        limit = arguments.get("limit", 5)
        articles = await db.search_articles(query, limit=limit)
        import json as _json

        payload = _json.dumps({"total": len(articles), "articles": articles})
        return CallToolResult(content=[TextContent(type="text", text=payload)])

    else:
        raise ValueError(f"Unknown tool: {name}")


# 3. Instanciar el servidor pasando los manejadores en el constructor
server = Server(
    "database-server", on_list_tools=handle_list_tools, on_call_tool=handle_call_tool
)


async def main():
    """Run the server via stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
