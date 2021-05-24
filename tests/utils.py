import json
from pathlib import Path
from unittest.mock import patch

import dill as pickle
from typing import Dict

from requests import Response

from stickybeak import  Injector
from stickybeak._priv import handle_requests


class MockInjector(Injector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.post_mock = patch("stickybeak._priv.utils.Session.post")
        self.get_mock = patch("stickybeak._priv.utils.Session.get")

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

        data: Dict[str, Dict[str, str]] = handle_requests.get_data(django_srv.root)
        response._content = json.dumps(data)

        response.status_code = 200
        return response
