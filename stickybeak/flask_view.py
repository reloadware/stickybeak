import json
from pathlib import Path
from typing import Dict

import flask
from flask import Flask, Response, request
from flask.views import MethodView

from stickybeak.handle_requests import get_source, inject


class StickybeakAPI(MethodView):
    def get(self) -> Response:
        project_dir: Path = Path(flask.current_app.root_path)  # type: ignore
        return Response(json.dumps(get_source(project_dir)), status=200)

    def post(self) -> Response:
        data: Dict[str, str] = request.json
        return Response(inject(data), status=200)


def setup(app: Flask) -> None:
    app.add_url_rule("/stickybeak/", view_func=StickybeakAPI.as_view("stickybeak"))
