"""Screen capture for the active window or full screen — universal fallback for apps UIA can't see."""

from __future__ import annotations
import base64
import ctypes
import io
import uiautomation as auto

try:
    from PIL import Image, ImageGrab
    _PIL_OK = True
except Exception:
    _PIL_OK = False


def _ensure_pil() -> str | None:
    if not _PIL_OK:
        return "Pillow not installed. Run: pip install pillow"
    return None


def capture_active_window() -> dict:
    """Capture the foreground window as a base64-encoded PNG."""
    err = _ensure_pil()
    if err:
        return {"error": err}

    fw = auto.GetForegroundControl()
    if fw is None:
        return {"error": "No foreground window"}

    rect = fw.BoundingRectangle
    bbox = (rect.left, rect.top, rect.right, rect.bottom)
    if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        return {"error": "Window has zero size"}

    try:
        img = ImageGrab.grab(bbox=bbox, all_screens=True)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return {
            "data": base64.b64encode(buf.getvalue()).decode(),
            "format": "png",
            "window": (fw.Name or "").strip(),
            "bbox": {"left": bbox[0], "top": bbox[1], "right": bbox[2], "bottom": bbox[3]},
        }
    except Exception as e:
        return {"error": str(e)}


def capture_screen() -> dict:
    """Capture the entire primary screen as a base64-encoded PNG."""
    err = _ensure_pil()
    if err:
        return {"error": err}
    try:
        img = ImageGrab.grab(all_screens=True)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return {
            "data": base64.b64encode(buf.getvalue()).decode(),
            "format": "png",
            "size": {"width": img.width, "height": img.height},
        }
    except Exception as e:
        return {"error": str(e)}
