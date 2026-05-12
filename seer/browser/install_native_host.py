"""
Install the Seer Native Messaging Host on Windows.

What this does:
  1. Generates a launcher .bat that runs `python -m seer.browser.native_host`
  2. Writes a Native Messaging manifest JSON pointing to that launcher
  3. Registers the manifest in HKCU\\Software\\Google\\Chrome\\NativeMessagingHosts\\com.seer.host

After running, install/load the Seer Bridge extension in Chrome — it'll auto-connect on startup.
The extension ID must be in `allowed_origins`. Pass it as the first argument or set SEER_EXTENSION_ID.
"""

from __future__ import annotations
import json
import os
import sys
from pathlib import Path

HOST_NAME = "com.seer.host"


def install(extension_id: str) -> str:
    if not extension_id:
        raise SystemExit("Extension ID required. Load the unpacked extension in chrome://extensions, copy its ID, then re-run.")

    home = Path.home() / ".seer"
    home.mkdir(parents=True, exist_ok=True)

    # Launcher .bat — uses the current Python interpreter
    py = sys.executable
    bat = home / "native_host.bat"
    bat.write_text(f'@echo off\r\n"{py}" -m seer.browser.native_host\r\n', encoding="utf-8")

    # Manifest
    manifest = {
        "name": HOST_NAME,
        "description": "Seer Bridge native messaging host",
        "path": str(bat),
        "type": "stdio",
        "allowed_origins": [f"chrome-extension://{extension_id}/"],
    }
    manifest_path = home / f"{HOST_NAME}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Register in Windows registry under HKCU
    import winreg
    key_path = rf"Software\Google\Chrome\NativeMessagingHosts\{HOST_NAME}"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValue(key, "", winreg.REG_SZ, str(manifest_path))

    return str(manifest_path)


def main() -> None:
    ext_id = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SEER_EXTENSION_ID", "")
    path = install(ext_id)
    print(f"Native messaging host registered.")
    print(f"  Manifest: {path}")
    print(f"  Extension ID: {ext_id}")
    print(f"\nReload the Seer Bridge extension in chrome://extensions to pick up the new connection.")


if __name__ == "__main__":
    main()
