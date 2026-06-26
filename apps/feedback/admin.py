from django.contrib import admin

from .models import SuggestionFeedback


@admin.register(SuggestionFeedback)
class SuggestionFeedbackAdmin(admin.ModelAdmin):
    list_display = ["suggestion", "user", "rating", "failure_tag", "created_at"]
    list_filter = ["rating", "failure_tag", "created_at"]
    search_fields = ["comment", "suggestion__ticket__subject", "user__username"]
