import logging
import re
import random
from collections import Counter
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

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

_PROXY_LIST = [
    "http://vqspqqfa:tc7n0vvfktix@38.154.203.95:5863",
    "http://vqspqqfa:tc7n0vvfktix@198.105.121.200:6462",
    "http://vqspqqfa:tc7n0vvfktix@64.137.96.74:6641",
    "http://vqspqqfa:tc7n0vvfktix@209.127.138.10:5784",
    "http://vqspqqfa:tc7n0vvfktix@38.154.185.97:6370",
    "http://vqspqqfa:tc7n0vvfktix@84.247.60.125:6095",
    "http://vqspqqfa:tc7n0vvfktix@142.111.67.146:5611",
    "http://vqspqqfa:tc7n0vvfktix@191.96.254.138:6185",
    "http://vqspqqfa:tc7n0vvfktix@31.58.9.4:6077",
    "http://vqspqqfa:tc7n0vvfktix@104.239.107.47:5699",
]


def _get_proxy() -> str:
    return random.choice(_PROXY_LIST)


async def scrape_profile(username: str, settings=None) -> dict:
    """Scrape an Instagram profile via the Instagram mobile API with proxy rotation."""
    
    # Try up to 3 different proxies before giving up
    last_error = None
    tried_proxies = set()
    
    for attempt in range(3):
        proxy_url = _get_proxy()
        # Avoid retrying the same proxy
        while proxy_url in tried_proxies and len(tried_proxies) < len(_PROXY_LIST):
            proxy_url = _get_proxy()
        tried_proxies.add(proxy_url)
        
        logger.info("Scraping @%s via proxy attempt %d/3", username, attempt + 1)
        
        try:
            async with httpx.AsyncClient(
                headers=_HEADERS,
                timeout=30,
                follow_redirects=True,
                proxy=proxy_url,
            ) as client:
                url = _IG_API_URL.format(username=username)
                resp = await client.get(url)

            if resp.status_code == 404:
                raise ValueError(f"Instagram profile '{username}' does not exist")
            
            if resp.status_code == 401:
                raise RuntimeError(f"Instagram blocked the request for '{username}' (401). Try again later.")
            
            if resp.status_code == 429:
                logger.warning("Proxy %s got 429 for @%s, trying another...", proxy_url, username)
                last_error = RuntimeError(f"Instagram rate-limited @'{username}' (429) on all attempted proxies.")
                continue  # try next proxy
            
            if resp.status_code != 200:
                raise RuntimeError(f"Instagram returned {resp.status_code} for '{username}'")

            data = resp.json()
            user = data.get("data", {}).get("user")
            if not user:
                raise ValueError(f"Instagram profile '{username}' does not exist or is private")

            return _parse_user(user)

        except (ValueError, RuntimeError):
            raise  # don't retry on definitive errors
        except httpx.RequestError as e:
            logger.warning("Network error on proxy %s for @%s: %s", proxy_url, username, e)
            last_error = RuntimeError(f"Network error fetching Instagram profile '{username}': {e}")
            continue  # try next proxy

    raise last_error or RuntimeError(f"All proxy attempts failed for '{username}'")


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