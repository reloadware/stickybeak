import pytest
from stickybeak.injector import Injector, DjangoInjector

from requests import Response
import os

# TODO Try to get rid of it
os.environ['DJANGO_SETTINGS_MODULE'] = 'django_settings'
import django
django.setup()

from stickybeak.django_view import InjectView


@pytest.fixture(params=['http://flask-srv:5000',
                        'http://django-srv:8000',
                        'http://local-mock'])
def injector(request, mocker):
    if request.param == 'http://local-mock':

        def mock_post(endpoint: str, data: str, headers: dict):
            request = lambda x: None
            request.body = data

            django_response = InjectView.post(request)
            response = Response()
            response._content = django_response.content
            response.status_code = django_response.status_code
            return response

        def mock_get(endpoint: str):
            request = lambda x: None
            django_response = InjectView.get(request)

            response = Response()
            response._content = django_response.content
            response.status_code = django_response.status_code
            return response

        post_mock = mocker.patch('requests.post')
        post_mock.side_effect = mock_post

        get_mock = mocker.patch('requests.get')
        get_mock.side_effect = mock_get

        injector = DjangoInjector(address=request.param, django_settings='django_srv.settings')

        return injector

    return DjangoInjector(address=request.param, django_settings='django_srv.settings')


@pytest.fixture(scope="class")
def django_injector(request):
    request.cls.injector = DjangoInjector(address='http://django-srv:8000', django_settings='django_srv.settings')
