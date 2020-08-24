from dataclasses import dataclass
from typing import Any, Dict, List  # noqa: F401

import envo  # noqa: F401
from envo import command, run
from envo import ondestroy  # noqa: F401
from loguru import logger  # noqa: F401

from env_comm import StickybeakEnvComm


@dataclass
class StickybeakEnv(StickybeakEnvComm):  # type: ignore
    class Meta(StickybeakEnvComm.Meta):  # type: ignore
        stage: str = "local"
        emoji: str = "🐣"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @command
    def flake(self) -> None:
        self.black()
        run("flake8 .")

    @command
    def black(self) -> None:
        self.isort()
        run("black .")

    @command
    def isort(self) -> None:
        run("isort .")

    @command
    def mypy(self) -> None:
        run("mypy .")

    @command
    def ci(self) -> None:
        self.flake()
        self.mypy()

    @command
    def test(self) -> None:
        run("pytest -v tests")


Env = StickybeakEnv
