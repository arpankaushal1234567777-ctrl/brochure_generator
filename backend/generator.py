import json
import os
import re
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
        if not value or value == NOT_FOUND_MESSAGE:
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


def _repair_json(raw: str) -> str:
    """Attempt to repair truncated JSON by closing open structures."""
    # Strip any markdown fences
    raw = re.sub(r"^```[a-z]*\n?", "", raw.strip())
    raw = re.sub(r"\n?```$", "", raw.strip())
    raw = raw.strip()

    # If it already parses, great
    try:
        json.loads(raw)
        return raw
    except json.JSONDecodeError:
        pass

    # Try to close truncated JSON by counting open braces/brackets
    open_braces = raw.count("{") - raw.count("}")
    open_brackets = raw.count("[") - raw.count("]")

    # Remove trailing comma if present before closing
    repaired = raw.rstrip().rstrip(",")
    repaired += "]" * open_brackets
    repaired += "}" * open_braces

    try:
        json.loads(repaired)
        return repaired
    except json.JSONDecodeError:
        return raw


def generate_brochure_sections(content_data: str) -> dict:
    empty = {
        "overview": NOT_FOUND_MESSAGE,
        "services": [],
        "products": [],
        "industries": [],
    }

    if not content_data.strip():
        return empty

    user_prompt = BROCHURE_JSON_TEMPLATE.format(content=content_data)

    for attempt in range(3):
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
            raw = (resp.choices[0].message.content or "").strip()
            print(f"  [Groq] raw response length: {len(raw)} chars")

            repaired = _repair_json(raw)
            parsed = json.loads(repaired)

            result = {
                "overview": _normalize_overview(parsed.get("overview")),
                "services": _normalize_list(parsed.get("services")),
                "products": _normalize_list(parsed.get("products")),
                "industries": _normalize_list(parsed.get("industries")),
            }
            print(f"  [Groq] extracted — overview: {len(result['overview'])} chars, "
                  f"services: {len(result['services'])}, products: {len(result['products'])}, "
                  f"industries: {len(result['industries'])}")
            return result

        except json.JSONDecodeError as e:
            print(f"  [Groq] JSON parse error on attempt {attempt + 1}: {e}")
            if attempt < 2:
                time.sleep(1)
                continue
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"  [Groq] rate-limited — waiting 5s then retrying…")
                time.sleep(5)
                continue
            print(f"  [Groq] error on attempt {attempt + 1}: {e}")
            if attempt < 2:
                time.sleep(1)
                continue

    print("  [Groq] all attempts failed, returning empty result")
    return empty