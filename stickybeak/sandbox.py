"""Purpose of this file is to run code in clear environment, without any unnecessary imports etc."""
from typing import Dict


def execute(__code: str) -> bytes:
    """Function where the injected code will be executed.
       Helps to avoid local variable conflicts."""

    __results: Dict[str, object]
    try:
        exec(__code)
    except SyntaxError as exc:
        __results = {'__exception': exc}
    else:
        __results = dict(locals())

    __results.pop('__code')

    import pickle as pickle
    import types as types
    cleared_results: Dict[str, object] = {}

    for key, value in __results.items():
        if isinstance(value, types.ModuleType):
            continue
        if isinstance(value, types.FunctionType):
            continue
        if isinstance(value, types.MethodType):
            continue

        cleared_results[key] = value

    ret: bytes = pickle.dumps(cleared_results)

    return ret
