from config import MAX_CHUNK_WORDS


def compress_page(content: str) -> str:
    words = content.split()
    truncated = " ".join(words[:MAX_CHUNK_WORDS])
    return _deduplicate_lines(truncated)


def _deduplicate_lines(text: str) -> str:
    seen = set()
    unique = []
    for raw_line in text.split("\n"):
        line = " ".join(raw_line.split()).strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(line)
    return "\n".join(unique)
