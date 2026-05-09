# Eyeva

Give AI agents structured vision and control over the Windows desktop — no screenshots, no OCR.

Eyeva is an MCP server that exposes Windows UI Automation (UIA) as tools any AI agent can call. Instead of "look at a screenshot and guess," your agent reads a real semantic element tree and acts on exact elements by ID.

## Works with

- Claude Desktop / Claude Code
- OpenAI Agents (MCP support added Q3 2025)
- Cursor, Windsurf, Zed
- Any MCP-compatible agent client

## Install

```bash
pip install eyeva
```

Requires Windows 10/11. Python 3.10+.

## Usage with Claude Code

Add to your `.claude/mcp.json` (or Claude Desktop config):

```json
{
  "mcpServers": {
    "eyeva": {
      "command": "eyeva"
    }
  }
}
```

Then in Claude:

```
get the active window, then show me what's clickable
```

## Available tools

| Tool | What it does |
|------|-------------|
| `get_active_window` | Returns the title and class of the focused window |
| `get_element_tree` | Returns a numbered, filtered element tree (name, role, value) |
| `click` | Clicks a UI element by its tree node id |
| `type_text` | Types text into an editable element by its tree node id |

## Example

```
Agent: get_element_tree
→ { "window_title": "Notepad", "tree": [
     { "id": 0, "role": "Window", "name": "Notepad" },
     { "id": 1, "role": "Edit", "name": "Text Editor" },
     ...
   ]}

Agent: type_text(element_id=1, text="Hello from Eyeva")
→ { "success": true }
```

## Roadmap

- [ ] Chrome extension for browser DOM/AX tree
- [ ] Electron app fallback (VS Code, Slack, Discord)
- [ ] System tray app with action log
- [ ] One-click installer (.exe)

## License

AGPL-3.0. Commercial license available — contact avii29gemini@gmail.com.
