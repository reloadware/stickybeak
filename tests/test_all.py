from typing import Any, Dict

import pytest

from stickybeak import Injector, InjectorException


@pytest.mark.usefixtures("injector", "flask_server", "django_server")
class TestInjectors:
    def test_syntax_errors(self, injector):
        with pytest.raises(SyntaxError):
            ret: int = injector.run_code("a=1////2")
            assert ret == 0.5

    def test_not_connected(self):
        injector = Injector(address="some_addr")
        with pytest.raises(InjectorException):
            injector.run_code("a=1////2")

    def test_cant_pickle_errors(self, injector):
        @injector.function
        def fun() -> Any:
            import sys

            return sys.modules

        with pytest.raises(TypeError):
            fun()

    def test_run_code(self, injector):
        ret: Dict[str, Any] = injector.run_code("a=5")
        assert ret["a"] == 5
        assert len(ret) == 1

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

    def test_arguments_default(self, injector):
        @injector.function
        def fun(d: int, e: int, x: int = 2) -> int:
            a = 1
            b = 4
            return a + b + d + e + x

        assert fun(5, 6) == 18

    def test_env_variables(self, injector):
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


@pytest.mark.usefixtures("django_injector")
class TestDjango:
    def test_accessing_fields(self):
        @self.injector.function
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
