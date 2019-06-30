from typing import Dict

from flask import request, Flask
from flask.views import MethodView
from flask import Response

from stickybeak import sandbox


class StickybeakAPI(MethodView):
    def get(self) -> Response:
        return Response("{}", status=200)

    def post(self) -> Response:
        data: Dict[str, str] = request.json

        code: str = data['code']

        result: bytes = sandbox.execute(code)
        response = Response(result, status=200)

        return response


def setup(app: Flask) -> None:
    app.add_url_rule('/stickybeak/', view_func=StickybeakAPI.as_view('stickybeak'))
