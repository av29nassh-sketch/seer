"""
Seer installer — adds Seer to Claude Code's MCP config automatically.
Run once after `pip install seer` (or `pip install -e .` for dev).

Usage:
    python install.py
"""

import json
import sys
from pathlib import Path


def find_claude_config() -> Path | None:
    """Find Claude Code's user config file."""
    candidates = [
        Path.home() / ".claude.json",                          # macOS / Linux / Windows
        Path.home() / "AppData" / "Roaming" / ".claude.json",  # Windows fallback
    ]
    for p in candidates:
        if p.exists():
            return p
    # Return the default path even if it doesn't exist yet
    return Path.home() / ".claude.json"


def main() -> None:
    config_path = find_claude_config()

    # Load existing config or start fresh
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Error: {config_path} exists but is not valid JSON. Fix it manually.")
            sys.exit(1)
    else:
        config = {}

    if "mcpServers" not in config:
        config["mcpServers"] = {}

    if "seer" in config["mcpServers"]:
        print("Seer is already configured in Claude Code.")
        print(f"  Config: {config_path}")
        print("  To reconfigure, remove the 'seer' entry and run this script again.")
        return

    # Use the exact Python that's running this script
    python_exe = sys.executable

    config["mcpServers"]["seer"] = {
        "type": "stdio",
        "command": python_exe,
        "args": ["-m", "seer"],
        "env": {},
    }

    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    print("Seer installed successfully.")
    print(f"  Config: {config_path}")
    print(f"  Python: {python_exe}")
    print()
    print("Restart Claude Code and Seer will be available as an MCP server.")


if __name__ == "__main__":
    main()
