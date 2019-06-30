import json
from pathlib import Path
from typing import Dict

from django import urls
from django.http import HttpResponse, HttpRequest
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from stickybeak.handle_requests import inject, get_source


class InjectView(APIView):
    @staticmethod
    def post(request: HttpRequest) -> HttpResponse:
        data: Dict[str, str] = json.loads(request.body)
        return HttpResponse(inject(data), status=200)

    @staticmethod
    def get(request: HttpRequest) -> HttpResponse:
        project_dir: Path = Path(settings.BASE_DIR)  # type: ignore
        return HttpResponse(json.dumps(get_source(project_dir)), status=200)


stickybeak_url = urls.path(r'stickybeak/', csrf_exempt(InjectView.as_view()), name='stickybeak')
