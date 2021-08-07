from pathlib import Path

root = Path(__file__).parent.absolute()

import envo

envo.add_source_roots([root])

import os
from typing import Any, Dict, List, Optional, Tuple

from envo import Env, Namespace, VirtualEnv, run, ctx_var

# Declare your command namespaces here
# like this:
sb = Namespace("sb")


class StickybeakCommEnv(Env, VirtualEnv):
    class Meta(Env.Meta):
        root = root
        name: str = "stickybeak"
        verbose_run = True

    class Environ(Env.Environ, VirtualEnv.Environ):
        ...

    class Ctx(Env.Ctx, VirtualEnv.Ctx):
        pip_ver: str = ctx_var("21.1.3")
        poetry_ver: str = ctx_var("1.1.7")
        envo_ver: str = ctx_var("0.9.27")
        black_ver: str = ctx_var("21.6b0")
        python_versions: List[float] = ctx_var(default_factory=lambda: [3.6, 3.7, 3.8, 3.9])

    e: Environ
    ctx: Ctx

    # Declare your variables here
    test_dir: Path
    test_srvs_dir: Path
    django_srv_dir: Path
    flask_srv_dir: Path
    app_srv_dir: Path

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
        run(f"pip install pip=={self.ctx.pip_ver}")
        run(f"pip install poetry=={self.ctx.poetry_ver}")
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
