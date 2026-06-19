from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

print("GEMINI_API_KEY Found:", bool(os.getenv("GEMINI_API_KEY")))

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


def summarize_chunk(chunk):

    prompt = f"""
Extract ONLY important business information.

Keep:
- company overview
- products
- services
- industries
- locations
- contact information

Remove:
- navigation text
- legal text
- cookie notices
- repetitive marketing language

Return concise bullet points.

Content:
{chunk}
"""

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        return response.text

    except Exception as e:

        print(f"Summarization failed: {e}")

        return chunk