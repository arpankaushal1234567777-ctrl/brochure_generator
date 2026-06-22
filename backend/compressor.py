from summarizer import summarize_page
from config import MAX_CHUNK_WORDS


def compress_page(content: str) -> str:
    words = content.split()
    truncated = " ".join(words[:MAX_CHUNK_WORDS])

    summary = summarize_page(truncated)
    return _deduplicate(summary)


def _deduplicate(text: str) -> str:
    seen = set()
    unique = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        key = line.lower()
        if key not in seen:
            seen.add(key)
            unique.append(line)
    return "\n".join(unique)