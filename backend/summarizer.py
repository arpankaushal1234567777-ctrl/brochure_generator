import os
import time
import signal
from google import genai
from dotenv import load_dotenv
from config import GEMINI_MODEL, GEMINI_TIMEOUT_SEC

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


_PROMPT = """You are extracting structured business information from a web page.

Extract ONLY facts explicitly stated in the text below. Return concise bullet points.
Keep:
- Company name / description
- Products and services (named specifically)
- Industries or sectors served
- Locations / offices
- Contact details (email, phone)

Discard: navigation menus, cookie banners, legal boilerplate, generic marketing phrases.

If a category has no information, omit it entirely.

Text:
{text}"""


def summarize_page(content: str) -> str:
   
    prompt = _PROMPT.format(text=content[:4000])  

    try:
        client = _get_client()

        start = time.time()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={"timeout": GEMINI_TIMEOUT_SEC}
        )
        elapsed = time.time() - start
        print(f"  [Gemini] page summarized in {elapsed:.2f}s")

        result = (response.text or "").strip()
        return result if result else content[:1000]

    except Exception as e:
        print(f"  [Gemini] summarization failed: {e} — using raw text")
        return content[:1000]


def summarize_chunk(chunk: str) -> str:
    return summarize_page(chunk)