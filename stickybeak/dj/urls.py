from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from .views import EnvsView, InjectView, SourceView

urlpatterns = [
    path(r"inject", csrf_exempt(InjectView.as_view()), name="inject"),
    path(r"source", csrf_exempt(SourceView.as_view()), name="source"),
    path(r"envs", csrf_exempt(EnvsView.as_view()), name="envs"),
]
