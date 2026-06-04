import asyncio
import json
import logging
import random
import re
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_REHYDRATION_RE = re.compile(
    r'<script[^>]+id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
    re.DOTALL,
)

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


async def scrape_profile(username: str, settings=None) -> dict:
    """Scrape TikTok profile via Playwright stealth, with httpx fallback."""
    if settings is None:
        from ..config import settings as _settings
        settings = _settings

    try:
        return await _scrape_playwright(username, settings)
    except Exception as e:
        logger.warning("Playwright scrape failed for @%s (%s), trying httpx", username, e)
        return await _scrape_httpx(username)


async def _scrape_playwright(username: str, settings) -> dict:
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth
    except ImportError:
        raise RuntimeError("playwright / playwright-stealth not installed")

    url = f"https://www.tiktok.com/@{username}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--headless=new", "--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            viewport={"width": random.randint(1280, 1440), "height": random.randint(800, 900)},
            user_agent=_USER_AGENT,
            locale="en-US",
        )
        page = await ctx.new_page()
        await Stealth().apply_stealth_async(page)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        except Exception:
            await page.goto(url, wait_until="commit", timeout=45_000)

        wait = settings.tt_page_wait + random.uniform(0, 4)
        await asyncio.sleep(wait)
        html = await page.content()
        await browser.close()

    return _parse_html(username, html)


async def _scrape_httpx(username: str) -> dict:
    url = f"https://www.tiktok.com/@{username}"
    headers = {
        "User-Agent": _USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.tiktok.com/",
    }
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    return _parse_html(username, resp.text)


def _parse_html(username: str, html: str) -> dict:
    match = _REHYDRATION_RE.search(html)
    if not match:
        raise RuntimeError(
            f"Could not find TikTok data blob for @{username}. "
            "TikTok may have blocked the request."
        )

    raw = json.loads(match.group(1))
    scope = raw.get("__DEFAULT_SCOPE__", {})

    user_detail = scope.get("webapp.user-detail", {})
    user_info = user_detail.get("userInfo", {})
    user = user_info.get("user", {})
    stats = user_info.get("stats", {})

    if not user:
        raise RuntimeError(f"Could not parse user data from TikTok page for @{username}")

    followers = stats.get("followerCount", 0)
    following = stats.get("followingCount", 0)
    total_videos = stats.get("videoCount", 0)
    heart_count = stats.get("heartCount", 0)  # lifetime total likes

    display_name = user.get("nickname", username)
    bio = user.get("signature", "")
    is_verified = bool(user.get("verified", False))
    avatar = user.get("avatarLarger") or user.get("avatarMedium") or ""
    sec_uid = user.get("secUid", "")

    # Compute avg_likes from aggregate stats (TikTok doesn't expose per-video data without auth)
    avg_likes_estimate = round(heart_count / total_videos, 1) if total_videos > 0 else 0.0

    # Build synthetic post stubs so the grid shows something meaningful
    posts_data = _build_post_stubs(username, sec_uid, total_videos, avg_likes_estimate)

    return {
        "username": user.get("uniqueId", username),
        "display_name": display_name,
        "profile_pic_url": avatar,
        "bio": bio,
        "followers": followers,
        "following": following,
        "total_posts": total_videos,
        "is_verified": is_verified,
        "posts": posts_data,
        "has_comments_data": False,
        # Pass avg_likes directly so kpi_calculator uses it rather than re-computing
        "_precomputed_avg_likes": avg_likes_estimate,
    }


def _build_post_stubs(username: str, sec_uid: str, total_videos: int, avg_likes: float) -> list:
    """Return empty list — TikTok video thumbnails require auth. KPIs are computed from aggregate stats."""
    return []
