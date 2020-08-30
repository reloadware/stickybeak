import os
from pathlib import Path

from flask import Flask

import stickybeak

stickybeak.Server(project_root=Path(os.getcwd()), port=5884).run()


app = Flask(__name__)
app.run()
