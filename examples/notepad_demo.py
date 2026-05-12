"""
Notepad demo — direct Seer library usage. Confirms install + UIA tools work end-to-end.

Run this with Notepad open. You should see the element tree print, then text appear in Notepad.

  python examples/notepad_demo.py
"""

from __future__ import annotations
import time

import uiautomation as auto

from seer.uia.tree import get_active_window_tree
from seer.uia.actions import type_into_element


def main() -> None:
    # Find and focus Notepad
    notepad = auto.WindowControl(searchDepth=1, ClassName="Notepad")
    if not notepad.Exists():
        print("Open Notepad first, then run this script.")
        return

    notepad.SetFocus()
    time.sleep(0.3)

    # Step 1: See the element tree the way an agent would
    print("=== Element Tree ===")
    tree = get_active_window_tree()
    print(f"Window: {tree['window_title']}")
    print(f"Nodes:  {tree['node_count']}")
    for node in tree["tree"][:15]:
        indent = "  " * node["depth"]
        val = f" = {node['value'][:40]!r}" if node["value"] else ""
        print(f"  {indent}[{node['id']}] {node['role']} | {node['name']}{val}")

    # Step 2: Find the text editor element (DocumentControl with "editor" in name)
    editor_id = None
    for node in tree["tree"]:
        if node["role"] == "DocumentControl" and "editor" in node["name"].lower():
            editor_id = node["id"]
            break

    if editor_id is None:
        print("\nCould not find text editor element. Layout may have changed.")
        return

    # Step 3: Type into it. This is what `mcp__seer__type_text` does when called by an agent.
    print(f"\n=== Typing into element [{editor_id}] ===")
    result = type_into_element(editor_id, "Hello from Seer!\n")
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
