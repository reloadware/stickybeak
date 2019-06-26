import inspect
from typing import Callable
import requests
import json
import pickle
import textwrap

from urllib.parse import urljoin


class Injector:
    """Provides interface for code injection."""

    def __init__(self, address: str, endpoint: str='inject/') -> None:
        """
        :param address: service address that's gonna be injected.
        :param endpoint:
        """
        self.address: str = address
        self.endpoint: str = urljoin(self.address, endpoint)

    def run_code(self, code_line: str) -> dict:
        """Execute code.
        Returns:
            Dictionary containing all the local variables.
        Raises:
            All exceptions from the code run remotely.
        Sample usage.
        >>> injector: Injector = Injector('http://testedservice.local')
        >>> injector.run_code('a = 1')
        """
        code = code_line
        code = self._add_try_except(code)

        headers: dict = {'Content-type': 'application/json'}
        payload: dict = {'code': code}
        data: str = json.dumps(payload)

        response: requests.Response = requests.post(self.endpoint, data=data, headers=headers)
        response.raise_for_status()
        ret: dict = pickle.loads(response.content)

        # handle exceptions
        if '__exception' in ret:
            raise ret['__exception']

        return ret

    def run_fun(self, fun: Callable) -> dict:
        code = inspect.getsource(fun)

        # remove indent
        code = textwrap.dedent(code)

        # remove function header
        code = ''.join(code.splitlines(True)[1:])

        # remove indent that's left
        code = textwrap.dedent(code)
        ret = self.run_code(code)
        return ret

    def decorator(self, fun: Callable) -> Callable:
        """
        Decorator
        :param fun: function to be decorated:
        :return decorated function:
        """
        def wrapped() -> dict:
            return self._run_decorated(fun)

        return wrapped

    @staticmethod
    def _add_try_except(code: str) -> str:
        ret = textwrap.indent(code, '    ')  # use tabs instead of spaces, easier to debug
        code_lines = ret.splitlines(True)
        code_lines.insert(0, 'try:\n')
        except_block = """except Exception as __exc:\n    __exception = __exc\n"""

        code_lines.append(except_block)

        ret = ''.join(code_lines)
        return ret

    def _run_decorated(self, fun: Callable) -> dict:
        code = inspect.getsource(fun)

        # remove indent
        code = textwrap.dedent(code)

        # remove function header
        code = ''.join(code.splitlines(True)[2:])

        # remove indent that's left
        code = textwrap.dedent(code)
        ret = self.run_code(code)
        return ret
