import logging
import re
from collections import Counter
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

_APIFY_RUN_SYNC = (
    "https://api.apify.com/v2/acts/clockworks~tiktok-scraper"
    "/run-sync-get-dataset-items"
)


async def scrape_profile(username: str, settings=None) -> dict:
    if settings is None:
        from app.config import settings as _settings
        settings = _settings

    api_key = getattr(settings, "apify_api_key", "") or ""
    if not api_key:
        raise RuntimeError(
            "APIFY_API_KEY is not set — add it to .env and restart the container"
        )

    # Strip leading @ if present
    handle = username.lstrip("@")
    logger.info("Scraping TikTok @%s via Apify clockworks~tiktok-scraper", handle)

    async with httpx.AsyncClient(timeout=180) as client:
        try:
            resp = await client.post(
                _APIFY_RUN_SYNC,
                params={"token": api_key, "timeout": 120, "memory": 1024},
                json={
                    "profiles": [handle],
                    "resultsPerPage": 30,
                    "profileScrapingDelay": 0,
                },
            )
        except httpx.RequestError as exc:
            raise RuntimeError(f"Network error calling Apify for TikTok '{handle}': {exc}")

    if resp.status_code == 401:
        raise RuntimeError("Apify API key is invalid or expired")
    if resp.status_code == 402:
        raise RuntimeError("Apify account has insufficient credits")
    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"Apify returned {resp.status_code} for TikTok '{handle}': {resp.text[:300]}"
        )

    try:
        items = resp.json()
    except Exception:
        raise RuntimeError(f"Invalid JSON from Apify for TikTok '{handle}': {resp.text[:200]}")

    if not items:
        raise ValueError(f"TikTok profile '{handle}' not found or is private")

    return _parse_items(handle, items)


def _parse_items(username: str, items: list) -> dict:
    # Profile info lives in authorMeta on every video item
    first = items[0]
    author = first.get("authorMeta") or {}

    followers = author.get("fans") or author.get("followerCount") or 0
    following = author.get("following") or author.get("followingCount") or 0
    total_videos = author.get("video") or author.get("videoCount") or 0
    heart_count = author.get("heart") or author.get("heartCount") or 0
    display_name = author.get("nickName") or author.get("nickname") or username
    bio = author.get("signature") or ""
    is_verified = bool(author.get("verified") or False)
    avatar = author.get("avatar") or author.get("avatarLarger") or author.get("avatarMedium") or ""
    canonical_username = author.get("name") or author.get("uniqueId") or username

    posts_data = []
    for item in items:
        video_id = str(item.get("id") or "")
        caption = item.get("text") or ""
        posted_at = None
        ts = item.get("createTime")
        if ts:
            try:
                posted_at = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            except Exception:
                pass

        likes = item.get("diggCount") or 0
        comments = item.get("commentCount") or 0
        plays = item.get("playCount") or 0
        thumbnail = (
            item.get("covers", {}).get("default")
            or item.get("covers", {}).get("origin")
            or item.get("coverUrl")
            or ""
        )
        post_url = item.get("webVideoUrl") or (
            f"https://www.tiktok.com/@{canonical_username}/video/{video_id}" if video_id else ""
        )

        posts_data.append({
            "post_id": video_id,
            "thumbnail_url": thumbnail,
            "post_url": post_url,
            "likes": likes,
            "comments": comments,
            "posted_at": posted_at,
            "is_video": True,
            "caption": caption,
            "media_type": "video",
            "view_count": plays,
        })

    all_text = " ".join(p["caption"] for p in posts_data if p["caption"])
    hashtag_counts = Counter(re.findall(r"#(\w+)", all_text.lower()))

    # Also extract structured hashtags from item["hashtags"] if present
    for item in items:
        for tag in item.get("hashtags") or []:
            name = tag.get("name") or tag.get("title") or ""
            if name:
                hashtag_counts[name.lower()] += 1

    mention_counts = Counter(re.findall(r"@(\w+)", all_text.lower()))

    # Compute avg_likes from actual per-video data when available
    if posts_data:
        avg_likes = sum(p["likes"] for p in posts_data) / len(posts_data)
    elif total_videos > 0:
        avg_likes = round(heart_count / total_videos, 1)
    else:
        avg_likes = 0.0

    return {
        "username": canonical_username,
        "display_name": display_name,
        "profile_pic_url": avatar,
        "bio": bio,
        "followers": followers,
        "following": following,
        "total_posts": total_videos,
        "is_verified": is_verified,
        "posts": posts_data,
        "has_comments_data": True,
        "top_hashtags": [
            {"tag": f"#{t}", "count": c} for t, c in hashtag_counts.most_common(10)
        ],
        "top_mentions": [
            {"mention": f"@{m}", "count": c} for m, c in mention_counts.most_common(10)
        ],
        "_precomputed_avg_likes": avg_likes,
    }
