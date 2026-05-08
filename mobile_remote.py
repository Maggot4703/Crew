"""LAN-only mobile remote for Crew."""

from __future__ import annotations

import html
import json
import logging
import secrets
import socket
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Optional
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger("CrewMobileRemote")


def detect_lan_ip() -> str:
    """Return the best-effort LAN IP address for this machine."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return str(sock.getsockname()[0])
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


class CrewMobileRemoteServer:
    """Serve a simple touch-friendly Crew remote over HTTP."""

    def __init__(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 0,
        token: Optional[str] = None,
        status_callback: Optional[Callable[[], dict[str, Any]]] = None,
        action_callback: Optional[
            Callable[[str, dict[str, Any]], dict[str, Any]]
        ] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.token = token or secrets.token_urlsafe(12)
        self.status_callback = status_callback or (lambda: {})
        self.action_callback = action_callback or (lambda action, payload: {})
        self.httpd: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None

    @property
    def is_running(self) -> bool:
        """Return whether the server is active."""
        return self.httpd is not None and self.thread is not None

    @property
    def access_url(self) -> str:
        """Return the LAN URL for the current server."""
        if not self.httpd:
            return ""
        return f"http://{detect_lan_ip()}:{self.httpd.server_address[1]}/?token={self.token}"

    def start(self) -> str:
        """Start the HTTP server and return the access URL."""
        if self.httpd is not None:
            return self.access_url

        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                if not server._is_authorized(params):
                    server._write_json(
                        self, HTTPStatus.FORBIDDEN, {"error": "invalid token"}
                    )
                    return

                if parsed.path == "/api/status":
                    server._write_json(self, HTTPStatus.OK, server.status_callback())
                    return

                if parsed.path not in {"/", "/index.html"}:
                    server._write_json(
                        self, HTTPStatus.NOT_FOUND, {"error": "not found"}
                    )
                    return

                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    server.render_html(
                        server.status_callback(), params.get("message", [""])[0]
                    ).encode("utf-8")
                )

            def do_POST(self) -> None:  # noqa: N802
                parsed = urlparse(self.path)
                if parsed.path != "/api/action":
                    server._write_json(
                        self, HTTPStatus.NOT_FOUND, {"error": "not found"}
                    )
                    return

                content_length = int(self.headers.get("Content-Length", "0") or 0)
                raw_body = self.rfile.read(content_length).decode("utf-8")
                params = parse_qs(raw_body)
                if not server._is_authorized(params):
                    server._write_json(
                        self, HTTPStatus.FORBIDDEN, {"error": "invalid token"}
                    )
                    return

                action = params.get("action", [""])[0]
                payload = {
                    key: values[0] if len(values) == 1 else values
                    for key, values in params.items()
                    if key not in {"token", "action"}
                }
                result = server.action_callback(action, payload)
                accepts_json = "application/json" in self.headers.get("Accept", "")
                wants_json = accepts_json or params.get("format", [""])[0] == "json"
                if wants_json:
                    server._write_json(self, HTTPStatus.OK, result)
                    return

                message = result.get("message", "Action completed.")
                self.send_response(HTTPStatus.SEE_OTHER)
                self.send_header(
                    "Location", f"/?token={server.token}&message={message}"
                )
                self.end_headers()

            def log_message(self, format: str, *args: Any) -> None:
                logger.debug("Crew mobile remote: " + format, *args)

        self.httpd = ThreadingHTTPServer((self.host, self.port), Handler)
        self.thread = threading.Thread(
            target=self.httpd.serve_forever, name="CrewMobileRemote", daemon=True
        )
        self.thread.start()
        logger.info("Crew mobile remote started at %s", self.access_url)
        return self.access_url

    def stop(self) -> None:
        """Stop the HTTP server if it is running."""
        if not self.httpd:
            return
        self.httpd.shutdown()
        self.httpd.server_close()
        self.httpd = None
        self.thread = None
        logger.info("Crew mobile remote stopped.")

    def _is_authorized(self, params: dict[str, list[str]]) -> bool:
        return params.get("token", [""])[0] == self.token

    def _write_json(
        self,
        handler: BaseHTTPRequestHandler,
        status: HTTPStatus,
        payload: dict[str, Any],
    ) -> None:
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.end_headers()
        handler.wfile.write(json.dumps(payload).encode("utf-8"))

    def render_html(self, status: dict[str, Any], message: str = "") -> str:
        """Render the touch-friendly remote page."""
        escaped_message = html.escape(message or "")
        escaped_status = html.escape(str(status.get("status", "Ready")))
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Crew Mobile Remote</title>
  <style>
    body {{
      background: #111827;
      color: #f9fafb;
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 1rem;
    }}
    .card {{
      background: #1f2937;
      border-radius: 14px;
      margin-bottom: 1rem;
      padding: 1rem;
    }}
    h1, h2 {{
      margin-top: 0;
    }}
    .status {{
      font-size: 1.1rem;
      line-height: 1.5;
    }}
    button, input, select {{
      border: 0;
      border-radius: 12px;
      box-sizing: border-box;
      font-size: 1rem;
      margin-top: 0.5rem;
      min-height: 48px;
      padding: 0.85rem 1rem;
      width: 100%;
    }}
    button {{
      background: #2563eb;
      color: white;
      font-weight: bold;
    }}
    .secondary {{
      background: #374151;
    }}
    .message {{
      color: #86efac;
      font-weight: bold;
      min-height: 1.5rem;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Crew Mobile Remote</h1>
    <div class="status"><strong>Status:</strong> {escaped_status}</div>
    <div class="status"><strong>LAN URL:</strong> {html.escape(self.access_url)}</div>
    <div class="message">{escaped_message}</div>
  </div>
  <div class="card">
    <h2>Quick Actions</h2>
    {self._action_form('open_chatbot', 'Open Chatbot')}
    {self._action_form('open_crew_chat', 'Open Crew Chat')}
    {self._action_form('read_status', 'Read Status Aloud')}
    {self._action_form('stop_reading', 'Stop Reading', css_class='secondary')}
  </div>
  <div class="card">
    <h2>Send Crew Message</h2>
    <form method="post" action="/api/action">
      <input type="hidden" name="token" value="{html.escape(self.token)}">
      <input type="hidden" name="action" value="send_crew_message">
      <input type="text" name="sender" value="Mobile" placeholder="Sender">
      <input type="text" name="recipient" value="All" placeholder="Recipient">
      <input type="text" name="text" placeholder="Message to Crew">
      <button type="submit">Send Message</button>
    </form>
  </div>
</body>
</html>"""

    def _action_form(self, action: str, label: str, css_class: str = "") -> str:
        class_attr = f' class="{css_class}"' if css_class else ""
        return (
            '<form method="post" action="/api/action">'
            f'<input type="hidden" name="token" value="{html.escape(self.token)}">'
            f'<input type="hidden" name="action" value="{html.escape(action)}">'
            f'<button type="submit"{class_attr}>{html.escape(label)}</button>'
            "</form>"
        )
