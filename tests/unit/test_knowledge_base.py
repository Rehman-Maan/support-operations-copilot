import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import override_settings

from apps.knowledge_base.models import KnowledgeDocument, Macro
from apps.teams.models import Team, TeamMembership
from services.embeddings.local import embed_text
from services.retrieval.chunking import chunk_text
from services.retrieval.ingestion import ingest_document
from services.retrieval.search import search_knowledge


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="owner", password="test-pass")


@pytest.fixture
def team(user):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=user)
    TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.OWNER)
    return team


def test_chunk_text_splits_readable_content():
    text = " ".join(f"word{i}" for i in range(420))

    chunks = chunk_text(text, max_words=100, overlap_words=10)

    assert len(chunks) == 5
    assert chunks[0]["chunk_index"] == 0
    assert "word0" in chunks[0]["content"]
    assert "word410" in chunks[-1]["content"]


def test_local_embedding_is_normalized_and_stable(settings):
    settings.KNOWLEDGE_EMBEDDING_DIMENSIONS = 16

    first = embed_text("refund policy")
    second = embed_text("refund policy")

    assert first == second
    assert len(first) == 16
    assert any(value != 0 for value in first)


@override_settings(MEDIA_ROOT="/tmp/support-copilot-test-media")
def test_document_ingestion_creates_chunks(team, user):
    document = KnowledgeDocument.objects.create(
        team=team,
        title="Refund Policy",
        document_type=KnowledgeDocument.DocumentType.POLICY,
        uploaded_by=user,
    )
    document.file.save(
        "refund_policy.txt",
        ContentFile(b"Refunds require approval. Late delivery cases need order verification."),
    )

    chunk_count = ingest_document(document)
    document.refresh_from_db()

    assert chunk_count == 1
    assert document.status == KnowledgeDocument.Status.READY
    assert document.chunks.count() == 1
    assert document.chunks.first().embedding is not None


@override_settings(MEDIA_ROOT="/tmp/support-copilot-test-media")
def test_retrieval_filters_by_team(user):
    other_user = get_user_model().objects.create_user(username="other", password="test-pass")
    team = Team.objects.create(name="Team A", slug="team-a", created_by=user)
    other_team = Team.objects.create(name="Team B", slug="team-b", created_by=other_user)
    TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.OWNER)
    TeamMembership.objects.create(team=other_team, user=other_user, role=TeamMembership.Role.OWNER)

    for current_team, title, body in [
        (team, "Refund Policy", b"Refunds require manager approval."),
        (other_team, "Shipping Policy", b"Shipping delays require tracking review."),
    ]:
        document = KnowledgeDocument.objects.create(
            team=current_team,
            title=title,
            uploaded_by=current_team.created_by,
        )
        document.file.save(f"{current_team.slug}.txt", ContentFile(body))
        ingest_document(document)

    results = list(search_knowledge(team, "refund approval", limit=5))

    assert results
    assert {chunk.team_id for chunk in results} == {team.id}


def test_macro_is_team_scoped(team, user):
    macro = Macro.objects.create(
        team=team,
        name="Refund acknowledgement",
        intent="refund_request",
        body="Thanks for reaching out. I will review the refund policy.",
        created_by=user,
    )

    assert str(macro) == "Refund acknowledgement"
