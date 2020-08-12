from dataclasses import dataclass
from typing import Any, Dict, List  # noqa: F401

import envo  # noqa: F401
from envo import ondestroy  # noqa: F401
from loguru import logger  # noqa: F401

from .env_comm import EnvComm


@dataclass
class Env(EnvComm):  # type: ignore
    class Meta(EnvComm.Meta):  # type: ignore
        stage: str = "test"
        emoji: str = "🛠"

    # Declare your variables here

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Define your variables here

    # Define your commands, hooks and properties here
