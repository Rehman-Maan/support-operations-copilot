from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.teams.models import Team
from apps.teams.permissions import can_manage_team
from workers.ingest_knowledge import ingest_knowledge_document

from .forms import KnowledgeDocumentForm, MacroForm
from .models import KnowledgeDocument, Macro


def _first_user_team(user) -> Team | None:
    membership = user.team_memberships.select_related("team").order_by("team__name").first()
    return membership.team if membership else None


@login_required
def knowledge_list(request):
    team = _first_user_team(request.user)
    documents = KnowledgeDocument.objects.none()
    macros = Macro.objects.none()
    if team:
        documents = team.knowledge_documents.select_related("uploaded_by")
        macros = team.macros.select_related("created_by")

    return render(
        request,
        "knowledge_base/list.html",
        {
            "document_form": KnowledgeDocumentForm(),
            "documents": documents,
            "macro_form": MacroForm(),
            "macros": macros,
            "team": team,
        },
    )


@login_required
def upload_document(request):
    team = _first_user_team(request.user)
    if not team:
        messages.error(request, "Create or join a team before uploading knowledge.")
        return redirect("knowledge_base:list")
    if not can_manage_team(request.user, team):
        messages.error(request, "Only team managers can upload knowledge documents.")
        return redirect("knowledge_base:list")

    form = KnowledgeDocumentForm(request.POST, request.FILES)
    if form.is_valid():
        document = form.save(commit=False)
        document.team = team
        document.uploaded_by = request.user
        document.save()
        ingest_knowledge_document.delay(document.id)
        messages.success(request, "Document uploaded and queued for ingestion.")

    return redirect("knowledge_base:list")


@login_required
def retry_document(request, document_id: int):
    document = get_object_or_404(
        KnowledgeDocument,
        id=document_id,
        team__memberships__user=request.user,
    )
    if request.method == "POST" and can_manage_team(request.user, document.team):
        document.status = KnowledgeDocument.Status.UPLOADED
        document.failure_reason = ""
        document.save(update_fields=["status", "failure_reason", "updated_at"])
        ingest_knowledge_document.delay(document.id)
        messages.success(request, "Document ingestion queued again.")

    return redirect("knowledge_base:list")


@login_required
def create_macro(request):
    team = _first_user_team(request.user)
    if not team:
        messages.error(request, "Create or join a team before creating macros.")
        return redirect("knowledge_base:list")
    if not can_manage_team(request.user, team):
        messages.error(request, "Only team managers can create macros.")
        return redirect("knowledge_base:list")

    form = MacroForm(request.POST)
    if form.is_valid():
        macro = form.save(commit=False)
        macro.team = team
        macro.created_by = request.user
        macro.save()
        messages.success(request, "Macro created.")

    return redirect("knowledge_base:list")
