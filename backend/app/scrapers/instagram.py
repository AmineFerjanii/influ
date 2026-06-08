import asyncio
import logging
import re
from collections import Counter
from datetime import timezone

import instaloader
from instaloader import Profile, ProfileNotExistsException, PrivateProfileNotFollowedException

logger = logging.getLogger(__name__)

_TYPENAME_MAP = {
    "GraphImage": "photo",
    "GraphVideo": "video",
    "GraphSidecar": "carousel",
}

_loader: instaloader.Instaloader = None
_loader_lock = asyncio.Lock()


def _make_loader(proxy_url: str = "") -> instaloader.Instaloader:
    loader = instaloader.Instaloader(
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
    if proxy_url:
        loader.context._session.proxies = {"http": proxy_url, "https": proxy_url}
        logger.info("Instaloader proxy configured: %s", proxy_url[:40])
    return loader


async def _get_loader(ig_username: str, ig_password: str, proxy_url: str = "") -> instaloader.Instaloader:
    global _loader
    async with _loader_lock:
        if _loader is None:
            _loader = _make_loader(proxy_url)
            if not ig_username or not ig_password:
                logger.warning("No Instagram credentials configured — scraping unauthenticated (heavy rate limits)")
            else:
                logger.info("Logging into Instagram as @%s ...", ig_username)
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, _loader.login, ig_username, ig_password)
                logger.info("Instagram login successful as @%s", ig_username)
    return _loader


def _fetch_in_thread(context, username: str, posts_limit: int):
    """Blocking: fetch profile + posts. Runs in thread pool."""
    try:
        profile = Profile.from_username(context, username)
    except ProfileNotExistsException:
        raise ValueError(f"Instagram profile '{username}' does not exist")
    except PrivateProfileNotFollowedException:
        raise ValueError(f"Instagram profile '{username}' is private")

    posts = []
    try:
        for post in profile.get_posts():
            if len(posts) >= posts_limit:
                break
            all_text = post.caption or ""
            posts.append({
                "post_id": post.shortcode,
                "thumbnail_url": post.url,
                "post_url": f"https://www.instagram.com/p/{post.shortcode}/",
                "likes": post.likes,
                "comments": post.comments,
                "posted_at": post.date_utc.replace(tzinfo=timezone.utc) if post.date_utc else None,
                "is_video": post.is_video,
                "caption": all_text,
                "media_type": _TYPENAME_MAP.get(post.typename, "photo"),
                "view_count": post.video_view_count if post.is_video else 0,
            })
    except Exception as e:
        logger.warning("Could not fetch posts for @%s: %s", username, e)

    return profile, posts


async def scrape_profile(username: str, settings=None) -> dict:
    """Scrape Instagram profile via instaloader with credential-based auth."""
    from app.config import settings as app_settings
    cfg = settings or app_settings
    ig_username = getattr(cfg, "ig_username", "") or ""
    ig_password = getattr(cfg, "ig_password", "") or ""
    posts_limit = getattr(cfg, "posts_per_profile", 30) or 30
    proxy_url = getattr(cfg, "proxy_url", "") or ""

    # Build ScraperAPI residential proxy if no explicit proxy is configured
    if not proxy_url:
        api_key = getattr(cfg, "scraper_api_key", "") or ""
        if api_key:
            proxy_url = f"http://scraperapi.residential=true:{api_key}@proxy-server.scraperapi.com:8001"

    loader = await _get_loader(ig_username, ig_password, proxy_url)

    loop = asyncio.get_running_loop()
    try:
        profile, posts_data = await loop.run_in_executor(
            None, _fetch_in_thread, loader.context, username, posts_limit
        )
    except (ValueError, RuntimeError):
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to scrape Instagram profile '{username}': {e!r}")

    all_text = " ".join(p["caption"] for p in posts_data if p["caption"])
    hashtag_counts = Counter(re.findall(r"#(\w+)", all_text.lower()))
    mention_counts = Counter(re.findall(r"@(\w+)", all_text.lower()))

    return {
        "username": profile.username,
        "display_name": profile.full_name or "",
        "profile_pic_url": profile.profile_pic_url or "",
        "bio": profile.biography or "",
        "followers": profile.followers,
        "following": profile.followees,
        "total_posts": profile.mediacount,
        "is_verified": bool(profile.is_verified),
        "posts": posts_data,
        "top_hashtags": [{"tag": f"#{t}", "count": c} for t, c in hashtag_counts.most_common(10)],
        "top_mentions": [{"mention": f"@{m}", "count": c} for m, c in mention_counts.most_common(10)],
    }
