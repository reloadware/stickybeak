import json
from pathlib import Path
from typing import Dict

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from rest_framework.views import APIView

from stickybeak.handle_requests import get_data, inject


class InjectView(APIView):
    @staticmethod
    def post(request: HttpRequest) -> HttpResponse:
        data: Dict[str, str] = json.loads(request.body)
        return HttpResponse(inject(data), status=200)


class DataView(APIView):
    @staticmethod
    def get(request: HttpRequest) -> HttpResponse:
        project_dir: Path = Path(settings.BASE_DIR)
        return HttpResponse(json.dumps(get_data(project_dir)), status=200)
