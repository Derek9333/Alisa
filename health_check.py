"""
health_check.py - small web server for health checks and VoAPI test.
Run with: python health_check.py
"""
import os, json, logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from voapi_adapter import chat_completion

logging.basicConfig(level=os.environ.get("LOG_LEVEL","INFO"))
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", "8080"))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type","text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
            return
        if self.path == "/voapi_test":
            try:
                sample = chat_completion([{"role":"user","content":"ping"}], timeout=10)
                body = json.dumps({"ok": True, "sample": sample})
                self.send_response(200)
                self.send_header("Content-Type","application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))
            except Exception as e:
                logger.exception("VoAPI test failed")
                body = json.dumps({"ok": False, "error": str(e)})
                self.send_response(500)
                self.send_header("Content-Type","application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(body.encode("utf-8"))
            return
        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(('', PORT), Handler)
    logger.info("Starting health server on port %d", PORT)
    server.serve_forever()
