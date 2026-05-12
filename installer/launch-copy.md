# Launch copy

Pre-written posts. Fire on launch day. Tuesday or Wednesday 9am EST is the slot.

---

## Hacker News — Show HN

**Title** (max 80 char, no clickbait, HN hates exclamation marks):

```
Show HN: Seer – structured eyes and hands for AI agents on Windows
```

**URL field:** `https://github.com/av29nassh-sketch/seer`

**Text** (only if you need it — for Show HN with a repo, often skip the text and let the README + first comment do the work). If you do add text, keep it ~150 words:

```
Hi HN — Seer is an MCP server that gives any AI agent (Claude, GPT, Gemini, local) the ability to see and control Windows apps and Chrome without screenshots.

Every existing approach (Claude Computer Use, OpenAI Codex Desktop, browser-use) takes a screenshot every turn and asks a vision model what's on screen. It's slow (1–3s per glance), brittle (one UI redraw breaks it), and costs vision tokens that compound.

Seer reads Windows UI Automation trees + Chrome DOM directly. Sub-100ms per query. Element-precise. Works with any MCP-compatible agent client (Claude Code, Cursor, custom Anthropic SDK).

I also wrote a 5000-word handbook on building a real personal AI assistant on top of it: https://github.com/av29nassh-sketch/seer/blob/master/docs/jarvis-handbook.md

AGPL-3.0, Windows only for now. Native Messaging architecture so the Chrome extension works with your real browser session — no debug flags, no separate Chrome instance.

Demos in the README. Happy to answer questions.
```

**First comment (post yourself, immediately):**

```
A few notes from building this:

1. UIA on Electron apps is a nightmare — VS Code, Slack, Discord all expose broken trees. Seer detects this and falls back to screenshot + click_at coordinates.

2. CSP-strict sites (HN, GitHub, banks) block eval() in content scripts. Solved with chrome.scripting.executeScript in MAIN world — bypasses page CSP through Chrome's official sandboxed API.

3. The Native Messaging architecture (extension <-> local helper <-> MCP server) was the hardest part. Earlier versions used an HTTP polling bridge — battery-drainy and brittle. The current TCP-server-in-the-native-host pattern handles the case where Claude Code spawns multiple MCP processes.

Looking for feedback on:
- Things that should be MCP tools but aren't yet
- Apps where the UIA tree is broken in interesting ways
- Security holes (I'm not a security person; the threat model is in SECURITY.md)
```

---

## Reddit — r/LocalLLaMA

**Title** (Reddit allows more flavor than HN):

```
Built Seer — an MCP server that gives AI agents real eyes and hands on Windows. No screenshots. Sub-100ms per click. AGPL.
```

**Body:**

```
Hey r/LocalLLaMA — wanted to share something I've been building.

The problem: every "AI controls your computer" tool right now (Claude Computer Use, OpenAI's desktop thing, browser-use, OpenClaw) takes a screenshot every turn and asks a vision model where the button is. This is:

- Slow (1-3 seconds per glance, 6 turns to do anything useful = 18 seconds wasted)
- Vision-token-expensive (compounds fast)
- Brittle (one UI redraw and the agent loses its place)
- Imprecise (misclicks constantly)

**Seer skips the pixels.** It reads Windows UI Automation trees + Chrome DOM directly, so an agent sees the actual structure — buttons, text fields, lists, with stable IDs — and acts on them precisely.

```
Agent: get_element_tree(window="Notepad")
→ [{ id: 5, role: "Edit", name: "Text Editor" }, ...]

Agent: type_text(element_id=5, text="Hello")
→ { success: true }
```

Works with **any MCP-compatible client**: Claude Code, Cursor, Windsurf, custom Anthropic/OpenAI SDK calls. Tools include click, type, scroll, browser_navigate, browser_extract (CSP-safe DOM extraction), screenshot fallback for Electron apps.

I also wrote a 5000-word handbook on building a full personal Jarvis on top — voice, memory, wake word, voice output — wired together in <100 lines of glue:
[https://github.com/av29nassh-sketch/seer/blob/master/docs/jarvis-handbook.md](https://github.com/av29nassh-sketch/seer/blob/master/docs/jarvis-handbook.md)

Repo (AGPL-3.0): [https://github.com/av29nassh-sketch/seer](https://github.com/av29nassh-sketch/seer)

Windows-first because UIA is Windows-only. Mac (AXTree) + Linux (AT-SPI) coming.

Happy to answer anything.
```

---

## Reddit — r/programming

Same body as r/LocalLLaMA but with the title trimmed:

**Title:**
```
Seer — MCP server that gives AI agents structured Windows + Chrome access. No screenshots. Sub-100ms per call.
```

---

## Reddit — r/ChatGPT

**Title** (more accessible angle):

```
You can now give ChatGPT/Claude full hands-on access to your Windows apps. I built the missing piece.
```

**Body** (less technical, more "look what this does"):

```
For the past few months I kept hitting the same wall: every tutorial about "build your own Jarvis" was just ChatGPT in a Discord bot. Nobody had built the actual missing piece — letting AI **see** and **act on** your screen reliably.

Existing tools (Claude Computer Use, OpenAI's stuff) use screenshots and vision models. They're slow, miss clicks, and burn through tokens.

I built **Seer** — it reads the actual structure of your Windows apps and Chrome tabs, so an AI agent can interact with them precisely. Sub-second per action.

The cool part: you bring your own AI. Works with Claude, GPT, local Llama, anything that speaks MCP. Free and open source (AGPL).

Repo: [https://github.com/av29nassh-sketch/seer](https://github.com/av29nassh-sketch/seer)

Also wrote a full guide on building a personal voice-controlled assistant on top of it: [Jarvis handbook](https://github.com/av29nassh-sketch/seer/blob/master/docs/jarvis-handbook.md)

Windows only for now. Demos in the README.
```

---

## Twitter / X thread

Skip on launch day if you only have 1 follower. But here's the structure for when you have an audience:

```
[1/8] Searched "how to build Jarvis." 1000 results. All garbage — ChatGPT wrappers.

Nobody had built the actual missing piece: letting an AI **see** and **act on** your screen.

So I did. Open source. 🧵

[2/8] [GIF of seer doing something — Notepad demo or browser extraction]

Seer reads the OS's UI tree directly. No screenshots. Sub-100ms per call. Works with any AI agent.

[3/8] The 7 components of a real personal AI assistant:
- Eyes 👀 ← the missing one
- Hands ✋ ← also missing
- Brain (any LLM) ✅
- Memory (Chroma) ✅
- Voice in (Whisper) ✅
- Voice out (ElevenLabs) ✅
- Wake word (Picovoice) ✅

6 of 7 are solved. The missing 2 are what Seer is.

[4/8] Why screenshots-based agents fail:
- 1-3 seconds per glance
- Vision tokens compound
- One UI redraw and they're lost
- Misclicks constantly

[5/8] How Seer does it:
- Windows UI Automation tree (read native apps as structured data)
- Chrome DOM via Native Messaging (no debug flags, real browser session)
- Element-precise actions, not pixel coordinates

[6/8] Works with: Claude Code, Cursor, Windsurf, OpenAI Agents SDK, local Ollama, any MCP-compatible client. Bring your own brain.

[7/8] 5000-word handbook on building a real Jarvis on top: voice + memory + the works.
[link to handbook]

[8/8] AGPL-3.0. Windows-first. Mac + Linux coming.
[link to repo]
```

---

## Product Hunt (the day after HN)

**Tagline (60 char):**
```
Structured eyes and hands for AI agents on Windows
```

**Description:**
Same as Reddit r/ChatGPT body, trimmed to 250 words.

---

## Posting order (launch day)

| Time (EST) | Channel | Why |
|---|---|---|
| Mon evening | Tweak repo, double-check demos, sleep | Reset |
| Tue 9:00am | **Show HN** | First mover advantage on HN front page |
| Tue 9:15am | Post your own first comment to HN | Engagement signal |
| Tue 11:00am | r/LocalLLaMA | Reddit warm |
| Tue 12:00pm | r/programming + r/ChatGPT | Different audiences |
| Tue 1:00pm | Indie Hackers | Founder crowd |
| Tue 2:00pm | LinkedIn post | Indian audience |
| Wed 9:00am | Product Hunt | Next-day momentum |
| Wed–Fri | **Respond to every comment, issue, DM within 4 hours** | Engagement compounds |

---

## Failure signals to watch

- **HN <50 upvotes in 4 hours** → demos weren't compelling enough. Don't relaunch — wait, iterate, try Twitter next month
- **Stars plateau under 1k after 2 weeks** → distribution gap, need creator outreach
- **High install + low retention** → onboarding friction, simplify first-run
- **Curiosity stars but zero PRs/issues** → not solving a real problem; talk to 10 users
