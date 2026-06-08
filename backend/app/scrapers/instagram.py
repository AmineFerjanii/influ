import asyncio
import logging
import re
from collections import Counter
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_RAPIDAPI_HOST = "instagram-scraper-api2.p.rapidapi.com"
_RAPIDAPI_PROFILE_URL = f"https://{_RAPIDAPI_HOST}/v1.2/info"

_TYPENAME_MAP = {
    "GraphImage": "photo",
    "GraphVideo": "video",
    "GraphSidecar": "carousel",
}


# ── RapidAPI path ─────────────────────────────────────────────────────────────

async def _scrape_via_rapidapi(username: str, api_key: str, posts_limit: int) -> dict:
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": _RAPIDAPI_HOST,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            _RAPIDAPI_PROFILE_URL,
            params={"username_or_id_or_url": username},
            headers=headers,
        )

    logger.info("RapidAPI status for @%s: %d", username, resp.status_code)

    if resp.status_code == 404:
        raise ValueError(f"Instagram profile '{username}' does not exist")
    if resp.status_code == 429:
        raise RuntimeError(f"RapidAPI rate limit reached for '{username}'")
    if resp.status_code != 200:
        raise RuntimeError(f"RapidAPI error {resp.status_code} for '{username}': {resp.text[:200]}")

    data = resp.json()
    user = (data.get("data") or {}).get("user") or data.get("data")
    if not user:
        raise ValueError(f"No user data for '{username}'. Response: {str(data)[:200]}")

    return _parse_user(user, posts_limit)


# ── Instaloader fallback ───────────────────────────────────────────────────────

_loader = None
_loader_lock = asyncio.Lock()


async def _get_loader(ig_username: str, ig_password: str):
    global _loader
    async with _loader_lock:
        if _loader is None:
            import instaloader
            _loader = instaloader.Instaloader(
                quiet=True,
                download_pictures=False,
                download_videos=False,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False,
                request_timeout=30,
            )
            if ig_username and ig_password:
                logger.info("Logging into Instagram as @%s ...", ig_username)
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, _loader.login, ig_username, ig_password)
                logger.info("Instagram login successful as @%s", ig_username)
            else:
                logger.warning("No Instagram credentials — scraping unauthenticated")
    return _loader


def _fetch_instaloader(context, username: str, posts_limit: int):
    from instaloader import Profile, ProfileNotExistsException
    try:
        profile = Profile.from_username(context, username)
    except ProfileNotExistsException:
        raise ValueError(f"Instagram profile '{username}' does not exist")

    posts = []
    try:
        for post in profile.get_posts():
            if len(posts) >= posts_limit:
                break
            posts.append({
                "post_id": post.shortcode,
                "thumbnail_url": post.url,
                "post_url": f"https://www.instagram.com/p/{post.shortcode}/",
                "likes": post.likes,
                "comments": post.comments,
                "posted_at": post.date_utc.replace(tzinfo=timezone.utc) if post.date_utc else None,
                "is_video": post.is_video,
                "caption": post.caption or "",
                "media_type": _TYPENAME_MAP.get(post.typename, "photo"),
                "view_count": post.video_view_count if post.is_video else 0,
            })
    except Exception as e:
        logger.warning("Could not fetch posts for @%s: %s", username, e)

    all_text = " ".join(p["caption"] for p in posts if p["caption"])
    return {
        "username": profile.username,
        "display_name": profile.full_name or "",
        "profile_pic_url": profile.profile_pic_url or "",
        "bio": profile.biography or "",
        "followers": profile.followers,
        "following": profile.followees,
        "total_posts": profile.mediacount,
        "is_verified": bool(profile.is_verified),
        "posts": posts,
        "top_hashtags": [{"tag": f"#{t}", "count": c} for t, c in Counter(re.findall(r"#(\w+)", all_text.lower())).most_common(10)],
        "top_mentions": [{"mention": f"@{m}", "count": c} for m, c in Counter(re.findall(r"@(\w+)", all_text.lower())).most_common(10)],
    }


# ── Shared response parser (for RapidAPI) ─────────────────────────────────────

def _parse_user(user: dict, posts_limit: int) -> dict:
    timeline = user.get("edge_owner_to_timeline_media") or {}
    edges = (timeline.get("edges") or [])[:posts_limit]

    posts_data = []
    for edge in edges:
        node = edge.get("node", {})
        shortcode = node.get("shortcode", "")
        likes = (node.get("edge_media_preview_like") or {}).get("count", 0) or (node.get("edge_liked_by") or {}).get("count", 0)
        comments = (node.get("edge_media_to_comment") or {}).get("count", 0)
        ts = node.get("taken_at_timestamp")
        caption_edges = (node.get("edge_media_to_caption") or {}).get("edges", [])
        caption = caption_edges[0]["node"]["text"] if caption_edges else ""
        posts_data.append({
            "post_id": shortcode,
            "thumbnail_url": node.get("thumbnail_src") or node.get("display_url") or "",
            "post_url": f"https://www.instagram.com/p/{shortcode}/",
            "likes": likes,
            "comments": comments,
            "posted_at": datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None,
            "is_video": node.get("is_video", False),
            "caption": caption,
            "media_type": _TYPENAME_MAP.get(node.get("__typename", ""), "photo"),
            "view_count": node.get("video_view_count") or 0,
        })

    all_text = " ".join(p["caption"] for p in posts_data if p["caption"])
    return {
        "username": user.get("username", ""),
        "display_name": user.get("full_name", "") or "",
        "profile_pic_url": user.get("profile_pic_url_hd") or user.get("profile_pic_url") or "",
        "bio": user.get("biography", "") or "",
        "followers": (user.get("edge_followed_by") or {}).get("count", 0),
        "following": (user.get("edge_follow") or {}).get("count", 0),
        "total_posts": timeline.get("count", 0),
        "is_verified": bool(user.get("is_verified", False)),
        "posts": posts_data,
        "top_hashtags": [{"tag": f"#{t}", "count": c} for t, c in Counter(re.findall(r"#(\w+)", all_text.lower())).most_common(10)],
        "top_mentions": [{"mention": f"@{m}", "count": c} for m, c in Counter(re.findall(r"@(\w+)", all_text.lower())).most_common(10)],
    }


# ── Public entry point ─────────────────────────────────────────────────────────

async def scrape_profile(username: str, settings=None) -> dict:
    from app.config import settings as app_settings
    cfg = settings or app_settings
    rapidapi_key = getattr(cfg, "rapidapi_key", "") or ""
    posts_limit = getattr(cfg, "posts_per_profile", 30) or 30

    if rapidapi_key:
        logger.info("Scraping @%s via RapidAPI", username)
        return await _scrape_via_rapidapi(username, rapidapi_key, posts_limit)

    # Fallback: instaloader with credentials
    logger.warning("RAPIDAPI_KEY not set — falling back to instaloader (may be rate-limited from datacenter IPs)")
    ig_username = getattr(cfg, "ig_username", "") or ""
    ig_password = getattr(cfg, "ig_password", "") or ""
    loader = await _get_loader(ig_username, ig_password)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _fetch_instaloader, loader.context, username, posts_limit)
