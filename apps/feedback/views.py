from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect

from apps.audit.models import AuditEvent
from apps.copilot.models import CopilotSuggestion
from apps.teams.permissions import can_work_tickets

from .forms import SuggestionFeedbackForm
from .models import SuggestionFeedback


@login_required
def submit_feedback(request, suggestion_id: int):
    suggestion = get_object_or_404(
        CopilotSuggestion.objects.select_related("ticket", "ticket__team"),
        id=suggestion_id,
    )
    ticket = suggestion.ticket
    if not ticket.team.has_member(request.user):
        raise Http404
    if not can_work_tickets(request.user, ticket.team):
        return HttpResponseForbidden("You do not have permission to rate this suggestion.")
    if request.method != "POST":
        return redirect("tickets:detail", ticket_id=ticket.id)

    form = SuggestionFeedbackForm(request.POST)
    if form.is_valid():
        feedback, _ = SuggestionFeedback.objects.update_or_create(
            suggestion=suggestion,
            user=request.user,
            defaults=form.cleaned_data,
        )
        AuditEvent.objects.create(
            team=ticket.team,
            ticket=ticket,
            actor_user=request.user,
            actor_type=AuditEvent.ActorType.USER,
            event_type="suggestion_feedback_submitted",
            payload={
                "suggestion_id": suggestion.id,
                "feedback_id": feedback.id,
                "rating": feedback.rating,
                "failure_tag": feedback.failure_tag,
            },
        )
        messages.success(request, "Suggestion feedback saved.")
    return redirect("tickets:detail", ticket_id=ticket.id)
