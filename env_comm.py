from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

import envo
from envo import VirtualEnv, command, run
from envo import oncreate  # noqa: F401
from loguru import logger  # noqa: F401


@dataclass
class StickybeakEnvComm(VirtualEnv, envo.Env):
    class Meta(envo.Env.Meta):
        root = Path(__file__).parent.absolute()
        name: str = "stickybeak"
        version: str = "0.1.0"
        watch_files: Tuple[str, ...] = ()
        ignore_files: Tuple[str, ...] = ()
        parent: Optional[str] = None

    # Declare your variables here

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Define your variables here

    @command
    def bootstrap(self) -> None:
        run("poetry config virtualenvs.create true")
        run("poetry config virtualenvs.in-project true")
        run("poetry install")


Env = StickybeakEnvComm
