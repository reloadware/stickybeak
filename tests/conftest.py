import json
import os
import signal
import subprocess
import sys
import time
from typing import Any, Dict

from furl import furl
import pytest
import requests
from requests import Response

from stickybeak import DjangoInjector, Injector
from stickybeak._priv import handle_requests

from .env_test import Env

env = Env()

local_srv: str = "http://local-mock"


@pytest.fixture(params=[local_srv, env.django.hostname, env.flask.hostname])
def injector(request, mocker):
    if request.param == local_srv:

        def mock_post(endpoint: str, json: Dict[str, Any], *args, **kwargs) -> Response:
            result: bytes = handle_requests.inject(json)
            response = Response()
            response._content = result
            response.status_code = 200
            return response

        def mock_get(endpoint: str, *args, **kwargs) -> Response:
            url: furl = furl(endpoint)
            response = Response()

            data: Dict[str, Dict[str, str]] = handle_requests.get_data(env.root / "test_srvs/django_srv")
            response._content = json.dumps(data)

            response.status_code = 200
            return response

        post_mock = mocker.patch("stickybeak._priv.utils.Session.post")
        post_mock.side_effect = mock_post

        get_mock = mocker.patch("stickybeak._priv.utils.Session.get")
        get_mock.side_effect = mock_get

        injector = DjangoInjector(address=request.param, django_settings_module="django_srv.settings")
        injector.connect()

        return injector

    if request.param == env.django.hostname:
        injector = DjangoInjector(address=request.param, django_settings_module="django_srv.settings")
        injector.connect()
        return injector

    if request.param == env.flask.hostname:
        injector = Injector(address=request.param)
        injector.connect()
        return injector


@pytest.fixture(scope="class")
def django_injector(request):
    injector = DjangoInjector(address=env.django.hostname, django_settings_module="django_srv.settings")
    injector.connect()
    request.cls.injector = injector


@pytest.fixture(scope="session")
def flask_server():
    srv_dir = env.root / "test_srvs/flask_srv"
    bin_path = srv_dir / ".venv/bin"
    environ = os.environ.copy()
    p = subprocess.Popen(
        [".venv/bin/flask", "run", "--no-reload", f"--host=localhost", f"--port=8235"], env=environ, cwd=str(srv_dir),
    )

    yield
    p.send_signal(signal.SIGINT)
    p.kill()


@pytest.fixture(scope="session")
def django_server():
    srv_dir = env.root / "test_srvs/django_srv"
    hostname = "localhost:8336"
    p = subprocess.Popen([".venv/bin/python", "manage.py", "migrate"], cwd=str(srv_dir))
    p.wait(timeout=10)

    p = subprocess.Popen([".venv/bin/python", "manage.py", "runserver", "--noreload", hostname], cwd=str(srv_dir),)

    yield
    p.send_signal(signal.SIGINT)
    p.kill()
