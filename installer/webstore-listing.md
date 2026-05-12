# Chrome Web Store listing copy

## Name
Seer Bridge

## Category
Developer Tools

## Short description (132 char max)
Lets AI agents read and control the active Chrome tab. Pairs with the local Seer app for native Windows + browser automation.

## Full description

Seer Bridge connects the Chrome browser to AI agents running on your computer through the Seer desktop app. Once installed, any MCP-compatible AI agent (Claude, ChatGPT, Cursor, local models) can read your active tab's DOM and interact with the page — click, type, scroll, extract data — using your real browser session and existing logins.

WHAT IT DOES
- Provides AI agents with structured DOM access to the active Chrome tab
- Executes interactions: click elements, type text, scroll, navigate, extract data
- Works with any MCP-compatible AI agent via the Seer desktop app
- Uses your real Chrome session — your logins, cookies, history

WHAT IT IS NOT
- Not a standalone tool — requires the Seer desktop app installed and running locally (https://github.com/av29nassh-sketch/seer)
- Not a remote-control tool — only works with AI agents running on your machine
- Not data-collecting — nothing leaves your machine

HOW IT WORKS
1. Install the Seer desktop app on Windows
2. Install this extension
3. Your AI agent connects via the Seer MCP server
4. Agent can now see and interact with your browser through structured tools

PERMISSIONS WE REQUEST
- "Read and change all your data on all websites": needed so the agent can read DOM and execute actions on the page you're currently viewing. We only ever read the ACTIVE tab — never silently scan other tabs.
- "Tabs": to know which tab is active when the agent makes a request.
- "Scripting": to run agent-requested JavaScript in the page's main world via Chrome's official scripting API (bypasses some CSP restrictions safely).
- "Native messaging": to talk to the Seer desktop app on your machine.
- "Alarms": to keep the connection to the Seer app warm (Chrome MV3 idles service workers every 30 seconds).

PRIVACY
We don't have a server. We don't collect anything. The extension talks ONLY to the Seer app on your local machine. See https://github.com/av29nassh-sketch/seer/blob/master/PRIVACY.md for full policy.

OPEN SOURCE
Seer is AGPL-3.0 open source. Code: https://github.com/av29nassh-sketch/seer

## Justification text (for Chrome's review form)

**Single purpose:** Provide AI agents (Claude, GPT, etc.) with structured access to the active Chrome tab so they can act on your behalf — read content, click buttons, fill forms — when you're using an MCP-compatible AI agent paired with the Seer desktop app.

**`<all_urls>` host permission:** AI agents need to be able to operate on whichever website the user is currently visiting. The extension only ever interacts with the ACTIVE tab in the currently-focused window, only in response to a request from the locally-running Seer app, which is in turn only invoked by the user's AI agent. The extension does not silently scan, collect, or analyze any other tabs.

**`scripting` permission:** Used to inject AI-agent-requested JavaScript into the page via `chrome.scripting.executeScript` so the agent can extract data or trigger actions on sites with strict CSP. This is Chrome's official, sandboxed scripting API — not eval.

**`nativeMessaging` permission:** The extension's only outbound communication is to the local Seer app via Native Messaging. It never makes network requests.

**`tabs` and `activeTab`:** To identify which tab the user is currently viewing when the AI agent makes a request.

**`alarms`:** Chrome MV3 idles service workers after ~30 seconds of inactivity, which would kill the connection to the Seer app. The alarm fires every 24 seconds to keep the worker warm — it does no other work.

## Promotional images checklist

- [ ] 1280x800 main screenshot (Chrome with the popup open, showing the seer eye icon)
- [ ] 1280x800 screenshot showing an agent action sequence (optional)
- [ ] 440x280 small promo tile
- [ ] 128x128 store icon (already in extension/icons/icon-128.png)
