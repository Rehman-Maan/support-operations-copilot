from django.urls import path

from .views import health_check

app_name = "health"

urlpatterns = [
    path("", health_check, name="check"),
]
