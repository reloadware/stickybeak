import json
from pathlib import Path
from typing import Dict, Union

import dill as pickle
import flask
from flask import Flask, Response, request
from flask.views import MethodView

from stickybeak.handle_requests import InjectData, get_server_data, inject


def setup(app: Flask, endpoint: str, project_dir: Union[str, Path]) -> None:
    project_dir = Path(project_dir)

    class InjectView(MethodView):
        def post(self) -> Response:
            data: InjectData = pickle.loads(request.data)
            return Response(inject(data), status=200)

    class DataView(MethodView):
        def get(self) -> Response:
            data = get_server_data(project_dir)
            response_data = json.dumps(data)
            return Response(response_data, status=200)

    app.add_url_rule(f"/{endpoint}/inject", view_func=InjectView.as_view("inject"))
    app.add_url_rule(f"/{endpoint}/data", view_func=DataView.as_view("data"))
