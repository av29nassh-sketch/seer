"""UIA element tree extraction and filtering."""

from __future__ import annotations
from typing import Generator
import uiautomation as auto


_SKIP_CONTROL_TYPES = {
    auto.ControlType.PaneControl,
    auto.ControlType.GroupControl,
    auto.ControlType.SeparatorControl,
    auto.ControlType.ThumbControl,
    auto.ControlType.CustomControl,
}

_MAX_DEPTH = 6
_MAX_NODES = 150


def _is_useful(control: auto.Control) -> bool:
    if not control.IsEnabled:
        return False
    name = (control.Name or "").strip()
    ct = control.ControlType
    if ct in _SKIP_CONTROL_TYPES and not name:
        return False
    return True


def iter_tree(root: auto.Control, depth: int = 0, counter: list[int] | None = None) -> Generator[tuple[int, auto.Control, int], None, None]:
    """
    Yield (node_id, control, depth) for every useful element in the tree.
    node_id is stable — same walk order as get_active_window_tree().
    counter is shared state; pass None on first call.
    """
    if counter is None:
        counter = [0]
    if depth > _MAX_DEPTH or counter[0] >= _MAX_NODES:
        return

    if _is_useful(root):
        node_id = counter[0]
        counter[0] += 1
        yield node_id, root, depth
        for child in root.GetChildren():
            yield from iter_tree(child, depth + 1, counter)
    else:
        for child in root.GetChildren():
            yield from iter_tree(child, depth, counter)


def find_window_by_title(title: str) -> auto.Control | None:
    """Find the first top-level window whose title contains the given string (case-insensitive)."""
    title_lower = title.lower()
    for ctrl in auto.GetRootControl().GetChildren():
        if title_lower in (ctrl.Name or "").lower():
            return ctrl
    return None


def get_active_window_tree(window: str | None = None) -> dict:
    """Return a compact filtered element tree for the foreground window, or a named window."""
    if window:
        fw = find_window_by_title(window)
        if fw is None:
            return {"error": f"No window found matching '{window}'"}
    else:
        fw = auto.GetForegroundControl()
        if fw is None:
            return {"error": "No foreground window found"}

    nodes = []
    for node_id, control, depth in iter_tree(fw):
        node: dict = {
            "id": node_id,
            "name": (control.Name or "").strip(),
            "role": auto.ControlTypeNames.get(control.ControlType, "Unknown"),
            "value": "",
            "depth": depth,
        }
        try:
            vp = control.GetValuePattern()
            node["value"] = vp.Value or ""
        except Exception:
            pass
        nodes.append(node)

    return {
        "window_title": (fw.Name or "").strip(),
        "window_class": (fw.ClassName or "").strip(),
        "node_count": len(nodes),
        "truncated": len(nodes) >= _MAX_NODES,
        "tree": nodes,
    }
