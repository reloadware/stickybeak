import signal
from textwrap import dedent
from time import sleep
from typing import Any

import pytest
from pytest import raises, mark
from rhei import Stopwatch

from tests import utils
from tests.facade import ConnectionError, InjectorException


injector_fixture = mark.parametrize(
    "injector_type",
    [
        "mock_injector",
        "app_injector",
        "django_injector",
        "flask_injector",
    ],
)


class TestInjectors:
    @injector_fixture
    def test_syntax_errors(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        @injector.function
        def fun() -> Any:
            exec("a=1////2")

        with raises(SyntaxError):
            ret = fun()
            assert ret == 0.5

    @injector_fixture
    def test_function(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        def fun() -> int:
            a = 5
            b = 3
            c = a + b
            return c

        ret: int = injector.run_fun(fun)
        assert ret == 8

    @injector_fixture
    def test_decorator(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        @injector.function
        def fun() -> int:
            a = 1
            b = 4
            return a + b

        assert fun() == 5

    @injector_fixture
    def test_return_none(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        @injector.function
        def fun() -> None:
            print("Hello this is a remote server.")

        assert fun() is None

    @injector_fixture
    def test_arguments(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        @injector.function
        def fun(d: int, e: int, x: int) -> int:
            a = 1
            b = 4
            return a + b + d + e + x

        assert fun(5, 6, x=2) == 18

    @injector_fixture
    def test_datetime(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        @injector.function
        def fun(date) -> int:
            from datetime import datetime

            ret = datetime(date.year + 1, date.month, date.day, date.hour, date.minute, date.second)
            return ret

        from datetime import datetime

        assert fun(datetime(2020, 1, 1, 12, 0, 0)) == datetime(2021, 1, 1, 12, 0, 0)

    @injector_fixture
    def test_arguments_default(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        @injector.function
        def fun(d: int, e: int, x: int = 2) -> int:
            a = 1
            b = 4
            return a + b + d + e + x

        assert fun(5, 6) == 18

    @injector_fixture
    def test_env_variables(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        if isinstance(injector, utils.MockInjector):
            return

        @injector.function
        def fun() -> str:
            import os

            return os.environ["TEST_ENV"]

        assert fun() == "TEST_ENV_VALUE"

    @injector_fixture
    def test_exceptions(self, capsys, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        @injector.function
        def raises_exception_fun() -> float:
            a = 1 / 0
            return a

        with raises(ZeroDivisionError) as e:
            raises_exception_fun()

        assert f"line {self.test_exceptions.__code__.co_firstlineno + 9}" in capsys.readouterr().err

    @injector_fixture
    def test_interface_in_class(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

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

    @injector_fixture
    def test_inheritance(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        class BaseCakeshop:
            @classmethod
            def bake(cls) -> str:
                ret = "\nBaking base cake\n"
                return ret

        @injector.klass
        class Cakeshop(BaseCakeshop):
            @classmethod
            def bake(cls) -> str:
                ret = super().bake()
                ret += "Baking extra cake"
                return ret

            @classmethod
            def open(cls) -> str:
                return "Open"

        assert Cakeshop.bake() == dedent(
            """
        Baking base cake
        Baking extra cake"""
        )
        assert Cakeshop.open() == "Open"

    @injector_fixture
    def test_return_object(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        @injector.function
        def fun() -> float:
            from rhei import Stopwatch

            stopwatch = Stopwatch()
            stopwatch.start()
            return stopwatch

        assert type(fun()).__name__ == "Stopwatch"

    @injector_fixture
    def test_string_passed(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        # Bug reproduction
        @injector.klass
        class Klass2:
            @classmethod
            def fun(cls, test_str: str) -> str:
                return test_str + "_added"

        assert Klass2.fun(test_str="value") == "value_added"
        assert Klass2.fun("value") == "value_added"

    @injector_fixture
    def test_multiple_injectors_per_class(self, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        class Klass3:
            @classmethod
            def fun(cls, test_str: str) -> str:
                return test_str + "_added"

        first_instance = injector.klass(Klass3)
        second_instance = injector.klass(Klass3)

        assert first_instance.fun(test_str="value") == "value_added"
        assert second_instance.fun(test_str="value") == "value_added"

    @injector_fixture
    def test_class_exceptions(self, capsys, injector_type, request):
        injector = request.getfixturevalue(injector_type)

        @injector.klass
        class Klass4:
            @classmethod
            def fun(cls) -> float:
                a = 1 / 0
                return a

        with raises(ZeroDivisionError) as e:
            Klass4.fun()

        assert f"line {self.test_class_exceptions.__code__.co_firstlineno+12}" in capsys.readouterr().err


def test_server_timeout():
    injector = utils.Injector(host=f"http://localhost", name="app")

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
    injector = utils.Injector(host=f"http://localhost", name="app")

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
    injector = utils.Injector(host=f"http://localhost", name="app")

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
