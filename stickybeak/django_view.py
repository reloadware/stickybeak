import glob
import json
from pathlib import Path
from typing import Dict

from django.http import HttpResponse, HttpRequest
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django import urls
from stickybeak import sandbox
from django.conf import settings


class InjectView(APIView):
    @staticmethod
    def post(request: HttpRequest) -> HttpResponse:
        data: Dict[str, str] = json.loads(request.body)

        code: str = data['code']

        result: bytes = sandbox.execute(code)
        response = HttpResponse(result, status=200)

        return response

    @staticmethod
    def get(request: HttpRequest) -> HttpResponse:
        project_dir: Path = Path(settings.BASE_DIR)  # type: ignore

        source_code: Dict[str, str] = {}

        for p in glob.iglob(str(project_dir) + '/**/*.py', recursive=True):
            path: Path = Path(p)
            rel_path: str = str(path.relative_to(project_dir))
            source_code[rel_path] = path.read_text()

        return HttpResponse(json.dumps(source_code), status=200)


stickybeak_url = urls.path(r'stickybeak/', csrf_exempt(InjectView.as_view()), name='stickybeak')
