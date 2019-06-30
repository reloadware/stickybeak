import inspect
from pathlib import Path
from typing import Callable, Dict
import requests
import json
import pickle
import textwrap
import os
import sys
import django
from abc import ABC

from urllib.parse import urljoin, urlparse


class Injector(ABC):
    """Provides interface for code injection."""

    def __init__(self, address: str,
                 endpoint: str = 'stickybeak/',
                 sources_dir: Path = Path('.remote_sources')) -> None:
        """
        :param address: service address that's gonna be injected.
        :param endpoint:
        """
        self.address: str = address
        self.endpoint: str = urljoin(self.address, endpoint)

        self.name: str = urlparse(self.address).netloc

        self.sources_dir: Path = sources_dir / Path(self.name)

        self._download_remote_code()

    def _download_remote_code(self) -> None:
        response: requests.Response = requests.get(self.endpoint)
        response.raise_for_status()

        sources: Dict[str, str] = json.loads(response.content)

        for path, source in sources.items():
            abs_path: Path = self.sources_dir / Path(path)

            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.touch()
            abs_path.write_text(source)

    def execute_remote_code(self, code: str) -> bytes:
        code = self._add_try_except(code)

        headers: Dict[str, str] = {'Content-type': 'application/json'}
        payload: Dict[str, str] = {'code': code}
        data: str = json.dumps(payload)

        response: requests.Response = requests.post(self.endpoint, data=data, headers=headers)
        response.raise_for_status()

        return response.content

    def run_code(self, code: str) -> Dict[str, object]:
        """Execute code.
        Returns:
            Dictionary containing all local variables.
        Raises:
            All exceptions from the code run remotely.
        Sample usage.
        >>> injector: Injector = Injector('http://testedservice.local')
        >>> injector.run_code('a = 1')
        """
        raise NotImplementedError

    def run_fun(self, fun: Callable[[], None]) -> Dict[str, object]:
        code = inspect.getsource(fun)

        # remove indent
        code = textwrap.dedent(code)

        # remove function header
        code = ''.join(code.splitlines(True)[1:])

        # remove indent that's left
        code = textwrap.dedent(code)
        ret = self.run_code(code)
        return ret

    def decorator(self, fun: Callable[[], None]) -> Callable[[], Dict[str, object]]:
        """
        Decorator
        :param fun: function to be decorated:
        :return decorated function:
        """
        def wrapped() -> Dict[str, object]:
            code = inspect.getsource(fun)

            # remove indent
            code = textwrap.dedent(code)

            # remove function header
            code = ''.join(code.splitlines(True)[2:])

            # remove indent that's left
            code = textwrap.dedent(code)
            ret = self.run_code(code)
            return ret

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


class DjangoInjector(Injector):
    def __init__(self, address: str,
                 django_settings_module: str,
                 endpoint: str = 'stickybeak/',
                 sources_dir: Path = Path('.remote_sources')) -> None:
        super().__init__(address=address, endpoint=endpoint, sources_dir=sources_dir)
        self.django_settings_module = django_settings_module

    def run_code(self, code: str) -> Dict[str, object]:
        # we have to unload all the django modules so django accepts the new configuration
        # make a module copy so we can iterate over it and delete modules from the original one
        modules = dict(sys.modules)
        for n in modules.keys():
            # delete all django modules
            if 'django' in n:
                sys.modules.pop(n)

        sys.path.append(str(self.sources_dir.absolute()))

        os.environ['DJANGO_SETTINGS_MODULE'] = self.django_settings_module
        django.setup()
        content: bytes = self.execute_remote_code(code)
        ret: Dict[str, object] = pickle.loads(content)

        sys.path.remove(str(self.sources_dir.absolute()))

        # handle exceptions
        if '__exception' in ret:
            raise ret['__exception']  # type: ignore

        return ret
