import glob
import os
from pathlib import Path
import sys
from typing import Dict, List, Optional

from stickybeak._priv import sandbox, utils
from stickybeak._priv.pip._internal.operations import freeze  # type: ignore


def inject(data: Dict[str, str]) -> bytes:
    code: str = data["code"]

    result: bytes = sandbox.execute(code)

    return result


def get_source(project_dir: Path) -> Dict[str, str]:
    if not project_dir.exists():
        raise RuntimeError(f"{str(project_dir)} directory doesn't exist on the remote server.")

    source_code: Dict[str, str] = {}

    for p in glob.iglob(str(project_dir) + "/**/*.py", recursive=True):
        path: Path = Path(p)
        rel_path: str = str(path.relative_to(project_dir))
        source_code[rel_path] = path.read_text()

    return source_code


def get_requirements(venv_path: Optional[Path] = None) -> Dict[str, str]:
    paths: Optional[List[str]] = None
    if venv_path:
        site_packages = utils.get_site_packges_from_venv(venv_path)
        paths = [str(site_packages)]

    cleared_reqs: Dict[str, str] = {}

    for r in freeze.freeze(
        paths=paths, exclude_editable=True, skip=["stickybeak", "pip", "pkg-resources", "setuptools"]
    ):
        name: str = r.split("==")[0]
        version: str = r.split("==")[1]
        cleared_reqs[name] = version

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
