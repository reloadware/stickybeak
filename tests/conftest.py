import json
import os
import signal
import subprocess
import sys
import time
from typing import Dict

from furl import furl
import pytest
import requests
from requests import Response

from stickybeak import handle_requests
from stickybeak.injector import DjangoInjector, Injector

from .env_test import Env

env = Env()

local_srv: str = "http://local-mock"


@pytest.fixture(params=[local_srv, env.django.hostname, env.flask.hostname])
def injector(request, mocker):
    if request.param == local_srv:

        def mock_post(endpoint: str, data: str, headers: dict) -> Response:
            result: bytes = handle_requests.inject(json.loads(data))
            response = Response()
            response._content = result
            response.status_code = 200
            return response

        def mock_get(endpoint: str) -> Response:
            url: furl = furl(endpoint)
            response = Response()

            if url.path.segments[-1] == "data":
                data: Dict[str, Dict[str, str]] = handle_requests.get_data(env.root / "test_srvs/django_srv")
                data["requirements"]["django-health-check"] = "3.11.0"
                data["requirements"]["rhei"] = "0.5.2"
                response._content = json.dumps(data)

            response.status_code = 200
            return response

        post_mock = mocker.patch("requests.post")
        post_mock.side_effect = mock_post

        get_mock = mocker.patch("requests.get")
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
    environ = os.environ.copy()
    p = subprocess.Popen(
        ["flask", "run", "--no-reload", f"--host={env.flask.host}", f"--port={env.flask.port}"],
        env=environ,
        cwd=str(env.root / "test_srvs/flask_srv"),
    )

    yield
    p.send_signal(signal.SIGINT)
    p.kill()


@pytest.fixture(scope="session")
def django_server():
    p = subprocess.Popen(["python", "manage.py", "migrate"], cwd=str(env.root / "test_srvs/django_srv"))
    p.wait(timeout=10)

    p = subprocess.Popen(
        ["python", "manage.py", "runserver", "--noreload", f"{env.django.host}:{env.django.port}"],
        cwd=str(env.root / "test_srvs/django_srv"),
    )
    timeout: int = 10

    while True:
        try:
            response: requests.Response = requests.get(f"{env.django.hostname}/health-check/")
            if response.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            pass

        time.sleep(1)
        timeout -= 1

        if timeout == 0:
            print("timeout")
            sys.exit(1)

    yield
    p.send_signal(signal.SIGINT)
    p.kill()
