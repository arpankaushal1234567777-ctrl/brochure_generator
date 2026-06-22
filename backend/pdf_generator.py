from xml.sax.saxutils import escape

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from io import BytesIO
from reportlab.lib.styles import getSampleStyleSheet


def _para(text: str, style) -> Paragraph:
    return Paragraph(escape(text or ""), style)


def generate_pdf(brochure):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    content = []

    content.append(_para(brochure["company_name"], styles["Title"]))
    content.append(Spacer(1, 20))

    sections = [
        ("Company Overview", brochure.get("overview", "")),
        ("Products & Services", brochure.get("offerings", "")),
        ("Industry Expertise", brochure.get("industry", "")),
    ]

    for heading, text in sections:
        content.append(_para(heading, styles["Heading1"]))
        content.append(_para(text, styles["BodyText"]))
        content.append(Spacer(1, 15))

    contact = brochure.get("contact", {})
    content.append(_para("Contact Information", styles["Heading1"]))
    content.append(_para(
        f"Emails: {', '.join(contact.get('emails', []))}",
        styles["BodyText"],
    ))
    content.append(_para(
        f"Phones: {', '.join(contact.get('phones', []))}",
        styles["BodyText"],
    ))

    doc.build(content)
    buffer.seek(0)
    return buffer.getvalue()
