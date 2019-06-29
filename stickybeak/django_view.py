import glob
import json
from pathlib import Path

from django.http import HttpResponse, HttpRequest
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from django.urls import path
from stickybeak import sandbox
from django.conf import settings


class InjectView(APIView):
    @staticmethod
    def post(request: HttpRequest):
        data = json.loads(request.body)

        code = data['code']

        result = sandbox.execute(code)
        response = HttpResponse(result, status=200)

        return response

    @staticmethod
    def get(request):
        project_dir: Path = Path(settings.BASE_DIR)

        source_code = {}

        for p in glob.iglob(str(project_dir) + '/**/*.py', recursive=True):
            p = Path(p)
            rel_path: str = str(p.relative_to(project_dir))
            source_code[rel_path] = p.read_text()

        return HttpResponse(json.dumps(source_code), status=200)


stickybeak_url = path(r'stickybeak/', csrf_exempt(InjectView.as_view()), name='stickybeak')
