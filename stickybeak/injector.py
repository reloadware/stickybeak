from contextlib import closing
from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import textwrap
from threading import Thread
from time import sleep
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import dill as pickle
import requests.exceptions

from stickybeak import utils
from stickybeak.handle_requests import INJECT_ENDPOINT, SERVER_DATA_ENDPOINT, InjectData, Requirement, get_requirements
from stickybeak.utils import Client
from stickybeak.vendored import inspect, pip

__all__ = ["InjectorException", "Injector", "DjangoInjector", "FlaskInjector", "ConnectionError"]


class InjectorException(Exception):
    pass


class ConnectionError(Exception):
    pass


@dataclass
class DependencyInstallError(Exception):
    return_code: int


@dataclass
class BaseInjector:
    """Provides interface for code injection."""

    name: str  # injector name. Will be used as id in stickybeak_dir
    host: str
    port: int
    download_deps: bool
    stickybeak_dir: Path = field(init=False)  # directory where remote dependencies and project source is kept

    _client: Optional[Client] = field(init=False)

    _server_data: Dict[str, Any] = field(
        init=False, default_factory=dict
    )  # server data like source or pip freeze requirements

    connected: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self._init()

    def _init(self) -> None:
        self._client = Client(self.host)
        self.stickybeak_dir = Path.home() / ".stickybeak" / Path(f"{self.name}")

    def connect(self, blocking: bool = True) -> None:
        def target() -> None:
            try:
                # ########## Get data
                self._server_data = self._client.get(SERVER_DATA_ENDPOINT)

                # ########## Collect remote code
                sources: Dict[str, str] = self._server_data["source"]

                for path, source in sources.items():
                    abs_path: Path = self.stickybeak_dir / Path(path)

                    abs_path.parent.mkdir(parents=True, exist_ok=True)
                    abs_path.touch()
                    abs_path.write_text(source, "utf-8")

                # ########## collect requirements
                if self.download_deps:
                    self._do_download_deps()

                self.connected = True
            except requests.exceptions.ConnectionError as e:
                raise ConnectionError from None

        if blocking:
            target()
        else:
            Thread(target=target).start()

    def wait_until_connected(self, timeout: float = 5.0) -> None:
        waited = 0.0
        one_sleep = 0.1
        while not self.connected:
            sleep(one_sleep)
            waited += one_sleep

            if waited >= timeout:
                raise TimeoutError

    def _do_download_deps(self) -> None:
        venv_dir = (self.stickybeak_dir / ".venv").absolute()

        if not venv_dir.exists():
            subprocess.check_output([f"virtualenv", f"{venv_dir}"], stderr=subprocess.DEVNULL)

        remote_reqs = self._server_data["requirements"]
        local_reqs = get_requirements(venv_dir)

        @dataclass
        class ReqDiff:
            local: Optional[Requirement]
            remote: Requirement

        reqs_diff = {}
        for p, v in remote_reqs.items():
            remote = remote_reqs[p]
            local = local_reqs.get(p)

            if not local or remote["version"] != local["version"]:
                reqs_diff[p] = ReqDiff(local=local, remote=remote)

        if reqs_diff:
            # delete packages manualy (sometimes pip doesn't downgrade for some reason)
            site_packages = utils.get_site_packages_dir_from_venv(venv_dir)
            for p, r in reqs_diff.items():
                if not r.local:
                    continue
                package_dir = site_packages / r.local["key"]
                shutil.rmtree(package_dir, ignore_errors=True)

                shutil.rmtree(r.local["egg_info"], ignore_errors=True)

            reqs = [f"{p}=={r.remote['version']}" for p, r in reqs_diff.items()]
            ret = pip.main(["install", f"--target={str(site_packages)}", "--upgrade", *reqs])

            if ret:
                raise DependencyInstallError(return_code=ret)

    def _raise_if_not_connected(self) -> None:
        if not self.connected:
            raise InjectorException("Injector not connected! Run connect() first.")

    def _run_remote_fun(self, source: str, filename: str, offset: int, call: str, args: Any, kwargs: Any) -> object:
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
        os.environ = self._server_data["envs"]  # type: ignore

        if self.download_deps:
            sys.path = [p for p in sys.path if "site-packages" not in p]

            # remove project dir from sys.path so there's no conflicts
            sys.path.pop(0)
            sys.path.insert(0, str(self.stickybeak_dir.absolute()))

            site_packages = utils.get_site_packages_dir_from_venv(self.stickybeak_dir.absolute() / ".venv")
            sys.path = [str(site_packages), *sys.path]

        self._before_execute()
        data = InjectData(source=source, filename=filename, offset=offset, call=call, args=list(args), kwargs=kwargs)
        pickled_data = pickle.dumps(data)
        try:
            content: bytes = self._client.post(INJECT_ENDPOINT, data=pickled_data).content
        except requests.exceptions.ConnectionError:
            raise ConnectionError from None
        ret: object = pickle.loads(content)

        os.environ = envs_before
        sys.path = sys_path_before

        modules_after: List[str] = list(sys.modules.keys())[:]
        diff: List[str] = list(set(modules_after) - set(modules_before))

        for m in diff:
            sys.modules.pop(m)

        if isinstance(ret, Exception):
            sys.stderr.write(ret.__traceback_str__)  # type: ignore
            raise ret

        return ret

    def _before_execute(self) -> None:
        pass

    def _get_fun_src(self, fun: Callable[[], None]) -> Tuple[str, int]:
        code: str = inspect.getsource(fun)
        offset = inspect.getsourcelines(fun)[1]

        code_lines: List[str] = code.splitlines(True)

        if "@" in code_lines[0]:
            code_lines.pop(0)
            offset += 1

        code = "".join(code_lines)

        # remove indent that's left
        code = textwrap.dedent(code)
        return code, offset

    def run_fun(self, fun: Callable, *args: Any, **kwargs: Any) -> object:
        self._raise_if_not_connected()

        source, offset = self._get_fun_src(fun)
        filename = inspect.getsourcefile(fun)
        ret = self._run_remote_fun(
            source, filename=filename, offset=offset, call=fun.__name__, args=args, kwargs=kwargs
        )
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
        filename = inspect.getsourcefile(klass)
        offset = inspect.getsourcelines(klass)[1]
        ret = self._run_remote_fun(
            source, filename=filename, offset=offset, call=f"{klass.__name__}.{fun.__name__}", args=args, kwargs=kwargs
        )
        return ret

    def klass(self, cls: type) -> type:
        # re execute class to get copy
        # this way original class can yield multiple injected classes
        # first_instance = injector1.klass(Klass)
        # second_instance = injector2.klass(Klass)
        source: str = textwrap.dedent(inspect.getsource(cls))

        definition_module = sys.modules[cls.__module__]
        sandbox: Dict[str, Any] = {}
        exec(source, definition_module.__dict__, sandbox)
        cls_cpy = sandbox[cls.__name__]

        cls_cpy._injector = self  # type: ignore
        methods: List[str] = [a for a in dir(cls_cpy) if not a.startswith("__") and callable(getattr(cls_cpy, a))]

        for m in methods:

            def decorator(func: Callable[[], None]) -> Callable:
                def wrapped(*args: Any, **kwargs: Any) -> object:
                    return cls_cpy._injector.run_klass_fun(cls_cpy, func, args, kwargs)  # type: ignore

                return wrapped

            method: Callable[[], None] = getattr(cls_cpy, m)
            setattr(cls_cpy, m, decorator(method))

        return cls_cpy

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


@dataclass
class Injector(BaseInjector):
    port: int = field(init=False)

    def __post_init__(self) -> None:
        pass

    def _get_free_port(self) -> int:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(("", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]

    def prepare(self, port: Optional[int] = None) -> None:
        self.port = port or self._get_free_port()
        self.host = f"{self.host}:{self.port}"
        self._init()


@dataclass
class DjangoInjector(BaseInjector):
    port: int = field(init=False)

    django_settings_module: str

    def _before_execute(self) -> None:
        if not self.download_deps:
            return
        modules = list(sys.modules.keys())[:]
        for m in modules:
            if "django" in m:
                sys.modules.pop(m)

        os.environ["DJANGO_SETTINGS_MODULE"] = self.django_settings_module
        import django

        django.setup()


@dataclass
class FlaskInjector(BaseInjector):
    port: int = field(init=False)
