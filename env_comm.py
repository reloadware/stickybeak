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
    VirtualEnv
)

# Declare your command namespaces here
# like this:
# my_namespace = command(namespace="my_namespace")


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

    # Declare your variables here

    def __init__(self) -> None:
        # Define your variables here
        ...

    @command
    def bootstrap(self) -> None:
        run("poetry config virtualenvs.create true")
        run("poetry config virtualenvs.in-project true")
        run("poetry install")


Env = StickybeakCommEnv
