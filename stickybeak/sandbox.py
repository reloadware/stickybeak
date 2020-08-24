"""Purpose of this file is to run code in clear environment, without any unnecessary imports etc."""
import pickle
from typing import *  # noqa: F401, F403


def execute(__code: str) -> bytes:
    """Function where the injected code will be executed.
       Helps to avoid local variable conflicts."""

    ret: bytes

    try:
        exec(__code)

        results = dict(locals())
        results.pop("__code")
        if "__return" in results:
            ret = pickle.dumps(results["__return"])
        elif "__exception" in results:
            ret = pickle.dumps(results["__exception"])
        else:
            ret = pickle.dumps(results)
    except Exception as exc:
        ret = pickle.dumps(exc)

    return ret
