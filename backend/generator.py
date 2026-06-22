import json
import os
import re
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


def _parse_list_response(content: str) -> list[str]:
    text = content.strip()
    if not text or text == NOT_FOUND_MESSAGE:
        return []

    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL).strip()

    try:
        parsed = json.loads(fenced)
        if isinstance(parsed, list):
            normalized = []
            for item in parsed:
                if isinstance(item, str):
                    normalized.append(item)
                elif isinstance(item, dict):
                    normalized.extend(str(value) for value in item.values() if isinstance(value, str))
            return _normalize_list(normalized)
    except Exception:
        pass

    json_array_match = re.search(r"\[[\s\S]*\]", fenced)
    if json_array_match:
        try:
            parsed = json.loads(json_array_match.group(0))
            if isinstance(parsed, list):
                normalized = []
                for item in parsed:
                    if isinstance(item, str):
                        normalized.append(item)
                    elif isinstance(item, dict):
                        normalized.extend(str(value) for value in item.values() if isinstance(value, str))
                return _normalize_list(normalized)
        except Exception:
            pass

    lines = []
    for raw_line in fenced.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith("here is the json array"):
            continue
        if line in {"```json", "```", "[", "]", "{", "}"}:
            continue
        line = re.sub(r"^[-*•]\s*", "", line)
        line = re.sub(r'^"(?:name|service|industry|product)"\s*:\s*', "", line)
        line = re.sub(r"^(?:name|service|industry|product)\s*:\s*", "", line, flags=re.IGNORECASE)
        if line.startswith('"') and line.endswith('"'):
            line = line[1:-1]
        line = line.strip(" ,")
        if line and line.lower() != NOT_FOUND_MESSAGE.lower():
            lines.append(line)

    if len(lines) == 1 and lines[0].startswith("[") and lines[0].endswith("]"):
        try:
            parsed = json.loads(lines[0])
            if isinstance(parsed, list):
                return _normalize_list([str(item) for item in parsed])
        except Exception:
            return []

    return _normalize_list([line for line in lines if len(line) > 1])


def _clean_overview(text: str) -> str:
    value = " ".join(text.split()).strip()
    lowered = value.lower()
    prefixes = [
        "here is a concise 2-3 sentence overview based on the provided extracted content:",
        "here is a concise 3-sentence overview based on the provided extracted content:",
        "here is a concise overview based on the provided extracted content:",
        "based on the provided extracted content,",
    ]
    for prefix in prefixes:
        if lowered.startswith(prefix):
            value = value[len(prefix):].strip(" :")
            lowered = value.lower()
    return value or NOT_FOUND_MESSAGE


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
                return _clean_overview(content)
            return _parse_list_response(content)
        except Exception as e:
            if "429" in str(e) and attempt == 0:
                print("  [Groq] rate-limited — waiting 5 s then retrying…")
                time.sleep(5)
                continue
            print(f"  [Groq] error on section '{section_name}': {e}")
            return NOT_FOUND_MESSAGE if section_name == "overview" else []

    return NOT_FOUND_MESSAGE if section_name == "overview" else []
