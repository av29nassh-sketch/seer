# Recipe: Cross-app workflow

A real test of "Jarvis-like" behavior: pull data from one app, transform it, paste into another.

**Prompt:**

```
Open https://news.ycombinator.com in Chrome. Extract the top 10 story titles and their points using browser_extract.

Then open Notepad. Type a clean numbered list into Notepad:
  1. [Title] — [points] points
  2. ...

Don't paste the URLs. One line per story.
```

**What happens:**

1. **Browser layer:** `browser_navigate` → `browser_extract(".titleline a", "innerText", 10)` and `browser_extract(".score", "innerText", 10)`
2. **Agent reasoning:** zips the two lists, formats each line
3. **Desktop layer:** opens Notepad (via `subprocess.Popen("notepad.exe")` or the Start Menu), waits for it to appear, calls `get_element_tree`, finds the Edit control, calls `type_text` with the formatted list

**Why this matters:**

This is the kind of task that's trivial when described in English but historically requires 30 lines of scripting. With Seer the agent stitches its own tools together — you just describe the goal.

**Variations:**
- "Get the trending searches from Google Trends, write them into an Excel sheet, save as `trends.xlsx`"
- "Read my Notion 'todo' database (via the Notion MCP), write each undone task to Notepad as a checklist"
- "Compare prices of [item] across Amazon and Flipkart, summarize the cheaper option in a Slack DM"

**The pattern:**
- Use API MCPs where available (Notion, Slack, GitHub) — fast
- Use Seer's browser tools for web — works on logged-in sessions
- Use Seer's UIA for desktop apps — for anything else
