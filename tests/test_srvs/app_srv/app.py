import os
from pathlib import Path
from time import sleep

import stickybeak

os.environ["TEST_ENV"] = "TEST_ENV_VALUE"
stickybeak_port = int(os.environ["STICKYBEAK_PORT"])
timeout = os.environ.get("STICKYBEAK_TIMEOUT")
timeout = float(timeout) if timeout else None

stickybeak.Server(project_root=Path(__file__).parent, port=stickybeak_port, timeout=timeout).run()


while True:
    sleep(1)
