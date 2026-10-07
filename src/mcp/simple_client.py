"""Simple MCP client for testing."""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_hello_server():
    """Test hello world MCP server."""
    print("🔌 Connecting to hello-world server...")

    # Server parameters
    # Same interpreter + absolute script path: works from any directory.
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).resolve().parent / "hello_server.py")],
    )

    # Connect to server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"\n📋 Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Call greet tool
            print(f"\n🔧 Calling 'greet' tool...")
            result = await session.call_tool("greet", {"name": "Alice"})
            print(f"   Result: {result.content[0].text}")

            # Call add tool
            print(f"\n🔧 Calling 'add' tool...")
            result = await session.call_tool("add", {"a": 5, "b": 3})
            print(f"   Result: {result.content[0].text}")

            print("\n✅ MCP communication working!")


if __name__ == "__main__":
    # Windows console (cp1252) can't encode emojis in print output
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(test_hello_server())
