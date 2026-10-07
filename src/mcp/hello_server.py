"""Hello World MCP server using the low-level MCP SDK."""

import asyncio
import sys
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

server = Server("hello-world")

# Some names get a warmer welcome than others.
_KNOWN_GUESTS = {
    "deepcanoom": "Hello, deepcanoom! 🛶 You found the paddle — this server remembers who built it.",
}


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="greet",
            description="Greet someone by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of person to greet",
                    }
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="add",
            description="Add two numbers",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute a tool."""
    arguments = arguments or {}

    if name == "greet":
        person_name = arguments.get("name", "World")
        greeting = _KNOWN_GUESTS.get(
            person_name.strip().lower(), f"Hello, {person_name}! 👋"
        )
        return [TextContent(type="text", text=greeting)]

    if name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        return [TextContent(type="text", text=f"{a} + {b} = {a + b}")]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the server."""
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
