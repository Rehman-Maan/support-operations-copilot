import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.teams.models import Team, TeamMembership
from apps.tickets.models import Customer, Ticket, TicketMessage


@pytest.fixture
def agent(db):
    return get_user_model().objects.create_user(username="agent", password="test-pass")


@pytest.fixture
def lead(db):
    return get_user_model().objects.create_user(username="lead", password="test-pass")


@pytest.fixture
def team(agent, lead):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=agent)
    TeamMembership.objects.create(team=team, user=agent, role=TeamMembership.Role.SUPPORT_AGENT)
    TeamMembership.objects.create(team=team, user=lead, role=TeamMembership.Role.SUPPORT_LEAD)
    return team


@pytest.fixture
def customer(team):
    return Customer.objects.create(team=team, name="Amina Khan", email="amina@example.com")


@pytest.fixture
def ticket(team, customer, agent):
    ticket = Ticket.objects.create(
        team=team,
        customer=customer,
        subject="Package never arrived",
        priority=Ticket.Priority.HIGH,
        assigned_to=agent,
    )
    TicketMessage.objects.create(
        ticket=ticket,
        sender_type=TicketMessage.SenderType.CUSTOMER,
        customer=customer,
        body="Tracking has not moved for a week.",
    )
    return ticket


def test_inbox_requires_login(client):
    response = client.get(reverse("inbox:list"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_my_inbox_shows_assigned_ticket(client, agent, ticket):
    client.force_login(agent)

    response = client.get(reverse("inbox:list"))

    assert response.status_code == 200
    assert b"Package never arrived" in response.content
    assert b"Tracking has not moved" in response.content


def test_ticket_detail_allows_assignment_status_and_reply(client, agent, lead, ticket):
    client.force_login(agent)

    assign_response = client.post(
        reverse("tickets:assign", args=[ticket.id]),
        {"assigned_to": lead.id},
    )
    ticket.refresh_from_db()

    assert assign_response.status_code == 302
    assert ticket.assigned_to == lead

    status_response = client.post(
        reverse("tickets:status", args=[ticket.id]),
        {"status": Ticket.Status.PENDING_INTERNAL},
    )
    ticket.refresh_from_db()

    assert status_response.status_code == 302
    assert ticket.status == Ticket.Status.PENDING_INTERNAL

    message_response = client.post(
        reverse("tickets:add_message", args=[ticket.id]),
        {"body": "Thanks for the details. I am checking this now."},
    )
    ticket.refresh_from_db()

    assert message_response.status_code == 302
    assert ticket.status == Ticket.Status.PENDING_CUSTOMER
    assert ticket.messages.filter(sender_type=TicketMessage.SenderType.AGENT).exists()
