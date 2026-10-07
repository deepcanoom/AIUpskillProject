"""Hello World MCP server using low-level MCP SDK constructor handlers."""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ListToolsResult, CallToolResult


# 1. Definir los manejadores con la firma correcta: async (ctx, params) -> result
async def handle_list_tools(ctx, params) -> ListToolsResult:
    """List available tools."""
    return ListToolsResult(
        tools=[
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
    )


async def handle_call_tool(ctx, params) -> CallToolResult:
    """Execute a tool."""
    name = params.name
    arguments = params.arguments or {}

    if name == "greet":
        person_name = arguments.get("name", "World")
        greeting = f"Hello, {person_name}! 👋"
        return CallToolResult(content=[TextContent(type="text", text=greeting)])

    elif name == "add":
        a = arguments.get("a", 0)
        b = arguments.get("b", 0)
        result = a + b
        return CallToolResult(
            content=[TextContent(type="text", text=f"{a} + {b} = {result}")]
        )

    else:
        raise ValueError(f"Unknown tool: {name}")


# 2. Registrar los manejadores directamente en el constructor del Server
server = Server(
    "hello-world", on_list_tools=handle_list_tools, on_call_tool=handle_call_tool
)


async def main():
    """Run the server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
