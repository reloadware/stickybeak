import os
import signal
import subprocess
from pytest import fixture

from .env_test import Env
from . import utils

from stickybeak import DjangoInjector, Injector

env = Env()


@fixture
def mock_injector():
    mock_injector = utils.MockInjector(address="http://local-mock")
    mock_injector.mock()
    mock_injector.connect()

    yield mock_injector

    mock_injector.unmock()


@fixture
def django_injector():
    injector = DjangoInjector(address=env.django.hostname, django_settings_module="django_srv.settings")
    injector.connect()
    return injector


@fixture
def flask_injector():
    injector = utils.Injector(address=env.flask.hostname)
    injector.connect()
    return injector


@fixture
def django_injector_no_download():
    django_injector_no_download = DjangoInjector(address=env.django.hostname, django_settings_module="django_srv.settings",
                                                 download_deps=False)
    django_injector_no_download.connect()

    return django_injector_no_download


@fixture
def django_injector_not_connected():
    django_injector_no_download = DjangoInjector(address=env.django.hostname, django_settings_module="django_srv.settings",
                                                 download_deps=False)
    return django_injector_no_download


@fixture(scope="session", autouse=True)
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


@fixture(scope="session", autouse=True)
def django_server():
    srv_dir = env.root / "test_srvs/django_srv"
    hostname = "localhost:8336"
    p = subprocess.Popen([".venv/bin/python", "manage.py", "migrate"], cwd=str(srv_dir))
    p.wait(timeout=10)

    p = subprocess.Popen([".venv/bin/python", "manage.py", "runserver", "--noreload", hostname], cwd=str(srv_dir),)

    yield
    p.send_signal(signal.SIGINT)
    p.kill()


