"""
Build seer into three standalone .exe files using PyInstaller.

Outputs (in installer/dist/):
  - seer.exe              — MCP server, console (stdin/stdout transport)
  - seer-tray.exe         — System tray app, windowed (no console)
  - seer-native-host.exe  — Chrome native messaging host, console

Usage:
  python installer/build.py
"""

from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INSTALLER_DIR = Path(__file__).resolve().parent
DIST = INSTALLER_DIR / "dist"
BUILD = INSTALLER_DIR / "build"


COMMON_HIDDEN_IMPORTS = [
    "mcp.server",
    "mcp.server.stdio",
    "mcp.server.models",
    "mcp.types",
    "seer.browser.bridge",
    "seer.browser.cdp",
    "seer.browser.constants",
    "seer.browser.native_host",
    "seer.browser.token",
    "seer.spotify.client",
    "seer.spotify.auth",
    "seer.uia.tree",
    "seer.uia.actions",
    "seer.uia.screenshot",
]


def _run_pyinstaller(entry: str, name: str, *, windowed: bool, extra_imports: list[str] | None = None) -> None:
    """Invoke PyInstaller for a single target. Cleans previous build first."""
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name", name,
        "--distpath", str(DIST),
        "--workpath", str(BUILD),
        "--specpath", str(INSTALLER_DIR),
    ]
    if windowed:
        args.append("--windowed")
    for mod in COMMON_HIDDEN_IMPORTS + (extra_imports or []):
        args.extend(["--hidden-import", mod])
    args.append(entry)
    print(f"\n=== Building {name} ===")
    print(" ".join(args))
    result = subprocess.run(args, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(f"PyInstaller failed for {name}")


def _copy_extension() -> None:
    """Copy the Chrome extension folder next to the .exes so the installer can ship it."""
    src = ROOT / "seer" / "browser" / "extension"
    dst = DIST / "extension"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"copied extension to {dst}")


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)

    # MCP server (console — needs stdio for the MCP transport)
    _run_pyinstaller(
        entry=str(ROOT / "seer" / "__main__.py"),
        name="seer",
        windowed=False,
    )

    # Tray app (windowed — no console)
    _run_pyinstaller(
        entry=str(ROOT / "seer" / "tray.py"),
        name="seer-tray",
        windowed=True,
        extra_imports=["pystray._win32", "PIL.ImageDraw", "PIL.Image"],
    )

    # Native messaging host (console — needs stdio for Chrome NM protocol)
    _run_pyinstaller(
        entry=str(ROOT / "seer" / "browser" / "native_host.py"),
        name="seer-native-host",
        windowed=False,
    )

    _copy_extension()

    print("\n[OK] Build complete")
    print(f"  Output: {DIST}")
    for f in sorted(DIST.iterdir()):
        print(f"    {f.name}")


if __name__ == "__main__":
    main()
