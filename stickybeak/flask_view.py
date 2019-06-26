from flask import Blueprint, request

from . import sandbox


inject = Blueprint('inject', 'inject')


@inject.route('/inject/', methods=['POST'])
def inject_view():
    data = request.json

    code = data['code']

    result = sandbox.execute(code)
    response = result

    return response
