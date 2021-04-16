from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple  # noqa: F401

import envo  # noqa: F401
from dataclasses import dataclass
from envo import (  # noqa: F401
    Namespace,
    Plugin,
    Raw,
    UserEnv,
    VirtualEnv,
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
)

# Declare your command namespaces here
# like this:
# my_namespace = command(namespace="my_namespace")


class EnvoCommEnv(UserEnv):  # type: ignore
    class Meta(UserEnv.Meta):  # type: ignore
        root = Path(__file__).parent.absolute()
        stage: str = "comm"
        emoji: str = "👌"
        parents: List[str] = []
        plugins: List[Plugin] = []
        name: str = "env"
        version: str = "0.1.0"
        watch_files: List[str] = []
        ignore_files: List[str] = []

    poetry_ver: str
    some_var: str

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
        self.django = self.App(port=5883, host="localhost")
        self.flask = self.App(port=5884, host="localhost")


Env = EnvoCommEnv

