# Seer · [github.com/av29nassh-sketch/seer](https://github.com/av29nassh-sketch/seer)

Give AI agents structured vision and control over the Windows desktop — no screenshots, no OCR.

Seer is an MCP server that exposes Windows UI Automation (UIA) as tools any AI agent can call. Instead of "look at a screenshot and guess," your agent reads a real semantic element tree and acts on exact elements by ID.

## Works with

- Claude Desktop / Claude Code
- OpenAI Agents (MCP support added Q3 2025)
- Cursor, Windsurf, Zed
- Any MCP-compatible agent client

## Install

```bash
pip install seer
python -c "import seer; import runpy; runpy.run_path('install.py')"
```

Or clone and run directly:

```bash
git clone https://github.com/av29nassh-sketch/seer
cd seer
pip install -e .
python install.py
```

Requires Windows 10/11. Python 3.10+. Restart Claude Code after installing.

## Usage with Claude Code

After running `install.py`, restart Claude Code. Then:

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

Agent: type_text(element_id=1, text="Hello from Seer")
→ { "success": true }
```

## Roadmap

- [ ] Chrome extension for browser DOM/AX tree
- [ ] Electron app fallback (VS Code, Slack, Discord)
- [ ] System tray app with action log
- [ ] One-click installer (.exe)

## License

AGPL-3.0. Commercial license available — contact avii29gemini@gmail.com.
