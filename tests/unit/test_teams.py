import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.teams.models import Team, TeamMembership
from apps.teams.permissions import can_manage_team, can_review_approvals, can_work_tickets


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="agent", password="test-pass")


@pytest.fixture
def lead(db):
    return get_user_model().objects.create_user(username="lead", password="test-pass")


@pytest.fixture
def team(user):
    return Team.objects.create(name="Demo Support", slug="demo-support", created_by=user)


def test_team_membership_roles_support_expected_permissions(user, lead, team):
    owner_membership = TeamMembership.objects.create(
        team=team,
        user=user,
        role=TeamMembership.Role.OWNER,
    )
    lead_membership = TeamMembership.objects.create(
        team=team,
        user=lead,
        role=TeamMembership.Role.SUPPORT_LEAD,
    )

    assert owner_membership.can_manage_team is True
    assert owner_membership.can_review_approvals is True
    assert owner_membership.can_work_tickets is True
    assert lead_membership.can_manage_team is False
    assert lead_membership.can_review_approvals is True
    assert lead_membership.can_work_tickets is True


def test_team_role_helpers_return_user_permissions(user, lead, team):
    TeamMembership.objects.create(team=team, user=lead, role=TeamMembership.Role.SUPPORT_AGENT)

    assert team.user_role(lead) == TeamMembership.Role.SUPPORT_AGENT
    assert team.has_member(lead) is True
    assert can_work_tickets(lead, team) is True
    assert can_review_approvals(lead, team) is False
    assert can_manage_team(lead, team) is False
    assert team.has_member(user) is False


def test_user_can_only_have_one_membership_per_team(user, team):
    TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.VIEWER)

    with pytest.raises(IntegrityError):
        TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.ADMIN)
