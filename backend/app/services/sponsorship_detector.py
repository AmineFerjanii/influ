import re
from typing import List, Optional

SPONSORSHIP_TAGS = {
    "#ad", "#sponsored", "#partnership", "#collab", "#collaboration",
    "#publicite", "#partenariat", "#publi", "#brandpartner", "#paidpartnership",
}


def detect_sponsorships(
    posts,
    brand_names: List[str],
    brand_handles: List[str],
) -> List[dict]:
    """
    Scan post captions for sponsorship signals:
    - Standard disclosure hashtags (SPONSORSHIP_TAGS)
    - Brand name substrings (case-insensitive)
    - @brand handle mentions

    Returns list of dicts for posts with at least one match.
    """
    brand_names_lower = [b.lower() for b in brand_names if b]
    brand_handles_lower = [h.lower().lstrip("@") for h in brand_handles if h]

    results = []
    for post in posts:
        caption = post.caption or ""
        if not caption:
            continue

        caption_lower = caption.lower()
        matched_tags: List[str] = []
        matched_brands: List[str] = []

        # 1. Disclosure hashtags
        caption_tags = set(re.findall(r"#\w+", caption_lower))
        for tag in SPONSORSHIP_TAGS:
            if tag in caption_tags:
                matched_tags.append(tag)

        # 2. Brand name substrings
        for name, original in zip(brand_names_lower, brand_names):
            if name and name in caption_lower and original not in matched_brands:
                matched_brands.append(original)

        # 3. @brand handle mentions
        caption_mentions = set(re.findall(r"@(\w+)", caption_lower))
        for handle, original_handle in zip(brand_handles_lower, brand_handles):
            if handle and handle in caption_mentions:
                label = f"@{original_handle}"
                if label not in matched_brands:
                    matched_brands.append(label)

        if not matched_tags and not matched_brands:
            continue

        results.append({
            "post_id": post.post_id,
            "post_url": post.post_url,
            "thumbnail_url": post.local_thumbnail or post.thumbnail_url,
            "matched_tags": matched_tags,
            "matched_brands": matched_brands,
            "caption_snippet": caption[:120] if caption else None,
        })

    return results
