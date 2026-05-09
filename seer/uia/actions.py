"""UIA click and type actions."""

from __future__ import annotations
import ctypes
import time
import uiautomation as auto
from .tree import iter_tree, find_window_by_title


def _move_cursor_to(control: auto.Control) -> None:
    """Smoothly move the physical mouse cursor to the center of the element."""
    try:
        rect = control.BoundingRectangle
        cx = rect.left + (rect.right - rect.left) // 2
        cy = rect.top + (rect.bottom - rect.top) // 2

        # Get current cursor position
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        sx, sy = pt.x, pt.y

        # Animate 12 steps over ~120ms
        steps = 12
        for i in range(1, steps + 1):
            t = i / steps
            # Ease in-out
            t = t * t * (3 - 2 * t)
            mx = int(sx + (cx - sx) * t)
            my = int(sy + (cy - sy) * t)
            ctypes.windll.user32.SetCursorPos(mx, my)
            time.sleep(0.01)
    except Exception:
        pass


def _find_by_id(target_id: int, window: str | None = None) -> auto.Control | None:
    """Find the control with the given tree node id in the foreground window or a named window."""
    if window:
        fw = find_window_by_title(window)
    else:
        fw = auto.GetForegroundControl()
    if fw is None:
        return None
    for node_id, control, _ in iter_tree(fw):
        if node_id == target_id:
            return control
    return None


def click_element(element_id: int, window: str | None = None) -> dict:
    """Click a UI element by its tree node id."""
    control = _find_by_id(element_id, window)
    if control is None:
        return {"error": f"Element id {element_id} not found in current window"}
    try:
        _move_cursor_to(control)
        control.Click()
        return {"success": True, "element": (control.Name or "").strip()}
    except Exception as e:
        return {"error": str(e)}


def double_click_element(element_id: int, window: str | None = None) -> dict:
    """Double-click a UI element by its tree node id."""
    control = _find_by_id(element_id, window)
    if control is None:
        return {"error": f"Element id {element_id} not found in current window"}
    try:
        _move_cursor_to(control)
        control.DoubleClick()
        return {"success": True, "element": (control.Name or "").strip()}
    except Exception as e:
        return {"error": str(e)}


def type_into_element(element_id: int, text: str, window: str | None = None) -> dict:
    """Type text into a UI element by its tree node id."""
    control = _find_by_id(element_id, window)
    if control is None:
        return {"error": f"Element id {element_id} not found in current window"}
    try:
        control.SetFocus()
        try:
            vp = control.GetValuePattern()
            vp.SetValue(text)
            return {"success": True, "method": "value_pattern"}
        except Exception:
            pass
        control.SendKeys(text)
        return {"success": True, "method": "send_keys"}
    except Exception as e:
        return {"error": str(e)}
