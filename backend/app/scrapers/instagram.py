import logging
import re
import time
from collections import Counter
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_IG_API_URL = "https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
_LOGIN_URL = "https://www.instagram.com/accounts/login/ajax/"
_CSRF_URL = "https://www.instagram.com/accounts/login/"

_API_HEADERS = {
    "User-Agent": "Instagram 219.0.0.12.117 Android (33/13; 420dpi; 1080x2400; samsung; SM-G991B; o1s; exynos2100)",
    "x-ig-app-id": "936619743392459",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "*/*",
    "x-ig-www-claim": "0",
    "origin": "https://www.instagram.com",
    "referer": "https://www.instagram.com/",
}

_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
}

_TYPENAME_MAP = {
    "GraphImage": "photo",
    "GraphVideo": "video",
    "GraphSidecar": "carousel",
}

# Cached session: (sessionid, obtained_at_timestamp)
_cached_session: tuple = (None, 0)
_SESSION_TTL = 3600 * 6  # 6 hours


async def _get_session(ig_username: str, ig_password: str) -> str:
    """Login via browser flow and return a sessionid cookie. Cached for 6 hours."""
    global _cached_session
    sessionid, obtained_at = _cached_session
    if sessionid and (time.time() - obtained_at) < _SESSION_TTL:
        return sessionid

    logger.info("Logging into Instagram as @%s ...", ig_username)

    async with httpx.AsyncClient(headers=_BROWSER_HEADERS, follow_redirects=True, timeout=30) as client:
        # Get CSRF token from login page
        resp = await client.get(_CSRF_URL)
        csrf = client.cookies.get("csrftoken")
        if not csrf:
            m = re.search(r'"csrf_token":"([^"]+)"', resp.text)
            csrf = m.group(1) if m else ""
        if not csrf:
            raise RuntimeError("Could not obtain Instagram CSRF token")

        login_resp = await client.post(
            _LOGIN_URL,
            data={
                "username": ig_username,
                "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{ig_password}",
                "queryParams": "{}",
                "optIntoOneTap": "false",
                "trustedDeviceRecords": "{}",
            },
            headers={
                **_BROWSER_HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": csrf,
                "X-Instagram-AJAX": "1",
                "X-Requested-With": "XMLHttpRequest",
                "X-IG-App-ID": "936619743392459",
                "Referer": "https://www.instagram.com/accounts/login/",
            },
        )

    result = login_resp.json()
    if not result.get("authenticated"):
        raise RuntimeError(f"Instagram login failed: {result.get('message') or result}")

    sessionid = login_resp.cookies.get("sessionid") or client.cookies.get("sessionid")
    if not sessionid:
        raise RuntimeError("Login succeeded but no sessionid returned")

    _cached_session = (sessionid, time.time())
    logger.info("Instagram session obtained for @%s", ig_username)
    return sessionid


async def scrape_profile(username: str, settings=None) -> dict:
    from app.config import settings as app_settings
    cfg = settings or app_settings
    ig_username = getattr(cfg, "ig_username", "") or ""
    ig_password = getattr(cfg, "ig_password", "") or ""

    cookies = {}
    if ig_username and ig_password:
        try:
            sessionid = await _get_session(ig_username, ig_password)
            cookies = {"sessionid": sessionid}
        except Exception as e:
            logger.warning("Instagram login failed (%s) — proceeding unauthenticated", e)

    url = _IG_API_URL.format(username=username)
    logger.info("Scraping @%s (authenticated=%s)", username, bool(cookies))

    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=_API_HEADERS, cookies=cookies)
        except httpx.RequestError as e:
            raise RuntimeError(f"Network error fetching Instagram profile '{username}': {e}")

    logger.info("Instagram status for @%s: %d", username, resp.status_code)

    if resp.status_code == 404:
        raise ValueError(f"Instagram profile '{username}' does not exist")
    if resp.status_code in (401, 429):
        # Invalidate session so next attempt re-logins
        global _cached_session
        _cached_session = (None, 0)
        raise RuntimeError(f"Instagram rate-limited '{username}' ({resp.status_code}). Will retry.")
    if resp.status_code != 200:
        raise RuntimeError(f"Instagram returned {resp.status_code} for '{username}': {resp.text[:200]}")

    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"Invalid JSON for '{username}': {resp.text[:200]}")

    user = data.get("data", {}).get("user")
    if not user:
        raise ValueError(f"Instagram profile '{username}' does not exist or is private")

    return _parse_user(user)


def _parse_user(user: dict) -> dict:
    timeline = user.get("edge_owner_to_timeline_media", {})
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
        posts_data.append({
            "post_id": shortcode,
            "thumbnail_url": thumbnail,
            "post_url": f"https://www.instagram.com/p/{shortcode}/",
            "likes": likes,
            "comments": comments,
            "posted_at": posted_at,
            "is_video": node.get("is_video", False),
            "caption": caption,
            "media_type": _TYPENAME_MAP.get(node.get("__typename", ""), "photo"),
            "view_count": node.get("video_view_count") or 0,
        })

    all_text = " ".join(p["caption"] for p in posts_data if p["caption"])
    hashtag_counts = Counter(re.findall(r"#(\w+)", all_text.lower()))
    mention_counts = Counter(re.findall(r"@(\w+)", all_text.lower()))

    return {
        "username": user.get("username", ""),
        "display_name": user.get("full_name", "") or "",
        "profile_pic_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url") or "",
        "bio": user.get("biography", "") or "",
        "followers": user.get("edge_followed_by", {}).get("count", 0),
        "following": user.get("edge_follow", {}).get("count", 0),
        "total_posts": timeline.get("count", 0),
        "is_verified": bool(user.get("is_verified", False)),
        "posts": posts_data,
        "top_hashtags": [{"tag": f"#{t}", "count": c} for t, c in hashtag_counts.most_common(10)],
        "top_mentions": [{"mention": f"@{m}", "count": c} for m, c in mention_counts.most_common(10)],
    }
