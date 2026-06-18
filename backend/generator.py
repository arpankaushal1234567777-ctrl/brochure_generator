import os
from groq import Groq
from dotenv import load_dotenv
from config import MODEL_NAME

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is not set in the environment or .env file.")

client = Groq(api_key=api_key)

def get_ai_response(section_name, content_data):
    from prompts import BROCHURE_SYSTEM_PROMPT, SECTION_TEMPLATES
    template = SECTION_TEMPLATES.get(section_name)
    if not template:
        return f"Error: No template found for section '{section_name}'."

    user_prompt = template.format(content=content_data)
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": BROCHURE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            model=MODEL_NAME,  
            temperature=0.7,                  
            max_tokens=1024
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        if "429" in str(e):
            return "Generation temporarily unavailable due to API rate limits."
        return f"Error generating content: {e}"
