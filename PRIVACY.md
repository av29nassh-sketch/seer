# Privacy Policy

**Last updated:** 2026-05-12

Seer is a local-only tool. **Nothing leaves your machine.**

## What Seer can access

- **Windows UI elements** — when an AI agent calls Seer's tools, Seer reads the UI Automation tree of the active window (or one you specify by title).
- **The active Chrome tab's DOM** — via the Seer Bridge browser extension, scoped to the tab you're currently viewing.
- **Screen pixels** — only when an agent explicitly calls `screenshot_window` or `screenshot_full`.
- **Your Spotify account** — only if you've completed the optional `seer.spotify.setup` flow and provided OAuth credentials. Credentials are stored locally in `~/.seer/spotify.json` with owner-only permissions.

## What Seer does NOT do

- **No network telemetry.** Seer does not send any data, usage stats, error reports, or analytics to any server.
- **No third-party services.** Seer has no backend. There is no "Seer cloud."
- **No remote access.** The bridge binds to `127.0.0.1` (localhost) only and rejects non-local connections.
- **No data sale or sharing.** There is no data to sell — we don't collect any.

## Data the AI agent sees

The AI agent connected to Seer (Claude, GPT, Gemini, etc.) will see whatever Seer returns to it: window titles, UI element names and values, page content, screenshot pixels. **What that agent does with that data is governed by the agent's own privacy policy** — not by Seer.

If your agent runs locally (e.g. Ollama), no data leaves your machine. If your agent uses a cloud API, then yes, that data goes to that provider as part of the conversation. This is a property of the agent you choose, not of Seer.

## The Seer Bridge Chrome extension

- Reads the **active tab's** DOM when an agent requests it. Does not silently scrape other tabs or run in the background.
- Communicates only with the local Seer process via Chrome Native Messaging — no network requests.
- Requires `<all_urls>` host permission because the agent can ask to interact with any site you visit. Permissions are not used for collection.

## Contact

Privacy questions or concerns: **avii29gemini@gmail.com**

If we ever change how data is handled, this file will be updated and the change visible in git history.
