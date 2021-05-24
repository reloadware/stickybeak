import hashlib
import inspect
import os
from pathlib import Path

from dataclasses import dataclass

import dill as pickle
import subprocess
import sys
import textwrap
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from time import sleep

import requests.exceptions

from stickybeak._priv import pip, utils
from stickybeak._priv.handle_requests import get_requirements
from stickybeak._priv.utils import Client
from threading import Thread

__all__ = ["InjectorException", "Injector", "DjangoInjector"]


class InjectorException(Exception):
    pass


class ConnectionError(Exception):
    pass


@dataclass
class DependencyInstallError(Exception):
    return_code: int


class Injector:
    """Provides interface for code injection."""

    connected: bool
    stickybeak_dir: Path
    address: Optional[str]
    name: Optional[str]

    _client: Optional[Client]
    _data: Dict[str, Dict[str, str]]  # server data like source or pip freeze requirements

    def __init__(self, download_deps: bool = True) -> None:
        """
        :param address: service address that's gonna be injected.
        :param endpoint:
        """
        self.address = None
        self._client = None
        self.name = None

        self._download_deps = download_deps

        project_dir: Path = Path(".").absolute()
        project_hash = hashlib.sha1(str(project_dir).encode("utf-8")).hexdigest()[0:8]
        self.stickybeak_dir = Path.home() / ".stickybeak" / Path(f"{self.name}_{project_hash}")

        self._data = {}
        self.connected = False

    def connect(self, address: str, blocking: bool = True) -> None:
        self.address: str = address
        self._client = Client(self.address)
        self.name: str = urlparse(self.address).netloc.replace(":", "_")

        def target():
            try:
                # ########## Get data
                self._data = self._client.get("")

                # ########## Collect remote code
                sources: Dict[str, str] = self._data["source"]

                if sources == {}:
                    raise RuntimeError("Couldn't find any source files (*.py).")

                for path, source in sources.items():
                    abs_path: Path = self.stickybeak_dir / Path(path)

                    abs_path.parent.mkdir(parents=True, exist_ok=True)
                    abs_path.touch()
                    abs_path.write_text(source,"utf-8")

                # ########## collect requirements
                if self._download_deps:
                    self._do_download_deps()

                self.connected = True
            except requests.exceptions.ConnectionError as e:
                raise ConnectionError from None

        if blocking:
            target()
        else:
            Thread(target=target).start()

    def wait_until_connected(self, timeout=5) -> None:
        waited = 0.0
        one_sleep = 0.1
        while not self.connected:
            sleep(one_sleep)
            waited += one_sleep

            if waited >= timeout:
                raise TimeoutError

    def _do_download_deps(self):
        venv_dir = (self.stickybeak_dir / ".venv").absolute()

        if not venv_dir.exists():
            subprocess.check_output([f"virtualenv", f"{venv_dir}"], stderr=subprocess.DEVNULL)

        remote_reqs = self._data["requirements"]
        local_reqs = get_requirements(venv_dir)

        reqs_diff = {p: v for p, v in remote_reqs.items() if p not in local_reqs or local_reqs[p] != remote_reqs[p]}

        if reqs_diff:
            # delete packages manualy (sometimes pip doesn't downgrade for some reason)
            site_packages = utils.get_site_packges_from_venv(venv_dir)
            reqs = [f"{p}=={v}" for p, v in reqs_diff.items()]
            ret = pip.main(["install", f"--target={str(site_packages)}", "--upgrade", *reqs])

            if ret:
                raise DependencyInstallError(return_code=ret)

    def _raise_if_not_connected(self) -> None:
        if not self.connected:
            raise InjectorException("Injector not connected! Run connect() first.")

    def _run_remote_fun(self, source: str, call: str, args: Tuple[Any], kwargs: Dict[str, Any]) -> object:
        """Execute code.
        Returns:
            Dictionary containing all local variables.
        Raises:
            All exceptions from the code run remotely.
        """
        self._raise_if_not_connected()

        # we have to unload all the django modules so django accepts the new configuration
        # make a module copy so we can iterate over it and delete modules from the original one
        modules_before: List[str] = list(sys.modules.keys())[:]
        sys_path_before = sys.path[:]

        envs_before: os._Environ = os.environ.copy()  # type: ignore
        os.environ = self._data["envs"]  # type: ignore

        sys.path = [p for p in sys.path if "site-packages" not in p]

        # remove project dir from sys.path so there's no conflicts
        sys.path.pop(0)
        sys.path.insert(0, str(self.stickybeak_dir.absolute()))

        if self._download_deps:
            site_packages = utils.get_site_packges_from_venv(self.stickybeak_dir.absolute() / ".venv")
            sys.path = [str(site_packages), *sys.path]

        self._before_execute()
        data = {
            "source": source,
            "call": call,
            "args": args,
            "kwargs": kwargs
        }
        pickled_data = pickle.dumps(data)
        content: bytes = self._client.post("", data=pickled_data).content
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

    def run_fun(
        self,
        fun: Callable,
        *args: Tuple[Any],
        **kwargs: Dict[str, Any],
    ) -> object:
        self._raise_if_not_connected()

        source: str = self._get_fun_src(fun)
        ret = self._run_remote_fun(source, call=fun.__name__, args=args, kwargs=kwargs)
        return ret

    def run_klass_fun(
        self,
        klass: type,
        fun: Callable,
        args: Tuple[Any],
        kwargs: Dict[str, Any],
    ) -> object:
        self._raise_if_not_connected()

        source: str = textwrap.dedent(inspect.getsource(klass))
        ret = self._run_remote_fun(source, call=f"{klass.__name__}.{fun.__name__}", args=args, kwargs=kwargs)
        return ret

    def klass(self, cls: type) -> type:
        cls._injector = self  # type: ignore
        methods: List[str] = [a for a in dir(cls) if not a.startswith("__") and callable(getattr(cls, a))]

        for m in methods:

            def decorator(func: Callable[[], None]) -> Callable:
                def wrapped(*args: object, **kwargs: object) -> object:
                    return cls._injector.run_klass_fun(  # type: ignore
                        cls, func, args, kwargs
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

        def wrapped(*args: Any, **kwargs: Any) -> object:
            ret = self.run_fun(fun, *args, **kwargs)
            return ret

        return wrapped


class DjangoInjector(Injector):
    def __init__(self, django_settings_module: str, download_deps: bool = True) -> None:
        super().__init__(download_deps=download_deps)
        self.django_settings_module = django_settings_module

    def _before_execute(self) -> None:
        modules = list(sys.modules.keys())[:]
        for m in modules:
            if "django" in m:
                sys.modules.pop(m)

        os.environ["DJANGO_SETTINGS_MODULE"] = self.django_settings_module
        import django

        django.setup()
