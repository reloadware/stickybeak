import json
import os
from pathlib import Path

import pytest

from requests import Response

from stickybeak.handle_requests import get_source, inject
from stickybeak.injector import DjangoInjector, FlaskInjector


flask_srv: str
django_srv: str
local_srv: str

if "CIRCLECI" in os.environ:
    flask_srv: str = f"http://{os.environ['FLASK_SRV_HOST']}:{os.environ['FLASK_SRV_PORT']}"
    django_srv: str = f"http://{os.environ['DJANGO_SRV_HOSTNAME']}"
    local_srv: str = "http://local-mock"
else:
    flask_srv: str = "http://flask-srv:5000"
    django_srv: str = "http://django-srv:8000"
    local_srv: str = "http://local-mock"


@pytest.fixture(params=[flask_srv,
                        django_srv,
                        local_srv])
def injector(request, mocker):
    if request.param == local_srv:
        def mock_post(endpoint: str, data: str, headers: dict) -> Response:
            result: bytes = inject(json.loads(data))
            response = Response()
            response._content = result
            response.status_code = 200
            return response

        def mock_get(endpoint: str) -> Response:
            response = Response()
            response._content = json.dumps(get_source(Path('tests/django_srv')))
            response.status_code = 200
            return response

        post_mock = mocker.patch('requests.post')
        post_mock.side_effect = mock_post

        get_mock = mocker.patch('requests.get')
        get_mock.side_effect = mock_get

        return DjangoInjector(address=request.param,
                              django_settings_module='tests.django_srv.django_srv.settings')

    if request.param == django_srv:
        return DjangoInjector(address=request.param, django_settings_module='django_srv.settings')

    if request.param == flask_srv:
        return FlaskInjector(address=request.param)


@pytest.fixture(scope="class")
def django_injector(request):
    request.cls.injector = DjangoInjector(address=django_srv,
                                          django_settings_module='django_srv.settings')
