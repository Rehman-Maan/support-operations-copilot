import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.teams.models import Team, TeamMembership
from apps.tickets.models import Customer, Ticket, TicketMessage


@pytest.fixture
def agent(db):
    return get_user_model().objects.create_user(username="agent", password="test-pass")


@pytest.fixture
def ticket(agent):
    team = Team.objects.create(name="Demo Support", slug="demo-support", created_by=agent)
    TeamMembership.objects.create(team=team, user=agent, role=TeamMembership.Role.SUPPORT_AGENT)
    customer = Customer.objects.create(team=team, name="Amina Khan", email="amina@example.com")
    ticket = Ticket.objects.create(team=team, customer=customer, subject="Refund request")
    TicketMessage.objects.create(
        ticket=ticket,
        sender_type=TicketMessage.SenderType.CUSTOMER,
        customer=customer,
        body="I want a refund for my order.",
    )
    return ticket


def test_classify_action_queues_task(client, monkeypatch, agent, ticket):
    queued = []

    class FakeTask:
        @staticmethod
        def delay(ticket_id):
            queued.append(ticket_id)

    monkeypatch.setattr("apps.tickets.views.classify_ticket", FakeTask)
    client.force_login(agent)

    response = client.post(reverse("tickets:classify", args=[ticket.id]))

    assert response.status_code == 302
    assert queued == [ticket.id]
