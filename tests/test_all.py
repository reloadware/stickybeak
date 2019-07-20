from typing import Dict

import pytest


@pytest.mark.usefixtures("injector")
class TestInjectors:
    def test_exception(self, injector):
        with pytest.raises(ZeroDivisionError):
            injector.run_code("1/0")

        with pytest.raises(SyntaxError):
            injector.run_code("1===1")

    def test_simple_code(self, injector):
        ret: Dict[str, object] = injector.run_code("a = 123")
        assert ret["a"] == 123

    def test_function(self, injector):
        def fun():
            a = 5
            b = 3
            c = a + b  # noqa

        ret: Dict[str, object] = injector.run_fun(fun)
        # TODO: check dict size we don't wanna anything more that needed
        assert ret["a"] == 5
        assert ret["b"] == 3
        assert ret["c"] == 8

    def test_context_manager(self, injector):
        @injector.decorator
        def fun():
            a = 1  # noqa
            b = 4  # noqa

        ret: Dict[str, object] = fun()

        assert ret["a"] == 1
        assert ret["b"] == 4

    def test_env_variables(self, injector):
        @injector.decorator
        def fun():
            import os

            variable = os.environ["TEST_ENV"]  # noqa

        ret: Dict[str, object] = fun()
        assert ret["variable"] == "TEST_ENV_VALUE"


@pytest.mark.usefixtures("django_injector")
class TestDjango:
    def test_importing_model(self):
        def fun():
            from app.models import Currency

            Currency.objects.all().delete()
            currency = Currency()
            currency.name = "test_currency"
            currency.endpoint = "test_endpoint"
            currency.save()

            objects = Currency.objects.all()  # noqa
            obj = Currency.objects.all()[0]  # noqa

        ret: Dict[str, object] = self.injector.run_fun(fun)
        assert "obj" in ret
        assert "objects" in ret

    def test_accessing_fields(self):
        def fun():
            from app.models import Currency

            Currency.objects.all().delete()
            currency = Currency()
            currency.name = "test_currency"
            currency.endpoint = "test_endpoint"
            currency.save()
            obj = Currency.objects.all()[0]  # noqa

        ret: Dict[str, object] = self.injector.run_fun(fun)
        obj = ret["obj"]

        assert obj.name == "test_currency"
        assert obj.endpoint == "test_endpoint"
