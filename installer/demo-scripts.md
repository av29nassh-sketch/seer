# Demo video scripts

Two videos to film + edit before HN launch. Both Windows screen recording, captions essential (people watch HN/Reddit videos muted).

---

## Video 1 — Technical demo (90 seconds)

**Goal:** prove Seer is faster and more reliable than screenshot-based AI desktop control. Show a head-to-head against a screenshot tool.

**The task:** "Open Notepad, search for 'replace' in the menu, click it, type 'find' in the find box, type 'replace' in the replace box, click Replace All."

This is a 6-step task. Multi-step UIA chains are exactly where screenshot agents fall over.

**Shot list:**

| Time | Visual | Caption / Voiceover |
|---|---|---|
| 0:00–0:05 | Title card: black background, white text "**Computer Use vs. Seer — same task, same agent, different eyes**" | (silent intro) |
| 0:05–0:30 | **Left half of screen:** Claude Computer Use trying the task. Screenshot every ~2s, agent narrates "I see a menu", click misses, retry. Show it failing or being slow. | "Computer Use takes a screenshot every turn. The agent has to figure out what's on screen each time. Watch." |
| 0:30–0:35 | "**Same prompt. Same model. Different tool.**" full-screen text card. | (silent transition) |
| 0:35–1:00 | **Same screen:** Seer running. Element tree appears in the chat panel as JSON. Agent calls `click(element_id=12)` → exact menu item activates instantly. Multi-step chain executes in <2 seconds. | "Seer reads the actual UI tree. Element-precise. Sub-100ms per query." |
| 1:00–1:20 | Speed comparison side-by-side: Computer Use = 47 seconds, Seer = 4 seconds. Same task, same outcome. | "12× faster. Zero vision tokens." |
| 1:20–1:30 | End card: **"Seer — github.com/av29nassh-sketch/seer — AGPL-3.0**" | (silent outro) |

**Recording tools:** OBS Studio (free) or Windows + G game bar. Cut in DaVinci Resolve or Clipchamp (built into Windows 11).

**Critical**: caption *every* word — most viewers watch silent.

---

## Video 2 — Vibe-coder demo (60 seconds)

**Goal:** show a non-coder achieving something useful by *talking* to an AI. No code visible. Friendly, casual.

**The task:** "Hey Claude, organize my Downloads folder by file type" → Claude actually does it via Seer.

**Shot list:**

| Time | Visual | Caption / Voiceover |
|---|---|---|
| 0:00–0:05 | Webcam-style intro: you, casual, holding phone or mic. **Pinned text: "No code. Just talking."** | "What if you could just tell your computer what to do?" |
| 0:05–0:15 | **Voice command pop-up overlay:** "Hey Claude, my Downloads is a mess. Sort everything by file type." | (your actual voice — record clean audio) |
| 0:15–0:45 | **Screen:** Downloads folder visible (cluttered, 50+ files of mixed types). File Explorer animates: new subfolders appear (Images, Documents, Code, Installers), files glide into them. Time-lapse if too slow. | "Claude is using Seer to read the folder, classify each file, and move it. No script. No setup beyond installing Seer." |
| 0:45–0:55 | **Result:** clean Downloads folder, files neatly grouped. Show the time elapsed: 12 seconds. | "Done. Twelve seconds." |
| 0:55–1:00 | End card: **"Seer — free, open source, install once → talk to your computer forever — github.com/av29nassh-sketch/seer"** | (silent outro) |

**The emotional beat:** the moment of "the folder is clean now" should land *visually* — they see chaos → see order, like a satisfying before/after. Don't talk over that moment.

---

## Recording checklist (both videos)

- [ ] **OBS Studio** installed, configured to 1920×1080, 30fps, mp4 output
- [ ] Quiet environment — no fan, no kids, no Slack notifications
- [ ] **Mute** Discord/Slack/email entirely during recording
- [ ] **Hide bookmarks bar** in Chrome (clean look)
- [ ] **Hide taskbar** during full-screen captures
- [ ] **Hide tray icons** with personal info
- [ ] Practice the task once before recording so you don't fumble
- [ ] Record audio separately if possible — easier to clean up
- [ ] Subtitle every spoken word — most viewers watch muted

## Editing checklist

- [ ] Cut every dead second — viewer attention drops fast
- [ ] Add captions throughout
- [ ] Background music: pick something low-energy from YouTube Audio Library (free, no copyright)
- [ ] End card on screen for at least 3 seconds with the GitHub URL clearly readable
- [ ] Export at 1080p, MP4, under 30 MB (so it embeds inline on Twitter/HN)

## Hosting

- Upload to YouTube (unlisted is fine if you want to release them as part of the launch)
- Also upload a copy directly to the repo as `docs/demo-*.mp4` for embed reliability — GitHub README plays mp4 inline
