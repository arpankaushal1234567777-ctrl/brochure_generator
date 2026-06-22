from config import SIMILARITY_THRESHOLD

def jaccard_similarity(text1, text2):

    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0

    return len(words1 & words2) / len(words1 | words2)


def remove_similar_pages(page_data):

    unique_pages = []

    for url, data in page_data.items():

        if not data:
            continue

        is_duplicate = False

        current_text = data["content"][:3000]

        for existing in unique_pages:

            existing_text = existing["content"][:3000]

            similarity = jaccard_similarity(
                current_text,
                existing_text
            )

            if similarity > SIMILARITY_THRESHOLD:
                is_duplicate = True
                break

        if not is_duplicate:
            unique_pages.append(data)

    return unique_pages