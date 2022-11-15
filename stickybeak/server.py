import atexit
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
import json
import os
from pathlib import Path
import sys
from threading import Thread
from time import sleep
from typing import Any, Optional

import dill as pickle

from stickybeak import handle_requests

__all__ = ["Server"]

from stickybeak.handle_requests import InjectData


class Server(Thread):
    project_root: Path
    port: int
    timeout: Optional[float]
    collect_source: bool

    def __init__(
        self,
        port: int,
        project_root: Optional[Path] = None,
        timeout: Optional[float] = None,
        collect_source: bool = False,
    ) -> None:
        super().__init__()

        self.project_root = project_root
        self.port = port
        self.collect_source = collect_source
        self.timeout = timeout

        class Handler(BaseHTTPRequestHandler):
            project_root = self.project_root

            def do_POST(self) -> None:
                content_length = int(self.headers["Content-Length"])
                body = self.rfile.read(content_length)

                self.send_response(200)
                self.end_headers()

                data: InjectData = pickle.loads(body)
                response = BytesIO()
                response.write(handle_requests.inject(data))
                self.wfile.write(response.getvalue())

            def do_GET(self2) -> None:
                self2.send_response(200)
                self2.send_header("content-type", "application/json")
                self2.end_headers()

                data = handle_requests.get_server_data(self2.project_root)
                response_data = json.dumps(data)
                self2.wfile.write(response_data.encode("utf-8"))

            def handle_http(self) -> None:
                return

            def respond(self) -> None:
                return

            def exit(self) -> None:
                pass

            def log_message(self, format: str, *args: Any) -> None:
                return

        self.httpd = HTTPServer(("localhost", self.port), Handler)
        self.setDaemon(True)

    def _watchdog(self) -> None:
        assert self.timeout is not None
        sleep(self.timeout)
        os._exit(0)

    def exit(self) -> None:
        self.httpd.shutdown()

    def run(self) -> None:
        atexit.register(self.exit)

        if self.timeout:
            watchdog_thread = Thread(target=self._watchdog)
            watchdog_thread.daemon = True
            watchdog_thread.start()

        self.httpd.serve_forever()
        self.httpd.server_close()

    def is_running(self) -> bool:
        return self.is_alive()
