"""UIA element tree extraction and filtering."""

from __future__ import annotations
import uiautomation as auto


# Roles that are decorative / invisible — skip them to shrink the tree
_SKIP_CONTROL_TYPES = {
    auto.ControlType.PaneControl,    # generic containers that add noise
    auto.ControlType.GroupControl,
    auto.ControlType.SeparatorControl,
    auto.ControlType.ThumbControl,
    auto.ControlType.CustomControl,
}

_MAX_DEPTH = 6          # deeper than this and we're usually in decorative chrome
_MAX_NODES = 150        # hard cap — prevents context overflow for any LLM


def _is_useful(control: auto.Control) -> bool:
    """Return True if this element is worth including in the tree."""
    if not control.IsEnabled:
        return False
    if not control.IsOffscreen is False:
        # IsOffscreen == True means hidden; == False means visible
        # the property can also raise, so we check carefully
        pass
    name = (control.Name or "").strip()
    ct = control.ControlType
    if ct in _SKIP_CONTROL_TYPES and not name:
        return False
    return True


def _walk(control: auto.Control, depth: int, counter: list[int], nodes: list[dict]) -> None:
    if depth > _MAX_DEPTH or counter[0] >= _MAX_NODES:
        return
    if not _is_useful(control):
        for child in control.GetChildren():
            _walk(child, depth, counter, nodes)
        return

    node_id = counter[0]
    counter[0] += 1

    node = {
        "id": node_id,
        "name": (control.Name or "").strip(),
        "role": auto.ControlTypeNames.get(control.ControlType, "Unknown"),
        "value": "",
        "depth": depth,
    }

    # Try to get current value (text fields, combo boxes, etc.)
    try:
        vp = control.GetValuePattern()
        node["value"] = vp.Value or ""
    except Exception:
        pass

    nodes.append(node)

    for child in control.GetChildren():
        _walk(child, depth + 1, counter, nodes)


def get_active_window_tree() -> dict:
    """
    Return a compact, filtered element tree for the foreground window.
    """
    fw = auto.GetForegroundControl()
    if fw is None:
        return {"error": "No foreground window found"}

    nodes: list[dict] = []
    counter = [0]
    _walk(fw, depth=0, counter=counter, nodes=nodes)

    return {
        "window_title": (fw.Name or "").strip(),
        "window_class": (fw.ClassName or "").strip(),
        "node_count": len(nodes),
        "truncated": counter[0] >= _MAX_NODES,
        "tree": nodes,
    }
