from apps.knowledge_base.models import KnowledgeDocument
from config.celery import app
from services.retrieval.ingestion import ingest_document


@app.task
def ingest_knowledge_document(document_id: int) -> dict:
    document = KnowledgeDocument.objects.get(id=document_id)
    chunk_count = ingest_document(document)
    return {"document_id": document_id, "status": "ready", "chunks": chunk_count}
