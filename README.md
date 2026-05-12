# Seer

**Structured eyes and hands for AI agents on Windows. No screenshots. No OCR.**

[![License: AGPL-3.0](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)

Seer is an MCP server that gives any AI agent (Claude, ChatGPT, Gemini, local models) the ability to **see and control your Windows desktop and Chrome browser**. Instead of "look at a screenshot and guess," your agent reads a real semantic element tree and acts on exact elements by ID.

```
Agent: get_element_tree(window="Notepad")
→ [{ id: 5, role: "Edit", name: "Text Editor" }, ...]

Agent: type_text(element_id=5, text="Hello from Seer")
→ { success: true }
```

---

## Why this exists

Every existing AI computer-control approach uses **screenshots + vision models**:
- Claude Computer Use
- OpenAI Codex desktop
- Browser-use, OpenClaw

Screenshots are slow (vision tokens add up fast), brittle (one UI redraw breaks the agent), and imprecise (misclicks are constant).

Seer skips the pixels. We read Windows UI Automation (UIA) trees + Chrome DOM directly. **Sub-100ms per query. Element-precise. CSP-safe.**

| | Screenshots (CUA/Codex) | Seer |
|---|---|---|
| Speed | 1-3s per glance | <100ms |
| Reliability | Breaks on UI redraws | Survives them |
| Cost | Vision tokens compound | Tiny text payload |
| Integration | Anthropic/OpenAI only | MCP — works with any agent |
| Browser session | Sandboxed | Your real Chrome, your logins |

---

## What's in the box

**Desktop control (UIA)**
- `get_active_window`, `get_element_tree`, `click`, `double_click`, `type_text`

**Universal fallback (works on any app — Electron, games, anything UIA can't see)**
- `screenshot_window`, `screenshot_full`, `click_at`

**Chrome browser (via the Seer Bridge extension)**
- `browser_navigate`, `browser_click`, `browser_query_click`, `browser_dblclick`, `browser_type`, `browser_select`
- `browser_scroll`, `browser_hover`, `browser_key`
- `get_browser_page` — full DOM tree extraction
- `browser_extract` — CSP-safe data extraction by CSS selector + attribute
- `browser_eval` — arbitrary JS (works on most sites; blocked by strict CSP)

**Spotify** *(bundled convenience tool — uses the Spotify Web API directly, not the desktop app)*
- `spotify_search`, `spotify_play`, `spotify_pause`, `spotify_next`, `spotify_previous`, `spotify_current`, `spotify_play_liked`
- Requires a one-time `python -m seer.spotify.setup` to provide your OAuth credentials. This is a bundled exception to the "Seer is the muscles, install separate MCPs for API-driven services" rule — it shipped early and stayed because it's useful.

**Reliability**
- Resilient element matching survives UI shifts mid-session
- 250 ms auto-settle after every action so the next read sees fresh state
- Confirmation gate on destructive verbs (`delete`, `send`, `submit`, etc.) — agent must re-call with `confirm=true`

---

## Install

### Option A — One-click installer (Windows)

Download the latest `seer-setup-X.Y.Z.exe` from the [releases page](https://github.com/av29nassh-sketch/seer/releases). Run it. Done.

After install:
1. Open `chrome://extensions` (the installer will offer to do this)
2. Enable "Developer mode" (top-right toggle)
3. "Load unpacked" → select `C:\Program Files\Seer\extension` (or your install dir + `\extension`)
4. Copy the extension ID it gives you
5. Right-click the Seer tray icon → "Set extension ID" *(coming soon — for now edit `%LOCALAPPDATA%\Programs\Seer\com.seer.host.json` and put the ID in `allowed_origins`)*

### Option B — From source (developers)

```bash
git clone https://github.com/av29nassh-sketch/seer
cd seer
pip install -e .

# Register the native messaging host (replace EXT_ID with your unpacked extension ID)
python -m seer.browser.install_native_host EXT_ID

# Add to your MCP client (e.g. Claude Code's .mcp.json):
# { "mcpServers": { "seer": { "command": "python", "args": ["-m", "seer"] } } }
```

Restart your MCP client. Tools should appear under the `seer` namespace.

### Requirements
- Windows 10/11
- Python 3.10+ (only if installing from source)
- Chrome (for browser tools)

---

## Even better with…

Seer is the **muscles** — it can touch any window, button, or web page on your computer. But for apps that expose a real API, dedicated MCPs are much faster. Your agent uses the right tool for the job: API shortcuts when available, Seer for everything else.

Drop these alongside Seer in your `.mcp.json` (or your client's equivalent):

| MCP | What it adds | Setup |
|---|---|---|
| **Notion** | Read/write pages, databases | `npx -y mcp-remote https://mcp.notion.com/mcp` — OAuth via browser, no token paste |
| **Filesystem** | File ops scoped to allowlisted dirs | `npx -y @modelcontextprotocol/server-filesystem <dir1> <dir2>` |
| **GitHub** | Repos, issues, PRs | `npx -y @modelcontextprotocol/server-github` — needs a personal access token |
| **Discord** | Read/post in channels | `npx -y @iqai/mcp-discord` — needs a Discord bot token |
| **Slack** | Read/post, channels, users | Bot token via Slack dev portal |

Most users only really need 2-3. Pick the ones for the services you actually use daily. OAuth-style ones (Notion, GitHub remote) are friction-free; bot-token ones are a one-time 5-minute setup.

In 12 months, expect one-click MCP installers in every client. Until then, this is the manual path.

## Architecture

```
┌────────────────┐        stdio          ┌────────────┐
│   AI agent     │  ◄──────────────────► │  seer MCP  │
│ (Claude, etc.) │                       │   server   │
└────────────────┘                       └─────┬──────┘
                                               │
                       ┌───────────────────────┼─────────────────────┐
                       ▼                       ▼                     ▼
              ┌────────────────┐    ┌──────────────────┐    ┌────────────────┐
              │  UI Automation │    │  Native Messaging│    │  Spotify Web   │
              │   (Win32 apps) │    │  bridge ↔ Chrome │    │     API        │
              └────────────────┘    └──────────────────┘    └────────────────┘
```

Each layer is independent. The Chrome bridge uses Native Messaging (no debug flag, no separate browser instance, works with your real session).

---

## Status

**Engine: shipping-ready.** All Phase 1-3 work done (UIA, browser bridge, reliability layer).

**Installer: working.** Single .exe bundles everything.

**Pre-launch:** Chrome Web Store submission, demo videos.

📖 **[Read: How to Build Jarvis (For Real This Time)](docs/jarvis-handbook.md)** — the actual end-to-end guide to building a real personal AI assistant using Seer + commodity components. Five thousand words, working code for every layer.

---

## License

AGPL-3.0. Commercial license available — contact **avii29gemini@gmail.com**.

If you build a personal AI assistant on top of Seer, you're not required to open-source your assistant — only changes to Seer itself.

---

## Security

Seer can see and control everything on your computer. Take that seriously.

- **Localhost-only**: bridge binds to `127.0.0.1`, never `0.0.0.0`
- **Token auth**: TCP bridge requires a shared secret stored in `~/.seer/token`
- **Confirmation gate**: destructive verbs trigger an agent-mediated user confirmation
- **No telemetry**: nothing leaves your machine

See [SECURITY.md](SECURITY.md) for the full threat model and disclosure process.

---

## Contributing

Issues and PRs welcome. Open a discussion before large changes so we can talk through scope.

