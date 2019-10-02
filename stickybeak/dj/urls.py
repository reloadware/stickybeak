from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path(r"inject", csrf_exempt(views.InjectView.as_view()), name="inject"),
    path(r"source", csrf_exempt(views.SourceView.as_view()), name="source"),
    path(
        r"requirements",
        csrf_exempt(views.RequirementsView.as_view()),
        name="requirements",
    ),
    path(r"envs", csrf_exempt(views.EnvsView.as_view()), name="envs"),
]
