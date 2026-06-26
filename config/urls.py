from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("approvals/", include("apps.approvals.urls")),
    path("evaluations/", include("apps.evaluations.urls")),
    path("feedback/", include("apps.feedback.urls")),
    path("health/", include("apps.health.urls")),
    path("inbox/", include("apps.inbox.urls")),
    path("knowledge/", include("apps.knowledge_base.urls")),
    path("tickets/", include("apps.tickets.urls")),
    path("", include("apps.teams.urls")),
]
