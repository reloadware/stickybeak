import hashlib
import inspect
import json
import os
from pathlib import Path
import pickle
import subprocess
import sys
import textwrap
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests


class Injector:
    """Provides interface for code injection."""

    def __init__(self, address: str, endpoint: str = "stickybeak/") -> None:
        """
        :param address: service address that's gonna be injected.
        :param endpoint:
        """
        self.address: str = address
        self.endpoint: str = urljoin(self.address, endpoint)

        self.name: str = urlparse(self.address).netloc

        project_dir: Path = Path(".").absolute()
        project_hash = hashlib.sha1(str(project_dir).encode("utf-8")).hexdigest()[0:8]
        self.stickybeak_dir: Path = Path.home() / ".stickybeak" / Path(
            f"{self.name}_{project_hash}"
        )
        self.stickybeak_dir = Path(str(self.stickybeak_dir).replace(":", "_"))

        self._requirements: str = ""
        self._download_remote_code()
        self._download_requirements()

    def _download_remote_code(self) -> None:
        url: str = urljoin(self.endpoint, "source")
        response: requests.Response = requests.get(url)
        response.raise_for_status()

        sources: Dict[str, str] = json.loads(response.content)

        if sources == {}:
            raise RuntimeError("Couldn't find any source files (*.py).")

        for path, source in sources.items():
            abs_path: Path = self.stickybeak_dir / Path(path)

            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.touch()
            abs_path.write_text(source)

    def _download_requirements(self) -> None:
        url: str = urljoin(self.endpoint, "requirements")
        response: requests.Response = requests.get(url)
        response.raise_for_status()

        requirements: str = json.loads(response.content)
        requirements_path: Path = (self.stickybeak_dir / "requirements.txt").absolute()
        if requirements_path.exists():
            if requirements_path.read_text() == requirements:
                return

        requirements_path.write_text(requirements)

        venv_dir: Path = (self.stickybeak_dir / ".venv").absolute()
        python_path: Path = Path(sys.real_prefix) / "bin/python"  # type: ignore

        if not venv_dir.exists():
            subprocess.run(f"{python_path} -m venv {venv_dir}", shell=True)

        if self._requirements != requirements:
            subprocess.run(
                f"{(venv_dir / 'bin/pip')} install -r {requirements_path}", shell=True
            )
            self._requirements = requirements

    def _get_env_vars(self) -> os._Environ:  # type: ignore
        url: str = urljoin(self.endpoint, "envs")
        response: requests.Response = requests.get(url)
        response.raise_for_status()

        envs: Dict[str, str] = json.loads(response.content)

        environ = os._Environ(  # type: ignore
            data=envs,
            encodekey=lambda x: x,
            decodekey=lambda x: x,
            encodevalue=lambda x: x,
            decodevalue=lambda x: x,
            putenv=lambda k, v: None,
            unsetenv=lambda k, v: None,
        )

        return environ

    def execute_remote_code(self, code: str) -> bytes:
        url: str = urljoin(self.endpoint, "inject")
        headers: Dict[str, str] = {"Content-type": "application/json"}
        payload: Dict[str, str] = {"code": code}
        data: str = json.dumps(payload)

        response: requests.Response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()

        return response.content

    def run_code(self, code: str) -> object:
        """Execute code.
        Returns:
            Dictionary containing all local variables.
        Raises:
            All exceptions from the code run remotely.
        Sample usage.
        >>> injector: Injector = Injector('http://testedservice.local')
        >>> injector.run_code('a = 1')
        """
        # we have to unload all the django modules so django accepts the new configuration
        # make a module copy so we can iterate over it and delete modules from the original one
        modules_before: List[str] = list(sys.modules.keys())[:]
        sys_path_before = sys.path[:]

        envs_before: os._Environ = os.environ.copy()  # type: ignore
        os.environ = self._get_env_vars()

        sys.path = [p for p in sys.path if "site-packages" not in p]

        # remove project dir from sys.path so there's no conflicts
        sys.path.pop(0)
        sys.path.append(str(self.stickybeak_dir.absolute()))
        sys.path.append(
            str(self.stickybeak_dir.absolute() / ".venv/lib/python3.7/site-packages")
        )

        self._before_execute()
        content: bytes = self.execute_remote_code(code)
        ret: object = pickle.loads(content)

        os.environ = envs_before
        sys.path = sys_path_before

        modules_after: List[str] = list(sys.modules.keys())[:]
        diff: List[str] = list(set(modules_after) - set(modules_before))

        for m in diff:
            sys.modules.pop(m)

        if isinstance(ret, Exception):
            raise ret

        return ret

    def _before_execute(self) -> None:
        pass

    def _get_fun_src(self, fun: Callable[[], None]) -> str:
        code: str = inspect.getsource(fun)

        code_lines: List[str] = code.splitlines(True)

        if "@" in code_lines[0]:
            code_lines.pop(0)

        code = "".join(code_lines)

        # remove indent that's left
        code = textwrap.dedent(code)
        return code

    @staticmethod
    def _format_args(
        args: Optional[Tuple[object, ...]], kwargs: Optional[Dict[str, object]]
    ) -> str:
        ret = ""
        if args:
            args_clean: str = ", ".join([str(a) for a in args])
            ret += args_clean

        if kwargs:
            kwargs_clean: str = ", ".join([f"{str(k)}={v}" for k, v in kwargs.items()])
            ret += (", " if args else "") + kwargs_clean

        return f"({ret})"

    def run_fun(
        self,
        fun: Callable[[], None],
        args: Optional[Tuple[object, ...]] = None,
        kwargs: Optional[Dict[str, object]] = None,
    ) -> object:
        code: str = self._get_fun_src(fun)
        code += f"\n__return = {fun.__name__}{self._format_args(args, kwargs)}"
        code = self._add_try_except(code)
        ret = self.run_code(code)
        return ret

    def run_klass_fun(
        self,
        klass: type,
        fun: str,
        args: Optional[Tuple[object, ...]] = None,
        kwargs: Optional[Dict[str, object]] = None,
    ) -> object:
        code: str = textwrap.dedent(inspect.getsource(klass))
        code += f"\n__return = {klass.__name__}.{fun}{self._format_args(args, kwargs)}"
        code = self._add_try_except(code)
        ret = self.run_code(code)
        return ret

    def klass(self, cls: type) -> type:
        cls._injector = self  # type: ignore
        methods: List[str] = [
            a for a in dir(cls) if not a.startswith("__") and callable(getattr(cls, a))
        ]

        for m in methods:

            def decorator(func: Callable[[], None]) -> Callable:
                def wrapped(*args: object, **kwargs: object) -> object:
                    return cls._injector.run_klass_fun(  # type: ignore
                        cls, func.__name__, args, kwargs
                    )

                return wrapped

            method: Callable[[], None] = getattr(cls, m)
            setattr(cls, m, decorator(method))

        return cls

    def function(self, fun: Callable[[], None]) -> Callable:
        """
        Decorator
        :param fun: function to be decorated:
        :return decorated function:
        """

        def wrapped(*args: object, **kwargs: object) -> object:
            ret = self.run_fun(fun, args, kwargs)
            return ret

        return wrapped

    @staticmethod
    def _add_try_except(code: str) -> str:
        ret = textwrap.indent(
            code, "    "
        )  # use tabs instead of spaces, easier to debug
        code_lines = ret.splitlines(True)
        code_lines.insert(0, "try:\n")
        except_block = """\nexcept Exception as __exc:\n    __exception = __exc\n"""

        code_lines.append(except_block)

        ret = "".join(code_lines)
        return ret


class DjangoInjector(Injector):
    def __init__(
        self, address: str, django_settings_module: str, endpoint: str = "stickybeak/"
    ) -> None:
        super().__init__(address=address, endpoint=endpoint)
        self.django_settings_module = django_settings_module

    def _before_execute(self) -> None:
        os.environ["DJANGO_SETTINGS_MODULE"] = self.django_settings_module
        import django

        django.setup()
