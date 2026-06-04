"""
Standalone bulk scraper using Instagram's mobile API (i.instagram.com).
Uses a single persistent httpx session — avoids GraphQL entirely.

Usage (from backend/):
    source venv/bin/activate
    python scrape_csv.py ../Influencer\ CSV.csv
"""

import asyncio
import csv
import io
import json
import logging
import random
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import httpx
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent))
from app.database import SessionLocal, Base, engine
from app.models.influencer import Influencer, Post
from app.services.kpi_calculator import compute_kpis
from app.services.niche_service import infer_niches
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

_IG_API = "https://i.instagram.com/api/v1/users/web_profile_info/?username={}"
_HEADERS = {
    "User-Agent": "Instagram 219.0.0.12.117 Android (33/13; 420dpi; 1080x2400; samsung; SM-G991B; o1s; exynos2100)",
    "x-ig-app-id": "936619743392459",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "*/*",
    "x-ig-www-claim": "0",
    "origin": "https://www.instagram.com",
    "referer": "https://www.instagram.com/",
}
_TYPENAME_MAP = {"GraphImage": "photo", "GraphVideo": "video", "GraphSidecar": "carousel"}


async def _scrape_one(client: httpx.AsyncClient, username: str) -> dict:
    resp = await client.get(_IG_API.format(username), headers=_HEADERS)

    if resp.status_code == 404:
        raise ValueError(f"Profile '{username}' not found or private")
    if resp.status_code == 401:
        raise RuntimeError("Rate-limited (401) — need to wait or switch IP")
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}")

    user = resp.json().get("data", {}).get("user")
    if not user:
        raise ValueError(f"Empty profile data for '{username}'")

    followers = user.get("edge_followed_by", {}).get("count", 0)
    following = user.get("edge_follow", {}).get("count", 0)
    total_posts = user.get("edge_owner_to_timeline_media", {}).get("count", 0)
    edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])

    posts_data = []
    for edge in edges:
        node = edge.get("node", {})
        shortcode = node.get("shortcode", "")
        likes = (node.get("edge_media_preview_like", {}).get("count", 0)
                 or node.get("edge_liked_by", {}).get("count", 0))
        comments = node.get("edge_media_to_comment", {}).get("count", 0)
        ts = node.get("taken_at_timestamp")
        posted_at = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
        thumbnail = node.get("thumbnail_src") or node.get("display_url") or ""
        caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
        caption = caption_edges[0]["node"]["text"] if caption_edges else ""
        typename = node.get("__typename", "")
        posts_data.append({
            "post_id": shortcode,
            "thumbnail_url": thumbnail,
            "post_url": f"https://www.instagram.com/p/{shortcode}/",
            "likes": likes,
            "comments": comments,
            "posted_at": posted_at,
            "is_video": node.get("is_video", False),
            "caption": caption,
            "media_type": _TYPENAME_MAP.get(typename, "photo"),
            "view_count": node.get("video_view_count") or 0,
        })

    all_text = " ".join(p["caption"] for p in posts_data if p["caption"])
    top_hashtags = [{"tag": f"#{t}", "count": c} for t, c in Counter(re.findall(r"#(\w+)", all_text.lower())).most_common(10)]
    top_mentions = [{"mention": f"@{m}", "count": c} for m, c in Counter(re.findall(r"@(\w+)", all_text.lower())).most_common(10)]

    return {
        "username": user.get("username", username),
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


def _upsert_influencer(db: Session, platform: str, username: str) -> Influencer:
    inf = db.query(Influencer).filter_by(platform=platform, username=username).first()
    if not inf:
        inf = Influencer(platform=platform, username=username)
        db.add(inf)
        db.commit()
        db.refresh(inf)
    return inf


def _save(db: Session, inf: Influencer, data: dict):
    inf.display_name = data.get("display_name") or inf.display_name
    inf.profile_pic_url = data.get("profile_pic_url") or inf.profile_pic_url
    inf.bio = data.get("bio") or inf.bio
    inf.followers = data.get("followers", 0)
    inf.following = data.get("following", 0)
    inf.total_posts = data.get("total_posts", 0)
    inf.is_verified = data.get("is_verified", False)

    posts_raw = data.get("posts", [])
    kpis = compute_kpis(posts_raw, inf.followers, True)
    inf.avg_likes = kpis["avg_likes"]
    inf.avg_comments = kpis["avg_comments"]
    inf.engagement_rate = kpis["engagement_rate"]
    inf.posts_per_week = kpis["posts_per_week"]
    inf.has_comments_data = kpis["has_comments_data"]

    top_hashtags = data.get("top_hashtags", [])
    top_mentions = data.get("top_mentions", [])
    inf.top_hashtags = json.dumps(top_hashtags)
    inf.top_mentions = json.dumps(top_mentions)
    inf.inferred_niches = json.dumps(infer_niches(inf.bio or "", top_hashtags))
    inf.estimated_reach = round(inf.followers * 0.35)
    inf.estimated_impressions = round(inf.followers * 0.50)
    inf.photo_count = sum(1 for p in posts_raw if p.get("media_type") == "photo")
    inf.video_count = sum(1 for p in posts_raw if p.get("media_type") in ("video", "carousel"))
    inf.scrape_status = "success"
    inf.scrape_error = None
    inf.last_scraped_at = datetime.now(timezone.utc)

    existing_map = {p.post_id: p for p in inf.posts}
    for p in posts_raw:
        pid = p["post_id"]
        if pid in existing_map:
            ep = existing_map[pid]
            ep.likes = p.get("likes", 0)
            ep.comments = p.get("comments", 0)
            ep.thumbnail_url = p.get("thumbnail_url") or ep.thumbnail_url
            ep.caption = p.get("caption")
            ep.media_type = p.get("media_type")
            ep.view_count = p.get("view_count", 0)
        else:
            db.add(Post(
                influencer_id=inf.id,
                post_id=pid,
                thumbnail_url=p.get("thumbnail_url"),
                post_url=p.get("post_url"),
                likes=p.get("likes", 0),
                comments=p.get("comments", 0),
                posted_at=p.get("posted_at"),
                is_video=p.get("is_video", False),
                caption=p.get("caption"),
                media_type=p.get("media_type"),
                view_count=p.get("view_count", 0),
            ))
    db.commit()


def _load_csv(path: str) -> List[tuple]:
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    delimiter = ";" if text[:2048].count(";") >= text[:2048].count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
    has_platform = "platform" in fieldnames

    rows, seen = [], set()
    for row in reader:
        norm = {k.strip().lower(): v.strip() for k, v in row.items() if v}
        username = norm.get("username", "").lstrip("@").split("?")[0].strip()
        if not username:
            continue
        platform = norm.get("platform", "instagram").lower() if has_platform else "instagram"
        if platform not in ("instagram", "tiktok"):
            continue
        key = (platform, username)
        if key not in seen:
            seen.add(key)
            rows.append(key)
    return rows


# How long to wait after hitting a 401 before retrying (seconds)
RATE_LIMIT_COOLDOWN = 5 * 60   # 5 minutes
RATE_LIMIT_MAX_RETRIES = 10    # give up after 10 consecutive 401s


async def _scrape_with_retry(client: httpx.AsyncClient, username: str) -> dict:
    """Scrape one profile, auto-waiting on rate-limit (401) up to MAX_RETRIES times."""
    attempts = 0
    while True:
        try:
            return await _scrape_one(client, username)
        except RuntimeError as e:
            if "401" not in str(e):
                raise
            attempts += 1
            if attempts >= RATE_LIMIT_MAX_RETRIES:
                raise RuntimeError(f"Rate-limited {attempts}× in a row — giving up on @{username}")
            log.warning(
                "       ⏳ Rate limit hit (attempt %d/%d) — cooling down %d min …",
                attempts, RATE_LIMIT_MAX_RETRIES, RATE_LIMIT_COOLDOWN // 60,
            )
            await asyncio.sleep(RATE_LIMIT_COOLDOWN)
            log.info("       ↩  Retrying @%s …", username)


async def main(csv_path: str):
    handles = _load_csv(csv_path)
    total = len(handles)
    log.info("Loaded %d unique handles", total)

    ok = skip = fail = 0

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for i, (platform, username) in enumerate(handles, 1):
            db = SessionLocal()
            try:
                inf = _upsert_influencer(db, platform, username)

                if inf.scrape_status == "success":
                    log.info("[%d/%d] SKIP  @%s", i, total, username)
                    skip += 1
                    continue

                log.info("[%d/%d] @%s …", i, total, username)
                try:
                    data = await _scrape_with_retry(client, username)
                    _save(db, inf, data)
                    log.info("       ✓ %s — %s followers", data.get("display_name", username), f"{data['followers']:,}")
                    ok += 1
                except Exception as e:
                    inf.scrape_status = "error"
                    inf.scrape_error = str(e)
                    db.commit()
                    log.warning("       ✗ @%s — %s", username, e)
                    fail += 1
            finally:
                db.close()

            if i < total:
                delay = random.uniform(settings.ig_min_delay, settings.ig_max_delay)
                log.info("       sleeping %.0fs …", delay)
                await asyncio.sleep(delay)

    log.info("Done — ✓ %d  skipped %d  ✗ %d", ok, skip, fail)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../Influencer CSV.csv"
    asyncio.run(main(path))
