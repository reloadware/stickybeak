from pathlib import Path

root = Path(__file__).parent.absolute()

import envo  # noqa: F401

envo.add_source_roots([root])

import os
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

from envo import Env, Namespace, VirtualEnv, run

# Declare your command namespaces here
# like this:
sb = Namespace("sb")


class StickybeakCommEnv(Env, VirtualEnv):  # type: ignore
    class Meta(Env.Meta):  # type: ignore
        root = root
        name: str = "stickybeak"
        verbose_run = True

    class Environ(Env.Environ, VirtualEnv.Environ):
        ...

    e: Environ

    # Declare your variables here
    test_dir: Path
    test_srvs_dir: Path
    django_srv_dir: Path
    flask_srv_dir: Path
    app_srv_dir: Path
    pip_ver: str = "21.1.3"
    poetry_ver: str = "1.1.7"
    envo_ver: str = "0.9.12"
    black_ver: str = "21.6b0"

    def init(self) -> None:
        super().init()
        self.e.pythonpath = f"{self.meta.root}"

        self.test_dir = self.meta.root / "tests"
        self.test_srvs_dir = self.test_dir / "test_srvs"
        self.django_srv_dir = self.test_srvs_dir / "django_srv"
        self.flask_srv_dir = self.test_srvs_dir / "flask_srv"
        self.app_srv_dir = self.test_srvs_dir / "app_srv"

    @sb.command
    def clean(self) -> None:
        run("rm **/*/__pycache__ -rf")
        run("rm **/*/.eggs -rf")
        run("rm **/*/*.egg-info -rf")
        run("rm **/*/*.egg-info -rf")

    @sb.command
    def bootstrap(self, test_apps=True) -> None:
        run(f"pip install pip=={self.pip_ver}")
        run(f"pip install poetry=={self.poetry_ver}")
        run("poetry config virtualenvs.create true")
        run("poetry config virtualenvs.in-project true")
        run("poetry install --no-root")

        if not test_apps:
            return

        dirs = [self.django_srv_dir, self.flask_srv_dir, self.app_srv_dir]

        for d in dirs:
            os.chdir(d)
            run("poetry config virtualenvs.create true")
            run("poetry config virtualenvs.in-project true")
            run("poetry install --no-root")


ThisEnv = StickybeakCommEnv
