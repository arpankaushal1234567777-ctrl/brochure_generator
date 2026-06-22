import json
import os
import time
from groq import Groq
from dotenv import load_dotenv
from config import GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MAX_TOKENS
from prompts import BROCHURE_SYSTEM_PROMPT, SECTION_TEMPLATES, NOT_FOUND_MESSAGE

load_dotenv()

_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set.")
        _client = Groq(api_key=api_key)
    return _client


def _normalize_list(items: list[str]) -> list[str]:
    seen = set()
    cleaned = []
    for item in items:
        value = " ".join(str(item).split()).strip(" -")
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(value)
    return cleaned


def get_ai_response(section_name: str, content_data: str):
    template = SECTION_TEMPLATES.get(section_name)
    if not template or not content_data.strip():
        return NOT_FOUND_MESSAGE if section_name == "overview" else []

    user_prompt = template.format(content=content_data)

    for attempt in range(2):
        try:
            resp = _get_client().chat.completions.create(
                messages=[
                    {"role": "system", "content": BROCHURE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                model=GROQ_MODEL,
                temperature=GROQ_TEMPERATURE,
                max_tokens=GROQ_MAX_TOKENS,
            )
            content = (resp.choices[0].message.content or "").strip()
            if section_name == "overview":
                return content or NOT_FOUND_MESSAGE

            if content == NOT_FOUND_MESSAGE:
                return []

            parsed = json.loads(content)
            if isinstance(parsed, list):
                return _normalize_list([str(item) for item in parsed])
            return []
        except Exception as e:
            if "429" in str(e) and attempt == 0:
                print("  [Groq] rate-limited — waiting 5 s then retrying…")
                time.sleep(5)
                continue
            print(f"  [Groq] error on section '{section_name}': {e}")
            return NOT_FOUND_MESSAGE if section_name == "overview" else []

    return NOT_FOUND_MESSAGE if section_name == "overview" else []
