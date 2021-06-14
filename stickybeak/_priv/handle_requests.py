import glob
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from dataclasses import dataclass

import dill as pickle
from typing_extensions import TypedDict

from stickybeak._priv import sandbox, utils
from stickybeak._priv.pip._internal.operations import freeze  # type: ignore
from stickybeak._priv.pip._internal.utils.misc import (
    get_installed_distributions,
)


class Requirement(TypedDict):
    project_name: str
    egg_info: str
    key: str
    version: str


def call_function(source: str, call: str, args: List[Any], kwargs: Dict[str, Any]) -> bytes:
    """Function where the injected code will be executed.
       Helps to avoid local variable conflicts."""

    ret: bytes
    results = {}

    code = f"""
{source}
try:
    __return = {call}(*__args__, **__kwargs__)
except Exception as __exc:
    __exception = __exc
    """

    context = sandbox.__dict__
    context["__args__"] = args
    context["__kwargs__"] = kwargs

    try:
        exec(code, context, results)
        if "__return" in results:
            ret = pickle.dumps(results["__return"])
        elif "__exception" in results:
            ret = pickle.dumps(results["__exception"])
        else:
            ret = pickle.dumps(results)
    except Exception as exc:
        ret = pickle.dumps(exc)

    return ret


def inject(data: Dict[str, str]) -> bytes:
    source: str = data["source"]
    call: str = data["call"]
    args: List[Any] = data["args"]
    kwargs: Dict[str, Any] = data["kwargs"]

    result: bytes = call_function(source=source, call=call, args=args, kwargs=kwargs)

    return result


def get_source(project_dir: Path) -> Dict[str, str]:
    if not project_dir.exists():
        raise RuntimeError(f"{str(project_dir)} directory doesn't exist on the remote server.")

    source_code: Dict[str, str] = {}

    for p in glob.iglob(str(project_dir) + "/**/*.py", recursive=True):
        path: Path = Path(p)
        rel_path: str = str(path.relative_to(project_dir))
        source_code[rel_path] = path.read_text("utf-8")

    return source_code


def get_requirements(venv_path: Optional[Path] = None) -> Dict[str, Requirement]:
    paths: Optional[List[str]] = None
    if venv_path:
        site_packages = utils.get_site_packages_dir_from_venv(venv_path)
        paths = [str(site_packages)]

    cleared_reqs = {}

    from stickybeak._priv.pip._vendor.pkg_resources import EggInfoDistribution

    for r in get_installed_distributions(
        paths=paths, skip=["pip", "pkg-resources", "setuptools", "packaging"], local_only=False,
            include_editables=False
    ):
        # Skip -e installs?
        if isinstance(r, EggInfoDistribution):
            continue

        req = Requirement(project_name=r.project_name,
                          key=r.key,
                          egg_info=r.egg_info,
                          version=r.version)
        cleared_reqs[r.project_name] = req

    return cleared_reqs


def get_envs() -> Dict[str, str]:
    envs: Dict[str, str] = dict()

    for key, value in os.environ.items():
        envs[key] = value

    return envs


def get_data(project_dir: Path) -> Dict[str, Dict[str, str]]:
    data: Dict[str, Dict[str, str]] = {
        "source": get_source(project_dir),
        "requirements": get_requirements(),
        "envs": get_envs(),
    }

    return data
