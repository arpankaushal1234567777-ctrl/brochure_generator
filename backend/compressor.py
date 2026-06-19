from content_extractor import chunk_text
from summarizer import summarize_chunk


def compress_page(content):

    chunks = chunk_text(content)

    summaries = []

    for chunk in chunks:

        summary = summarize_chunk(chunk)

        if summary:
            summaries.append(summary)

    merged = "\n".join(summaries)

    return deduplicate_summary(merged)

def deduplicate_summary(text):

    lines = text.split("\n")

    unique = []

    seen = set()

    for line in lines:

        line = line.strip()

        if not line:
            continue

        lower = line.lower()

        if lower in seen:
            continue

        seen.add(lower)

        unique.append(line)

    return "\n".join(unique)