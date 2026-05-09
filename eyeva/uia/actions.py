"""UIA click and type actions."""

from __future__ import annotations
import uiautomation as auto
from .tree import get_active_window_tree


def _find_by_id(target_id: int) -> auto.Control | None:
    """Walk the foreground window tree to find element with the given tree node id."""
    fw = auto.GetForegroundControl()
    if fw is None:
        return None

    counter = [0]

    def _walk(control: auto.Control) -> auto.Control | None:
        if counter[0] == target_id:
            return control
        counter[0] += 1
        for child in control.GetChildren():
            result = _walk(child)
            if result is not None:
                return result
        return None

    return _walk(fw)


def click_element(element_id: int) -> dict:
    """
    Click a UI element by its tree node id.
    Returns {"success": True} or {"error": "reason"}.
    """
    control = _find_by_id(element_id)
    if control is None:
        return {"error": f"Element id {element_id} not found in current window"}
    try:
        control.Click()
        return {"success": True, "element": (control.Name or "").strip()}
    except Exception as e:
        return {"error": str(e)}


def type_into_element(element_id: int, text: str) -> dict:
    """
    Type text into a UI element by its tree node id.
    Focuses the element first, then sends keystrokes.
    Returns {"success": True} or {"error": "reason"}.
    """
    control = _find_by_id(element_id)
    if control is None:
        return {"error": f"Element id {element_id} not found in current window"}
    try:
        control.SetFocus()
        # Try value pattern first (faster, no keyboard events)
        try:
            vp = control.GetValuePattern()
            vp.SetValue(text)
            return {"success": True, "method": "value_pattern"}
        except Exception:
            pass
        # Fall back to SendKeys
        control.SendKeys(text)
        return {"success": True, "method": "send_keys"}
    except Exception as e:
        return {"error": str(e)}
