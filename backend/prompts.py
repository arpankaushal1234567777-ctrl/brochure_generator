NOT_FOUND_MESSAGE = "Information not found on the website."

BROCHURE_SYSTEM_PROMPT = f"""You are a strict website-grounded brochure extraction assistant.

Rules:
1. Use only the provided extracted website content.
2. Do not infer, assume, guess, or invent information.
3. If information is unavailable, return exactly: {NOT_FOUND_MESSAGE}
4. Do not use outside knowledge.
5. Preserve only facts explicitly present in the source snippets.
6. Remove duplicates and ignore navigation, footer, and legal boilerplate.
"""

SECTION_TEMPLATES = {
    "overview": f"""Using only the provided extracted content, write a concise 2-3 sentence overview.
Do not invent any history, scale, awards, offices, products, or services unless explicitly stated.
If the content is insufficient, return exactly:
{NOT_FOUND_MESSAGE}

Extracted content:
{{content}}""",
    "services": f"""Using only the provided extracted content, return only a raw JSON array of strings for services explicitly stated on the website.
Rules:
- Output must start with [ and end with ].
- Do not include markdown fences, labels, commentary, keys, or explanations.
- Each item must be a plain string copied or tightly normalized from the source.
- No inferred umbrella categories.
- If nothing reliable is present, return exactly:
{NOT_FOUND_MESSAGE}

Extracted content:
{{content}}""",
    "products": f"""Using only the provided extracted content, return only a raw JSON array of strings for products explicitly stated on the website.
Rules:
- Output must start with [ and end with ].
- Do not include markdown fences, labels, commentary, keys, or explanations.
- Each item must be a plain string copied or tightly normalized from the source.
- Do not infer product lines from company context.
- If nothing reliable is present, return exactly:
{NOT_FOUND_MESSAGE}

Extracted content:
{{content}}""",
    "industries": f"""Using only the provided extracted content, return only a raw JSON array of strings for industries or sectors explicitly stated on the website.
Rules:
- Output must start with [ and end with ].
- Do not include markdown fences, labels, commentary, keys, or explanations.
- Each item must be a plain string directly supported by the source.
- Do not guess industries from products or services.
- If nothing reliable is present, return exactly:
{NOT_FOUND_MESSAGE}

Extracted content:
{{content}}""",
}
