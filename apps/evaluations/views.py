from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from apps.teams.permissions import can_work_tickets
from workers.run_eval import run_evaluation

from .models import EvaluationRun


@login_required
def evaluation_dashboard(request):
    team_ids = list(request.user.team_memberships.values_list("team_id", flat=True))
    runs = EvaluationRun.objects.filter(team_id__in=team_ids).select_related("team")
    latest_run = runs.first()
    return render(
        request,
        "evaluations/dashboard.html",
        {
            "latest_run": latest_run,
            "runs": runs[:10],
        },
    )


@login_required
def queue_evaluation(request):
    if request.method != "POST":
        return redirect("evaluations:dashboard")

    membership = request.user.team_memberships.select_related("team").first()
    if not membership:
        return HttpResponseForbidden("You need a team membership to run evaluations.")
    if not can_work_tickets(request.user, membership.team):
        return HttpResponseForbidden("You do not have permission to run evaluations.")

    run_evaluation.delay("support_cases.yml", membership.team_id)
    messages.success(request, "Evaluation run queued. Refresh in a few seconds.")
    return redirect("evaluations:dashboard")
