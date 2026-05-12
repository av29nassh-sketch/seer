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

# Signature cache: id → (name, role, parent_name) for the most recent tree.
# Used by click/type to re-locate elements if the tree shifted between calls.
_LAST_SNAPSHOT: dict[int, tuple[str, str, str]] = {}


def get_snapshot() -> dict[int, tuple[str, str, str]]:
    return _LAST_SNAPSHOT


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
    _LAST_SNAPSHOT.clear()
    for node_id, control, depth in iter_tree(fw):
        name = (control.Name or "").strip()
        role = auto.ControlTypeNames.get(control.ControlType, "Unknown")
        parent_name = ""
        try:
            parent = control.GetParentControl()
            if parent is not None:
                parent_name = (parent.Name or "").strip()
        except Exception:
            pass
        node: dict = {"id": node_id, "name": name, "role": role, "value": "", "depth": depth}
        try:
            vp = control.GetValuePattern()
            node["value"] = vp.Value or ""
        except Exception:
            pass
        nodes.append(node)
        _LAST_SNAPSHOT[node_id] = (name, role, parent_name)

    rect = fw.BoundingRectangle
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    is_large = width > 600 and height > 400
    looks_broken = is_large and len(nodes) < 5
    class_name = (fw.ClassName or "").strip()
    # Common Electron / Chromium-derived window classes
    is_electron_like = class_name in {"Chrome_WidgetWin_1", "Chrome_WidgetWin_0", "Intermediate D3D Window"}

    result = {
        "window_title": (fw.Name or "").strip(),
        "window_class": class_name,
        "node_count": len(nodes),
        "truncated": len(nodes) >= _MAX_NODES,
        "tree": nodes,
    }
    if looks_broken or (is_electron_like and len(nodes) < 10):
        result["hint"] = (
            "UIA tree looks sparse — likely an Electron app (VS Code, Slack, Discord, Notion) "
            "or a custom-rendered UI. Use screenshot_window + click_at(x, y) as fallback."
        )
    return result
