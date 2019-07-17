
=============================================
Stickybeak - Life changing E2E tests solution
=============================================

.. image:: https://badge.fury.io/py/stickybeak.svg
    :target: https://pypi.org/project/stickybeak/

.. image:: https://circleci.com/gh/dkrystki/stickybeak.svg?style=svg
    :target: https://circleci.com/gh/dkrystki/stickybeak

.. image:: https://codecov.io/gh/dkrystki/stickybeak/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/dkrystki/stickybeak

.. image:: https://img.shields.io/badge/python-3.6-blue.svg
    :target: https://www.python.org/downloads/release/python-360/

.. image:: https://img.shields.io/badge/python-3.7-blue.svg
    :target: https://www.python.org/downloads/release/python-370/

Stickybeak is an end to end test helper library that saves lots of testing endpoints and boilerplate code.
Usually end to end testing is hard to debug when something goes wrong since modern microservice architecture can be quite convoluted.
This library can flatten even the most complex application and help developers write tests that are easy to debug and reflect real life scenarios.
This can save Hundreds of unit and integration tests.

How does it work
------------
Stickybeak uses code injection to execute arbitrary python code on remote servers in local python script environment.
Code injection might sound scary but this solution is completely safe since code injection endpoints are only enabled
in testing or staging environment.
Results of executed code including all local variables or raised exceptions are pickled on remote server and sent back to
the testing script where are unpickled and available for further testing and debugging - just like the code was executed locally.
Pretty amazing huh :) ?
At the moment stickybeak supports Django and Flask frameworks.


Installation
------------
.. code-block:: console

    pip install stickybeak


Example usage
-------------

Django app (remote server)
##########################

.. code-block:: python

    from django.contrib import admin
    from django.urls import include, path

    from stickybeak.django_view import stickybeak_url

    urlpatterns = [
        path('admin/', admin.site.urls),
        stickybeak_url,
    ]



Flask app (remote server)
#########################
.. code-block:: python

    from flask import Flask
    from stickybeak.flask_view import setup

    app = Flask(__name__)
    setup(app)


Testing app (local server)
##########################
.. code-block:: python

    from stickybeak.injector import DjangoInjector, FlaskInjector

    def test_exception():
        injector = DjangoInjector(address='http://django-srv:8000',
                                  django_settings_module='django_srv.settings')

        with pytest.raises(ZeroDivisionError):
            injector.run_code('1/0')

    def test_simple_code():
        injector = DjangoInjector(address='http://django-srv:8000',
                                  django_settings_module='django_srv.settings')
        ret: Dict[str, object] = injector.run_code('a = 123')
        assert ret['a'] == 123

    def test_function():
        injector = DjangoInjector(address='http://django-srv:8000',
                                  django_settings_module='django_srv.settings')

        def fun():
            # this code executes on the remote server
            a = 5
            b = 3
            c = a + b

        ret: Dict[str, object] = injector.run_fun(fun)
        assert ret['a'] == 5
        assert ret['b'] == 3
        assert ret['c'] == 8

    def test_using_decorators():
        injector = DjangoInjector(address='http://django-srv:8000',
                                  django_settings_module='django_srv.settings')

        @injector.decorator
        def fun():
            # this code executes on the remote server
            a = 1
            b = 4

        ret: Dict[str, object] = fun()

        assert ret['a'] == 1
        assert ret['b'] == 4

    def test_django_feature():
        injector = DjangoInjector(address='http://django-srv:8000',
                                  django_settings_module='django_srv.settings')

        @injector.decorator
        def fun():
            # this code executes on the remote server
            from app.models import Currency
            Currency.objects.all().delete()
            currency = Currency()
            currency.name = "test_currency"
            currency.endpoint = "test_endpoint"
            currency.save()
            obj = Currency.objects.all()[0]  # noqa

        ret: Dict[str, object] = fun()
        obj = ret['obj']

        # with a little bit of python magic the object is available locally as if we were running code on the remote server
        assert obj.name == "test_currency"
        assert obj.endpoint == "test_endpoint"
        # it is also available for debugger so it is possible to lookup all values and even run some class functions



Development
-----------
Stickybeak uses docker to create an isolated development environment so your system is not being polluted.

Requirements
############
In order to run local development you have to have Docker and Docker Compose installed.


Starting things up
##################
.. code-block:: console

    docker-compose up -d

Logging into the docker terminal
################################
.. code-block:: console

    ./bin/terminal

The code is synchronised between a docker container and the host using volumes so any changes ( ``pipenv install`` etc ) will be affected on the host.
