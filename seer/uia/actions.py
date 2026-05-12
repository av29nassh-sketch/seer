"""UIA click and type actions."""

from __future__ import annotations
import ctypes
import re
import time
import uiautomation as auto
from .tree import iter_tree, find_window_by_title, get_snapshot

_SETTLE_MS = 0.25  # wait after every successful action so UI has time to redraw


def _settle() -> None:
    time.sleep(_SETTLE_MS)


_DESTRUCTIVE_PATTERNS = re.compile(
    r"\b(delete|remove|drop|destroy|erase|wipe|purge|"
    r"send|submit|post|publish|share|"
    r"buy|pay|checkout|order|transfer|"
    r"format|shutdown|restart|uninstall|kill|terminate|reset|"
    r"sign\s*out|log\s*out|close\s*account|deactivate)\b",
    re.IGNORECASE,
)


def _is_destructive(name: str) -> bool:
    return bool(name and _DESTRUCTIVE_PATTERNS.search(name))


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
    """
    Find the control matching the given tree node id.

    Resilient strategy:
      1. Walk live tree, look for matching id.
      2. If id matches but signature (name, role, parent_name) changed, ignore — tree shifted.
      3. If no exact id match, fall back to searching for the original signature by content.
    Returns None only if no candidate matches the original signature.
    """
    if window:
        fw = find_window_by_title(window)
    else:
        fw = auto.GetForegroundControl()
    if fw is None:
        return None

    snapshot = get_snapshot()
    target_sig = snapshot.get(target_id)

    id_match: auto.Control | None = None
    sig_match: auto.Control | None = None

    for node_id, control, _ in iter_tree(fw):
        if node_id == target_id and id_match is None:
            id_match = control
        if target_sig is not None:
            name = (control.Name or "").strip()
            role = auto.ControlTypeNames.get(control.ControlType, "Unknown")
            parent_name = ""
            try:
                p = control.GetParentControl()
                if p is not None:
                    parent_name = (p.Name or "").strip()
            except Exception:
                pass
            if (name, role, parent_name) == target_sig and sig_match is None:
                sig_match = control

    # Prefer signature match — survives tree shifts. Fall back to id match if no signature available.
    return sig_match or id_match


def click_element(element_id: int, window: str | None = None, confirm: bool = False) -> dict:
    """Click a UI element by its tree node id. Set confirm=True to proceed with destructive actions."""
    control = _find_by_id(element_id, window)
    if control is None:
        return {"error": f"Element id {element_id} not found in current window"}
    name = (control.Name or "").strip()
    if _is_destructive(name) and not confirm:
        return {
            "needs_confirmation": True,
            "element": name,
            "reason": f"'{name}' looks destructive — ask the user before proceeding, then re-call with confirm=True",
        }
    try:
        invoke = control.GetInvokePattern()
        invoke.Invoke()
        _settle()
        return {"success": True, "element": name, "method": "invoke"}
    except Exception:
        pass
    try:
        toggle = control.GetTogglePattern()
        toggle.Toggle()
        _settle()
        return {"success": True, "element": name, "method": "toggle"}
    except Exception:
        pass
    try:
        _move_cursor_to(control)
        control.Click()
        _settle()
        return {"success": True, "element": name, "method": "physical_click"}
    except Exception as e:
        return {"error": str(e)}


def double_click_element(element_id: int, window: str | None = None) -> dict:
    """Double-click a UI element by its tree node id."""
    control = _find_by_id(element_id, window)
    if control is None:
        return {"error": f"Element id {element_id} not found in current window"}
    name = (control.Name or "").strip()
    try:
        _move_cursor_to(control)
        control.DoubleClick()
        _settle()
        return {"success": True, "element": name, "method": "physical_doubleclick"}
    except Exception as e:
        return {"error": str(e)}


def click_at_coords(x: int, y: int, double: bool = False) -> dict:
    """Click at absolute screen coordinates — universal fallback when UIA can't find the target."""
    try:
        # Animated cursor move for visibility
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        sx, sy = pt.x, pt.y
        steps = 12
        for i in range(1, steps + 1):
            t = i / steps
            t = t * t * (3 - 2 * t)
            ctypes.windll.user32.SetCursorPos(int(sx + (x - sx) * t), int(sy + (y - sy) * t))
            time.sleep(0.01)

        # Mouse down + up
        MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP = 0x0002, 0x0004
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        if double:
            time.sleep(0.05)
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        _settle()
        return {"success": True, "x": x, "y": y, "double": double}
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
            _settle()
            return {"success": True, "method": "value_pattern"}
        except Exception:
            pass
        control.SendKeys(text)
        _settle()
        return {"success": True, "method": "send_keys"}
    except Exception as e:
        return {"error": str(e)}
