import logging
import re
from collections import Counter
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

_APIFY_RUN_SYNC = (
    "https://api.apify.com/v2/acts/apify~instagram-profile-scraper"
    "/run-sync-get-dataset-items"
)

_TYPENAME_MAP = {
    "Image": "photo",
    "Video": "video",
    "Sidecar": "carousel",
    "GraphImage": "photo",
    "GraphVideo": "video",
    "GraphSidecar": "carousel",
}


async def scrape_profile(username: str, settings=None) -> dict:
    from app.config import settings as app_settings
    cfg = settings or app_settings
    api_key = getattr(cfg, "apify_api_key", "") or ""

    if not api_key:
        raise RuntimeError(
            "APIFY_API_KEY is not set — add it to .env and restart the container"
        )

    logger.info("Scraping @%s via Apify instagram-profile-scraper", username)

    async with httpx.AsyncClient(timeout=180) as client:
        try:
            resp = await client.post(
                _APIFY_RUN_SYNC,
                params={"token": api_key, "timeout": 120, "memory": 512},
                json={"usernames": [username], "resultsLimit": 30},
            )
        except httpx.RequestError as exc:
            raise RuntimeError(f"Network error calling Apify for '{username}': {exc}")

    if resp.status_code == 401:
        raise RuntimeError("Apify API key is invalid or expired")
    if resp.status_code == 402:
        raise RuntimeError("Apify account has insufficient credits")
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Apify returned {resp.status_code} for '{username}': {resp.text[:300]}"
        )

    try:
        items = resp.json()
    except Exception:
        raise RuntimeError(f"Invalid JSON from Apify for '{username}': {resp.text[:200]}")

    if not items:
        raise ValueError(f"Instagram profile '{username}' not found or is private")

    return _parse_item(items[0])


def _parse_item(item: dict) -> dict:
    latest = item.get("latestPosts") or []

    posts_data = []
    for post in latest:
        shortcode = post.get("shortCode") or post.get("id") or ""
        timestamp_raw = post.get("timestamp")
        posted_at = None
        if timestamp_raw:
            try:
                posted_at = datetime.fromisoformat(
                    timestamp_raw.replace("Z", "+00:00")
                )
            except Exception:
                pass

        raw_type = post.get("type") or ""
        media_type = _TYPENAME_MAP.get(raw_type, "photo")
        is_video = media_type == "video"

        posts_data.append({
            "post_id": shortcode,
            "thumbnail_url": post.get("displayUrl") or "",
            "post_url": post.get("url") or (
                f"https://www.instagram.com/p/{shortcode}/" if shortcode else ""
            ),
            "likes": post.get("likesCount") or 0,
            "comments": post.get("commentsCount") or 0,
            "posted_at": posted_at,
            "is_video": is_video,
            "caption": post.get("caption") or "",
            "media_type": media_type,
            "view_count": post.get("videoViewCount") or 0,
        })

    all_text = " ".join(p["caption"] for p in posts_data if p["caption"])
    hashtag_counts = Counter(re.findall(r"#(\w+)", all_text.lower()))
    mention_counts = Counter(re.findall(r"@(\w+)", all_text.lower()))

    return {
        "username": item.get("username") or "",
        "display_name": item.get("fullName") or "",
        "profile_pic_url": item.get("profilePicUrlHD") or item.get("profilePicUrl") or "",
        "bio": item.get("biography") or "",
        "followers": item.get("followersCount") or 0,
        "following": item.get("followsCount") or 0,
        "total_posts": item.get("postsCount") or 0,
        "is_verified": bool(item.get("verified") or item.get("isVerified") or False),
        "posts": posts_data,
        "top_hashtags": [
            {"tag": f"#{t}", "count": c} for t, c in hashtag_counts.most_common(10)
        ],
        "top_mentions": [
            {"mention": f"@{m}", "count": c} for m, c in mention_counts.most_common(10)
        ],
    }
