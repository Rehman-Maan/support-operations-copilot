from django.urls import path

from . import views

app_name = "evaluations"

urlpatterns = [
    path("", views.evaluation_dashboard, name="dashboard"),
    path("run/", views.queue_evaluation, name="run"),
]
