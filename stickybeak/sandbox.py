"""Purpose of this file is to run code in clear environment, without any unnecessary imports etc."""
from typing import Dict


def execute(__code: str) -> bytes:
    """Function where the injected code will be executed.
       Helps to avoid local variable conflicts."""

    results: Dict[str, object]
    try:
        exec(__code)
    except SyntaxError as exc:
        results = {"__exception": exc}
    else:
        results = dict(locals())

    import pickle as pickle

    ret: bytes = pickle.dumps(
        results["__exception"] if "__exception" in results else results["__return"]
    )

    return ret
