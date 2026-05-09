"""Seer MCP server — gives AI agents structured vision + control over Windows desktop and browser."""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from .uia.tree import get_active_window_tree
from .uia.actions import click_element, type_into_element
from .browser import bridge

app = Server("seer")


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ── Desktop tools ──────────────────────────────────────────────
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
                "Returns a filtered, numbered element tree for the active native window. "
                "Each element has an id, name, role, and optional value. "
                "Use the ids from this tree with click or type_text."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="click",
            description="Click a native UI element by its id from get_element_tree.",
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
                "Type text into a native UI element by its id from get_element_tree."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "element_id": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["element_id", "text"],
            },
        ),
        # ── Browser tools ──────────────────────────────────────────────
        types.Tool(
            name="get_browser_page",
            description=(
                "Returns the URL, title, and a filtered node tree of the active Chrome tab. "
                "Each node has an id, tag, text, and optional href/placeholder/value. "
                "Requires the Seer Bridge Chrome extension to be installed and Chrome open."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="browser_click",
            description=(
                "Click an element on the active Chrome tab by its node id from get_browser_page."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {
                        "type": "integer",
                        "description": "The id field from get_browser_page nodes",
                    }
                },
                "required": ["node_id"],
            },
        ),
        types.Tool(
            name="browser_type",
            description=(
                "Type text into an input or textarea on the active Chrome tab by its node id from get_browser_page."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["node_id", "text"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    import json
    import asyncio

    if name == "get_active_window":
        tree = get_active_window_tree()
        result = {"window_title": tree.get("window_title", ""), "window_class": tree.get("window_class", "")}
        if "error" in tree:
            result = {"error": tree["error"]}

    elif name == "get_element_tree":
        result = get_active_window_tree()

    elif name == "click":
        element_id = arguments.get("element_id")
        result = click_element(int(element_id)) if element_id is not None else {"error": "element_id required"}

    elif name == "type_text":
        element_id = arguments.get("element_id")
        text = arguments.get("text", "")
        result = type_into_element(int(element_id), text) if element_id is not None else {"error": "element_id required"}

    elif name == "get_browser_page":
        result = await asyncio.get_event_loop().run_in_executor(
            None, bridge.send_command, {"type": "GET_DOM"}
        )
        if result.get("ok"):
            result = result.get("data", result)

    elif name == "browser_click":
        node_id = arguments.get("node_id")
        if node_id is None:
            result = {"error": "node_id required"}
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, bridge.send_command, {"type": "CLICK", "nodeId": int(node_id)}
            )

    elif name == "browser_type":
        node_id = arguments.get("node_id")
        text = arguments.get("text", "")
        if node_id is None:
            result = {"error": "node_id required"}
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, bridge.send_command, {"type": "TYPE", "nodeId": int(node_id), "text": text}
            )

    else:
        result = {"error": f"Unknown tool: {name}"}

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def _run() -> None:
    bridge.start()  # start HTTP bridge for Chrome extension
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main() -> None:
    import asyncio
    asyncio.run(_run())


if __name__ == "__main__":
    main()
