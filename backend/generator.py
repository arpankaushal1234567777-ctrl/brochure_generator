import json
import os
import time

from dotenv import load_dotenv
from groq import Groq

from config import GROQ_MAX_TOKENS, GROQ_MODEL, GROQ_TEMPERATURE
from prompts import BROCHURE_JSON_TEMPLATE, BROCHURE_SYSTEM_PROMPT, NOT_FOUND_MESSAGE

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


def _normalize_list(items) -> list[str]:
    seen = set()
    cleaned = []
    for item in items or []:
        value = " ".join(str(item).split()).strip(" -")
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(value)
    return cleaned


def _normalize_overview(value) -> str:
    text = " ".join(str(value or "").split()).strip()
    return text or NOT_FOUND_MESSAGE


def generate_brochure_sections(content_data: str) -> dict:
    if not content_data.strip():
        return {
            "overview": NOT_FOUND_MESSAGE,
            "services": [],
            "products": [],
            "industries": [],
        }

    user_prompt = BROCHURE_JSON_TEMPLATE.format(content=content_data)

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
                response_format={"type": "json_object"},
            )
            content = (resp.choices[0].message.content or "").strip()
            parsed = json.loads(content)
            return {
                "overview": _normalize_overview(parsed.get("overview")),
                "services": _normalize_list(parsed.get("services")),
                "products": _normalize_list(parsed.get("products")),
                "industries": _normalize_list(parsed.get("industries")),
            }
        except Exception as e:
            if "429" in str(e) and attempt == 0:
                print("  [Groq] rate-limited — waiting 5 s then retrying…")
                time.sleep(3)
                continue
            print(f"  [Groq] error generating brochure: {e}")
            return {
                "overview": NOT_FOUND_MESSAGE,
                "services": [],
                "products": [],
                "industries": [],
            }

    return {
        "overview": NOT_FOUND_MESSAGE,
        "services": [],
        "products": [],
        "industries": [],
    }
