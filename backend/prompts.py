
BROCHURE_SYSTEM_PROMPT = """
You are a corporate brochure extraction assistant.

CRITICAL RULES:

1. Use ONLY information explicitly present in the provided content.

2. NEVER invent:
- products 
- services
- industries
- technologies
- locations
- statistics
- company history
- achievements
- awards

3. If information is not present, return:
"Information not available"

4. Do not use generic business language such as:
- innovative solutions
- industry-leading
- cutting-edge
- world-class
- tailored services
- trusted partner

unless those exact phrases appear in the content.

5. Extraction is preferred over summarization.

Return only the requested section.
"""
SECTION_TEMPLATES = {

    "overview": """
Write a professional company overview using ONLY the information below.

Do not invent facts.
If information is missing, state "Information not available".

Content:
{content}
""",

    "mission": """
Extract the company's mission, vision and core values.

Use ONLY the information below.

Content:
{content}
""",

    "leadership": """
Summarize leadership and management information.

Use ONLY the information below.

Content:
{content}
""",

    "products": """
Extract products explicitly mentioned in the content.

Rules:
- Do NOT invent products.
- Do NOT infer products.
- If no products are mentioned, return:
  "Information not available"

Content:
{content}

Return bullet points only.
""",

    "services": """
Extract services explicitly mentioned in the content.

Rules:
- Do NOT invent services.
- Do NOT infer services.
- If no services are mentioned, return:
  "Information not available"

Content:
{content}

Return bullet points only.
""",

    "solutions": """
Describe business solutions explicitly mentioned.

Use ONLY the information below.

Content:
{content}
""",

    "industry": """
Extract industries served.

Rules:
- Do NOT invent industries.
- Do NOT infer industries.
- If industries are not mentioned, return:
  "Information not available"

Content:
{content}

Return bullet points only.
""",

    "technology": """
Summarize technology capabilities and innovations.

Use ONLY the information below.

Content:
{content}
""",

    "differentiators": """
Identify differentiators and competitive advantages.

Use ONLY the information below.

Content:
{content}
""",

    "global_presence": """
Summarize global reach, locations and market presence.

Use ONLY the information below.

Content:
{content}
""",

    "sustainability": """
Summarize sustainability and ESG initiatives.

Use ONLY the information below.

Content:
{content}
""",

    "awards": """
Extract awards and recognitions.

Use ONLY the information below.

Content:
{content}
""",

    "contact": """
Extract contact information.

Use ONLY the information below.

Content:
{content}
"""
}