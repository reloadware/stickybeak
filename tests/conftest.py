import pytest
from stickybeak.injector import Injector
from stickybeak.sandbox import execute
import json
from requests import Response


@pytest.fixture
def local_injector(mocker):
    injector = Injector(address='mock_address')
    post_mock = mocker.patch('requests.post')

    def mock_post(endpoint: str, data: str, headers: dict):
        response = Response()
        response._content = execute(json.loads(data)['code'])
        response.status_code = 200
        return response

    post_mock.side_effect = mock_post

    return injector


@pytest.fixture(scope="class")
def django_injector(request):
    request.cls.injector = Injector(address='http://django-srv:8000')
