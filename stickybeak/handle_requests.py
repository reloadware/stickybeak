import glob
import os
from pathlib import Path
import traceback
from typing import Any, Dict, List, Optional, Union, TypedDict

import dill as pickle

from stickybeak import sandbox

INJECT_ENDPOINT = "inject"
SERVER_DATA_ENDPOINT = "data"


class InjectData(TypedDict):
    source: str  # source code of function/class
    filename: str  # filename of original injection function/class definition
    offset: int  # injection code line offset
    call: str  # call statement
    args: List[Any]
    kwargs: Dict[str, Any]


class ServerData(TypedDict):
    source: Dict[str, str]  # file -> source
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


def get_envs() -> Dict[str, str]:
    envs: Dict[str, str] = dict()

    for key, value in os.environ.items():
        envs[key] = value

    return envs


def get_server_data(project_dir: Union[str, Path, None]) -> ServerData:
    if project_dir:
        project_dir = Path(project_dir)
        source = get_source(project_dir)
    else:
        source = {}

    data = ServerData(
        source=source,
        envs=get_envs(),
    )
    return data
