
BROCHURE_SYSTEM_PROMPT = """
You are a professional corporate brochure writer.

Use ONLY information explicitly present in the provided content.

Do NOT invent:
- company names
- products
- services
- industries
- statistics
- awards
- achievements

If information is unavailable, omit it.

Write in a professional brochure style.

Do not use placeholders such as:
[Company Name]
[Product Name]
[Service Name]

Return only the final brochure content.
"""
SECTION_TEMPLATES = {
    "overview": """
Write a professional company overview (150-200 words).

Content:
{content}
""",
    "mission":
        "Extract and summarize the company's mission, vision and core values from: {content}",

    "leadership":
        "Summarize leadership and management information from: {content}",

    "products":
        """
        List up to 6 key products.

    Return bullet points only.
        """,

    "services":
        """
        List up to 6 key services.

        Return bullet points only.
        """,

    "solutions":
        "Describe the business solutions offered by the company from: {content}",

    "industry":
        """
        Summarize industries served.

        Maximum 100 words.
        """,

    "technology":
        "Summarize the company's technology capabilities and innovations from: {content}",

    "differentiators":
        "Identify key differentiators and competitive advantages from: {content}",

    "global_presence":
        "Summarize the company's global reach, locations and market presence from: {content}",

    "sustainability":
        "Summarize sustainability, ESG and environmental initiatives from: {content}",

    "awards":
        "Extract awards, recognitions and achievements from: {content}",

    "contact":
        "Generate a professional contact section from: {content}"
}