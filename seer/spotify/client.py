"""Spotify Web API calls — search, playback control."""

from __future__ import annotations
import json
import subprocess
import time
import urllib.request
import urllib.parse
import urllib.error
from .auth import get_access_token

_API = "https://api.spotify.com/v1"


def _request(method: str, path: str, body: dict | None = None) -> dict:
    token = get_access_token()
    url = f"{_API}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            return json.loads(content) if content else {"ok": True}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        return {"error": f"HTTP {e.code}: {body_text}"}
    except urllib.error.URLError as e:
        return {"error": f"Network error: {e.reason}"}
    except TimeoutError:
        return {"error": "Spotify API request timed out"}


def search(query: str, limit: int = 5) -> dict:
    params = urllib.parse.urlencode({"q": query, "type": "track", "limit": limit})
    result = _request("GET", f"/search?{params}")
    if "error" in result:
        return result
    tracks = result.get("tracks", {}).get("items", [])
    return {
        "results": [
            {
                "name": t["name"],
                "artist": ", ".join(a["name"] for a in t["artists"]),
                "album": t["album"]["name"],
                "uri": t["uri"],
                "duration_ms": t["duration_ms"],
            }
            for t in tracks
        ]
    }


def _ensure_active_device() -> str | None:
    """Launch Spotify if no active device, return device_id or None."""
    devices = get_devices().get("devices", [])
    if devices:
        active = next((d for d in devices if d.get("is_active")), devices[0])
        return active["id"]

    # Launch Spotify desktop
    import os
    spotify_exe = os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe")
    if os.path.exists(spotify_exe):
        subprocess.Popen([spotify_exe])
    else:
        subprocess.Popen(["cmd", "/c", "start", "spotify:"])

    # Wait up to 12s for a device to appear
    for _ in range(6):
        time.sleep(2)
        devices = get_devices().get("devices", [])
        if devices:
            # Activate it by transferring playback
            device_id = devices[0]["id"]
            _request("PUT", "/me/player", {"device_ids": [device_id], "play": False})
            time.sleep(1)
            return device_id

    return None


def play(uri: str | None = None, device_id: str | None = None) -> dict:
    body: dict = {}
    if uri:
        body["uris"] = [uri]
    path = "/me/player/play"
    if device_id:
        path += f"?device_id={device_id}"
    result = _request("PUT", path, body)
    # Only pay the device-lookup cost if no active device
    if "error" in result and "NO_ACTIVE_DEVICE" in result.get("error", ""):
        device_id = _ensure_active_device()
        if device_id:
            path = f"/me/player/play?device_id={device_id}"
            result = _request("PUT", path, body)
    return result


def pause() -> dict:
    return _request("PUT", "/me/player/pause")


def next_track() -> dict:
    return _request("POST", "/me/player/next")


def previous_track() -> dict:
    return _request("POST", "/me/player/previous")


def get_current() -> dict:
    result = _request("GET", "/me/player/currently-playing")
    if "error" in result or not result:
        return result or {"playing": False}
    item = result.get("item")
    if not item:
        return {"playing": False}
    return {
        "playing": result.get("is_playing", False),
        "name": item["name"],
        "artist": ", ".join(a["name"] for a in item["artists"]),
        "album": item["album"]["name"],
        "uri": item["uri"],
        "progress_ms": result.get("progress_ms", 0),
        "duration_ms": item["duration_ms"],
    }


def play_context(context_uri: str) -> dict:
    """Play a Spotify context (playlist, album, artist, or liked songs collection)."""
    devices = get_devices().get("devices", [])
    device_id = None
    if devices:
        active = next((d for d in devices if d.get("is_active")), devices[0])
        device_id = active["id"]

    body: dict = {"context_uri": context_uri}
    path = "/me/player/play"
    if device_id:
        path += f"?device_id={device_id}"
    result = _request("PUT", path, body)
    if "error" in result and "NO_ACTIVE_DEVICE" in result.get("error", ""):
        device_id = _ensure_active_device()
        if device_id:
            result = _request("PUT", f"/me/player/play?device_id={device_id}", body)
    return result


def get_current_user() -> dict:
    return _request("GET", "/me")


def get_devices() -> dict:
    result = _request("GET", "/me/player/devices")
    if "error" in result:
        return result
    return {"devices": result.get("devices", [])}
