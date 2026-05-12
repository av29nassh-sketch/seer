# Examples

Real things you can do with Seer. Mix of direct Python use (for developers debugging the library) and agent recipes (copy-paste prompts that work in Claude Code or any MCP-compatible agent).

## Direct Python

- [`notepad_demo.py`](notepad_demo.py) — minimal end-to-end: open Notepad, dump the element tree, type into it. Run this first to confirm install.

## Agent recipes (copy into your AI client)

- [`file_organization.md`](file_organization.md) — "Organize my Downloads folder by file type"
- [`browser_research.md`](browser_research.md) — "Find top 5 issues on this GitHub repo and summarize them"
- [`multi_app_workflow.md`](multi_app_workflow.md) — Cross-app: pull a metric from a webpage, paste into a spreadsheet
- [`voice_jarvis_quickstart.md`](voice_jarvis_quickstart.md) — Wire up wake-word + voice → Seer

Each recipe is a single prompt designed to be pasted into your agent. Tested with Claude Code + Seer.
