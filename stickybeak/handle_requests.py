import glob
import os
from pathlib import Path
import traceback
from typing import Any, Dict, List, Optional, Union

import dill as pickle
from typing_extensions import TypedDict

from stickybeak import sandbox, utils
from stickybeak.vendored.pip._internal.operations import freeze  # type: ignore
from stickybeak.vendored.pip._internal.utils.misc import get_installed_distributions

INJECT_ENDPOINT = "inject"
SERVER_DATA_ENDPOINT = "data"


class InjectData(TypedDict):
    source: str  # source code of function/class
    filename: str  # filename of original injection function/class definition
    offset: int  # injection code line offset
    call: str  # call statement
    args: List[Any]
    kwargs: Dict[str, Any]


class Requirement(TypedDict):
    project_name: str
    egg_info: str
    key: str
    version: str


class ServerData(TypedDict):
    source: Dict[str, str]  # file -> source
    requirements: Dict[str, Requirement]  # requirement name -> Requirement
    envs: Dict[str, str]  # env name -> env value


def call_function(data: InjectData) -> bytes:
    """Function where the injected code will be executed.
    Helps to avoid local variable conflicts."""

    ret: bytes
    results: Dict[str, Any] = {}

    offset = "\n" * (data["offset"] - 3)

    code = f"""
{offset}
{data["source"]}
__return = {data["call"]}(*__args__, **__kwargs__)
    """

    context = sandbox.__dict__
    context["__args__"] = data["args"]
    context["__kwargs__"] = data["kwargs"]

    try:
        code_obj = compile(code, filename=data["filename"], mode="exec")
        exec(code_obj, context, results)
        ret = pickle.dumps(results["__return"])
    except Exception as exc:
        exc.__traceback_str__ = traceback.format_exc()  # type: ignore
        ret = pickle.dumps(exc)

    return ret


def inject(data: InjectData) -> bytes:
    result: bytes = call_function(data)

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

    from stickybeak.vendored.pip._vendor.pkg_resources import EggInfoDistribution

    for r in get_installed_distributions(
        paths=paths, skip=["pip", "pkg-resources", "setuptools", "packaging"], local_only=False, include_editables=False
    ):
        # Skip -e installs?
        if isinstance(r, EggInfoDistribution):
            continue

        req = Requirement(project_name=r.project_name, key=r.key, egg_info=r.egg_info, version=r.version)
        cleared_reqs[r.project_name] = req

    return cleared_reqs


def get_envs() -> Dict[str, str]:
    envs: Dict[str, str] = dict()

    for key, value in os.environ.items():
        envs[key] = value

    return envs


def get_server_data(project_dir: Union[str, Path]) -> ServerData:
    project_dir = Path(project_dir)
    data = ServerData(
        source=get_source(project_dir),
        requirements=get_requirements(),
        envs=get_envs(),
    )
    return data
