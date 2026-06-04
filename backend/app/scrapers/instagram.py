import logging
import re
from collections import Counter
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_SCRAPER_API_KEY = "54992c77618597a7b2b9cf1863d48555"

_TYPENAME_MAP = {
    "GraphImage": "photo",
    "GraphVideo": "video",
    "GraphSidecar": "carousel",
}


async def scrape_profile(username: str, settings=None) -> dict:
    """Scrape an Instagram profile via ScraperAPI structured endpoint."""

    api_key = _SCRAPER_API_KEY
    if settings:
        api_key = getattr(settings, 'scraper_api_key', None) or _SCRAPER_API_KEY

    scraper_url = (
        f"https://api.scraperapi.com/structured/instagram/profile"
        f"?api_key={api_key}"
        f"&username={username}"
    )

    logger.info("Scraping @%s via ScraperAPI structured endpoint", username)

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        try:
            resp = await client.get(scraper_url)
        except httpx.RequestError as e:
            raise RuntimeError(f"Network error fetching Instagram profile '{username}': {e}")

    logger.info("ScraperAPI response status for @%s: %d", username, resp.status_code)

    if resp.status_code == 404:
        raise ValueError(f"Instagram profile '{username}' does not exist")
    if resp.status_code == 401:
        raise RuntimeError(f"Invalid ScraperAPI key or unauthorized.")
    if resp.status_code == 403:
        raise RuntimeError(f"ScraperAPI 403 for '{username}'. Endpoint may not be available on your plan.")
    if resp.status_code == 429:
        raise RuntimeError(f"ScraperAPI quota exhausted for '{username}'.")
    if resp.status_code != 200:
        raise RuntimeError(f"ScraperAPI returned {resp.status_code} for '{username}'")

    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Invalid JSON response for '{username}': {resp.text[:200]}")

    logger.info("ScraperAPI raw keys for @%s: %s", username, list(data.keys()))

    return _parse_structured(data, username)


def _parse_structured(data: dict, username: str) -> dict:
    """Parse ScraperAPI structured Instagram profile response."""

    # ScraperAPI structured endpoint returns flat profile fields
    followers = data.get("followers") or data.get("edge_followed_by", {}).get("count", 0)
    following = data.get("following") or data.get("edge_follow", {}).get("count", 0)
    total_posts = data.get("posts_count") or data.get("total_posts", 0)
    bio = data.get("biography") or data.get("bio", "") or ""
    display_name = data.get("full_name") or data.get("display_name", "") or ""
    profile_pic = data.get("profile_pic_url_hd") or data.get("profile_pic_url", "") or ""
    is_verified = bool(data.get("is_verified", False))

    # Posts — ScraperAPI may return them under different keys
    raw_posts = (
        data.get("posts")
        or data.get("edge_owner_to_timeline_media", {}).get("edges", [])
        or []
    )

    posts_data = []
    for item in raw_posts:
        # Handle both flat and nested (edges) formats
        node = item.get("node", item)

        shortcode = node.get("shortcode") or node.get("id", "")
        likes = (
            node.get("likes")
            or node.get("edge_media_preview_like", {}).get("count", 0)
            or node.get("edge_liked_by", {}).get("count", 0)
            or 0
        )
        comments = (
            node.get("comments")
            or node.get("edge_media_to_comment", {}).get("count", 0)
            or 0
        )
        timestamp = node.get("taken_at_timestamp") or node.get("timestamp")
        posted_at = None
        if timestamp:
            try:
                posted_at = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
            except Exception:
                pass

        thumbnail = (
            node.get("thumbnail_url")
            or node.get("thumbnail_src")
            or node.get("display_url")
            or node.get("image_url")
            or ""
        )

        caption_raw = node.get("caption", "")
        if isinstance(caption_raw, dict):
            caption = caption_raw.get("text", "")
        elif isinstance(caption_raw, list) and caption_raw:
            caption = caption_raw[0].get("node", {}).get("text", "") if isinstance(caption_raw[0], dict) else str(caption_raw[0])
        else:
            caption = str(caption_raw) if caption_raw else ""

        # Also handle edge_media_to_caption nested format
        if not caption:
            caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
            caption = caption_edges[0]["node"]["text"] if caption_edges else ""

        typename = node.get("__typename", "")
        media_type = _TYPENAME_MAP.get(typename, "photo")
        if not media_type or media_type == "photo":
            if node.get("is_video"):
                media_type = "video"

        view_count = node.get("video_view_count") or node.get("view_count") or 0
        post_url = (
            node.get("post_url")
            or (f"https://www.instagram.com/p/{shortcode}/" if shortcode else "")
        )

        if shortcode:
            posts_data.append({
                "post_id": shortcode,
                "thumbnail_url": thumbnail,
                "post_url": post_url,
                "likes": likes,
                "comments": comments,
                "posted_at": posted_at,
                "is_video": bool(node.get("is_video", False)),
                "caption": caption,
                "media_type": media_type,
                "view_count": view_count,
            })

    all_text = " ".join(p["caption"] for p in posts_data if p["caption"])
    hashtag_counts = Counter(re.findall(r"#(\w+)", all_text.lower()))
    mention_counts = Counter(re.findall(r"@(\w+)", all_text.lower()))

    top_hashtags = [{"tag": f"#{t}", "count": c} for t, c in hashtag_counts.most_common(10)]
    top_mentions = [{"mention": f"@{m}", "count": c} for m, c in mention_counts.most_common(10)]

    return {
        "username": data.get("username", username),
        "display_name": display_name,
        "profile_pic_url": profile_pic,
        "bio": bio,
        "followers": followers,
        "following": following,
        "total_posts": total_posts,
        "is_verified": is_verified,
        "posts": posts_data,
        "top_hashtags": top_hashtags,
        "top_mentions": top_mentions,
    }