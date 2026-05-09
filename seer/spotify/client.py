"""Spotify Web API calls — search, playback control."""

from __future__ import annotations
import json
import urllib.request
import urllib.parse
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
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            return json.loads(content) if content else {"ok": True}
    except urllib.error.HTTPError as e:
        body_text = e.read().decode()
        return {"error": f"HTTP {e.code}: {body_text}"}


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


def play(uri: str | None = None, device_id: str | None = None) -> dict:
    body: dict = {}
    if uri:
        body["uris"] = [uri]
    path = "/me/player/play"
    if device_id:
        path += f"?device_id={device_id}"
    return _request("PUT", path, body)


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


def get_devices() -> dict:
    result = _request("GET", "/me/player/devices")
    if "error" in result:
        return result
    return {"devices": result.get("devices", [])}
