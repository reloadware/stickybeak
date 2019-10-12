from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = [
    path(r"inject", csrf_exempt(views.InjectView.as_view()), name="inject"),
    path(r"data", csrf_exempt(views.DataView.as_view()), name="data"),
]
