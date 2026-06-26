import re

SECTION_RE = re.compile(r"^(#{1,6}\s+|[A-Z][A-Z0-9 ,/&-]{4,})")


def chunk_text(text: str, max_words: int = 180, overlap_words: int = 30) -> list[dict]:
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    index = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        content = " ".join(words[start:end]).strip()
        if content:
            chunks.append(
                {
                    "chunk_index": index,
                    "content": content,
                    "section_title": _section_title(content),
                }
            )
            index += 1
        if end == len(words):
            break
        start = max(end - overlap_words, start + 1)

    return chunks


def _section_title(content: str) -> str:
    first_line = content.splitlines()[0].strip()
    if SECTION_RE.match(first_line):
        return first_line.lstrip("# ").strip()[:255]
    return ""
