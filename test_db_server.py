"""Test database MCP server."""
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_database_server():
    """Test database MCP server."""
    print("🔌 Connecting to database server...")

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).resolve().parent / "src" / "mcp" / "database_server.py")],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(f"\n📋 Database tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Get sources
            print(f"\n🔧 Getting sources...")
            result = await session.call_tool("get_sources", {})
            print(f"   {result.content[0].text[:200]}")

            # Query articles
            print(f"\n🔧 Querying articles...")
            result = await session.call_tool("query_articles", {"limit": 5})
            print(f"   {result.content[0].text[:300]}")

            # Search
            print(f"\n🔧 Searching for 'AI'...")
            result = await session.call_tool("search_articles", {
                "query": "AI",
                "limit": 3
            })
            print(f"   {result.content[0].text[:300]}")

            print("\n✅ Database MCP server working!")


if __name__ == "__main__":
    # Windows console (cp1252) can't encode emojis in print output
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(test_database_server())