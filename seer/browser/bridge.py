"""
Local HTTP bridge between the Chrome extension and the MCP server.

The extension polls GET /command for pending commands and POSTs results to /result.
MCP tools call send_command() which blocks until the extension responds.
"""

from __future__ import annotations
import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn


class _ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

PORT = 7842
_pending_command: dict | None = None
_pending_result: dict | None = None
_lock = threading.Lock()
_result_event = threading.Event()


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # silence access logs

    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        global _pending_command
        if self.path == '/ping':
            self._send(200, {'ok': True})
        elif self.path == '/command':
            with _lock:
                cmd = _pending_command
                _pending_command = None
            if cmd:
                self._send(200, cmd)
            else:
                self._send(204, {})
        else:
            self._send(404, {'error': 'not found'})

    def do_POST(self):
        global _pending_result
        if self.path == '/result':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            with _lock:
                _pending_result = body
            _result_event.set()
            self._send(200, {'ok': True})
        else:
            self._send(404, {'error': 'not found'})


def start(port: int = PORT) -> None:
    """Start the bridge server in a background daemon thread."""
    server = _ThreadingHTTPServer(('127.0.0.1', port), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()


def send_command(cmd: dict, timeout: float = 10.0) -> dict:
    """
    Send a command to the Chrome extension and wait for the result.
    Blocks until the extension responds or timeout expires.
    """
    global _pending_command, _pending_result
    with _lock:
        _pending_command = cmd
        _pending_result = None
    _result_event.clear()

    if not _result_event.wait(timeout):
        return {'ok': False, 'error': 'Browser extension did not respond (is it installed and Chrome open?)'}

    with _lock:
        result = _pending_result
    return result or {'ok': False, 'error': 'Empty response from extension'}
