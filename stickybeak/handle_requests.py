import glob
import os
from pathlib import Path
from typing import Dict, List

from stickybeak import sandbox


def inject(data: Dict[str, str]) -> bytes:
    code: str = data["code"]

    result: bytes = sandbox.execute(code)

    return result


def get_source(project_dir: Path) -> Dict[str, str]:
    if not project_dir.exists():
        raise RuntimeError(
            f"{str(project_dir)} directory doesn't exist on the remote server."
        )

    source_code: Dict[str, str] = {}

    for p in glob.iglob(str(project_dir) + "/**/*.py", recursive=True):
        path: Path = Path(p)
        rel_path: str = str(path.relative_to(project_dir))
        source_code[rel_path] = path.read_text()

    return source_code


def get_requirements() -> str:
    try:
        from pip._internal.operations import freeze  # type: ignore
    except ImportError:  # pip < 10.0
        from pip.operations import freeze  # type: ignore

    cleared_reqs: List[str] = []

    for r in freeze.freeze():
        if ("-e" not in r) and ("stickybeak" not in r):
            cleared_reqs.append(r)

    return "\n".join(cleared_reqs)


def get_envs() -> Dict[str, str]:
    envs: Dict[str, str] = dict()

    for key, value in os.environ.items():
        envs[key] = value

    return envs
