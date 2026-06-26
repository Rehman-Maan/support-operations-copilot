from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.copilot.models import CopilotSuggestion
from apps.feedback.models import SuggestionFeedback
from apps.teams.permissions import can_work_tickets
from services.approval_rules.approvals import create_approval_request
from workers.classify_ticket import classify_ticket
from workers.draft_reply import draft_reply
from workers.summarize_thread import summarize_thread

from .forms import AgentMessageForm, SuggestionReplyForm, TicketAssignmentForm, TicketStatusForm
from .models import Ticket, TicketMessage


def _get_accessible_ticket(user, ticket_id: int) -> Ticket:
    ticket = get_object_or_404(
        Ticket.objects.select_related("team", "customer", "assigned_to"),
        id=ticket_id,
    )
    if not ticket.team.has_member(user):
        raise Http404
    return ticket


@login_required
def ticket_detail(request, ticket_id: int):
    ticket = _get_accessible_ticket(request.user, ticket_id)
    assignment_form = TicketAssignmentForm(
        team=ticket.team,
        initial={"assigned_to": ticket.assigned_to_id},
    )
    status_form = TicketStatusForm(initial={"status": ticket.status})
    message_form = AgentMessageForm()
    timeline = ticket.messages.select_related("sender_user", "customer")
    approvals = ticket.approval_requests.select_related("requested_by", "decided_by", "suggestion")
    latest_summary = _latest_suggestion(ticket, CopilotSuggestion.SuggestionType.SUMMARY)
    latest_next_action = _latest_suggestion(ticket, CopilotSuggestion.SuggestionType.NEXT_ACTION)
    latest_macro = _latest_suggestion(ticket, CopilotSuggestion.SuggestionType.MACRO)
    reply_suggestion = (
        ticket.suggestions.filter(
            suggestion_type=CopilotSuggestion.SuggestionType.REPLY_DRAFT,
            status=CopilotSuggestion.Status.PROPOSED,
        )
        .prefetch_related("retrieved_contexts")
        .first()
    )
    suggestion_form = None
    if reply_suggestion:
        suggestion_form = SuggestionReplyForm(initial={"content": reply_suggestion.content})

    return render(
        request,
        "tickets/detail.html",
        {
            "assignment_form": assignment_form,
            "message_form": message_form,
            "status_form": status_form,
            "ticket": ticket,
            "timeline": timeline,
            "reply_suggestion": reply_suggestion,
            "suggestion_form": suggestion_form,
            "approvals": approvals,
            "latest_summary": latest_summary,
            "latest_next_action": latest_next_action,
            "latest_macro": latest_macro,
            "feedback_failure_tags": SuggestionFeedback.FailureTag.choices,
            "feedback_rating_choices": SuggestionFeedback.Rating.choices,
        },
    )


@login_required
def assign_ticket(request, ticket_id: int):
    if request.method != "POST":
        return redirect("tickets:detail", ticket_id=ticket_id)

    ticket = _get_accessible_ticket(request.user, ticket_id)
    if not can_work_tickets(request.user, ticket.team):
        return HttpResponseForbidden("You do not have permission to assign this ticket.")

    form = TicketAssignmentForm(request.POST, team=ticket.team)
    if form.is_valid():
        ticket.assign_to(form.cleaned_data["assigned_to"])
        ticket.save(update_fields=["assigned_to", "status", "closed_at", "updated_at"])
        messages.success(request, "Ticket assignment updated.")

    return redirect("tickets:detail", ticket_id=ticket.id)


@login_required
def update_ticket_status(request, ticket_id: int):
    if request.method != "POST":
        return redirect("tickets:detail", ticket_id=ticket_id)

    ticket = _get_accessible_ticket(request.user, ticket_id)
    if not can_work_tickets(request.user, ticket.team):
        return HttpResponseForbidden("You do not have permission to update this ticket.")

    form = TicketStatusForm(request.POST)
    if form.is_valid():
        ticket.transition_to(form.cleaned_data["status"])
        ticket.save(update_fields=["status", "closed_at", "updated_at"])
        messages.success(request, "Ticket status updated.")

    return redirect("tickets:detail", ticket_id=ticket.id)


@login_required
def queue_classification(request, ticket_id: int):
    if request.method != "POST":
        return redirect("tickets:detail", ticket_id=ticket_id)

    ticket = _get_accessible_ticket(request.user, ticket_id)
    if not can_work_tickets(request.user, ticket.team):
        return HttpResponseForbidden("You do not have permission to classify this ticket.")

    classify_ticket.delay(ticket.id)
    messages.success(request, "Ticket classification queued.")
    return redirect("tickets:detail", ticket_id=ticket.id)


@login_required
def queue_reply_draft(request, ticket_id: int):
    if request.method != "POST":
        return redirect("tickets:detail", ticket_id=ticket_id)

    ticket = _get_accessible_ticket(request.user, ticket_id)
    if not can_work_tickets(request.user, ticket.team):
        return HttpResponseForbidden("You do not have permission to draft a reply.")

    draft_reply.delay(ticket.id)
    messages.success(request, "Reply draft queued.")
    return redirect("tickets:detail", ticket_id=ticket.id)


@login_required
def queue_summary(request, ticket_id: int):
    if request.method != "POST":
        return redirect("tickets:detail", ticket_id=ticket_id)

    ticket = _get_accessible_ticket(request.user, ticket_id)
    if not can_work_tickets(request.user, ticket.team):
        return HttpResponseForbidden("You do not have permission to summarize this ticket.")

    summarize_thread.delay(ticket.id)
    messages.success(request, "Summary generation queued. Refresh in a few seconds.")
    return redirect("tickets:detail", ticket_id=ticket.id)


@login_required
def add_message(request, ticket_id: int):
    if request.method != "POST":
        return redirect("tickets:detail", ticket_id=ticket_id)

    ticket = _get_accessible_ticket(request.user, ticket_id)
    if not can_work_tickets(request.user, ticket.team):
        return HttpResponseForbidden("You do not have permission to reply to this ticket.")

    form = AgentMessageForm(request.POST)
    if form.is_valid():
        TicketMessage.objects.create(
            ticket=ticket,
            sender_type=TicketMessage.SenderType.AGENT,
            sender_user=request.user,
            body=form.cleaned_data["body"],
        )
        ticket.transition_to(Ticket.Status.PENDING_CUSTOMER)
        ticket.save(update_fields=["status", "closed_at", "updated_at"])
        messages.success(request, "Reply added to the timeline.")

    return redirect("tickets:detail", ticket_id=ticket.id)


@login_required
def accept_reply_suggestion(request, ticket_id: int, suggestion_id: int):
    if request.method != "POST":
        return redirect("tickets:detail", ticket_id=ticket_id)

    ticket = _get_accessible_ticket(request.user, ticket_id)
    if not can_work_tickets(request.user, ticket.team):
        return HttpResponseForbidden("You do not have permission to accept this draft.")

    suggestion = _get_reply_suggestion(ticket, suggestion_id)
    form = SuggestionReplyForm(request.POST)
    if form.is_valid():
        content = form.cleaned_data["content"]
        approval = create_approval_request(
            suggestion=suggestion,
            requested_by=request.user,
            edited_content=content,
        )
        if approval:
            messages.success(request, "Approval request created for support lead review.")
            return redirect("tickets:detail", ticket_id=ticket.id)

        TicketMessage.objects.create(
            ticket=ticket,
            sender_type=TicketMessage.SenderType.AGENT,
            sender_user=request.user,
            body=content,
        )
        suggestion.status = (
            CopilotSuggestion.Status.ACCEPTED
            if content == suggestion.content
            else CopilotSuggestion.Status.EDITED
        )
        suggestion.content = content
        suggestion.accepted_by = request.user
        suggestion.accepted_at = timezone.now()
        suggestion.save(
            update_fields=[
                "status",
                "content",
                "accepted_by",
                "accepted_at",
            ]
        )
        ticket.transition_to(Ticket.Status.PENDING_CUSTOMER)
        ticket.save(update_fields=["status", "closed_at", "updated_at"])
        AuditEvent.objects.create(
            team=ticket.team,
            ticket=ticket,
            actor_user=request.user,
            actor_type=AuditEvent.ActorType.USER,
            event_type="reply_draft_accepted",
            payload={
                "suggestion_id": suggestion.id,
                "status": suggestion.status,
                "edited": suggestion.status == CopilotSuggestion.Status.EDITED,
            },
        )
        messages.success(request, "Draft added to the ticket timeline.")

    return redirect("tickets:detail", ticket_id=ticket.id)


@login_required
def reject_reply_suggestion(request, ticket_id: int, suggestion_id: int):
    if request.method != "POST":
        return redirect("tickets:detail", ticket_id=ticket_id)

    ticket = _get_accessible_ticket(request.user, ticket_id)
    if not can_work_tickets(request.user, ticket.team):
        return HttpResponseForbidden("You do not have permission to reject this draft.")

    suggestion = _get_reply_suggestion(ticket, suggestion_id)
    suggestion.status = CopilotSuggestion.Status.REJECTED
    suggestion.rejected_by = request.user
    suggestion.rejected_at = timezone.now()
    suggestion.save(update_fields=["status", "rejected_by", "rejected_at"])
    AuditEvent.objects.create(
        team=ticket.team,
        ticket=ticket,
        actor_user=request.user,
        actor_type=AuditEvent.ActorType.USER,
        event_type="reply_draft_rejected",
        payload={"suggestion_id": suggestion.id},
    )
    messages.success(request, "Draft rejected.")
    return redirect("tickets:detail", ticket_id=ticket.id)


def _get_reply_suggestion(ticket: Ticket, suggestion_id: int) -> CopilotSuggestion:
    return get_object_or_404(
        CopilotSuggestion,
        id=suggestion_id,
        ticket=ticket,
        suggestion_type=CopilotSuggestion.SuggestionType.REPLY_DRAFT,
        status=CopilotSuggestion.Status.PROPOSED,
    )


def _latest_suggestion(ticket: Ticket, suggestion_type: str) -> CopilotSuggestion | None:
    return (
        ticket.suggestions.filter(suggestion_type=suggestion_type)
        .exclude(status=CopilotSuggestion.Status.REJECTED)
        .order_by("-created_at")
        .first()
    )
