"""
CDP (Chrome DevTools Protocol) client.

Connects to Chrome's remote debugging port (9222) via WebSocket.
Provides evaluate(), type(), click(), screenshot(), and get_page_info().
Falls back gracefully if Chrome isn't running with --remote-debugging-port=9222.
"""

from __future__ import annotations
import base64
import json
import subprocess
import time
import threading
import urllib.request
import urllib.error
import websocket  # websocket-client

_CDP_HOST = "http://localhost:9222"
_lock = threading.Lock()
_ws: websocket.WebSocket | None = None
_msg_id = 0
_pending: dict[int, dict] = {}
_pending_events: list[dict] = []


# ── Connection ──────────────────────────────────────────────────────────────

def _next_id() -> int:
    global _msg_id
    _msg_id += 1
    return _msg_id


def _get_active_tab_ws_url() -> str | None:
    try:
        with urllib.request.urlopen(f"{_CDP_HOST}/json", timeout=2) as r:
            tabs = json.loads(r.read())
        for tab in tabs:
            if tab.get("type") == "page" and "webSocketDebuggerUrl" in tab:
                return tab["webSocketDebuggerUrl"]
    except Exception:
        pass
    return None


def _connect() -> websocket.WebSocket | None:
    global _ws
    ws_url = _get_active_tab_ws_url()
    if not ws_url:
        return None
    try:
        ws = websocket.create_connection(ws_url, timeout=5)
        ws.settimeout(10)
        _ws = ws
        return ws
    except Exception:
        return None


def _ensure_connected() -> websocket.WebSocket | None:
    global _ws
    with _lock:
        if _ws:
            try:
                _ws.ping()
                return _ws
            except Exception:
                _ws = None
        if not available():
            launch_chrome()
        return _connect()


def available() -> bool:
    """Return True if Chrome is running with remote debugging on port 9222."""
    return _get_active_tab_ws_url() is not None


def launch_chrome() -> bool:
    """Launch Chrome with remote debugging. Returns True if successful."""
    from . import bridge
    chrome_exe = bridge._find_chrome()
    if not chrome_exe:
        return False
    try:
        subprocess.Popen([chrome_exe, "--remote-debugging-port=9222"])
        for _ in range(10):
            time.sleep(1)
            if available():
                return True
    except Exception as e:
        # surface to caller via debug log; don't silently fail
        import sys as _s
        print(f"[cdp] launch_chrome failed: {e}", file=_s.stderr)
    return False


# ── RPC ─────────────────────────────────────────────────────────────────────

def _call(method: str, params: dict | None = None, timeout: float = 10.0) -> dict:
    ws = _ensure_connected()
    if not ws:
        return {"error": "CDP not available — Chrome not running with --remote-debugging-port=9222"}

    msg_id = _next_id()
    payload = json.dumps({"id": msg_id, "method": method, "params": params or {}})
    try:
        ws.send(payload)
        deadline = time.time() + timeout
        while time.time() < deadline:
            ws.settimeout(deadline - time.time())
            raw = ws.recv()
            msg = json.loads(raw)
            if msg.get("id") == msg_id:
                if "error" in msg:
                    return {"error": msg["error"].get("message", "CDP error")}
                return msg.get("result", {})
    except Exception as e:
        global _ws
        _ws = None
        return {"error": str(e)}
    return {"error": "CDP timeout"}


# ── High-level API ───────────────────────────────────────────────────────────

def evaluate(code: str) -> dict:
    """Run JavaScript in the active tab. Bypasses CSP."""
    result = _call("Runtime.evaluate", {
        "expression": code,
        "returnByValue": True,
        "awaitPromise": True,
    })
    if "error" in result:
        return result
    rv = result.get("result", {})
    if rv.get("type") == "undefined":
        return {"result": None}
    if "value" in rv:
        return {"result": rv["value"]}
    return {"result": rv.get("description", str(rv))}


def screenshot() -> dict:
    """Capture a screenshot of the active tab. Returns base64 PNG."""
    result = _call("Page.captureScreenshot", {"format": "png", "quality": 80})
    if "error" in result:
        return result
    return {"data": result.get("data", ""), "format": "png"}


def type_text(text: str) -> dict:
    """Type text into the focused element using real key events (bypasses React state issues)."""
    for char in text:
        r = _call("Input.dispatchKeyEvent", {
            "type": "keyDown", "text": char, "key": char,
            "windowsVirtualKeyCode": ord(char) if len(char) == 1 else 0,
        })
        if "error" in r:
            return r
        _call("Input.dispatchKeyEvent", {"type": "keyUp", "key": char})
    return {"ok": True}


def click_coords(x: float, y: float) -> dict:
    """Click at specific page coordinates."""
    for evt in ("mousePressed", "mouseReleased"):
        r = _call("Input.dispatchMouseEvent", {
            "type": evt, "x": x, "y": y,
            "button": "left", "clickCount": 1,
        })
        if "error" in r:
            return r
    return {"ok": True}


def get_page_info() -> dict:
    """Get URL and title of the active tab."""
    result = _call("Runtime.evaluate", {
        "expression": "JSON.stringify({url: location.href, title: document.title})",
        "returnByValue": True,
    })
    if "error" in result:
        return result
    try:
        return json.loads(result.get("result", "{}"))
    except Exception:
        return result


def navigate(url: str) -> dict:
    result = _call("Page.navigate", {"url": url}, timeout=15.0)
    if "error" in result:
        return result
    time.sleep(1)
    return {"ok": True, "url": url}


def focus_element(selector: str) -> dict:
    """Focus a DOM element by CSS selector."""
    return evaluate(f"document.querySelector({json.dumps(selector)})?.focus(); 'ok'")


def fill_input(selector: str, text: str) -> dict:
    """Fill a React/Vue/Angular input properly using native setter + real key events."""
    # Set value via native setter (updates React state)
    js = f"""
    (function() {{
        const el = document.querySelector({json.dumps(selector)});
        if (!el) return 'not found';
        el.focus();
        const proto = el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
        if (setter) setter.call(el, {json.dumps(text)});
        else el.value = {json.dumps(text)};
        el.dispatchEvent(new Event('input', {{bubbles: true}}));
        el.dispatchEvent(new Event('change', {{bubbles: true}}));
        return 'ok';
    }})()
    """
    return evaluate(js)
