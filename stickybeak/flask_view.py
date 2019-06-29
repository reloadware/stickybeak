from flask import Blueprint, request
from flask.views import MethodView
from flask import Response

from stickybeak import sandbox


class StickybeakAPI(MethodView):
    def get(self):
        return Response("{}", status=200)

    def post(self):
        data = request.json

        code = data['code']

        result = sandbox.execute(code)
        response = Response(result, status=200)

        return response


def setup(app):
    app.add_url_rule('/stickybeak/', view_func=StickybeakAPI.as_view('stickybeak'))

