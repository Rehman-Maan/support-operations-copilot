from pgvector.django import CosineDistance

from apps.knowledge_base.models import KnowledgeChunk
from apps.teams.models import Team
from services.embeddings.local import embed_text


def search_knowledge(team: Team, query: str, limit: int = 5):
    query_embedding = embed_text(query)
    return (
        KnowledgeChunk.objects.filter(team=team)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .select_related("document")
        .order_by("distance")[:limit]
    )
