from django.contrib import admin

from .models import CopilotSuggestion, RetrievedContext


class RetrievedContextInline(admin.TabularInline):
    model = RetrievedContext
    extra = 0
    readonly_fields = ["knowledge_chunk", "relevance_score", "source_title", "content_snapshot"]


@admin.register(CopilotSuggestion)
class CopilotSuggestionAdmin(admin.ModelAdmin):
    list_display = [
        "ticket",
        "suggestion_type",
        "status",
        "needs_approval",
        "model_name",
        "created_at",
    ]
    list_filter = ["suggestion_type", "status", "needs_approval", "created_at"]
    search_fields = ["ticket__subject", "content", "internal_notes"]
    inlines = [RetrievedContextInline]


@admin.register(RetrievedContext)
class RetrievedContextAdmin(admin.ModelAdmin):
    list_display = ["suggestion", "source_title", "relevance_score", "created_at"]
    search_fields = ["source_title", "content_snapshot"]
