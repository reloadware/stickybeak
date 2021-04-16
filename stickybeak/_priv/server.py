import atexit
import signal
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
import json
from pathlib import Path
import dill as pickle
from threading import Thread

from stickybeak._priv import handle_requests

__all__ = ["Server"]


class Server(Thread):
    def __init__(self, project_root: Path, port: int) -> None:
        super().__init__()

        self.project_root = project_root
        self.port = port

        class Handler(BaseHTTPRequestHandler):
            project_root = self.project_root

            def do_POST(self):
                content_length = int(self.headers["Content-Length"])
                body = self.rfile.read(content_length)

                self.send_response(200)
                self.end_headers()

                data = pickle.loads(body)
                response = BytesIO()
                response.write(handle_requests.inject(data))
                self.wfile.write(response.getvalue())

            def do_GET(self):
                self.send_response(200)
                self.send_header("content-type", "application/json")
                self.end_headers()

                data = json.dumps(handle_requests.get_data(self.project_root))
                self.wfile.write(data.encode("utf-8"))

            def handle_http(self):
                return

            def respond(self):
                return

            def exit(self):
                pass

            def log_message(self, format, *args):
                return

        self.httpd = HTTPServer(("localhost", self.port), Handler)
        self.setDaemon(True)

    def exit(self):
        self.httpd.shutdown()

    def run(self) -> None:
        atexit.register(self.exit)
        self.httpd.serve_forever()
        self.httpd.server_close()

    def is_running(self) -> bool:
        return self.is_alive()
