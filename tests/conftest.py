import json
from pathlib import Path

import pytest
from requests import Response

from stickybeak.handle_requests import get_source, inject
from stickybeak.injector import DjangoInjector, FlaskInjector


@pytest.fixture(params=['http://flask-srv:5000',
                        'http://django-srv:8000',
                        'http://local-mock'])
def injector(request, mocker):
    if request.param == 'http://local-mock':
        def mock_post(endpoint: str, data: str, headers: dict) -> Response:
            result: bytes = inject(json.loads(data))
            response = Response()
            response._content = result
            response.status_code = 200
            return response

        def mock_get(endpoint: str) -> Response:
            response = Response()
            response._content = json.dumps(get_source(Path('tests/django_srv/flesh')))
            response.status_code = 200
            return response

        post_mock = mocker.patch('requests.post')
        post_mock.side_effect = mock_post

        get_mock = mocker.patch('requests.get')
        get_mock.side_effect = mock_get

        return DjangoInjector(address=request.param,
                              django_settings_module='tests.django_srv.flesh.django_srv.settings')

    if request.param == 'http://django-srv:8000':
        return DjangoInjector(address=request.param, django_settings_module='django_srv.settings')

    if request.param == 'http://flask-srv:5000':
        return FlaskInjector(address=request.param)


@pytest.fixture(scope="class")
def django_injector(request):
    request.cls.injector = DjangoInjector(address='http://django-srv:8000',
                                          django_settings_module='django_srv.settings')
