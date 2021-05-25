import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

import envo  # noqa: F401
from envo import (  # noqa: F401
    Plugin,
    Raw,
    boot_code,
    command,
    context,
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
    UserEnv,
    VirtualEnv,
    Namespace
)

# Declare your command namespaces here
# like this:
sb = Namespace("sb")


class StickybeakCommEnv(UserEnv):  # type: ignore
    class Meta(UserEnv.Meta):  # type: ignore
        root = Path(__file__).parent.absolute()
        stage: str = "comm"
        emoji: str = "👌"
        parents: List[str] = []
        name: str = "stickybeak"
        version: str = "0.1.0"
        watch_files: List[str] = []
        ignore_files: List[str] = []
        plugins: List[Plugin] = [VirtualEnv]
        verbose_run = True

    # Declare your variables here
    test_dir: Path
    test_srvs_dir: Path
    django_srv_dir: Path
    flask_srv_dir: Path
    pip_version: str
    poetry_version: str

    def __init__(self) -> None:
        # Define your variables here
        self.test_dir = self.root / "tests"
        self.test_srvs_dir = self.test_dir / "test_srvs"
        self.django_srv_dir = self.test_srvs_dir / "django_srv"
        self.flask_srv_dir = self.test_srvs_dir / "flask_srv"
        self.pip_version = "21.0.1"
        self.poetry_version = "1.0.10"

    @sb.command
    def bootstrap(self) -> None:
        run(f"pip install pip=={self.pip_version}")
        run(f"pip install poetry=={self.poetry_version}")
        run("poetry config virtualenvs.create true")
        run("poetry config virtualenvs.in-project true")
        run("poetry install --no-root")

        os.chdir(self.django_srv_dir)
        run("poetry config virtualenvs.create true")
        run("poetry config virtualenvs.in-project true")
        run("poetry install --no-root")

        os.chdir(self.flask_srv_dir)
        run("poetry config virtualenvs.create true")
        run("poetry config virtualenvs.in-project true")
        run("poetry install --no-root")


Env = StickybeakCommEnv
