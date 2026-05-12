"""One-time Spotify OAuth setup — run once to get a refresh token."""

import json
import urllib.parse
import urllib.request
import webbrowser
from .auth import save_config

_REDIRECT_URI = "http://127.0.0.1:8888/callback"
_SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
_AUTH_URL = "https://accounts.spotify.com/authorize"
_TOKEN_URL = "https://accounts.spotify.com/api/token"


def run():
    print("=== Seer Spotify Setup ===\n")
    client_id = input("Paste your Spotify Client ID: ").strip()
    client_secret = input("Paste your Spotify Client Secret: ").strip()

    params = urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": _REDIRECT_URI,
        "scope": _SCOPE,
    })
    auth_url = f"{_AUTH_URL}?{params}"
    print("\nOpening browser for Spotify authorization...")
    webbrowser.open(auth_url)

    print("\nAfter you click 'Agree' in the browser, Spotify will redirect to a")
    print("page that fails to load (localhost). That's expected.")
    print("Copy the full URL from your browser's address bar and paste it here.\n")
    callback_url = input("Paste the full redirect URL: ").strip()

    parsed = urllib.parse.urlparse(callback_url)
    params_out = urllib.parse.parse_qs(parsed.query)
    code = params_out.get("code", [None])[0]
    if not code:
        print("Error: no 'code' found in the URL. Make sure you copied the full URL.")
        return

    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": _REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret,
    }).encode()

    req = urllib.request.Request(_TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req) as resp:
            token_data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"Token exchange failed ({e.code}): {e.read().decode()}")
        return

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        print("Error: no refresh token in response.")
        return

    save_config(client_id, client_secret, refresh_token)
    print("\nSpotify connected successfully. Credentials saved to ~/.seer/spotify.json")


if __name__ == "__main__":
    run()
