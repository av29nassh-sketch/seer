"""
Bridge between MCP seer and the Native Messaging Host (which talks to the Chrome extension).

Inverted architecture: the native_host is a TCP server on localhost:7843. We connect
fresh per command. No daemon thread, no shared state, no pipe lifecycle nonsense.
This works regardless of how many seer processes Claude Code spawns.
"""

from __future__ import annotations
import json
import os
import socket
import struct
import subprocess
import time

from .constants import TCP_HOST, TCP_PORT, MAX_MSG_BYTES
from . import token as _token

_CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]


def _is_native_host_up() -> bool:
    try:
        with socket.create_connection((TCP_HOST, TCP_PORT), timeout=0.3):
            return True
    except OSError:
        return False


def _find_chrome() -> str | None:
    for p in _CHROME_PATHS:
        if os.path.exists(p):
            return p
    return None


def _ensure_chrome_running(wait_seconds: float = 30.0, initial_url: str | None = None) -> bool:
    """If native host TCP port isn't reachable, launch Chrome and wait for the extension.
    Pass initial_url to make the first tab a real page instead of chrome://newtab/."""
    if _is_native_host_up():
        return True
    chrome = _find_chrome()
    if not chrome:
        return False
    try:
        args = [chrome]
        if initial_url:
            args.append(initial_url)
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, ValueError) as e:
        import sys as _s
        print(f"[seer] Chrome launch failed: {e}", file=_s.stderr)
        return False
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if _is_native_host_up():
            return True
        time.sleep(0.5)
    return False


def start() -> None:
    """No-op for compatibility with old API. Native host is owned by Chrome, not us."""
    return


def _frame(obj: dict) -> bytes:
    data = json.dumps(obj).encode("utf-8")
    return struct.pack("<I", len(data)) + data


def _read_frame(sock) -> dict | None:
    try:
        raw_len = b""
        while len(raw_len) < 4:
            chunk = sock.recv(4 - len(raw_len))
            if not chunk:
                return None
            raw_len += chunk
        msg_len = struct.unpack("<I", raw_len)[0]
        if msg_len > MAX_MSG_BYTES:
            return None
        raw = b""
        while len(raw) < msg_len:
            chunk = sock.recv(msg_len - len(raw))
            if not chunk:
                return None
            raw += chunk
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def send_command(cmd: dict, timeout: float = 10.0) -> dict:
    """Open a TCP connection to the native host, send the command, read the response, close.
    Auto-launches Chrome if the native host isn't reachable. Authenticates with a shared token."""
    if not _is_native_host_up():
        if not _ensure_chrome_running():
            return {"ok": False, "error": "Chrome not running and could not launch it"}
    try:
        with socket.create_connection((TCP_HOST, TCP_PORT), timeout=2.0) as sock:
            sock.settimeout(timeout)
            # Authenticate before sending the real command.
            auth = {"_auth": _token.get_or_create()}
            sock.sendall(_frame(auth))
            sock.sendall(_frame(cmd))
            result = _read_frame(sock)
            return result or {"ok": False, "error": "Empty response from native host"}
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        return {"ok": False, "error": f"Browser extension not connected ({e})"}
