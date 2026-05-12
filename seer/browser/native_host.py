"""
Native Messaging Host — runs as a child process spawned by Chrome.

Architecture (inverted from typical NM): the native_host is also a TCP server on
localhost:7843. ANY seer MCP process connects to it to send browser commands.
This solves the multi-seer-process problem (Claude Code spawns 2+ seer processes,
each can call us via TCP without fighting over a named pipe).

Flow:
  seer ──TCP──> native_host ──stdout(NM)──> Chrome extension
  seer <──TCP── native_host <──stdin(NM)── Chrome extension

We process one TCP request at a time (sequential). Each request:
  1. Read framed JSON command from TCP client
  2. Forward to Chrome via stdout (NM 4-byte length + JSON)
  3. Read framed JSON response from Chrome via stdin
  4. Forward to TCP client
  5. Close client (next one accepted)
"""

from __future__ import annotations
import json
import socket
import struct
import sys
import threading
import time
from pathlib import Path

if sys.platform == "win32":
    import msvcrt
    import os as _os
    msvcrt.setmode(sys.stdin.fileno(), _os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), _os.O_BINARY)

TCP_HOST = "127.0.0.1"
TCP_PORT = 7843


def _log(msg: str) -> None:
    try:
        log_path = Path.home() / ".seer" / "native_host.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            import os
            f.write(f"[{time.strftime('%H:%M:%S')}] pid={os.getpid()} {msg}\n")
    except Exception:
        pass


# Stdin/stdout to Chrome (Native Messaging protocol)
_chrome_lock = threading.Lock()  # serialize stdout writes


def _read_chrome():
    raw_len = sys.stdin.buffer.read(4)
    if len(raw_len) < 4:
        return None
    msg_len = struct.unpack("<I", raw_len)[0]
    raw = sys.stdin.buffer.read(msg_len)
    if len(raw) < msg_len:
        return None
    return json.loads(raw.decode("utf-8"))


def _write_chrome(obj: dict) -> None:
    data = json.dumps(obj).encode("utf-8")
    with _chrome_lock:
        sys.stdout.buffer.write(struct.pack("<I", len(data)))
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()


# TCP framing: 4-byte LE length + JSON
def _read_tcp(sock) -> dict | None:
    try:
        raw_len = b""
        while len(raw_len) < 4:
            chunk = sock.recv(4 - len(raw_len))
            if not chunk:
                return None
            raw_len += chunk
        msg_len = struct.unpack("<I", raw_len)[0]
        raw = b""
        while len(raw) < msg_len:
            chunk = sock.recv(msg_len - len(raw))
            if not chunk:
                return None
            raw += chunk
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


def _write_tcp(sock, obj: dict) -> bool:
    try:
        data = json.dumps(obj).encode("utf-8")
        sock.sendall(struct.pack("<I", len(data)) + data)
        return True
    except Exception:
        return False


# Pending TCP client awaiting Chrome's response. Set by handle_tcp_client, cleared by chrome reader.
_pending_lock = threading.Lock()
_pending_sock = None


def _chrome_reader_loop() -> None:
    """Read responses from Chrome and route to the pending TCP client."""
    global _pending_sock
    while True:
        msg = _read_chrome()
        if msg is None:
            _log("chrome stdin EOF — exiting")
            return
        with _pending_lock:
            sock = _pending_sock
            _pending_sock = None
        if sock is None:
            _log("got chrome response but no pending TCP client — discarding")
            continue
        _write_tcp(sock, msg)
        try:
            sock.close()
        except Exception:
            pass


def _handle_tcp_client(sock) -> None:
    """One request per connection: read cmd → forward to Chrome → wait for chrome response → write to socket → close."""
    global _pending_sock
    try:
        cmd = _read_tcp(sock)
        if cmd is None:
            return
        with _pending_lock:
            _pending_sock = sock
        _write_chrome(cmd)
        # Reader thread will write to sock + close it
    except Exception as e:
        _log(f"handle_tcp_client error: {e}")
        try:
            sock.close()
        except Exception:
            pass


def _tcp_server_loop() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((TCP_HOST, TCP_PORT))
    except OSError as e:
        _log(f"TCP bind failed: {e}")
        return
    server.listen(8)
    _log(f"TCP listening on {TCP_HOST}:{TCP_PORT}")
    while True:
        try:
            client, _ = server.accept()
        except Exception as e:
            _log(f"accept failed: {e}")
            return
        threading.Thread(target=_handle_tcp_client, args=(client,), daemon=True).start()


def main() -> None:
    _log("native_host start")
    threading.Thread(target=_tcp_server_loop, daemon=True).start()
    # Block on chrome stdin reader (main thread). Exits when Chrome closes the port.
    _chrome_reader_loop()
    _log("native_host exit")


if __name__ == "__main__":
    main()
