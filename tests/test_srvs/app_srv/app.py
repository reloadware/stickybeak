import os
from pathlib import Path
from time import sleep

import stickybeak

os.environ["TEST_ENV"] = "TEST_ENV_VALUE"
stickybeak_port = int(os.environ["STICKYBEAK_PORT"])
timeout = os.environ.get("STICKYBEAK_TIMEOUT")
timeout = float(timeout) if timeout else None

start_delay = os.environ.get("STICKYBEAK_STARTDELAY")
start_delay = float(start_delay) if start_delay else None

project_root = os.environ.get("STICKYBEAK_PROJECTROOT", None)

if start_delay:
    sleep(start_delay)

stickybeak.Server(project_root=project_root, port=stickybeak_port, timeout=timeout).run()


while True:
    sleep(1)
