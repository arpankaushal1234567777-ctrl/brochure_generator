from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)

from reportlab.lib.styles import getSampleStyleSheet


def generate_pdf(brochure):

    filename = f"{brochure['company_name'].replace(' ', '_')}.pdf"

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    content = []

    title = Paragraph(
        brochure["company_name"],
        styles["Title"]
    )

    content.append(title)
    content.append(Spacer(1, 20))

    sections = [
        ("Company Overview", brochure.get("overview", "")),
        ("Services", brochure.get("services", "")),
        ("Products", brochure.get("products", "")),
        ("Industry Expertise", brochure.get("industry", ""))
    ]

    for heading, text in sections:

        content.append(
            Paragraph(
                heading,
                styles["Heading1"]
            )
        )

        content.append(
            Paragraph(
                text,
                styles["BodyText"]
            )
        )

        content.append(
            Spacer(1, 15)
        )

    contact = brochure.get("contact", {})

    content.append(
        Paragraph(
            "Contact Information",
            styles["Heading1"]
        )
    )

    content.append(
        Paragraph(
            f"Emails: {', '.join(contact.get('emails', []))}",
            styles["BodyText"]
        )
    )

    content.append(
        Paragraph(
            f"Phones: {', '.join(contact.get('phones', []))}",
            styles["BodyText"]
        )
    )

    doc.build(content)

    return filename