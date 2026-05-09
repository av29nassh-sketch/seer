"""UIA click and type actions."""

from __future__ import annotations
import uiautomation as auto
from .tree import iter_tree


def _find_by_id(target_id: int) -> auto.Control | None:
    """Find the control with the given tree node id in the foreground window."""
    fw = auto.GetForegroundControl()
    if fw is None:
        return None
    for node_id, control, _ in iter_tree(fw):
        if node_id == target_id:
            return control
    return None


def click_element(element_id: int) -> dict:
    """Click a UI element by its tree node id."""
    control = _find_by_id(element_id)
    if control is None:
        return {"error": f"Element id {element_id} not found in current window"}
    try:
        control.Click()
        return {"success": True, "element": (control.Name or "").strip()}
    except Exception as e:
        return {"error": str(e)}


def type_into_element(element_id: int, text: str) -> dict:
    """Type text into a UI element by its tree node id."""
    control = _find_by_id(element_id)
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
