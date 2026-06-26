from pathlib import Path

from django.db import transaction

from apps.knowledge_base.models import KnowledgeChunk, KnowledgeDocument
from services.embeddings.local import embed_text

from .chunking import chunk_text


def ingest_document(document: KnowledgeDocument) -> int:
    document.status = KnowledgeDocument.Status.PROCESSING
    document.failure_reason = ""
    document.save(update_fields=["status", "failure_reason", "updated_at"])

    try:
        text = extract_text(document.file.path)
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("Document did not contain any readable text.")

        with transaction.atomic():
            document.chunks.all().delete()
            for chunk in chunks:
                KnowledgeChunk.objects.create(
                    team=document.team,
                    document=document,
                    chunk_index=chunk["chunk_index"],
                    content=chunk["content"],
                    section_title=chunk["section_title"],
                    source_metadata={
                        "filename": Path(document.file.name).name,
                        "document_type": document.document_type,
                    },
                    embedding=embed_text(chunk["content"]),
                )

        document.status = KnowledgeDocument.Status.READY
        document.save(update_fields=["status", "updated_at"])
        return len(chunks)
    except Exception as exc:
        document.status = KnowledgeDocument.Status.FAILED
        document.failure_reason = str(exc)
        document.save(update_fields=["status", "failure_reason", "updated_at"])
        raise


def extract_text(path: str) -> str:
    raw = Path(path).read_bytes()
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")
