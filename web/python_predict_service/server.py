import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from os import getenv
from urllib.parse import urlparse

from app import PredictRequest, health, predict


class PredictHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/health":
            self.write_json({"error": "not found"}, status=404)
            return
        self.write_json(health())

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/predict":
            self.write_json({"error": "not found"}, status=404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(body or "{}")
            result = predict(PredictRequest.model_validate(payload))
            self.write_json(result)
        except Exception as exc:  # noqa: BLE001 - return error to Java caller
            self.write_json({"error": str(exc)}, status=500)

    def write_json(self, data, status=200):
        content = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        print("[%s] %s" % (self.log_date_time_string(), format % args))


def main():
    host = getenv("PREDICT_HOST", "127.0.0.1")
    port = int(getenv("PREDICT_PORT", "9000"))
    server = ThreadingHTTPServer((host, port), PredictHandler)
    print(f"Python prediction service listening on http://{host}:{port}")
    print("Health check:", f"http://{host}:{port}/health")
    server.serve_forever()


if __name__ == "__main__":
    main()
