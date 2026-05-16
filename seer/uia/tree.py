"""UIA element tree extraction and filtering."""

from __future__ import annotations
import threading
from typing import Generator
import uiautomation as auto

from .redact import redact


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
# Locked because async MCP handlers can call tree extraction concurrently in executor threads.
_LAST_SNAPSHOT: dict[int, tuple[str, str, str]] = {}

# Live Control cache: id → COM Control reference. Populated by get_active_window_tree.
# Fast path for click/type — avoids re-walking the whole tree per action.
# Invalidated implicitly when the next get_active_window_tree call runs.
_LIVE_CONTROLS: dict[int, auto.Control] = {}

_snapshot_lock = threading.Lock()


def get_snapshot() -> dict[int, tuple[str, str, str]]:
    with _snapshot_lock:
        return dict(_LAST_SNAPSHOT)


def get_cached_control(target_id: int) -> auto.Control | None:
    """Return the cached live Control for an id, or None if missing or stale."""
    with _snapshot_lock:
        return _LIVE_CONTROLS.get(target_id)


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
    """Find a top-level window whose title contains the given string (case-insensitive).

    Uses uiautomation's native UIA-engine search (SubName + a short timeout) instead of
    enumerating every desktop child in Python — the latter costs ~2.5s on a busy desktop
    because each window's .Name is a separate COM round-trip.
    """
    # SubName = case-insensitive substring match, evaluated inside the UIA engine.
    win = auto.WindowControl(searchDepth=1, SubName=title)
    if win.Exists(maxSearchSeconds=1.5, searchIntervalSeconds=0.1):
        return win

    # Fallback: pane-type top-level windows (some apps aren't WindowControl), still
    # via native search rather than full Python enumeration.
    pane = auto.PaneControl(searchDepth=1, SubName=title)
    if pane.Exists(maxSearchSeconds=0.5, searchIntervalSeconds=0.1):
        return pane
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
    fresh_snapshot: dict[int, tuple[str, str, str]] = {}
    fresh_controls: dict[int, auto.Control] = {}
    for node_id, control, depth in iter_tree(fw):
        raw_name = (control.Name or "").strip()
        role = auto.ControlTypeNames.get(control.ControlType, "Unknown")
        raw_parent = ""
        try:
            parent = control.GetParentControl()
            if parent is not None:
                raw_parent = (parent.Name or "").strip()
        except Exception:
            pass
        raw_value = ""
        try:
            vp = control.GetValuePattern()
            raw_value = vp.Value or ""
        except Exception:
            pass

        # Redact secrets before exposing to the agent. Snapshot keeps the *redacted*
        # signature so click/type still match the same node — agent only ever sees redacted text.
        name = redact(raw_name)
        value = redact(raw_value)
        parent_name = redact(raw_parent)

        nodes.append({"id": node_id, "name": name, "role": role, "value": value, "depth": depth})
        fresh_snapshot[node_id] = (name, role, parent_name)
        fresh_controls[node_id] = control

    # Publish snapshot + live controls atomically.
    with _snapshot_lock:
        _LAST_SNAPSHOT.clear()
        _LAST_SNAPSHOT.update(fresh_snapshot)
        _LIVE_CONTROLS.clear()
        _LIVE_CONTROLS.update(fresh_controls)

    rect = fw.BoundingRectangle
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    is_large = width > 600 and height > 400
    looks_broken = is_large and len(nodes) < 5
    class_name = (fw.ClassName or "").strip()
    # Common Electron / Chromium-derived window classes
    is_electron_like = class_name in {"Chrome_WidgetWin_1", "Chrome_WidgetWin_0", "Intermediate D3D Window"}

    result = {
        "window_title": redact((fw.Name or "").strip()),
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
