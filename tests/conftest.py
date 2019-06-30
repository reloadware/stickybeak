import pytest
from stickybeak.injector import DjangoInjector

from requests import Response
import os

import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'django_settings'
django.setup()


@pytest.fixture(params=['http://flask-srv:5000',
                        'http://django-srv:8000',
                        'http://local-django-mock'])
def injector(request, mocker):
    from stickybeak.django_view import InjectView

    if request.param == 'http://local-django-mock':
        def mock_post(endpoint: str, data: str, headers: dict) -> Response:
            req = type('', (), {})()
            req.body = data

            django_response = InjectView.post(req)
            response = Response()
            response._content = django_response.content
            response.status_code = django_response.status_code
            return response

        def mock_get(endpoint: str) -> Response:
            req = type('', (), {})()
            django_response = InjectView.get(req)

            response = Response()
            response._content = django_response.content
            response.status_code = django_response.status_code
            return response

        post_mock = mocker.patch('requests.post')
        post_mock.side_effect = mock_post

        get_mock = mocker.patch('requests.get')
        get_mock.side_effect = mock_get

        return DjangoInjector(address=request.param, django_settings_module='django_srv.settings')

    return DjangoInjector(address=request.param, django_settings_module='django_srv.settings')


@pytest.fixture(scope="class")
def django_injector(request):
    request.cls.injector = DjangoInjector(address='http://django-srv:8000',
                                          django_settings_module='django_srv.settings')
