# How to Build Jarvis (For Real This Time)

*The honest guide to building a real personal AI assistant on your computer. Not a ChatGPT wrapper. Not a Discord bot. The actual thing.*

---

## Why every "Build Jarvis" tutorial fails

Search "how to build Jarvis." You'll find a thousand tutorials. They are all variations of:

```python
import openai
while True:
    prompt = input("> ")
    print(openai.ChatCompletion.create(...))
```

That's not Jarvis. That's a chat window with a voice on top. Jarvis is the thing in the Iron Man movies that **does** things — opens apps, reads files, controls hardware, finishes your sentences, sets up calendar events while you're talking. None of the tutorials show you any of that, because the part that's actually hard has been missing from open source for years.

That missing part is the **eyes and hands** — the ability for an AI to *see* what's on your screen and *act* on it precisely.

Until you solve that, every Jarvis tutorial is a Speech-to-Text → LLM → Text-to-Speech pipeline, dressed up. Useless for any real task.

This guide shows you how to build the real thing, with working code for every layer.

---

## The 7 components of a real personal AI assistant

A real AI assistant has seven pieces. Six are commodity infrastructure. One is the wall everyone hits.

| Component | What it does | Status |
|---|---|---|
| **1. Eyes** | Perceive the screen — apps, windows, web pages | ❌ The wall |
| **2. Hands** | Act on the screen — click, type, navigate | ❌ The wall |
| **3. Brain** | Reasoning. Choose what to do. | ✅ Any LLM |
| **4. Memory** | Remember conversations and facts | ✅ Vector DB |
| **5. Voice in** | Hear you | ✅ Whisper |
| **6. Voice out** | Speak back | ✅ ElevenLabs / Coqui |
| **7. Wake word** | Activate on "Hey Jarvis" | ✅ Picovoice |

Six of seven are pip-install-and-go. The one that isn't is the one that matters most. We'll solve it first.

---

## Components 1 & 2: Eyes and Hands (Seer)

The reason no one has shipped a real personal Jarvis is that "let the AI control my computer" sounds easy and is hard. Two real attempts exist:

- **Screenshot-based**: Claude Computer Use, OpenAI Codex Desktop. Take a screenshot every second, ask vision model where the button is, hope it doesn't misclick. Slow (1-3 seconds per glance), expensive (vision tokens compound), brittle (any UI redraw breaks it).
- **Structured access**: Read the OS's accessibility tree directly. Sub-100ms per query, element-precise, costs nothing per query. This is what Seer does.

Seer is an MCP server. Install it, point your AI agent at it, and your agent gains real eyes and hands on Windows.

### Install Seer

```bash
# Windows. Python 3.10+.
git clone https://github.com/av29nassh-sketch/seer
cd seer
pip install -e .

# Tell your MCP client about it. For Claude Code, edit ~/.claude/.mcp.json:
# {
#   "mcpServers": {
#     "seer": { "command": "python", "args": ["-m", "seer"] }
#   }
# }
```

For the browser bridge, install the Seer Bridge Chrome extension from `seer/browser/extension/` (Load Unpacked in chrome://extensions), then run `python -m seer.browser.install_native_host <extension-id>`.

### Test it

Open Notepad. Then ask your agent:

> "Get the element tree of the active window. Type 'Hello from Jarvis' into the edit field."

The agent calls `get_element_tree`, sees the Edit control by ID, calls `type_text(id, "Hello from Jarvis")`. Sub-second. No screenshots.

That's the moment you realize this is going to work.

---

## Component 3: The Brain (any LLM)

Your brain is whichever model you trust to think. Three real options:

**Cloud (smartest, costs money per token):**
- Claude (Sonnet for reasoning, Haiku for fast tasks)
- GPT-4o / o1
- Gemini 2.0

**Local (free, slower, privacy):**
- Llama 3.3 70B via Ollama
- Qwen 2.5 Coder
- DeepSeek V3

For a personal Jarvis, my recommendation: **Claude Sonnet with Claude Code as the agent runtime**. Claude Code already speaks MCP, has tool-calling baked in, handles context management. You're not building an agent from scratch — you're plugging your MCPs into a pre-built one.

If you want to roll your own agent: use the Anthropic Python SDK and pass tools from your MCP servers. ~50 lines of code. But Claude Code saves you those lines and handles edge cases.

```python
# DIY agent skeleton if you really want one:
from anthropic import Anthropic
client = Anthropic()

# (Hook your MCP servers, expose tools, loop until done.)
# The agent calls Seer's tools to act on your screen.
# Honestly, just use Claude Code.
```

For local: point Ollama at Claude Code via a proxy, or use a generic MCP client like `mcphost`.

---

## Component 4: Memory (Chroma, in 20 lines)

Without memory, your assistant forgets every conversation. Add a vector DB.

```python
# pip install chromadb
import chromadb
from datetime import datetime

client = chromadb.PersistentClient(path=".jarvis_memory")
mem = client.get_or_create_collection("episodic")

def remember(text: str, meta: dict = None):
    mem.add(
        documents=[text],
        metadatas=[meta or {"ts": datetime.now().isoformat()}],
        ids=[f"mem_{datetime.now().timestamp()}"],
    )

def recall(query: str, k: int = 5) -> list[str]:
    results = mem.query(query_texts=[query], n_results=k)
    return results["documents"][0]

# Use it:
remember("User prefers dark mode in VS Code.")
remember("User's wife's name is Priya. Anniversary: March 12.")
print(recall("user preferences"))
# → ["User prefers dark mode in VS Code."]
```

Hook this into your agent. Before answering, call `recall(user_message)` to pull relevant context. After answering, decide what's worth storing with `remember()`. That's it. Persistent across sessions.

For more sophisticated memory (decay over time, importance scoring, semantic compression), look at LanceDB or Qdrant. Chroma is fine for a personal assistant.

---

## Component 5: Voice input (Whisper, in 30 lines)

`whisper.cpp` runs locally, no API key, no quota. Or use OpenAI's Whisper API if you don't want to manage models.

**Local, fast (recommended):**

```python
# pip install openai-whisper sounddevice numpy
import sounddevice as sd
import numpy as np
import whisper

model = whisper.load_model("base.en")  # 140 MB, fast on CPU

def listen(seconds: int = 5) -> str:
    print(f"Listening for {seconds}s...")
    audio = sd.rec(int(seconds * 16000), samplerate=16000, channels=1, dtype="float32")
    sd.wait()
    result = model.transcribe(audio.flatten(), language="en", fp16=False)
    return result["text"].strip()

print(listen())
```

For real-time (no fixed window), use `whisper_streaming` or push audio chunks into Whisper as they arrive. For best accuracy, use `medium.en` (1.5 GB).

---

## Component 6: Voice output (ElevenLabs or Coqui)

**Cloud, best quality:**

```python
# pip install elevenlabs
from elevenlabs import generate, play
audio = generate(text="Hello, sir.", voice="Adam")
play(audio)
```

**Local, free:**

```python
# pip install TTS
from TTS.api import TTS
tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")
tts.tts_to_file(text="Hello, sir.", file_path="output.wav")
```

For latency, the Windows native SAPI voice works in two lines (`pyttsx3`), is ugly, but starts in 100ms. Use that for "command acknowledged" beeps and ElevenLabs for full responses.

---

## Component 7: Wake word (Picovoice)

You don't want to hit a hotkey every time. You want to say "Hey Jarvis" and have it listen.

```python
# pip install pvporcupine pyaudio
import pvporcupine
import pyaudio
import struct

porcupine = pvporcupine.create(
    access_key="YOUR_PICOVOICE_KEY",  # free at picovoice.ai
    keywords=["jarvis"],  # built-in
)
pa = pyaudio.PyAudio()
stream = pa.open(
    rate=porcupine.sample_rate,
    channels=1,
    format=pyaudio.paInt16,
    input=True,
    frames_per_buffer=porcupine.frame_length,
)

print("Listening for 'Jarvis'...")
while True:
    pcm = stream.read(porcupine.frame_length)
    pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
    if porcupine.process(pcm) >= 0:
        print("Wake word!")
        # Trigger your listen() + agent loop here
```

Free tier handles personal use. Custom wake words ("Hey computer", "Yo Sam") cost ~$0 if you train them yourself.

---

## Wiring it all together

Here's the loop. ~80 lines.

```python
import asyncio
import pvporcupine, pyaudio, struct, sounddevice as sd, whisper, chromadb
from anthropic import Anthropic
from elevenlabs import generate, play
# Assume Seer is running as an MCP server already.

# ── Setup ───────────────────────────────────────────────────────────────────
porcupine = pvporcupine.create(access_key="...", keywords=["jarvis"])
asr = whisper.load_model("base.en")
mem = chromadb.PersistentClient(path=".jarvis_memory").get_or_create_collection("episodic")
brain = Anthropic()

pa = pyaudio.PyAudio()
audio_stream = pa.open(
    rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16,
    input=True, frames_per_buffer=porcupine.frame_length,
)


def listen(seconds=5):
    audio = sd.rec(int(seconds * 16000), samplerate=16000, channels=1, dtype="float32")
    sd.wait()
    return asr.transcribe(audio.flatten(), language="en", fp16=False)["text"].strip()


def speak(text):
    play(generate(text=text, voice="Adam"))


def recall(query, k=5):
    return mem.query(query_texts=[query], n_results=k)["documents"][0]


def remember(text):
    import time
    mem.add(documents=[text], ids=[f"mem_{time.time()}"])


async def think_and_act(user_text):
    # Pull memory
    context = "\n".join(recall(user_text))
    # Ask brain. In real life this would be Claude Code with MCP tools
    # so Seer's tools are exposed automatically; below is the simple version.
    resp = brain.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=f"You are Jarvis. Relevant memory:\n{context}",
        messages=[{"role": "user", "content": user_text}],
    )
    answer = resp.content[0].text
    # Decide if anything is worth remembering (the brain can do this for you)
    remember(f"User said: {user_text}\nI said: {answer}")
    return answer


print("Jarvis online. Say 'Jarvis' to wake.")
while True:
    pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
    if porcupine.process(struct.unpack_from("h" * porcupine.frame_length, pcm)) >= 0:
        speak("Yes?")
        user_text = listen(5)
        print(f"You: {user_text}")
        answer = asyncio.run(think_and_act(user_text))
        print(f"Jarvis: {answer}")
        speak(answer)
```

In the real version, you replace `brain.messages.create` with a Claude Code session (or MCP-tool-using SDK call) that has Seer's tools registered. That's where the "hands" come alive — the agent will decide on its own to call `seer.click(...)` or `seer.browser_navigate(...)` mid-response.

---

## Customizing for your workflow

This is where you go from "demo Jarvis" to "useful Jarvis." Some prompts that make a real difference:

- **Workflow shortcuts**: "Open my morning routine" → agent runs a sequence: launch VS Code, open today's notes, fetch calendar, summarize Slack DMs.
- **App-specific helpers**: "Send this to Priya in Slack" → agent uses the Slack MCP if installed, falls back to Seer driving the Slack web app.
- **Background watchers**: "Tell me when my deploy finishes" → agent polls the deploy URL, speaks when it sees the success page.
- **Voice-to-action pipelines**: "Write a thank-you email to the candidate I interviewed yesterday" → agent recalls the interview from memory, drafts the email, opens Gmail, types it for review.

Build these as named commands or as agent-level system prompts. The point is Jarvis doesn't have a UI — your *workflow* is the UI.

---

## Sharing your Jarvis (deployment, security)

You don't deploy a personal Jarvis. It runs on your machine. But two things matter:

**Backup your memory.** The vector DB is the soul. Back it up to your cloud (rclone, syncthing, whatever). If you lose it, your assistant forgets you.

**Security is on you.** A personal Jarvis has:
- Your microphone open most of the day
- Access to your screen and keyboard
- API keys for whatever cloud services you wired up

Treat the whole stack like a privileged tool. Don't share API keys. Don't run Jarvis on a public network (if your wake-word/voice service is cloud). Audit which apps your agent has permission to control. Seer ships with a confirmation gate on destructive actions; use it.

If you wire in cloud LLMs, you're sending whatever you say within wake-word range to that provider. Local-only Jarvis (Ollama + Whisper + Coqui + Picovoice) is doable and stays private.

---

## What's next

You now have a real personal AI assistant. Not a chat wrapper. Not a Discord bot. The actual thing.

A few directions from here:

- **Make it ambient**: keep the wake-word loop running 24/7. Cost of running locally = ~$0.
- **Add scheduled jobs**: `apscheduler` + agent prompts = "every Monday morning, summarize my unread emails into a Notion page."
- **Per-app skills**: write small Python scripts your agent can call ("send slack message to X", "create calendar event"). MCP makes them callable from any agent client.
- **Multi-agent**: split tasks across specialized agents (one for desktop, one for browser, one for email triage) coordinated by a router.

The reason this guide is short is that 90% of building Jarvis was building Seer. Once you have eyes and hands, the rest is glue.

If you build something, [open a discussion on the Seer repo](https://github.com/av29nassh-sketch/seer/discussions) — I want to see it.

---

*Seer is AGPL-3.0 open source. If you build a personal Jarvis on top, you're not required to open-source your Jarvis — only changes to Seer itself.*

*[Star Seer on GitHub →](https://github.com/av29nassh-sketch/seer)*
