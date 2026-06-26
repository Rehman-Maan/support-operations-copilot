import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.knowledge_base.models import KnowledgeDocument, Macro
from apps.teams.models import Team, TeamMembership


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="owner", password="test-pass")


@pytest.fixture
def team(user):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=user)
    TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.OWNER)
    return team


def test_knowledge_page_requires_login(client):
    response = client.get(reverse("knowledge_base:list"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_owner_can_upload_document(client, monkeypatch, user, team):
    queued = []

    class FakeTask:
        @staticmethod
        def delay(document_id):
            queued.append(document_id)

    monkeypatch.setattr("apps.knowledge_base.views.ingest_knowledge_document", FakeTask)
    client.force_login(user)

    response = client.post(
        reverse("knowledge_base:upload_document"),
        {
            "title": "Refund Policy",
            "document_type": KnowledgeDocument.DocumentType.POLICY,
            "file": SimpleUploadedFile("refund.txt", b"Refunds require approval."),
        },
    )

    document = KnowledgeDocument.objects.get(title="Refund Policy")
    assert response.status_code == 302
    assert document.team == team
    assert queued == [document.id]


def test_owner_can_create_macro(client, user, team):
    client.force_login(user)

    response = client.post(
        reverse("knowledge_base:create_macro"),
        {
            "name": "Refund acknowledgement",
            "intent": "refund_request",
            "body": "I will review the refund policy.",
            "active": "on",
        },
    )

    assert response.status_code == 302
    assert Macro.objects.filter(team=team, name="Refund acknowledgement").exists()
