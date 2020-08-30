import hashlib
import inspect
import os
from pathlib import Path
import pickle
import subprocess
import sys
import textwrap
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from stickybeak._priv import pip, utils
from stickybeak._priv.handle_requests import get_requirements
from stickybeak._priv.utils import Client

__all__ = ["InjectorException", "Injector", "DjangoInjector"]


class InjectorException(Exception):
    pass


class Injector:
    """Provides interface for code injection."""

    connected: bool
    stickybeak_dir: Path

    _client: Client
    _data: Dict[str, Dict[str, str]]  # server data like source or pip freeze requirements

    def __init__(self, address: str) -> None:
        """
        :param address: service address that's gonna be injected.
        :param endpoint:
        """
        self.address: str = address
        self._client = Client(self.address)

        self.name: str = urlparse(self.address).netloc

        project_dir: Path = Path(".").absolute()
        project_hash = hashlib.sha1(str(project_dir).encode("utf-8")).hexdigest()[0:8]
        self.stickybeak_dir = Path.home() / ".stickybeak" / Path(f"{self.name}_{project_hash}")
        self.stickybeak_dir = Path(str(self.stickybeak_dir).replace(":", "_"))

        self._data = {}
        self.connected = False

    def connect(self) -> None:
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
            abs_path.write_text(source)

        # ########## collect requirements

        venv_dir = (self.stickybeak_dir / ".venv").absolute()

        if not venv_dir.exists():
            subprocess.check_output([f"virtualenv", f"{venv_dir}"], stderr=subprocess.DEVNULL)

        remote_reqs = self._data["requirements"]
        local_reqs = get_requirements(venv_dir)

        reqs_diff = {p: v for p, v in remote_reqs.items() if p not in local_reqs or local_reqs[p] != remote_reqs[p]}

        if reqs_diff:
            reqs = [f"{p}=={v}" for p, v in reqs_diff.items()]
            pip.main(["install", f"--target={str(utils.get_site_packges_from_venv(venv_dir))}", *reqs])

        self.connected = True

    def _raise_if_not_connected(self) -> None:
        if not self.connected:
            raise InjectorException("Injector not connected! Run connect() first.")

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

        site_packages = utils.get_site_packges_from_venv(self.stickybeak_dir.absolute() / ".venv")
        sys.path = [str(site_packages), *sys.path]

        self._before_execute()
        content: bytes = self._client.post("", data={"code": code}).content
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
    def _format_args(args: Optional[Tuple[object, ...]], kwargs: Optional[Dict[str, object]]) -> str:
        def format_val(val: Any) -> Any:
            if isinstance(val, str):
                return f'"{val}"'
            return str(val)

        ret = ""
        if args:
            args_clean: str = ", ".join([format_val(a) for a in args])
            ret += args_clean

        if kwargs:
            kwargs_clean: str = ", ".join([f"{str(k)}={format_val(v)}" for k, v in kwargs.items()])
            ret += (", " if args else "") + kwargs_clean

        return f"({ret})"

    def run_fun(
        self,
        fun: Callable[[], None],
        args: Optional[Tuple[object, ...]] = None,
        kwargs: Optional[Dict[str, object]] = None,
    ) -> object:
        self._raise_if_not_connected()

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
        self._raise_if_not_connected()

        code: str = textwrap.dedent(inspect.getsource(klass))
        code += f"\n__return = {klass.__name__}.{fun}{self._format_args(args, kwargs)}"
        code = self._add_try_except(code)
        ret = self.run_code(code)
        return ret

    def klass(self, cls: type) -> type:
        cls._injector = self  # type: ignore
        methods: List[str] = [a for a in dir(cls) if not a.startswith("__") and callable(getattr(cls, a))]

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
        ret = textwrap.indent(code, "    ")  # use tabs instead of spaces, easier to debug
        code_lines = ret.splitlines(True)
        code_lines.insert(0, "try:\n")
        except_block = """\nexcept Exception as __exc:\n    __exception = __exc\n"""

        code_lines.append(except_block)

        ret = "".join(code_lines)
        return ret


class DjangoInjector(Injector):
    def __init__(self, address: str, django_settings_module: str) -> None:
        super().__init__(address=address)
        self.django_settings_module = django_settings_module

    def _before_execute(self) -> None:
        modules = list(sys.modules.keys())[:]
        for m in modules:
            if "django" in m:
                sys.modules.pop(m)

        os.environ["DJANGO_SETTINGS_MODULE"] = self.django_settings_module
        import django

        django.setup()
