from django.contrib import admin

from .models import KnowledgeChunk, KnowledgeDocument, Macro


class KnowledgeChunkInline(admin.TabularInline):
    model = KnowledgeChunk
    extra = 0
    fields = ("chunk_index", "section_title", "content", "created_at")
    readonly_fields = ("created_at",)


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "team", "document_type", "status", "uploaded_by", "created_at")
    list_filter = ("document_type", "status", "team", "created_at")
    search_fields = ("title", "team__name", "uploaded_by__username")
    inlines = [KnowledgeChunkInline]


@admin.register(KnowledgeChunk)
class KnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "team", "chunk_index", "section_title", "created_at")
    list_filter = ("team", "document__document_type", "created_at")
    search_fields = ("document__title", "content", "section_title")


@admin.register(Macro)
class MacroAdmin(admin.ModelAdmin):
    list_display = ("name", "team", "intent", "active", "created_by", "updated_at")
    list_filter = ("active", "team", "created_at")
    search_fields = ("name", "intent", "body", "team__name")
