import json
from pathlib import Path
from typing import Dict

import flask
from flask import Flask, Response, request
from flask.views import MethodView

from stickybeak import handle_requests


class InjectView(MethodView):
    def post(self) -> Response:
        data: Dict[str, str] = request.json
        return Response(handle_requests.inject(data), status=200)


class DataView(MethodView):
    def get(self) -> Response:
        project_dir: Path = Path(flask.current_app.root_path)  # type: ignore
        return Response(json.dumps(handle_requests.get_data(project_dir)), status=200)


def setup(app: Flask) -> None:
    app.add_url_rule("/stickybeak/inject", view_func=InjectView.as_view("inject"))
    app.add_url_rule("/stickybeak/data", view_func=DataView.as_view("data"))
