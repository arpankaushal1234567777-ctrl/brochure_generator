import os
import time
from google import genai
from dotenv import load_dotenv
from config import GEMINI_MODEL, GEMINI_TIMEOUT_SEC
from prompts import NOT_FOUND_MESSAGE

load_dotenv()

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set.")
        _client = genai.Client(api_key=api_key)
    return _client


_PROMPT = f"""You are cleaning extracted website text for downstream brochure generation.

Use only the text provided. Do not add outside knowledge.
Return concise factual bullet points only when they are explicitly present.
Preserve exact named entities whenever possible, especially:
- company descriptions
- products and product families
- services and offerings
- industries, sectors, and markets
- contact details

If the source contains useful bullet lists, offerings, product names, or markets, keep them as distinct bullets.
Remove:
- navigation labels
- repeated footer text
- cookie and legal banners
- duplicate lines
- generic boilerplate without business facts

If the source has no useful factual business information, return exactly:
{NOT_FOUND_MESSAGE}

Text:
{{text}}"""


def summarize_page(content: str) -> str:
    prompt = _PROMPT.format(text=content[:4000])

    try:
        client = _get_client()
        start = time.time()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={"timeout": GEMINI_TIMEOUT_SEC},
        )
        elapsed = time.time() - start
        print(f"  [Gemini] page summarized in {elapsed:.2f}s")

        result = (response.text or "").strip()
        return result if result else NOT_FOUND_MESSAGE
    except Exception as e:
        print(f"  [Gemini] summarization failed: {e} — using cleaned raw text")
        return content[:1000].strip() or NOT_FOUND_MESSAGE


def summarize_chunk(chunk: str) -> str:
    return summarize_page(chunk)
