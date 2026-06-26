from django.conf import settings
from django.db import models
from pgvector.django import VectorField

from apps.teams.models import Team


class KnowledgeDocument(models.Model):
    class DocumentType(models.TextChoices):
        POLICY = "policy", "Policy"
        FAQ = "faq", "FAQ"
        MACRO = "macro", "Macro"
        TROUBLESHOOTING = "troubleshooting", "Troubleshooting"
        PRODUCT_DOCS = "product_docs", "Product Docs"

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="knowledge_documents")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="knowledge_documents/")
    document_type = models.CharField(
        max_length=32,
        choices=DocumentType.choices,
        default=DocumentType.POLICY,
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.UPLOADED)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_knowledge_documents",
    )
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title


class KnowledgeChunk(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="knowledge_chunks")
    document = models.ForeignKey(
        KnowledgeDocument,
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    section_title = models.CharField(max_length=255, blank=True)
    source_metadata = models.JSONField(default=dict, blank=True)
    embedding = VectorField(dimensions=settings.KNOWLEDGE_EMBEDDING_DIMENSIONS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "chunk_index"],
                name="unique_chunk_index_per_document",
            ),
        ]
        ordering = ["document", "chunk_index"]

    def __str__(self) -> str:
        return f"{self.document} chunk {self.chunk_index}"


class Macro(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="macros")
    name = models.CharField(max_length=255)
    intent = models.CharField(max_length=64, blank=True)
    body = models.TextField()
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_macros",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "name"], name="unique_macro_name_per_team"),
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
