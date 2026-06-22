from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from prompts import NOT_FOUND_MESSAGE

TEMPLATE_STYLES = {
    "corporate": {"accent": colors.HexColor("#2451ff"), "title_size": 22, "section_gap": 12},
    "modern": {"accent": colors.HexColor("#0f766e"), "title_size": 24, "section_gap": 14},
    "minimal": {"accent": colors.HexColor("#111827"), "title_size": 20, "section_gap": 10},
    "executive": {"accent": colors.HexColor("#7c2d12"), "title_size": 24, "section_gap": 16},
}


def _styles(template_key: str):
    cfg = TEMPLATE_STYLES.get(template_key, TEMPLATE_STYLES["corporate"])
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "BrochureTitle",
            parent=styles["Title"],
            fontSize=cfg["title_size"],
            textColor=cfg["accent"],
            spaceAfter=18,
            alignment=TA_LEFT,
        ),
        "meta": ParagraphStyle(
            "BrochureMeta",
            parent=styles["BodyText"],
            fontSize=9,
            textColor=colors.HexColor("#6b7280"),
            spaceAfter=8,
        ),
        "heading": ParagraphStyle(
            "BrochureHeading",
            parent=styles["Heading2"],
            fontSize=12,
            textColor=cfg["accent"],
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BrochureBody",
            parent=styles["BodyText"],
            fontSize=10,
            leading=15,
            spaceAfter=cfg["section_gap"],
        ),
    }


def _paragraph_text(value):
    if isinstance(value, list):
        if not value:
            return NOT_FOUND_MESSAGE
        return "<br/>".join(f"• {item}" for item in value)
    return value or NOT_FOUND_MESSAGE


def generate_pdf(brochure):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
    )

    styles = _styles(brochure.get("template_used", "corporate"))
    content = [
        Paragraph(brochure["company_name"], styles["title"]),
        Paragraph(f"Template: {brochure.get('template_used', 'corporate').title()}", styles["meta"]),
        Paragraph(f"Generated at: {brochure.get('generated_at', '')}", styles["meta"]),
        Spacer(1, 8),
    ]

    sections = [
        ("Company Overview", brochure.get("overview", NOT_FOUND_MESSAGE)),
        ("Services", brochure.get("services", [])),
        ("Products", brochure.get("products", [])),
        ("Industries", brochure.get("industries", [])),
        (
            "Contact Information",
            [
                f"Emails: {', '.join(brochure.get('contact', {}).get('emails', [NOT_FOUND_MESSAGE]))}",
                f"Phones: {', '.join(brochure.get('contact', {}).get('phones', [NOT_FOUND_MESSAGE]))}",
            ],
        ),
    ]

    for heading, text in sections:
        content.append(Paragraph(heading, styles["heading"]))
        content.append(Paragraph(_paragraph_text(text), styles["body"]))

    doc.build(content)
    buffer.seek(0)
    return buffer.getvalue()
