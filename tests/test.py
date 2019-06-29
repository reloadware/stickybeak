import pytest


@pytest.mark.usefixtures("injector")
class TestInjectors:

    def test_exception(self, injector):
        with pytest.raises(ZeroDivisionError):
            injector.run_code('1/0')

        with pytest.raises(SyntaxError):
            injector.run_code('1===1')

    def test_simple_code(self, injector):
        ret = injector.run_code('a = 123')
        assert ret['a'] == 123

    def test_function(self, injector):
        def fun():
            a = 5
            b = 3
            c = a + b

        ret = injector.run_fun(fun)
        assert ret['a'] == 5
        assert ret['b'] == 3
        assert ret['c'] == 8

    def test_context_manager(self, injector):
        @injector.decorator
        def fun():
            a = 1
            b = 4
        ret = fun()

        assert ret['a'] == 1
        assert ret['b'] == 4


@pytest.mark.usefixtures("django_injector")
class TestDjango:
    def test_function(self):
        def fun():
            from app.models import Currency
            objects = Currency.objects.all()
            object = Currency.objects.all()[0]

        ret = self.injector.run_fun(fun)
        a = 1
