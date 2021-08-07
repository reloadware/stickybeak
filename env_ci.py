from pathlib import Path

root = Path(__file__).parent.absolute()

import envo

envo.add_source_roots([root])

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from envo import Env, Namespace, logger, run, env_var

from env_comm import StickybeakCommEnv as ParentEnv

p = Namespace("p")


class StickybeakCiEnv(ParentEnv):
    class Meta(ParentEnv.Meta):
        stage: str = "ci"
        emoji: str = "⚙"
        load_env_vars = True

    class Environ(ParentEnv.Environ):
        pypi_username: Optional[str] = env_var(raw=True)
        pypi_password: Optional[str] = env_var(raw=True)

    e: Environ

    def init(self) -> None:
        super().init()

    @p.command
    def bootstrap(self, test_apps=True) -> None:
        super().bootstrap(test_apps)

    @p.command
    def test(self) -> None:
        run("pytest --reruns 2 -v tests")

    @p.command
    def build(self) -> None:
        run("poetry build")

    @p.command
    def publish(self) -> None:
        run(f'poetry publish --username "{self.e.pypi_username}" --password "{self.e.pypi_password}"', verbose=False)

    @p.command
    def rstcheck(self) -> None:
        pass
        # run("rstcheck README.rst | tee ./workspace/rstcheck.txt")

    @p.command
    def flake(self) -> None:
        pass
        # run("flake8 . | tee ./workspace/flake8.txt")

    @p.command
    def check_black(self) -> None:
        run("black --check .")

    @p.command
    def check_isort(self) -> None:
        run("black --check .")

    @p.command
    def mypy(self) -> None:
        pass
        run("mypy .")

    @p.command
    def generate_version(self) -> None:
        import toml

        config = toml.load(str(self.meta.root / "pyproject.toml"))
        version: str = config["tool"]["poetry"]["version"]

        version_file = self.meta.root / "stickybeak/__version__.py"
        Path(version_file).touch()

        version_file.write_text(f'__version__ = "{version}"\n')


ThisEnv = StickybeakCiEnv
