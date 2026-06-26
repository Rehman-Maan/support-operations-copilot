from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("<int:ticket_id>/", views.ticket_detail, name="detail"),
    path("<int:ticket_id>/assign/", views.assign_ticket, name="assign"),
    path("<int:ticket_id>/classify/", views.queue_classification, name="classify"),
    path("<int:ticket_id>/draft-reply/", views.queue_reply_draft, name="draft_reply"),
    path("<int:ticket_id>/summarize/", views.queue_summary, name="summarize"),
    path("<int:ticket_id>/status/", views.update_ticket_status, name="status"),
    path("<int:ticket_id>/messages/", views.add_message, name="add_message"),
    path(
        "<int:ticket_id>/suggestions/<int:suggestion_id>/accept/",
        views.accept_reply_suggestion,
        name="accept_suggestion",
    ),
    path(
        "<int:ticket_id>/suggestions/<int:suggestion_id>/reject/",
        views.reject_reply_suggestion,
        name="reject_suggestion",
    ),
]
