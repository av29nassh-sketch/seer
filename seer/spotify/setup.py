"""One-time Spotify OAuth setup — run once to get a refresh token."""

import json
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from .auth import save_config

_REDIRECT_URI = "http://localhost:8888/callback"
_SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
_AUTH_URL = "https://accounts.spotify.com/authorize"
_TOKEN_URL = "https://accounts.spotify.com/api/token"

_auth_code: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2>Spotify connected! You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h2>Error: no code in callback.</h2>")

    def log_message(self, *args):
        pass


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
    print(f"\nOpening browser for authorization...")
    webbrowser.open(auth_url)

    print("Waiting for callback on http://localhost:8888/callback ...")
    server = HTTPServer(("localhost", 8888), _CallbackHandler)
    server.handle_request()

    if not _auth_code:
        print("Error: did not receive auth code.")
        return

    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": _auth_code,
        "redirect_uri": _REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret,
    }).encode()

    req = urllib.request.Request(_TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req) as resp:
        token_data = json.loads(resp.read())

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        print("Error: no refresh token in response.")
        return

    save_config(client_id, client_secret, refresh_token)
    print("\nSpotify connected successfully. Credentials saved to ~/.seer/spotify.json")


if __name__ == "__main__":
    run()
