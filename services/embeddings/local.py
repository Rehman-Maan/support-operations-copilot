import hashlib
import math
import re

from django.conf import settings

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


def embed_text(text: str, dimensions: int | None = None) -> list[float]:
    dimensions = dimensions or settings.KNOWLEDGE_EMBEDDING_DIMENSIONS
    vector = [0.0] * dimensions

    for token in TOKEN_RE.findall(text.lower()):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
