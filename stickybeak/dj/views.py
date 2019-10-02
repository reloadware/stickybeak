import json
from pathlib import Path
from typing import Dict

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from rest_framework.views import APIView

from stickybeak.handle_requests import (
    get_envs, get_requirements, get_source, inject,
)


class InjectView(APIView):
    @staticmethod
    def post(request: HttpRequest) -> HttpResponse:
        data: Dict[str, str] = json.loads(request.body)
        return HttpResponse(inject(data), status=200)


class SourceView(APIView):
    @staticmethod
    def get(request: HttpRequest) -> HttpResponse:
        project_dir: Path = Path(settings.BASE_DIR)  # type: ignore
        return HttpResponse(json.dumps(get_source(project_dir)), status=200)


class RequirementsView(APIView):
    @staticmethod
    def get(request: HttpRequest) -> HttpResponse:
        return HttpResponse(json.dumps(get_requirements()), status=200)


class EnvsView(APIView):
    @staticmethod
    def get(request: HttpRequest) -> HttpResponse:
        return HttpResponse(json.dumps(get_envs()), status=200)
