from flask import Flask

from stickybeak.flask_view import setup

app = Flask(__name__)
setup(app)
