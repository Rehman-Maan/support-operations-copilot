from django.urls import path

from . import views

app_name = "feedback"

urlpatterns = [
    path("suggestions/<int:suggestion_id>/", views.submit_feedback, name="submit"),
]
