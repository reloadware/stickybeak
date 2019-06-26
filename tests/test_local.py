import pytest
from stickybeak.injector import Injector


def test_function(local_injector):
    def fun():
        a = 1

    ret = local_injector.run_fun(fun)
    a = 1
