import shutil
from pickle import PicklingError
from typing import Any, Dict

from stickybeak._priv import pip
import pytest
from pytest import raises

from stickybeak import Injector, InjectorException
from tests import utils


@pytest.mark.parametrize("injector", [pytest.lazy_fixture("mock_injector"),
                                      pytest.lazy_fixture("django_injector"),
                                      pytest.lazy_fixture("flask_injector")])
class TestInjectors:
    def test_installs_missing_package(self, injector):
        from stickybeak._priv import utils

        @injector.function
        def get_humanize_version() -> str:
            import humanize
            return humanize.__version__

        for p in utils.get_site_packges_from_venv(injector.stickybeak_dir / ".venv").glob("loguru*"):
            shutil.rmtree(str(p))

        ver = get_humanize_version()

        assert ver == "3.5.0"

    def test_installs_upgrade(self, injector):
        from stickybeak._priv import utils

        @injector.function
        def get_humanize_version() -> str:
            import humanize
            return humanize.__version__

        for p in utils.get_site_packges_from_venv(injector.stickybeak_dir / ".venv").glob("humanize*"):
            shutil.rmtree(str(p))

        ret = pip.main(
            [
                "install",
                f"--target={str(utils.get_site_packges_from_venv(injector.stickybeak_dir / '.venv'))}",
                "humanize==3.4.0",
            ]
        )
        assert ret == 0

        # should upgrade
        ver = get_humanize_version()
        assert ver == "3.5.0"

    def test_syntax_errors(self, injector):
        @injector.function
        def fun() -> Any:
            exec("a=1////2")

        with pytest.raises(SyntaxError):
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
            ret = datetime(date.year+1, date.month, date.day, date.hour, date.minute, date.second)
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

    def test_exceptions(self, injector):
        @injector.function
        def fun() -> float:
            a = 1 / 0
            return a

        with pytest.raises(ZeroDivisionError):
            fun()

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


def test_no_download(django_injector_no_download):
    @django_injector_no_download.function
    def fun() -> int:
        a = 5
        b = 3
        c = a + b
        return c

    with raises(ModuleNotFoundError):
        ret: int = fun()


def test_not_connected(django_injector_not_connected):
    injector = Injector(address="some_addr")

    @injector.function
    def fun() -> Any:
        return "cake"

    with pytest.raises(InjectorException):
        fun()
