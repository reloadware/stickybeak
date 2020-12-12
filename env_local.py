from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

import envo  # noqa: F401
from envo import (  # noqa: F401
    Plugin,
    Raw,
    VirtualEnv,
    boot_code,
    command,
    context,
    dataclass,
    logger,
    oncreate,
    ondestroy,
    onload,
    onstderr,
    onstdout,
    onunload,
    postcmd,
    precmd,
    run,
)

# Declare your command namespaces here
# like this:
# my_namespace = command(namespace="my_namespace")

localci = command(namespace="localci")


@dataclass
class StickybeakLocalEnv(envo.Env):  # type: ignore
    class Meta(envo.Env.Meta):  # type: ignore
        root = Path(__file__).parent.absolute()
        stage: str = "local"
        emoji: str = "🐣"
        parents: List[str] = ["env_comm.py"]
        plugins: List[Plugin] = []
        name: str = "stickybeak"
        version: str = "0.1.0"
        watch_files: List[str] = []
        ignore_files: List[str] = []

    # Declare your variables here

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Define your variables here

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

    @localci
    def __flake(self) -> None:
        run("circleci local execute --job flake8")


Env = StickybeakLocalEnv
