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


@dataclass
class StickybeakCommEnv(envo.Env):  # type: ignore
    class Meta(envo.Env.Meta):  # type: ignore
        root = Path(__file__).parent.absolute()
        stage: str = "comm"
        emoji: str = "👌"
        parents: List[str] = []
        plugins: List[Plugin] = [VirtualEnv]
        name: str = "stickybeak"
        version: str = "0.1.0"
        watch_files: List[str] = []
        ignore_files: List[str] = []

    # Declare your variables here

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Define your variables here

    @command
    def bootstrap(self) -> None:
        run("poetry config virtualenvs.create true")
        run("poetry config virtualenvs.in-project true")
        run("poetry install")


Env = StickybeakCommEnv
