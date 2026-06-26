from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.tickets.models import Ticket


@login_required
def inbox(request):
    memberships = request.user.team_memberships.select_related("team")
    team_ids = [membership.team_id for membership in memberships]
    selected_filter = request.GET.get("filter", "my")

    tickets = Ticket.objects.filter(team_id__in=team_ids).select_related(
        "team",
        "customer",
        "assigned_to",
    )

    if selected_filter == "unassigned":
        tickets = tickets.filter(assigned_to__isnull=True)
    elif selected_filter == "urgent":
        tickets = tickets.filter(priority=Ticket.Priority.URGENT)
    elif selected_filter == "pending_approval":
        tickets = tickets.filter(status=Ticket.Status.PENDING_INTERNAL)
    elif selected_filter == "waiting_on_customer":
        tickets = tickets.filter(status=Ticket.Status.PENDING_CUSTOMER)
    elif selected_filter == "high_sla_risk":
        tickets = tickets.filter(sla_risk_level=Ticket.SlaRiskLevel.HIGH)
    else:
        selected_filter = "my"
        tickets = tickets.filter(assigned_to=request.user)

    tickets = list(tickets.order_by("-created_at"))
    for ticket in tickets:
        ticket.latest_inbox_message = ticket.latest_message()

    return render(
        request,
        "inbox/list.html",
        {
            "filter": selected_filter,
            "tickets": tickets,
        },
    )
