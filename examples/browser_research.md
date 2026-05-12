# Recipe: Browser research + structured extraction

**Prompt** (paste into Claude Code with Seer's browser tools):

```
Open https://github.com/microsoft/vscode/issues — find the top 5 most-commented open issues. For each, extract:
  - Title
  - Issue number
  - Comment count
  - First line of the description

Format the output as a table.
```

**What happens under the hood:**

1. `browser_navigate("https://github.com/microsoft/vscode/issues")` opens the page in your real Chrome (logged-in session preserved)
2. `browser_extract(selector: ".markdown-title", attribute: "innerText", limit: 5)` pulls titles directly via CSS selectors — works on GitHub even though GitHub blocks raw `eval()` via CSP
3. Agent constructs a markdown table from the structured results

**Why this is hard for screenshot-based agents:**
- 5 round-trips of vision-model parsing = ~15 seconds + several thousand vision tokens
- Misreads of comment counts when icons overlap text
- One UI redraw and the agent loses its place

**Why this works for Seer:**
- `browser_extract` returns structured text directly from the DOM
- Sub-second per query, no vision tokens
- Resilient to layout shifts

**Variations:**
- "Pull all the labels from issue #12345 and group them by category"
- "On amazon.in, search for 'sony headphones' and list the first 5 results with prices"
- "Read the changelog on the active tab and summarize the breaking changes"
