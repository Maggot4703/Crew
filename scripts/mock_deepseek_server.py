#!/usr/bin/env python3
"""
Simple mock DeepSeek-compatible HTTP server for testing.
Responds to POST /v1/completions with a JSON reply.
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/v1/completions":
            self.send_response(404)
            self.end_headers()
            return
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else ""
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}
        prompt = data.get("prompt") or data.get("input") or "hello"
        resp = {"result": f"Mock DeepSeek reply to: {prompt}"}
        payload = json.dumps(resp).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), Handler)
    print("Mock DeepSeek server listening on http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
