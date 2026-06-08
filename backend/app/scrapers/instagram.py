import logging
import re
from collections import Counter
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_IG_API_URL = "https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "x-ig-app-id": "936619743392459",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json, text/plain, */*",
    "x-requested-with": "XMLHttpRequest",
    "origin": "https://www.instagram.com",
    "referer": "https://www.instagram.com/",
}

_TYPENAME_MAP = {
    "GraphImage": "photo",
    "GraphVideo": "video",
    "GraphSidecar": "carousel",
}


async def scrape_profile(username: str, settings=None) -> dict:
    """Scrape Instagram profile. Tries ScraperAPI residential first, falls back to direct."""
    from app.config import settings as app_settings
    api_key = (settings and getattr(settings, 'scraper_api_key', None)) or app_settings.scraper_api_key

    target_url = _IG_API_URL.format(username=username)

    # Try via ScraperAPI (residential) first
    if api_key:
        import urllib.parse
        encoded = urllib.parse.quote(target_url, safe='')
        scraper_url = f"https://api.scraperapi.com/?api_key={api_key}&url={encoded}&residential=true"
        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                resp = await client.get(scraper_url, headers=_HEADERS)
            logger.info("ScraperAPI status for @%s: %d", username, resp.status_code)
            if resp.status_code == 200:
                return _extract(resp, username)
            logger.warning("ScraperAPI failed for @%s (%d), trying direct", username, resp.status_code)
        except httpx.RequestError as e:
            logger.warning("ScraperAPI request error for @%s: %s, trying direct", username, e)

    # Direct request fallback
    logger.info("Scraping @%s via direct request", username)
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            resp = await client.get(target_url, headers=_HEADERS)
        except httpx.RequestError as e:
            raise RuntimeError(f"Network error fetching Instagram profile '{username}': {e!r}")

    logger.info("Direct status for @%s: %d", username, resp.status_code)
    return _extract(resp, username)


def _extract(resp: httpx.Response, username: str) -> dict:
    if resp.status_code == 404:
        raise ValueError(f"Instagram profile '{username}' does not exist")
    if resp.status_code == 401:
        raise RuntimeError(f"Instagram blocked the request for '{username}' (401).")
    if resp.status_code == 429:
        raise RuntimeError(f"Instagram rate-limited '{username}' (429).")
    if resp.status_code == 403:
        raise RuntimeError(f"Instagram 403 for '{username}'. Body: {resp.text[:300]}")
    if resp.status_code != 200:
        raise RuntimeError(f"Unexpected status {resp.status_code} for '{username}'. Body: {resp.text[:300]}")

    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Invalid JSON for '{username}'. Raw: {resp.text[:300]}")

    user = data.get("data", {}).get("user")
    if not user:
        raise ValueError(f"Profile '{username}' not found or private. Keys: {list(data.keys())}")

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