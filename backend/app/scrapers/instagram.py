import logging
import re
from collections import Counter
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_SCRAPER_API_KEY = "54992c77618597a7b2b9cf1863d48555"

_IG_API_URL = "https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"

_HEADERS = {
    "User-Agent": "Instagram 219.0.0.12.117 Android (33/13; 420dpi; 1080x2400; samsung; SM-G991B; o1s; exynos2100)",
    "x-ig-app-id": "936619743392459",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "*/*",
    "x-ig-www-claim": "0",
    "origin": "https://www.instagram.com",
    "referer": "https://www.instagram.com/",
}

_TYPENAME_MAP = {
    "GraphImage": "photo",
    "GraphVideo": "video",
    "GraphSidecar": "carousel",
}


async def scrape_profile(username: str, settings=None) -> dict:
    """Scrape Instagram profile using ScraperAPI as HTTP proxy."""

    api_key = _SCRAPER_API_KEY
    if settings:
        api_key = getattr(settings, 'scraper_api_key', None) or _SCRAPER_API_KEY

    # ScraperAPI proxy — port 8012 for HTTPS targets
    proxy_url = f"http://scraperapi:{api_key}@proxy-server.scraperapi.com:8012"

    target_url = _IG_API_URL.format(username=username)

    logger.info("Scraping @%s via ScraperAPI proxy (port 8012)", username)

    async with httpx.AsyncClient(
        headers=_HEADERS,
        timeout=60,
        follow_redirects=True,
        proxy=proxy_url,
        verify=False,
    ) as client:
        try:
            resp = await client.get(target_url)
        except httpx.RequestError as e:
            raise RuntimeError(f"Network error fetching Instagram profile '{username}': {e}")

    logger.info("ScraperAPI response status for @%s: %d", username, resp.status_code)
    logger.info("ScraperAPI response preview for @%s: %s", username, resp.text[:300])

    if resp.status_code == 404:
        raise ValueError(f"Instagram profile '{username}' does not exist")
    if resp.status_code == 401:
        raise RuntimeError(f"Instagram blocked the request for '{username}' (401).")
    if resp.status_code == 429:
        raise RuntimeError(f"Instagram rate-limited '{username}' (429).")
    if resp.status_code == 403:
        raise RuntimeError(f"ScraperAPI 403 for '{username}'. Response: {resp.text[:200]}")
    if resp.status_code != 200:
        raise RuntimeError(f"Instagram returned {resp.status_code} for '{username}'. Body: {resp.text[:200]}")

    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Invalid JSON for '{username}': {resp.text[:200]}")

    user = data.get("data", {}).get("user")
    if not user:
        raise ValueError(f"Instagram profile '{username}' does not exist or is private")

    return _parse_user(user)


def _parse_user(user: dict) -> dict:
    username = user.get("username", "")
    followers = user.get("edge_followed_by", {}).get("count", 0)
    following = user.get("edge_follow", {}).get("count", 0)
    timeline = user.get("edge_owner_to_timeline_media", {})
    total_posts = timeline.get("count", 0)
    edges = timeline.get("edges", [])

    posts_data = []
    for edge in edges:
        node = edge.get("node", {})
        shortcode = node.get("shortcode", "")

        likes = (
            node.get("edge_media_preview_like", {}).get("count", 0)
            or node.get("edge_liked_by", {}).get("count", 0)
        )
        comments = node.get("edge_media_to_comment", {}).get("count", 0)
        timestamp = node.get("taken_at_timestamp")
        posted_at = datetime.fromtimestamp(timestamp, tz=timezone.utc) if timestamp else None

        thumbnail = node.get("thumbnail_src") or node.get("display_url") or ""

        caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
        caption = caption_edges[0]["node"]["text"] if caption_edges else ""

        typename = node.get("__typename", "")
        media_type = _TYPENAME_MAP.get(typename, "photo")

        view_count = node.get("video_view_count") or 0

        posts_data.append({
            "post_id": shortcode,
            "thumbnail_url": thumbnail,
            "post_url": f"https://www.instagram.com/p/{shortcode}/",
            "likes": likes,
            "comments": comments,
            "posted_at": posted_at,
            "is_video": node.get("is_video", False),
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
        "username": username,
        "display_name": user.get("full_name", "") or "",
        "profile_pic_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url") or "",
        "bio": user.get("biography", "") or "",
        "followers": followers,
        "following": following,
        "total_posts": total_posts,
        "is_verified": bool(user.get("is_verified", False)),
        "posts": posts_data,
        "top_hashtags": top_hashtags,
        "top_mentions": top_mentions,
    }