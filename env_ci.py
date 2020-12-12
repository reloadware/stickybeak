from typing import List, Dict, Any, Optional, Tuple  # noqa: F401

from pathlib import Path

import envo  # noqa: F401

from envo import (  # noqa: F401
    logger,
    command,
    context,
    Raw,
    run,
    precmd,
    onstdout,
    onstderr,
    postcmd,
    onload,
    oncreate,
    onunload,
    ondestroy,
    dataclass,
    boot_code,
    Plugin,
    VirtualEnv
)

# Declare your command namespaces here
# like this:
# my_namespace = command(namespace="my_namespace")


@dataclass
class StickybeakCiEnv(envo.Env):  # type: ignore
    class Meta(envo.Env.Meta):  # type: ignore
        root = Path(__file__).parent.absolute()
        stage: str = "ci"
        emoji: str = "🧪"
        parents: List[str] = ["env_comm.py"]
        plugins: List[Plugin] = []
        name: str = "stickybeak"
        version: str = "0.1.0"
        watch_files: List[str] = []
        ignore_files: List[str] = []

    # Declare your variables here

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Define your variables here

    # Define your commands, hooks and properties here


Env = StickybeakCiEnv
