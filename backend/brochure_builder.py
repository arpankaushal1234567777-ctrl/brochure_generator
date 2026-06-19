from generator import get_ai_response
from config import COMBINE_TOP_PAGES


def combine_pages(pages):

    return "\n\n".join(
        page["compressed_content"]
        for page in pages[:COMBINE_TOP_PAGES]
    )


def build_brochure(profile):

    brochure = {
        "company_name": profile["company_name"]
    }

    sections = {
        "overview": profile["overview_pages"],
        "services": profile["service_pages"],
        "products": profile["product_pages"],
        "industry": profile["industry_pages"]
    }

    for section_name, pages in sections.items():

        if not pages:
            brochure[section_name] = ""
            continue

        combined_content = combine_pages(pages)

        brochure[section_name] = get_ai_response(
            section_name,
            combined_content
        )

    brochure["contact"] = {
        "emails": profile["emails"],
        "phones": profile["phones"]
    }

    return brochure