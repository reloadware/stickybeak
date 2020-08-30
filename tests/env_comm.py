from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

import envo
from envo import ondestroy  # noqa: F401
from loguru import logger  # noqa: F401


@dataclass
class EnvComm(
    # Add plugins here
    envo.Env
):
    class Meta(envo.Env.Meta):
        root = Path(__file__).parent.absolute()
        name: str = "tests"
        version: str = "0.1.0"
        watch_files: Tuple[str, ...] = ()
        ignore_files: Tuple[str, ...] = ()
        parent: Optional[str] = None

    # Declare your variables here

    @dataclass
    class App(envo.BaseEnv):
        port: int
        host: str

        @property
        def hostname(self) -> str:
            return f"http://{self.host}:{self.port}"

    flask: App
    django: App

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.django = self.App(port=5883, host="localhost")
        self.flask = self.App(port=5884, host="localhost")

        # Define your variables here

    # Define your commands, hooks and properties here


Env = EnvComm
