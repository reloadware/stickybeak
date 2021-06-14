import os
from typing import List, Dict, Any, Optional, Tuple  # noqa: F401

from pathlib import Path

from envo import (  # noqa: F401
    logger,
    command,
    context,
    run,
    precmd,
    onstdout,
    onstderr,
    postcmd,
    onload,
    oncreate,
    onunload,
    ondestroy,
    boot_code,
    Plugin,
    VirtualEnv,
    UserEnv,
    Namespace
)

# Declare your command namespaces here
# like this:
# my_namespace = command(namespace="my_namespace")
sb = Namespace("sb")


class StickybeakCiEnv(UserEnv):  # type: ignore
    class Meta(UserEnv.Meta):  # type: ignore
        root = Path(__file__).parent.absolute()
        stage: str = "ci"
        emoji: str = "🧪"
        parents: List[str] = ["env_comm.py"]
        name: str = "stickybeak"
        version: str = "0.1.0"
        plugins: List[Plugin] = []
        watch_files: List[str] = []
        ignore_files: List[str] = []
        verbose_run = True

    class Environ(UserEnv.Environ):
        pass
    e: Environ

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Define your variables here

    @sb.command
    def bootstrap(self) -> None:
        run("mkdir -p workspace")
        super().bootstrap()

    @sb.command
    def test(self) -> None:
        os.chdir(self.root)
        logger.info("Running tests", print_msg=True)
        run("pytest --reruns 3 -v tests --cov-report xml:workspace/cov.xml --cov=stickybeak ./workspace")

    @sb.command
    def build(self) -> None:
        run("poetry build")

    @sb.command
    def publish(self) -> None:
        run("poetry publish --username $PYPI_USERNAME --password $PYPI_PASSWORD")

    @sb.command
    def rstcheck(self) -> None:
        pass
        # run("rstcheck README.rst | tee ./workspace/rstcheck.txt")

    @sb.command
    def flake(self) -> None:
        pass
        # run("flake8 . | tee ./workspace/flake8.txt")

    @sb.command
    def check_black(self) -> None:
        pass
        # run("black --check . | tee ./workspace/black.txt")

    @sb.command
    def mypy(self) -> None:
        pass
        # run("mypy . | tee ./workspace/mypy.txt")

    @sb.command
    def generate_version(self) -> None:
        import toml

        config = toml.load(str(self.root / "pyproject.toml"))
        version: str = config["tool"]["poetry"]["version"]

        version_file = self.root / "stickybeak/__version__.py"
        Path(version_file).touch()

        version_file.write_text(f'__version__ = "{version}"\n')

    @sb.command
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


Env = StickybeakCiEnv
