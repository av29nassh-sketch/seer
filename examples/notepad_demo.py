"""
Notepad demo — run this with Notepad open to see Eyeva in action.

This is what Claude Code does behind the scenes when it uses Eyeva tools.
"""

import uiautomation as auto
import time
from eyeva.uia.tree import get_active_window_tree
from eyeva.uia.actions import type_into_element, click_element


def main():
    # Find and focus Notepad
    notepad = auto.WindowControl(searchDepth=1, ClassName="Notepad")
    if not notepad.Exists():
        print("Open Notepad first, then run this script.")
        return

    notepad.SetFocus()
    time.sleep(0.3)

    # Step 1: See the element tree
    print("=== Element Tree ===")
    tree = get_active_window_tree()
    print(f"Window: {tree['window_title']}")
    print(f"Nodes:  {tree['node_count']}")
    for node in tree["tree"][:15]:
        indent = "  " * node["depth"]
        val = f" = {node['value'][:40]!r}" if node["value"] else ""
        print(f"  {indent}[{node['id']}] {node['role']} | {node['name']}{val}")

    print()

    # Step 2: Find the text editor node (role=DocumentControl, name=Text Editor)
    editor_id = None
    for node in tree["tree"]:
        if node["role"] == "DocumentControl" and "editor" in node["name"].lower():
            editor_id = node["id"]
            break

    if editor_id is None:
        print("Could not find text editor element.")
        return

    print(f"=== Typing into element [{editor_id}] ===")
    result = type_into_element(editor_id, "Hello from Eyeva!\n")
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
