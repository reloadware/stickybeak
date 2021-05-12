import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

from envo import (  # noqa: F401
    Plugin,
    Raw,
    VirtualEnv,
    boot_code,
    command,
    context,
    Namespace,
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
    UserEnv
)

# Declare your command namespaces here
# like this:

localci = Namespace(name="localci")


class StickybeakLocalEnv(UserEnv):  # type: ignore
    class Meta(UserEnv.Meta):  # type: ignore
        root = Path(__file__).parent.absolute()
        stage: str = "local"
        emoji: str = "🐣"
        parents: List[str] = ["env_comm.py"]
        name: str = "stickybeak"
        version: str = "0.1.0"
        plugins: List[Plugin] = []
        watch_files: List[str] = []
        ignore_files: List[str] = []

    # Declare your variables here

    def __init__(self) -> None:
        # Define your variables here
        ...

    @command
    def bootstrap(self) -> None:
        shutil.rmtree(".venv")
        shutil.rmtree(self.django_srv_dir / ".venv", ignore_errors=True)
        shutil.rmtree(self.flask_srv_dir / ".venv", ignore_errors=True)
        super().bootstrap()

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
        os.chdir(self.root)
        run("pytest -v tests")

    @localci.command
    def __flake(self) -> None:
        run("circleci local execute --job flake8")


Env = StickybeakLocalEnv
