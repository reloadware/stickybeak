from dataclasses import dataclass, field
from pathlib import Path
from textwrap import dedent
import os

root = Path(__file__).parent.absolute()

import envo

envo.add_source_roots([root])

import shutil
from typing import Any, Dict, List, Optional, Tuple

from envo import Env, inject, run, command

from env_comm import StickybeakCommEnv as ParentEnv


@dataclass
class Job:
    name: str
    command: str
    python_versions: List[float] = field(default_factory=lambda: [3.9])


def bootstrap_version(version: str) -> None:
    shutil.rmtree(".venv", ignore_errors=True)
    path_tmp = os.environ["PATH"]
    os.environ["PATH"] = f"{Path.home()}/.pyenv/versions/{version}/bin/:{os.environ['PATH']}"

    try:
        run(f"poetry config virtualenvs.create false")
        run(f"poetry config virtualenvs.in-project true")

        run(f"python -m venv .venv")

        run(f"poetry install")
    finally:
        os.environ["PATH"] = path_tmp


class StickybeakLocalEnv(ParentEnv):  # type: ignore
    class Meta(ParentEnv.Meta):  # type: ignore
        stage: str = "local"
        emoji: str = "🐣"

    class Environ(ParentEnv.Environ):
        pass

    e: Environ

    ci_template: Path
    ci_out: Path

    def init(self) -> None:
        super().init()

        self.ci_template = self.meta.root / ".github/workflows/test.yml.templ"
        self.ci_out = self.meta.root / ".github/workflows/test.yml"

    @command
    def render_ci(self) -> None:
        from jinja2 import StrictUndefined, Template

        bootstrap_code = dedent(
            """
        - uses: actions/checkout@v2
        - name: Set up Python
          uses: actions/setup-python@v2
          with:
            {%- raw %}
            python-version: ${{ matrix.python_version }}
            {%- endraw %}
        - uses: gerbal/always-cache@v1.0.3
          id: pip-cache
          with:
            path: ~/.cache/pip
            key: pip-cache-{{ ctx.pip_ver }}-{{ ctx.poetry_ver }}-{{ ctx.envo_ver }}
            restore-keys: pip-cache-
        - run: pip install pip=={{ ctx.pip_ver }}
        - run: pip install poetry=={{ ctx.poetry_ver }}
        - run: pip install envo=={{ ctx.envo_ver }}
        - uses: actions/cache@v2
          id: root-venv-cache
          with:
            path: |
              .venv
              tests/test_srvs/app_srv/.venv
              tests/test_srvs/django_srv/.venv
              tests/test_srvs/flask_srv/.venv
            {%- raw %}
            key: root-venv-v3-${{ hashFiles('poetry.lock') }}
            {%- endraw %}
            restore-keys: root-venv-v3-
        """
        )

        bootstrap_code = Template(bootstrap_code, undefined=StrictUndefined).render({"ctx": self.ctx})

        ctx = {
            "ctx": self.ctx,
            "bootstrap_code": bootstrap_code,
        }

        templ = Template(self.ci_template.read_text(), undefined=StrictUndefined)
        self.ci_out.write_text(templ.render(**ctx))

    @command
    def p__bootstrap(self) -> None:
        shutil.rmtree(".venv", ignore_errors=True)
        shutil.rmtree(self.django_srv_dir / ".venv", ignore_errors=True)
        shutil.rmtree(self.flask_srv_dir / ".venv", ignore_errors=True)
        super().p__bootstrap()

    @command
    def p__flake(self) -> None:
        self.black()
        inject("flake8 .")

    @command
    def p__black(self) -> None:
        self.isort()
        inject("black .")

    @command
    def p__isort(self) -> None:
        inject("isort .")

    @command
    def p__mypy(self) -> None:
        inject("mypy stickybeak")

    @command
    def p__ci(self) -> None:
        self.flake()
        self.mypy()

    @command
    def p__test(self) -> None:
        inject("pytest -v tests")


ThisEnv = StickybeakLocalEnv
