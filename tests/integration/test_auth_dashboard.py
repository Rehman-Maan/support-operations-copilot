import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.teams.models import Team, TeamMembership


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="agent", password="test-pass")


def test_dashboard_requires_login(client):
    response = client.get(reverse("teams:dashboard"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_logged_in_user_can_see_team_dashboard(client, user):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=user)
    TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.SUPPORT_AGENT)

    client.force_login(user)
    response = client.get(reverse("teams:dashboard"))

    assert response.status_code == 200
    assert b"Demo Support" in response.content
    assert b"Support Agent" in response.content
