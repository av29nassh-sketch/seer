"""Spotify OAuth token management — stores refresh token locally, auto-refreshes access token."""

from __future__ import annotations
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

_CONFIG_PATH = Path.home() / ".seer" / "spotify.json"
_TOKEN_URL = "https://accounts.spotify.com/api/token"

_cache: dict = {"access_token": None, "expires_at": 0}


def _load_config() -> dict:
    if not _CONFIG_PATH.exists():
        raise RuntimeError(
            "Spotify not configured. Run: python -m seer.spotify.setup"
        )
    return json.loads(_CONFIG_PATH.read_text())


def get_access_token() -> str:
    if _cache["access_token"] and time.time() < _cache["expires_at"] - 30:
        return _cache["access_token"]

    cfg = _load_config()
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": cfg["refresh_token"],
        "client_id": cfg["client_id"],
        "client_secret": cfg["client_secret"],
    }).encode()

    req = urllib.request.Request(_TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        token_data = json.loads(resp.read())

    _cache["access_token"] = token_data["access_token"]
    _cache["expires_at"] = time.time() + token_data.get("expires_in", 3600)
    return _cache["access_token"]


def save_config(client_id: str, client_secret: str, refresh_token: str) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(json.dumps({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }, indent=2))
