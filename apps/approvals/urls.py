from django.urls import path

from . import views

app_name = "approvals"

urlpatterns = [
    path("", views.approval_queue, name="queue"),
    path("<int:approval_id>/approve/", views.approve_request, name="approve"),
    path("<int:approval_id>/reject/", views.reject_request, name="reject"),
]
