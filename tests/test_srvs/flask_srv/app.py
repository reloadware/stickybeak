import os
from pathlib import Path

from flask import Flask

from stickybeak.flask_view import setup

os.environ["TEST_ENV"] = "TEST_ENV_VALUE"

app = Flask(__name__)
setup(app, endpoint="sb", project_dir=Path(__file__).parent)
