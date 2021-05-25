import os
from pathlib import Path

from flask import Flask

import stickybeak

os.environ["TEST_ENV"] = "TEST_ENV_VALUE"
stickybeak_port = int(os.environ["STICKYBEAK_PORT"])
timeout = os.environ.get("STICKYBEAK_TIMEOUT")
timeout = float(timeout) if timeout else None

stickybeak.Server(project_root=Path(os.getcwd()), port=stickybeak_port, timeout=timeout).run()


app = Flask(__name__)

if __name__ == "__main__":
    app.run()
