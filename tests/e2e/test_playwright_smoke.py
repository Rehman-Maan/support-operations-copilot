import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

from apps.teams.models import Team, TeamMembership  # noqa: E402
from apps.tickets.models import Customer, Ticket, TicketMessage  # noqa: E402


@pytest.mark.django_db
def test_agent_can_login_and_open_core_workspaces(live_server):
    user = get_user_model().objects.create_user(username="agent", password="test-pass")
    team = Team.objects.create(name="ShopWise Support", slug="shopwise-support", created_by=user)
    TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.SUPPORT_AGENT)
    customer = Customer.objects.create(
        team=team,
        name="Amina Khan",
        email="amina@example.com",
        tier=Customer.Tier.PREMIUM,
    )
    ticket = Ticket.objects.create(
        team=team,
        customer=customer,
        subject="Order SW-1042 arrived damaged",
        priority=Ticket.Priority.HIGH,
        assigned_to=user,
    )
    TicketMessage.objects.create(
        ticket=ticket,
        sender_type=TicketMessage.SenderType.CUSTOMER,
        customer=customer,
        body="The blender arrived cracked and I need help with a replacement.",
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{live_server.url}{reverse('accounts:login')}")
        page.locator("#id_username").fill("agent")
        page.locator("#id_password").fill("test-pass")
        page.locator("button[type='submit']").click()

        page.wait_for_url(f"{live_server.url}{reverse('teams:dashboard')}")
        assert "ShopWise Support" in page.content()

        page.goto(f"{live_server.url}{reverse('inbox:list')}")
        assert "Order SW-1042 arrived damaged" in page.content()

        page.goto(f"{live_server.url}{reverse('tickets:detail', args=[ticket.id])}")
        assert "Copilot" in page.content()
        assert "Draft reply" in page.content()
        assert "amina@example.com" in page.content()
        browser.close()
