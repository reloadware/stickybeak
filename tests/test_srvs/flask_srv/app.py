import os
from pathlib import Path

from flask import Flask

import stickybeak

os.environ["TEST_ENV"] = "TEST_ENV_VALUE"
stickybeak_port = int(os.environ["STICKYBEAK_PORT"])

stickybeak.Server(project_root=Path(os.getcwd()), port=stickybeak_port).run()


app = Flask(__name__)
app.run()
