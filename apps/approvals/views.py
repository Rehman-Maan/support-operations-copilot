from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.teams.permissions import can_review_approvals
from services.approval_rules.approvals import decide_approval

from .forms import ApprovalDecisionForm
from .models import ApprovalRequest


@login_required
def approval_queue(request):
    approvals = (
        ApprovalRequest.objects.filter(ticket__team__memberships__user=request.user)
        .select_related("ticket", "ticket__team", "requested_by", "decided_by")
        .distinct()
    )
    visible_approvals = [
        approval
        for approval in approvals
        if can_review_approvals(request.user, approval.ticket.team)
    ]
    return render(
        request,
        "approvals/queue.html",
        {
            "approvals": visible_approvals,
            "pending_count": sum(
                approval.status == ApprovalRequest.Status.PENDING
                for approval in visible_approvals
            ),
        },
    )


@login_required
def approve_request(request, approval_id: int):
    return _decide(request, approval_id, ApprovalRequest.Status.APPROVED)


@login_required
def reject_request(request, approval_id: int):
    return _decide(request, approval_id, ApprovalRequest.Status.REJECTED)


def _decide(request, approval_id: int, status: str):
    if request.method != "POST":
        return redirect("approvals:queue")

    approval = _get_accessible_approval(request.user, approval_id)
    form = ApprovalDecisionForm(request.POST)
    if form.is_valid():
        decide_approval(
            approval=approval,
            reviewer=request.user,
            status=status,
            decision_note=form.cleaned_data["decision_note"],
        )
        label = "approved" if status == ApprovalRequest.Status.APPROVED else "rejected"
        messages.success(request, f"Approval request {label}.")
    return redirect("approvals:queue")


def _get_accessible_approval(user, approval_id: int) -> ApprovalRequest:
    approval = get_object_or_404(
        ApprovalRequest.objects.select_related("ticket", "ticket__team"),
        id=approval_id,
    )
    if not approval.ticket.team.has_member(user):
        raise Http404
    if not can_review_approvals(user, approval.ticket.team):
        raise PermissionDenied("You do not have permission to review approvals.")
    return approval
