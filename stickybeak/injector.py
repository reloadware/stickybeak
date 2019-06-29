import inspect
from pathlib import Path
from typing import Callable
import requests
import json
import pickle
import textwrap
import os
import sys
import django


from urllib.parse import urljoin, urlparse


class Injector:
    """Provides interface for code injection."""

    def __init__(self, address: str, django_settings: str, endpoint: str='stickybeak/',
                 sources_dir: Path = '.remote_sources') -> None:
        """
        :param address: service address that's gonna be injected.
        :param endpoint:
        """
        self.django_settings = django_settings
        self.address: str = address
        self.endpoint: str = urljoin(self.address, endpoint)

        self.name = urlparse(self.address).netloc

        self.sources_dir: Path = sources_dir / Path(self.name)

        self._download_remote_code()

    def _download_remote_code(self) -> None:
        response: requests.Response = requests.get(self.endpoint)
        response.raise_for_status()

        sources: dict = json.loads(response.content)

        for path, source in sources.items():
            abs_path: Path = self.sources_dir / Path(path)

            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.touch()
            abs_path.write_text(source)

    def execute_remote_code(self, code: str) -> bytes:
        code = self._add_try_except(code)

        headers: dict = {'Content-type': 'application/json'}
        payload: dict = {'code': code}
        data: str = json.dumps(payload)

        response: requests.Response = requests.post(self.endpoint, data=data, headers=headers)
        response.raise_for_status()

        return response.content

    def run_code(self, code: str) -> dict:
        """Execute code.
        Returns:
            Dictionary containing all the local variables.
        Raises:
            All exceptions from the code run remotely.
        Sample usage.
        >>> injector: Injector = Injector('http://testedservice.local')
        >>> injector.run_code('a = 1')
        """

        content = self.execute_remote_code(code)
        ret: dict = pickle.loads(content)

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
        except_block = """\nexcept Exception as __exc:\n    __exception = __exc\n"""

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


class DjangoInjector(Injector):
    def run_code(self, code: str):
        # we have to unload all the django modules so django accepts the new configuration
        # make a module copy so we can iterate over it and delete modules from the original one
        modules = dict(sys.modules)
        for n in modules.keys():
            # delete all django modules
            if 'django' in n:
                sys.modules.pop(n)

        sys.path.append(str(self.sources_dir.absolute()))

        os.environ['DJANGO_SETTINGS_MODULE'] = self.django_settings
        django.setup()
        content: bytes = self.execute_remote_code(code)
        ret: dict = pickle.loads(content)

        sys.path.remove(str(self.sources_dir.absolute()))

        # handle exceptions
        if '__exception' in ret:
            raise ret['__exception']

        return ret
