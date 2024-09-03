from pathlib import Path

root = Path(__file__).parent.absolute()

import envo

envo.add_source_roots([root])

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from envo import Env, env_var, logger, run, command

from env_comm import StickybeakCommEnv as ParentEnv


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

    @command
    def p__bootstrap(self, test_apps=True) -> None:
        super().p__bootstrap(test_apps)

    @command
    def p__test(self) -> None:
        run("pytest --reruns 2 -v tests")

    @command
    def p__build(self) -> None:
        run("poetry build")

    @command
    def p__publish(self) -> None:
        run(f'poetry publish --username "{self.e.pypi_username}" --password "{self.e.pypi_password}"', verbose=False)

    @command
    def p__rstcheck(self) -> None:
        pass
        # run("rstcheck README.rst | tee ./workspace/rstcheck.txt")

    @command
    def p__flake(self) -> None:
        pass
        # run("flake8 . | tee ./workspace/flake8.txt")

    @command
    def p__check_black(self) -> None:
        run("black --check .")

    @command
    def p__check_isort(self) -> None:
        run("black --check .")

    @command
    def p__generate_version(self) -> None:
        import toml

        config = toml.load(str(self.meta.root / "pyproject.toml"))
        version: str = config["tool"]["poetry"]["version"]

        version_file = self.meta.root / "stickybeak/__version__.py"
        Path(version_file).touch()

        version_file.write_text(f'__version__ = "{version}"\n')


ThisEnv = StickybeakCiEnv
