# Security

Seer can see and control everything on your computer. We take that seriously and assume you don't blindly trust us. This document explains how we earn that trust.

## Threat model

| Threat | Mitigation |
|---|---|
| **Prompt injection** — malicious web page tells agent to do harmful things | Confirmation gate on destructive verbs (`delete`, `send`, `submit`, etc.); agent must re-call with `confirm=true` after the user approves |
| **Local server hijack** — other process on your machine connects to the bridge | TCP bridge requires a shared-secret token stored in `~/.seer/token` (owner-only); rejects unauthenticated connections |
| **Network exposure** | Bridge binds to `127.0.0.1` only. Rejects non-local connections. No `0.0.0.0`, no port forwarding, no public mode in v1 |
| **DoS via huge messages** | All framed messages capped at 8 MiB; oversized payloads are dropped |
| **Stolen API keys** | Spotify credentials stored locally in `~/.seer/spotify.json` with restricted file permissions |
| **Command injection via URLs** | Chrome launch validates URL scheme (`http`/`https` only) before passing to `subprocess.Popen` (no shell) |
| **Process privilege escalation** | Seer runs as the current user, never as admin or SYSTEM |
| **Browser extension scope** | Reads only the **active tab**, not all tabs. Cannot read Chrome's password fields (Chrome blocks this). Native messaging restricted to the registered extension ID |

## What we are NOT solving

- **Prompt injection cannot be fully solved** — it's an open AI safety research problem. We mitigate (confirmation gates, allowlists) but cannot eliminate.
- **Users who explicitly grant agent access to dangerous things** — our job is to make dangerous defaults impossible, not to override your explicit choice.
- **Chrome itself** — if your Chrome installation is compromised, no extension can save you.

## Defense-in-depth

- **Local-only by design.** No telemetry, no cloud, no remote control.
- **Open source.** Every line is auditable. AGPL-3.0 license means any fork must also be open.
- **Confirmation prompts.** Destructive actions surface to the user via the agent before executing.
- **Auditable.** Bridge and native host write to `~/.seer/*.log` so you can see what was requested.

## Reporting a vulnerability

Please email **avii29gemini@gmail.com** with details. Include:
- Steps to reproduce
- What the attacker can gain
- Severity in your judgment

We'll respond within 72 hours and coordinate a fix + disclosure timeline.

Do not file public GitHub issues for security bugs — open them only after a fix has shipped.

## Hall of fame

*Researchers credited here once we receive valid reports.*

## Roadmap

- [ ] Per-app permission profiles (whitelist which apps an agent may touch)
- [ ] Read-only mode toggle in the tray
- [ ] Action audit log surfaced in the tray UI
- [ ] Suspicious-behavior detection (e.g. agent reads 50 files then makes a network request → pause)
- [ ] Sensitive-data redaction (credit cards, SSNs, password fields) before sending DOM/UIA tree to agent
- [ ] Code signing certificate so Windows Defender stops scaring users
- [ ] Third-party security audit before paid-tier launch
- [ ] Bug bounty program
