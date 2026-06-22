NOT_FOUND_MESSAGE = "Information not found on the website."

BROCHURE_SYSTEM_PROMPT = f"""You are a strict website-grounded brochure extraction assistant.

Rules:
1. Use only the provided extracted website content.
2. Do not infer, assume, guess, or invent information.
3. Do not use outside knowledge.
4. If a section is unavailable, use exactly: {NOT_FOUND_MESSAGE}
5. Return only valid JSON with the exact requested schema.
6. Do not include markdown fences, commentary, labels, or explanations.
"""

BROCHURE_JSON_TEMPLATE = f"""Using only the extracted website evidence below, produce one JSON object with exactly this schema:

{{
  "overview": "2-3 grounded sentences or {NOT_FOUND_MESSAGE}",
  "services": ["plain string", "plain string"],
  "products": ["plain string", "plain string"],
  "industries": ["plain string", "plain string"]
}}

Rules:
- Use only facts explicitly present in the evidence.
- `services`, `products`, and `industries` must be arrays of plain strings only.
- No object items, no keys like "name" or "service", no markdown.
- If a list section has no reliable evidence, return an empty array.
- If overview is unsupported, return exactly: {NOT_FOUND_MESSAGE}

Extracted website evidence:
{{content}}"""
