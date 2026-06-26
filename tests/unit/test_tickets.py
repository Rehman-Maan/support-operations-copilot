import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.teams.models import Team, TeamMembership
from apps.tickets.models import Customer, Ticket, TicketMessage


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username="agent", password="test-pass")


@pytest.fixture
def other_user(db):
    return get_user_model().objects.create_user(username="outsider", password="test-pass")


@pytest.fixture
def team(user):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=user)
    TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.SUPPORT_AGENT)
    return team


@pytest.fixture
def customer(team):
    return Customer.objects.create(
        team=team,
        name="Amina Khan",
        email="amina@example.com",
        tier=Customer.Tier.PREMIUM,
    )


def test_ticket_assignment_opens_new_ticket(user, team, customer):
    ticket = Ticket.objects.create(team=team, customer=customer, subject="Package never arrived")

    ticket.assign_to(user)
    ticket.save()

    ticket.refresh_from_db()
    assert ticket.assigned_to == user
    assert ticket.status == Ticket.Status.OPEN


def test_ticket_rejects_assignment_to_non_member(other_user, team, customer):
    ticket = Ticket.objects.create(team=team, customer=customer, subject="Package never arrived")

    with pytest.raises(ValueError):
        ticket.assign_to(other_user)


def test_resolved_status_sets_closed_at(team, customer):
    ticket = Ticket.objects.create(team=team, customer=customer, subject="Refund request")

    ticket.transition_to(Ticket.Status.RESOLVED)
    ticket.save()

    assert ticket.closed_at is not None
    assert ticket.closed_at <= timezone.now()


def test_latest_message_returns_most_recent_message(team, customer):
    ticket = Ticket.objects.create(team=team, customer=customer, subject="Login help")
    TicketMessage.objects.create(
        ticket=ticket,
        sender_type=TicketMessage.SenderType.CUSTOMER,
        customer=customer,
        body="First message",
    )
    latest = TicketMessage.objects.create(
        ticket=ticket,
        sender_type=TicketMessage.SenderType.CUSTOMER,
        customer=customer,
        body="Latest message",
    )

    assert ticket.latest_message() == latest
