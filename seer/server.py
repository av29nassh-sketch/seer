"""Seer MCP server — gives AI agents structured vision + control over Windows desktop and browser."""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from .uia.tree import get_active_window_tree
from .uia.actions import click_element, double_click_element, type_into_element, click_at_coords
from .uia.screenshot import capture_active_window, capture_screen
from .browser import bridge
from .browser import cdp
from .spotify import client as spotify

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
                "Returns a filtered, numbered element tree for the active native window, "
                "or a specific window by title. Pass window='Spotify' to read Spotify even "
                "when it's not in focus. Each element has an id, name, role, and optional value. "
                "Use the ids from this tree with click or type_text."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "window": {
                        "type": "string",
                        "description": "Partial window title to target (e.g. 'Spotify'). Omit to use foreground window.",
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="click",
            description=(
                "Click a native UI element by its id from get_element_tree. Pass window= to target a background window. "
                "If the element name looks destructive (Delete, Send, etc.) you'll get needs_confirmation back — ask the user, then call again with confirm=true."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "element_id": {
                        "type": "integer",
                        "description": "The id field from get_element_tree output",
                    },
                    "window": {"type": "string", "description": "Partial window title (optional)"},
                    "confirm": {"type": "boolean", "description": "Set true to bypass destructive-action gate after user approval"},
                },
                "required": ["element_id"],
            },
        ),
        types.Tool(
            name="click_at",
            description=(
                "Click at absolute screen coordinates (x, y). Universal fallback when UIA can't find the element — "
                "typically used after screenshot_window when the agent has visually located the target."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Absolute screen X coordinate"},
                    "y": {"type": "integer", "description": "Absolute screen Y coordinate"},
                    "double": {"type": "boolean", "description": "Set true for double-click", "default": False},
                },
                "required": ["x", "y"],
            },
        ),
        types.Tool(
            name="screenshot_window",
            description=(
                "Capture the foreground window as a base64 PNG. Universal fallback for Electron apps "
                "(VS Code, Slack, Discord, Notion) and any UI UIA can't see. Returns bbox so you can compute click coords."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="screenshot_full",
            description="Capture the entire primary screen as a base64 PNG. Use when you need to see across multiple windows.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="double_click",
            description="Double-click a native UI element by its id from get_element_tree. Use for list items that require double-click to activate (e.g. Spotify tracks). Pass window= to target a background window.",
            inputSchema={
                "type": "object",
                "properties": {
                    "element_id": {
                        "type": "integer",
                        "description": "The id field from get_element_tree output",
                    },
                    "window": {"type": "string", "description": "Partial window title (optional)"},
                },
                "required": ["element_id"],
            },
        ),
        types.Tool(
            name="type_text",
            description=(
                "Type text into a native UI element by its id from get_element_tree. Pass window= to target a background window."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "element_id": {"type": "integer"},
                    "text": {"type": "string"},
                    "window": {"type": "string", "description": "Partial window title (optional)"},
                },
                "required": ["element_id", "text"],
            },
        ),
        # ── Browser tools ──────────────────────────────────────────────
        types.Tool(
            name="browser_query_click",
            description=(
                "Click all elements matching a CSS selector on the active Chrome tab. "
                "Use for closing dialogs, clicking buttons by aria-label, etc."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector to match elements"}
                },
                "required": ["selector"],
            },
        ),
        types.Tool(
            name="browser_dblclick",
            description=(
                "Double-click the first element matching a CSS selector on the active Chrome tab. "
                "Required for Spotify track rows and other double-click interactions."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector for the element to double-click"}
                },
                "required": ["selector"],
            },
        ),
        types.Tool(
            name="browser_eval",
            description=(
                "Execute arbitrary JavaScript in the active Chrome tab. Note: blocked by CSP on strict sites "
                "(GitHub, HN, banks). Prefer browser_extract for data extraction — it works everywhere."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "JavaScript expression or statement to evaluate"}
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="browser_extract",
            description=(
                "Extract a property from elements matching a CSS selector. CSP-safe — works on every site, "
                "including GitHub, HN, banks. Returns {ok, count, items}. "
                "Use this instead of browser_eval for reading data."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector"},
                    "attribute": {
                        "type": "string",
                        "description": "Property to read (innerText, textContent, href, value, src, id, className, etc.). Defaults to innerText.",
                    },
                    "limit": {"type": "integer", "description": "Max elements to return. Default 50."},
                },
                "required": ["selector"],
            },
        ),
        types.Tool(
            name="browser_scroll",
            description=(
                "Scroll the active Chrome tab. Omit all args to scroll the page to the bottom. "
                "Pass y= to scroll by pixels (positive=down). Pass selector= to scroll an element into view. "
                "Pass selector= + to_bottom=true to scroll a specific container (e.g. a terms div) to its bottom."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "y": {"type": "integer", "description": "Pixels to scroll vertically (positive=down)"},
                    "selector": {"type": "string", "description": "CSS selector of element to scroll into view or scroll to bottom"},
                    "to_bottom": {"type": "boolean", "description": "If true with selector, scrolls that container to its bottom"},
                },
                "required": [],
            },
        ),
        types.Tool(
            name="browser_hover",
            description="Hover over an element on the active Chrome tab by its node id from get_browser_page. Triggers mouseover/mouseenter events for dropdown menus.",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "integer", "description": "The id field from get_browser_page nodes"},
                },
                "required": ["node_id"],
            },
        ),
        types.Tool(
            name="browser_key",
            description=(
                "Press a keyboard key in the active Chrome tab. "
                "Common keys: Enter, Tab, Escape, Space, ArrowDown, ArrowUp, ArrowLeft, ArrowRight, Backspace. "
                "Optionally target a specific element by node_id."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key name e.g. 'Enter', 'Tab', 'Escape'"},
                    "node_id": {"type": "integer", "description": "Optional element to focus before pressing key"},
                },
                "required": ["key"],
            },
        ),
        types.Tool(
            name="browser_select",
            description="Select an option in a <select> dropdown on the active Chrome tab by its node id from get_browser_page.",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_id": {"type": "integer", "description": "The id of the select element from get_browser_page"},
                    "value": {"type": "string", "description": "Option value or visible text to select"},
                },
                "required": ["node_id", "value"],
            },
        ),
        types.Tool(
            name="browser_navigate",
            description=(
                "Open a URL in Chrome and return the page content once loaded. "
                "Handles opening Chrome and focusing the tab automatically — "
                "no manual tab switching required. Use this whenever you need to visit a URL."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Full URL to navigate to"}
                },
                "required": ["url"],
            },
        ),
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
        # ── CDP tools (require Chrome --remote-debugging-port=9222) ───
        types.Tool(
            name="browser_screenshot",
            description=(
                "Capture a screenshot of the active Chrome tab. "
                "Requires Chrome launched with --remote-debugging-port=9222 (use 'Chrome (Debug)' shortcut). "
                "Returns a base64-encoded PNG."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="browser_fill",
            description=(
                "Fill an input field on the active Chrome tab using a CSS selector. "
                "Uses CDP to properly update React/Vue/Angular controlled inputs — "
                "fixes the React state issue where browser_type leaves the Add button disabled. "
                "Requires Chrome launched with --remote-debugging-port=9222."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "CSS selector targeting the input element"},
                    "text": {"type": "string", "description": "Text to fill in"},
                },
                "required": ["selector", "text"],
            },
        ),
        types.Tool(
            name="browser_cdp_eval",
            description=(
                "Run JavaScript in the active Chrome tab via CDP — bypasses Content Security Policy. "
                "Use this instead of browser_eval when the page blocks script injection (e.g. developer.spotify.com). "
                "Requires Chrome launched with --remote-debugging-port=9222."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "JavaScript expression to evaluate"},
                },
                "required": ["code"],
            },
        ),
        # ── Spotify tools ──────────────────────────────────────────────
        types.Tool(
            name="spotify_search",
            description="Search for tracks on Spotify. Returns name, artist, album, and URI for each result.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (song name, artist, etc.)"},
                    "limit": {"type": "integer", "description": "Max results to return (default 5)"},
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="spotify_play",
            description="Play a Spotify track by URI (from spotify_search). Starts playback on the active device.",
            inputSchema={
                "type": "object",
                "properties": {
                    "uri": {"type": "string", "description": "Spotify track URI e.g. spotify:track:xxx"},
                },
                "required": ["uri"],
            },
        ),
        types.Tool(
            name="spotify_play_liked",
            description="Play the user's Liked Songs on Spotify.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="spotify_pause",
            description="Pause Spotify playback.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="spotify_next",
            description="Skip to the next track on Spotify.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="spotify_previous",
            description="Go to the previous track on Spotify.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="spotify_current",
            description="Get the currently playing track on Spotify.",
            inputSchema={"type": "object", "properties": {}, "required": []},
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
        result = get_active_window_tree(window=arguments.get("window"))

    elif name == "click":
        element_id = arguments.get("element_id")
        result = (
            click_element(
                int(element_id),
                window=arguments.get("window"),
                confirm=bool(arguments.get("confirm", False)),
            )
            if element_id is not None
            else {"error": "element_id required"}
        )

    elif name == "click_at":
        x, y = arguments.get("x"), arguments.get("y")
        if x is None or y is None:
            result = {"error": "x and y required"}
        else:
            result = click_at_coords(int(x), int(y), double=bool(arguments.get("double", False)))

    elif name == "screenshot_window":
        result = capture_active_window()

    elif name == "screenshot_full":
        result = capture_screen()

    elif name == "double_click":
        element_id = arguments.get("element_id")
        result = double_click_element(int(element_id), window=arguments.get("window")) if element_id is not None else {"error": "element_id required"}

    elif name == "type_text":
        element_id = arguments.get("element_id")
        text = arguments.get("text", "")
        result = type_into_element(int(element_id), text, window=arguments.get("window")) if element_id is not None else {"error": "element_id required"}

    elif name == "browser_eval":
        code = arguments.get("code", "")
        # Try CDP first (bypasses CSP); fall back to content script
        if await asyncio.get_event_loop().run_in_executor(None, cdp.available):
            result = await asyncio.get_event_loop().run_in_executor(None, cdp.evaluate, code)
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, bridge.send_command, {"type": "EVAL", "code": code}
            )

    elif name == "browser_extract":
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            bridge.send_command,
            {
                "type": "EXTRACT",
                "selector": arguments.get("selector", ""),
                "attribute": arguments.get("attribute", "innerText"),
                "limit": int(arguments.get("limit", 50)),
            },
        )

    elif name == "browser_scroll":
        cmd: dict = {"type": "SCROLL"}
        if "selector" in arguments:
            cmd["selector"] = arguments["selector"]
        if "to_bottom" in arguments:
            cmd["to_bottom"] = arguments["to_bottom"]
        if "y" in arguments:
            cmd["y"] = int(arguments["y"])
        result = await asyncio.get_event_loop().run_in_executor(
            None, bridge.send_command, cmd
        )

    elif name == "browser_hover":
        node_id = arguments.get("node_id")
        if node_id is None:
            result = {"error": "node_id required"}
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, bridge.send_command, {"type": "HOVER", "nodeId": int(node_id)}
            )

    elif name == "browser_key":
        key = arguments.get("key", "")
        kmd: dict = {"type": "KEY", "key": key}
        if "node_id" in arguments:
            kmd["nodeId"] = int(arguments["node_id"])
        result = await asyncio.get_event_loop().run_in_executor(
            None, bridge.send_command, kmd
        )

    elif name == "browser_select":
        node_id = arguments.get("node_id")
        value = arguments.get("value", "")
        if node_id is None:
            result = {"error": "node_id required"}
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, bridge.send_command, {"type": "SELECT", "nodeId": int(node_id), "value": value}
            )

    elif name == "browser_query_click":
        selector = arguments.get("selector", "")
        result = await asyncio.get_event_loop().run_in_executor(
            None, bridge.send_command, {"type": "QUERY_CLICK", "selector": selector}
        )

    elif name == "browser_dblclick":
        selector = arguments.get("selector", "")
        result = await asyncio.get_event_loop().run_in_executor(
            None, bridge.send_command, {"type": "QUERY_DBLCLICK", "selector": selector}
        )

    elif name == "browser_navigate":
        import time
        from urllib.parse import urlparse
        url = arguments.get("url", "")
        parsed = urlparse(url)
        target_domain = parsed.netloc
        target_path = parsed.path.rstrip("/")

        # Ensure Chrome is running. If launching fresh, open the target URL directly
        # so the first tab is the destination (no chrome://newtab/ detour).
        await asyncio.get_event_loop().run_in_executor(
            None, bridge._ensure_chrome_running, 30.0, url
        )

        # If a Chrome session already existed, navigate the existing active tab.
        # If it didn't, the launch above already opened the URL — no NAVIGATE needed.
        ping = await asyncio.get_event_loop().run_in_executor(
            None, bridge.send_command, {"type": "GET_DOM"}
        )
        if ping.get("ok"):
            current_url = ping.get("data", {}).get("url", "")
            if urlparse(current_url).netloc != target_domain:
                await asyncio.get_event_loop().run_in_executor(
                    None, bridge.send_command, {"type": "NAVIGATE", "url": url}
                )
                await asyncio.sleep(2.0)
        else:
            # Active tab is a chrome:// page (or no content script). Open URL as new tab via shell.
            import subprocess
            subprocess.Popen(f'start chrome "{url}"', shell=True)
            await asyncio.sleep(2.0)

        # Retry until the active tab URL matches domain + path. Don't return full DOM — too heavy.
        deadline = time.time() + 12
        result = {"ok": False, "error": "Page did not load within 12 seconds"}
        while time.time() < deadline:
            page = await asyncio.get_event_loop().run_in_executor(
                None, bridge.send_command, {"type": "GET_DOM"}
            )
            if page.get("ok"):
                data = page.get("data", {})
                page_url = data.get("url", "")
                page_parsed = urlparse(page_url)
                if (page_parsed.netloc == target_domain and
                        page_parsed.path.rstrip("/") == target_path):
                    result = {"ok": True, "url": page_url, "title": data.get("title", "")}
                    break
            await asyncio.sleep(0.8)

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

    elif name == "browser_screenshot":
        result = await asyncio.get_event_loop().run_in_executor(None, cdp.screenshot)

    elif name == "browser_fill":
        selector = arguments.get("selector", "")
        text = arguments.get("text", "")
        result = await asyncio.get_event_loop().run_in_executor(
            None, cdp.fill_input, selector, text
        )

    elif name == "browser_cdp_eval":
        code = arguments.get("code", "")
        result = await asyncio.get_event_loop().run_in_executor(None, cdp.evaluate, code)

    elif name == "spotify_search":
        query = arguments.get("query", "")
        limit = int(arguments.get("limit", 5))
        result = await asyncio.get_event_loop().run_in_executor(
            None, lambda: spotify.search(query, limit)
        )

    elif name == "spotify_play":
        uri = arguments.get("uri")
        if not uri:
            result = {"error": "uri required"}
        else:
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: spotify.play(uri)
            )

    elif name == "spotify_play_liked":
        def _play_liked():
            user = spotify.get_current_user()
            if "error" in user:
                return user
            user_id = user.get("id")
            if not user_id:
                return {"error": "Could not get Spotify user ID"}
            return spotify.play_context(f"spotify:user:{user_id}:collection")
        result = await asyncio.get_event_loop().run_in_executor(None, _play_liked)

    elif name == "spotify_pause":
        result = await asyncio.get_event_loop().run_in_executor(None, spotify.pause)

    elif name == "spotify_next":
        result = await asyncio.get_event_loop().run_in_executor(None, spotify.next_track)

    elif name == "spotify_previous":
        result = await asyncio.get_event_loop().run_in_executor(None, spotify.previous_track)

    elif name == "spotify_current":
        result = await asyncio.get_event_loop().run_in_executor(None, spotify.get_current)

    else:
        result = {"error": f"Unknown tool: {name}"}

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


async def _run() -> None:
    bridge.start()  # start named pipe server for Chrome extension via native messaging host
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main() -> None:
    import asyncio
    asyncio.run(_run())


if __name__ == "__main__":
    main()
