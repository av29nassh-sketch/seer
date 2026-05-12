"""
Seer tray app — system tray icon + menu. Runs as a standalone background process,
independent of the MCP server lifecycle. Provides:
  - Visible "seer is installed" presence
  - Live status: Browser connected? Spotify reachable?
  - Quick actions: open logs, toggle disable, quit
  - Click the icon → opens the seer status page

Run via: python -m seer.tray
"""

from __future__ import annotations
import os
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("pystray and pillow required. Run: pip install pystray pillow")
    sys.exit(1)

from seer.browser.constants import TCP_HOST, TCP_PORT, SEER_DIR

SEER_DIR.mkdir(parents=True, exist_ok=True)
DISABLED_SENTINEL = SEER_DIR / "disabled"
LOG_DIR = SEER_DIR

_state = {"browser": False, "disabled": DISABLED_SENTINEL.exists()}


# ── Icon rendering ──────────────────────────────────────────────────────────

def _make_icon(connected: bool, disabled: bool) -> Image.Image:
    """Eye-like icon. Green ring = connected, red = disconnected, gray = disabled."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if disabled:
        ring = (130, 130, 130, 255)
    elif connected:
        ring = (60, 200, 90, 255)
    else:
        ring = (220, 70, 70, 255)
    # Outer ring
    d.ellipse((4, 14, 60, 50), outline=ring, width=4)
    # Pupil
    d.ellipse((24, 24, 40, 40), fill=ring)
    return img


# ── Status probes ───────────────────────────────────────────────────────────

def _is_browser_bridge_up() -> bool:
    try:
        with socket.create_connection((TCP_HOST, TCP_PORT), timeout=0.3):
            return True
    except OSError:
        return False


def _refresh_loop(icon: pystray.Icon) -> None:
    while True:
        browser = _is_browser_bridge_up()
        disabled = DISABLED_SENTINEL.exists()
        if browser != _state["browser"] or disabled != _state["disabled"]:
            _state["browser"] = browser
            _state["disabled"] = disabled
            icon.icon = _make_icon(browser, disabled)
            icon.title = _status_text(browser, disabled)
        time.sleep(2.0)


def _status_text(browser: bool, disabled: bool) -> str:
    if disabled:
        return "Seer — disabled"
    return f"Seer — browser: {'on' if browser else 'off'}"


# ── Menu actions ────────────────────────────────────────────────────────────

def _open_logs(icon, item) -> None:
    subprocess.Popen(["explorer", str(LOG_DIR)])


def _toggle_disabled(icon, item) -> None:
    if DISABLED_SENTINEL.exists():
        DISABLED_SENTINEL.unlink()
    else:
        DISABLED_SENTINEL.write_text("disabled at " + time.strftime("%Y-%m-%d %H:%M:%S"))


def _open_homepage(icon, item) -> None:
    webbrowser.open("https://github.com/av29nassh-sketch/seer")


def _quit(icon, item) -> None:
    icon.stop()


# ── Entry ───────────────────────────────────────────────────────────────────

def _acquire_singleton_lock() -> bool:
    """Use a Windows-side TCP bind on a fixed local port as a singleton mutex.
    Returns False if another tray instance is already running."""
    global _singleton_socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 7844))  # listen-only, not used for accept
        s.listen(1)
        _singleton_socket = s  # keep alive for process lifetime
        return True
    except OSError:
        return False


_singleton_socket = None


def main() -> None:
    if not _acquire_singleton_lock():
        print("Seer tray already running. Exiting.")
        sys.exit(0)
    menu = pystray.Menu(
        pystray.MenuItem(lambda item: _status_text(_state["browser"], _state["disabled"]), None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open logs folder", _open_logs),
        pystray.MenuItem(
            lambda item: "Enable seer" if _state["disabled"] else "Disable seer",
            _toggle_disabled,
        ),
        pystray.MenuItem("Open seer on GitHub", _open_homepage),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", _quit),
    )
    icon = pystray.Icon(
        "seer",
        _make_icon(_state["browser"], _state["disabled"]),
        _status_text(_state["browser"], _state["disabled"]),
        menu,
    )
    threading.Thread(target=_refresh_loop, args=(icon,), daemon=True).start()
    icon.run()


if __name__ == "__main__":
    main()
