# Recipe: Voice-controlled Jarvis (60 lines)

The "Iron Man moment": say "Hey Jarvis" → speak a command → AI acts on your computer.

**Full code** (the long version with explanation is in [`docs/jarvis-handbook.md`](../docs/jarvis-handbook.md)):

```python
# pip install openai-whisper sounddevice pvporcupine pyaudio anthropic
import sounddevice as sd, whisper, pvporcupine, pyaudio, struct
from anthropic import Anthropic
# Assume Seer is running as an MCP server registered with Claude Code,
# OR you've wired your own SDK client with MCP tool routing.

asr = whisper.load_model("base.en")
porcupine = pvporcupine.create(access_key="YOUR_PICOVOICE_KEY", keywords=["jarvis"])
brain = Anthropic()
pa = pyaudio.PyAudio()
mic = pa.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16,
              input=True, frames_per_buffer=porcupine.frame_length)


def listen(seconds=5):
    audio = sd.rec(int(seconds * 16000), samplerate=16000, channels=1, dtype="float32")
    sd.wait()
    return asr.transcribe(audio.flatten(), language="en", fp16=False)["text"].strip()


print("Jarvis online. Say 'Jarvis' to wake.")
while True:
    pcm = mic.read(porcupine.frame_length, exception_on_overflow=False)
    if porcupine.process(struct.unpack_from("h" * porcupine.frame_length, pcm)) < 0:
        continue
    print("Yes?")
    user_text = listen(5)
    print(f"You: {user_text}")

    # In real life: hand off to Claude Code with Seer's MCP tools registered.
    # For a one-shot demo, send the prompt to the Anthropic API and print the reply.
    resp = brain.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": user_text}],
    )
    print(f"Jarvis: {resp.content[0].text}")
```

**The key handoff:** in production, `brain.messages.create` should actually be a Claude Code session (or any agent runtime with MCP tool calling). That's what makes Seer's tools available to the brain — without that, the brain can only *talk*, not *act*.

The minimum to make the brain act:
- Use the Anthropic SDK with the **MCP client** to expose Seer's tools as `tools` in the request
- Or pipe the voice transcript into Claude Code with `claude --print "$user_text"` from your script
- Or use a wrapper like `mcphost` that handles the agent loop

See [`docs/jarvis-handbook.md`](../docs/jarvis-handbook.md) for the full guide including memory, voice output, and wake-word customization.

**Use cases that suddenly work:**
- "Hey Jarvis, open VS Code and create a new file called notes.md"
- "Jarvis, what's on my screen right now?" (agent screenshots + describes)
- "Jarvis, send a Slack message to Priya saying I'll be 10 minutes late"
