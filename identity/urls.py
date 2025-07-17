from django.urls import path, include
from .views import Identify

urlpatterns = [
    path("identity/", Identify.as_view()),
]