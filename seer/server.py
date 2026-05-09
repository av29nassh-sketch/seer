"""Seer MCP server — gives AI agents structured vision + control over Windows desktop."""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from .uia.tree import get_active_window_tree
from .uia.actions import click_element, type_into_element

app = Server("seer")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_active_window",
            description=(
                "Returns the title and class of the currently focused window. "
                "Use this first to understand what the user is looking at."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_element_tree",
            description=(
                "Returns a filtered, numbered element tree for the active window. "
                "Each element has an id, name, role, and optional value. "
                "Use the ids from this tree to click or type into elements."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="click",
            description="Click a UI element by its id from get_element_tree.",
            inputSchema={
                "type": "object",
                "properties": {
                    "element_id": {
                        "type": "integer",
                        "description": "The id field from get_element_tree output",
                    }
                },
                "required": ["element_id"],
            },
        ),
        types.Tool(
            name="type_text",
            description=(
                "Type text into a UI element by its id from get_element_tree. "
                "The element must be an editable text field."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "element_id": {
                        "type": "integer",
                        "description": "The id field from get_element_tree output",
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to type",
                    },
                },
                "required": ["element_id", "text"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    import json

    if name == "get_active_window":
        tree = get_active_window_tree()
        result = {
            "window_title": tree.get("window_title", ""),
            "window_class": tree.get("window_class", ""),
        }
        if "error" in tree:
            result = {"error": tree["error"]}

    elif name == "get_element_tree":
        result = get_active_window_tree()

    elif name == "click":
        element_id = arguments.get("element_id")
        if element_id is None:
            result = {"error": "element_id is required"}
        else:
            result = click_element(int(element_id))

    elif name == "type_text":
        element_id = arguments.get("element_id")
        text = arguments.get("text", "")
        if element_id is None:
            result = {"error": "element_id is required"}
        else:
            result = type_into_element(int(element_id), text)

    else:
        result = {"error": f"Unknown tool: {name}"}

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def _run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main() -> None:
    import asyncio
    asyncio.run(_run())


if __name__ == "__main__":
    main()
