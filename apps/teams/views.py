from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.approvals.models import ApprovalRequest
from apps.tickets.models import Ticket


@login_required
def dashboard(request):
    memberships = request.user.team_memberships.select_related("team").order_by("team__name")
    team_ids = [membership.team_id for membership in memberships]
    tickets = Ticket.objects.filter(team_id__in=team_ids)
    pending_approvals = ApprovalRequest.objects.filter(
        ticket__team_id__in=team_ids,
        status=ApprovalRequest.Status.PENDING,
    )
    metrics = {
        "open_tickets": tickets.exclude(
            status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED],
        ).count(),
        "urgent_tickets": tickets.filter(priority=Ticket.Priority.URGENT).count(),
        "sla_risk": tickets.filter(
            sla_risk_level__in=[Ticket.SlaRiskLevel.MEDIUM, Ticket.SlaRiskLevel.HIGH],
        ).count(),
        "pending_approvals": pending_approvals.count(),
    }
    recent_tickets = tickets.select_related("customer", "assigned_to").order_by("-updated_at")[:6]
    return render(
        request,
        "teams/dashboard.html",
        {
            "memberships": memberships,
            "metrics": metrics,
            "recent_tickets": recent_tickets,
        },
    )
