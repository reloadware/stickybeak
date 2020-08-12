from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List  # noqa: F401kuba walczak

import envo  # noqa: F401
from envo import command, run
from envo import oncreate  # noqa: F401
from loguru import logger  # noqa: F401

from env_comm import StickybeakEnvComm


@dataclass
class StickybeakEnv(StickybeakEnvComm):  # type: ignore
    class Meta(StickybeakEnvComm.Meta):  # type: ignore
        stage: str = "ci"
        emoji: str = "🧪"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @command
    def bootstrap(self) -> None:
        run("mkdir -p workspace")
        super().bootstrap()

    @command
    def build(self) -> None:
        run("poetry build")

    @command
    def publish(self) -> None:
        run("poetry publish --username $PYPI_USERNAME --password $PYPI_PASSWORD")

    @command
    def rstcheck(self) -> None:
        run("rstcheck README.rst | tee ./workspace/rstcheck.txt")

    @command
    def test(self) -> None:
        run("pytest -v tests --cov-report xml:workspace/cov.xml --cov=stickybeak ./workspace")

    @command
    def flake(self) -> None:
        run("flake8 . | tee ./workspace/flake8.txt")

    @command
    def check_black(self) -> None:
        run("black --check . | tee ./workspace/black.txt")

    @command
    def mypy(self) -> None:
        run("mypy . | tee ./workspace/mypy.txt")

    @command
    def generate_version(self) -> None:
        import toml

        config = toml.load(str(self.root / "pyproject.toml"))
        version: str = config["tool"]["poetry"]["version"]

        version_file = self.root / "stickybeak/__version__.py"
        Path(version_file).touch()

        version_file.write_text(f'__version__ = "{version}"\n')

    @command
    def upload_codecov(self) -> None:
        run(
            """
            curl -s https://codecov.io/bash | bash -s -- \
            -t "${CODECOV_TOKEN}" \
            -n "${CIRCLE_BUILD_NUM}" \
            -f "./workspace/cov.xml" \
            -Z
            """
        )


Env = StickybeakEnv
