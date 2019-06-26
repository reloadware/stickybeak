from flask import Flask

from stickybeak.flask_view import inject

app = Flask(__name__)

app.register_blueprint(inject)
