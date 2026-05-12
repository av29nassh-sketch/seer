"""Shared-secret token for bridge ↔ native_host authentication.

Stored in ~/.seer/token with 0600 permissions. Generated on first use.
Both processes read the same file; clients must present the token in the first frame.
"""

from __future__ import annotations
import os
import secrets
import stat
import sys

from .constants import TOKEN_PATH, SEER_DIR


def _restrict_perms(path) -> None:
    """Best-effort: chmod 0600 on POSIX, owner-only ACL on Windows."""
    try:
        if sys.platform == "win32":
            # Windows: rely on default user-profile ACLs (already restricted to current user).
            # Setting NTFS ACLs cleanly requires pywin32 work — default is acceptable.
            pass
        else:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


def get_or_create() -> str:
    """Return the current token, generating + persisting one if missing."""
    SEER_DIR.mkdir(parents=True, exist_ok=True)
    try:
        existing = TOKEN_PATH.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    except FileNotFoundError:
        pass
    token = secrets.token_urlsafe(32)
    TOKEN_PATH.write_text(token, encoding="utf-8")
    _restrict_perms(TOKEN_PATH)
    return token
