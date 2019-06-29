"""Purpose of this file is to run code in clear environment, without any unnecessary imports etc."""


def execute(__code) -> bytearray:
    """Function where the injected code will be executed.
       Helps to avoid local variable conflicts."""

    try:
        exec(__code)
    except SyntaxError as exc:
        __results: dict = {'__exception': exc}
    else:
        __results: dict = dict(locals())

    #del __results['__code']

    import pickle as pickle
    import types as types
    cleared_results: dict = {}
    for key, value in __results.items():
        if isinstance(value, types.ModuleType):
            continue
        if isinstance(value, types.FunctionType):
            continue
        if isinstance(value, types.MethodType):
            continue

        cleared_results[key] = value

    ret: bytearray = pickle.dumps(cleared_results)

    return ret
