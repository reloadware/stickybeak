import os
import signal
import subprocess

from pytest import fixture

from tests import utils
from tests.facade import DjangoInjector, FlaskInjector
from tests.utils import app_server_factory


@fixture
def mock_injector():
    mock_injector = utils.MockInjector(download_deps=False, host="http://local-mock", name="mock")
    mock_injector.mock()
    mock_injector.prepare()
    mock_injector.connect()

    yield mock_injector

    mock_injector.unmock()


@fixture
def app_injector():
    injector = DjangoInjector(
        host=f"http://localhost:{utils.DJANGO_PORT}/sb/",
        django_settings_module="django_srv.settings",
        name="django_srv",
        download_deps=True,
    )
    injector.connect()
    return injector


@fixture
def django_injector():
    injector = DjangoInjector(
        host=f"http://localhost:{utils.DJANGO_PORT}/sb/",
        django_settings_module="django_srv.settings",
        name="django_srv",
        download_deps=True,
    )
    injector.connect()
    return injector


@fixture
def flask_injector():
    injector = FlaskInjector(host=f"http://localhost:{utils.FLASK_PORT}/sb/", name="flask_srv", download_deps=True)
    injector.connect()
    return injector


@fixture
def django_injector_no_download():
    django_injector_no_download = DjangoInjector(
        host=f"http://localhost:{utils.DJANGO_PORT}/sb/",
        django_settings_module="django_srv.settings",
        download_deps=False,
        name="django_srv",
    )
    django_injector_no_download.connect()

    return django_injector_no_download


@fixture
def django_injector_not_connected():
    django_injector_no_download = DjangoInjector(
        host=f"http://localhost:{utils.DJANGO_PORT}/sb/",
        django_settings_module="django_srv.settings",
        download_deps=False,
        name="django_srv",
    )
    return django_injector_no_download


@fixture(scope="session", autouse=True)
def app_server():
    p = app_server_factory(stickybeak_port=utils.APP_PORT)

    yield
    p.send_signal(signal.SIGINT)
    p.kill()


@fixture(scope="session", autouse=True)
def flask_server():
    from tests.test_srvs import flask_srv

    environ = os.environ.copy()
    p = subprocess.Popen(
        [".venv/bin/flask", "run", "--no-reload", f"--host=localhost", f"--port={utils.FLASK_PORT}"],
        env=environ,
        cwd=str(flask_srv.root),
    )

    yield
    p.send_signal(signal.SIGINT)
    p.kill()


@fixture(scope="session", autouse=True)
def django_server():
    from tests.test_srvs import django_srv

    hostname = f"localhost:{utils.DJANGO_PORT}"
    p = subprocess.Popen([".venv/bin/python", "manage.py", "migrate"], cwd=str(django_srv.root))
    p.wait(timeout=10)

    environ = os.environ.copy()

    p = subprocess.Popen(
        [".venv/bin/python", "manage.py", "runserver", "--noreload", hostname],
        env=environ,
        cwd=str(django_srv.root),
    )

    yield
    p.send_signal(signal.SIGINT)
    p.kill()
