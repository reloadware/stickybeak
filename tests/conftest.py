import os
import signal
import subprocess
from pytest import fixture

from . import utils

from stickybeak import DjangoInjector, Injector


DJANGO_STICKYBEAK_PORT = 6811
FLASK_STICKYBEAK_PORT = 8471


@fixture
def mock_injector():
    mock_injector = utils.MockInjector()
    mock_injector.mock()
    mock_injector.prepare(address="http://local-mock")
    mock_injector.connect()

    yield mock_injector

    mock_injector.unmock()


@fixture
def django_injector():
    injector = DjangoInjector(django_settings_module="django_srv.settings")
    injector.prepare(address="http://localhost", port=DJANGO_STICKYBEAK_PORT)
    injector.connect()
    return injector


@fixture
def flask_injector():
    injector = utils.Injector()
    injector.prepare(address="http://localhost", port=FLASK_STICKYBEAK_PORT)
    injector.connect()
    return injector


@fixture
def django_injector_no_download():
    django_injector_no_download = DjangoInjector(django_settings_module="django_srv.settings",
                                                 download_deps=False)
    django_injector_no_download.prepare(address="http://localhost", port=DJANGO_STICKYBEAK_PORT)
    django_injector_no_download.connect()

    return django_injector_no_download


@fixture
def django_injector_not_connected():
    django_injector_no_download = DjangoInjector(django_settings_module="django_srv.settings",
                                                 download_deps=False)

    return django_injector_no_download


@fixture(scope="session", autouse=True)
def flask_server():
    from tests.test_srvs import flask_srv

    environ = os.environ.copy()
    environ["STICKYBEAK_PORT"] = str(FLASK_STICKYBEAK_PORT)
    p = subprocess.Popen(
        [".venv/bin/flask", "run", "--no-reload", f"--host=localhost", f"--port=8235"], env=environ, cwd=str(flask_srv.root),
    )

    yield
    p.send_signal(signal.SIGINT)
    p.kill()


@fixture(scope="session", autouse=True)
def django_server():
    from tests.test_srvs import django_srv

    hostname = "localhost:8336"
    p = subprocess.Popen([".venv/bin/python", "manage.py", "migrate"], cwd=str(django_srv.root))
    p.wait(timeout=10)

    environ = os.environ.copy()
    environ["STICKYBEAK_PORT"] = str(DJANGO_STICKYBEAK_PORT)

    p = subprocess.Popen([".venv/bin/python", "manage.py", "runserver", "--noreload", hostname], env=environ,
                         cwd=str(django_srv.root),)

    yield
    p.send_signal(signal.SIGINT)
    p.kill()


