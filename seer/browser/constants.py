"""Shared constants for the seer browser bridge."""

from __future__ import annotations
from pathlib import Path

TCP_HOST = "127.0.0.1"
TCP_PORT = 7843
MAX_MSG_BYTES = 8 * 1024 * 1024  # 8 MiB cap on framed messages — prevents DoS via huge claimed length

SEER_DIR = Path.home() / ".seer"
TOKEN_PATH = SEER_DIR / "token"  # shared secret for TCP auth
