from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from stickybeak.handle_requests import INJECT_ENDPOINT, SERVER_DATA_ENDPOINT

from . import views

urlpatterns = [
    path(INJECT_ENDPOINT, csrf_exempt(views.InjectView.as_view()), name="inject"),
    path(SERVER_DATA_ENDPOINT, csrf_exempt(views.DataView.as_view()), name="data"),
]
