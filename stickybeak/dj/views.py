import json
from pathlib import Path

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.generic import View

import dill as pickle

from stickybeak.handle_requests import InjectData, get_server_data, inject


class InjectView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        data: InjectData = pickle.loads(request.body)
        return HttpResponse(inject(data), status=200)


class DataView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        project_dir: Path = Path(settings.BASE_DIR)
        data = get_server_data(project_dir)
        response_data = json.dumps(data)
        return HttpResponse(response_data, status=200)
