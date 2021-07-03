from contextlib import closing
from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
from typing import Dict, Optional
from unittest.mock import patch

import dill as pickle
from requests import Response

from stickybeak import Injector, handle_requests
from tests.test_srvs import app_srv

DJANGO_PORT = 8005
FLASK_PORT = 8006
APP_PORT = 8007


@dataclass
class MockInjector(Injector):
    def __post_init__(self) -> None:
        self.post_mock = patch("stickybeak.utils.Session.post")
        self.get_mock = patch("stickybeak.utils.Session.get")

    def mock(self, blocking: bool = True) -> None:
        self.post_mock.start().side_effect = self._mock_post
        self.get_mock.start().side_effect = self._mock_get

    def unmock(self):
        self.post_mock.stop()
        self.get_mock.stop()

    def _mock_post(self, endpoint: str, data: bytes, *args, **kwargs) -> Response:
        result: bytes = handle_requests.inject(pickle.loads(data))
        response = Response()
        response._content = result
        response.status_code = 200
        return response

    def _mock_get(self, endpoint: str, *args, **kwargs) -> Response:
        from tests.test_srvs import django_srv

        response = Response()

        data: Dict[str, Dict[str, str]] = handle_requests.get_server_data(django_srv.root)
        response._content = json.dumps(data)

        response.status_code = 200
        return response


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def app_server_factory(stickybeak_port: int, timeout: Optional[float] = None) -> subprocess.Popen:
    environ = os.environ.copy()
    environ["STICKYBEAK_PORT"] = str(stickybeak_port)

    if timeout:
        environ["STICKYBEAK_TIMEOUT"] = str(timeout)

    p = subprocess.Popen([".venv/bin/python", "app.py"], env=environ, cwd=str(app_srv.root))
    return p
