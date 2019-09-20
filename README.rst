
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
----------------
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

To enable stickybeak in a django application add the following line to your :code:`urls.py` file:

.. code-block:: python

    path("stickybeak/", include("stickybeak.dj.urls")),


And add :code:`stickybeak` to :code:`INSTALLED_APPS` list.

Flask app (remote server)
#########################
To enable stickybeak in a flask application add :code:`setup(app)` as follows:

.. code-block:: python

    from flask import Flask
    from stickybeak.flask_view import setup

    app = Flask(__name__)
    setup(app)


Testing app (local server)
##########################

Functions
+++++++++
Function arguments and returns as well as default arguments are allowed.

.. code-block:: python

    from stickybeak.injector import DjangoInjector

    injector = DjangoInjector(address='http://django-srv:8000',
                              django_settings_module='django_srv.settings')

    @injector.function
    def fun(a: int, b: int = 2) -> float:
        return a / b

    fun(2)


Exceptions
++++++++++
Exception are forwarded from remote to local server so the following piece of code raises :code:`ZeroDivisionError`:

.. code-block:: python

    from stickybeak.injector import DjangoInjector

    injector = DjangoInjector(address='http://django-srv:8000',
                              django_settings_module='django_srv.settings')

    @injector.function
    def fun() -> float:
        a = 1
        b = 0
        return a / b

    fun()  # raises ZeroDivisionError



Using complex objects from a remote server locally
++++++++++++++++++++++++++++++++++++++++++++++++++
Objects are pickled on the remote side and send back to the local script and are available for further inspection or use.

.. code-block:: python

    @self.injector.function
    def fun():
        from app.models import Currency

        currency = Currency()
        currency.name = "test_currency"
        currency.endpoint = "test_endpoint"
        currency.save()
        return Currency.objects.all()[0]  # noqa

    ret: object = fun()
    assert ret.name == "test_currency"
    assert ret.endpoint == "test_endpoint"

Classes
+++++++
The same concepts go to classes. Only classmethods are allowed at the moment.

.. code-block:: python

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

    Interface.fun(1)  # 4
    Interface.fun2(2)  # 9
    Interface.fun3() # 20

Development
-----------
Stickybeak uses pipenv. To install packages run:

.. code-block:: console

    pipenv install


Starting test servers
#####################
.. code-block:: console

    honcho start
