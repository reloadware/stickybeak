from pickle import PicklingError
import random
import shutil
import signal
from time import sleep
import traceback
from typing import Any, Dict

from pytest import lazy_fixture, mark, raises, skip
from rhei import Stopwatch

from tests import utils
from tests.facade import ConnectionError, Injector, InjectorException, pip, stickybeak_utils


@mark.parametrize(
    "injector", [lazy_fixture("app_injector"), lazy_fixture("django_injector"), lazy_fixture("flask_injector")]
)
class TestDownloadingRequirements:
    def test_installs_missing_package(self, injector):
        if isinstance(injector, utils.MockInjector):
            skip()

        @injector.function
        def get_humanize_version() -> str:
            import humanize

            return humanize.__version__

        for p in stickybeak_utils.get_site_packages_dir_from_venv(injector.stickybeak_dir / ".venv").glob("loguru*"):
            shutil.rmtree(str(p))

        ver = get_humanize_version()

        assert ver == "3.5.0"

    def test_installs_upgrade(self, injector):
        if isinstance(injector, utils.MockInjector):
            skip()

        @injector.function
        def get_humanize_version() -> str:
            import humanize

            return humanize.__version__

        for p in stickybeak_utils.get_site_packages_dir_from_venv(injector.stickybeak_dir / ".venv").glob("humanize*"):
            shutil.rmtree(str(p))

        ret = pip.main(
            [
                "install",
                f"--target={str(stickybeak_utils.get_site_packages_dir_from_venv(injector.stickybeak_dir / '.venv'))}",
                "humanize==3.4.0",
            ]
        )
        assert ret == 0

        # should upgrade
        ver = get_humanize_version()
        assert ver == "3.5.0"


@mark.parametrize(
    "injector",
    [
        lazy_fixture("mock_injector"),
        lazy_fixture("app_injector"),
        lazy_fixture("django_injector"),
        lazy_fixture("flask_injector"),
    ],
)
class TestInjectors:
    def test_syntax_errors(self, injector):
        @injector.function
        def fun() -> Any:
            exec("a=1////2")

        with raises(SyntaxError):
            ret = fun()
            assert ret == 0.5

    def test_function(self, injector):
        def fun() -> int:
            a = 5
            b = 3
            c = a + b
            return c

        ret: int = injector.run_fun(fun)
        assert ret == 8

    def test_decorator(self, injector):
        @injector.function
        def fun() -> int:
            a = 1
            b = 4
            return a + b

        assert fun() == 5

    def test_return_none(self, injector):
        @injector.function
        def fun() -> None:
            print("Hello this is a remote server.")

        assert fun() is None

    def test_arguments(self, injector):
        @injector.function
        def fun(d: int, e: int, x: int) -> int:
            a = 1
            b = 4
            return a + b + d + e + x

        assert fun(5, 6, x=2) == 18

    def test_datetime(self, injector):
        @injector.function
        def fun(date) -> int:
            from datetime import datetime

            ret = datetime(date.year + 1, date.month, date.day, date.hour, date.minute, date.second)
            return ret

        from datetime import datetime

        assert fun(datetime(2020, 1, 1, 12, 0, 0)) == datetime(2021, 1, 1, 12, 0, 0)

    def test_arguments_default(self, injector):
        @injector.function
        def fun(d: int, e: int, x: int = 2) -> int:
            a = 1
            b = 4
            return a + b + d + e + x

        assert fun(5, 6) == 18

    def test_env_variables(self, injector):
        if isinstance(injector, utils.MockInjector):
            return

        @injector.function
        def fun() -> str:
            import os

            return os.environ["TEST_ENV"]

        assert fun() == "TEST_ENV_VALUE"

    def test_exceptions(self, injector, capsys):
        @injector.function
        def fun() -> float:
            a = 1 / 0
            return a

        with raises(ZeroDivisionError) as e:
            fun()

        assert "line 154" in capsys.readouterr().err

    def test_interface_in_class(self, injector):
        @injector.klass
        class Interface:
            @classmethod
            def fun(cls, x: int) -> int:
                a = 1
                b = 2
                return a + b + x

            @classmethod
            def fun2(cls, x: int) -> int:
                c = 3
                d = 4
                return c + d + x

            @classmethod
            def fun3(cls) -> int:
                return cls.fun(5) + cls.fun2(x=5)

        assert Interface.fun(1) == 4
        assert Interface.fun2(2) == 9
        assert Interface.fun3() == 20

    def test_return_object(self, injector):
        @injector.function
        def fun() -> float:
            from rhei import Stopwatch

            stopwatch = Stopwatch()
            stopwatch.start()
            return stopwatch

        assert type(fun()).__name__ == "Stopwatch"

    def test_string_passed(self, injector):
        # Bug reproduction
        @injector.klass
        class Klass2:
            @classmethod
            def fun(cls, test_str: str) -> str:
                return test_str + "_added"

        assert Klass2.fun(test_str="value") == "value_added"
        assert Klass2.fun("value") == "value_added"

    def test_multiple_injectors_per_class(self, injector):
        class Klass3:
            @classmethod
            def fun(cls, test_str: str) -> str:
                return test_str + "_added"

        first_instance = injector.klass(Klass3)
        second_instance = injector.klass(Klass3)

        assert first_instance.fun(test_str="value") == "value_added"
        assert second_instance.fun(test_str="value") == "value_added"

    def test_class_exceptions(self, injector, capsys):
        @injector.klass
        class Klass4:
            @classmethod
            def fun(cls) -> float:
                a = 1 / 0
                return a

        with raises(ZeroDivisionError) as e:
            Klass4.fun()

        assert "line 224" in capsys.readouterr().err


def test_server_timeout():
    injector = utils.Injector(host=f"http://localhost", name="app", download_deps=False)

    @injector.klass
    class Klass:
        @classmethod
        def fun(cls) -> str:
            return "So fun"

    port = utils.find_free_port()
    process = utils.app_server_factory(timeout=3, stickybeak_port=port)

    injector.prepare(port=port)
    injector.connect()

    assert Klass.fun() == "So fun"
    sleep(3)
    with raises(ConnectionError):
        assert Klass.fun() == "So fun"

    process.send_signal(signal.SIGINT)
    process.kill()


def test_client_timeout():
    injector = utils.Injector(host=f"http://localhost", name="app", download_deps=False)

    port = utils.find_free_port()
    process = utils.app_server_factory(timeout=3, stickybeak_port=port, start_delay=4)

    sw = Stopwatch()
    injector.prepare(port=port)
    sw.start()
    injector.connect(timeout=5)
    sw.pause()

    assert sw.value <= 5.0 and sw.value >= 4.0

    process.send_signal(signal.SIGINT)
    process.kill()


def test_no_project_root():
    injector = utils.Injector(host=f"http://localhost", name="app", download_deps=False)

    @injector.klass
    class Klass:
        @classmethod
        def fun(cls) -> str:
            return "So fun"

    port = utils.find_free_port()
    process = utils.app_server_factory(timeout=3, stickybeak_port=port, project_root=None)

    injector.prepare(port=port)
    injector.connect()

    assert Klass.fun() == "So fun"
    process.send_signal(signal.SIGINT)
    process.kill()


def test_accessing_fields(django_injector):
    @django_injector.function
    def fun():
        from app.models import Currency

        Currency.objects.all().delete()
        currency = Currency()
        currency.name = "test_currency"
        currency.endpoint = "test_endpoint"
        currency.save()
        return Currency.objects.all()[0]  # noqa

    ret: object = fun()
    assert ret.name == "test_currency"
    assert ret.endpoint == "test_endpoint"


def test_not_connected(django_injector_not_connected):
    @django_injector_not_connected.function
    def fun() -> Any:
        return "cake"

    with raises(InjectorException):
        fun()
