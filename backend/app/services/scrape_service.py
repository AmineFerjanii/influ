import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models.influencer import Influencer, Post, ScrapeJob
from ..scrapers import instagram as ig_scraper
from ..scrapers import tiktok as tt_scraper
from .kpi_calculator import compute_kpis
from .niche_service import infer_niches

logger = logging.getLogger(__name__)

# Serial job queue — prevents concurrent SQLite writes and platform rate limits
_job_queue: asyncio.Queue = asyncio.Queue()
_worker_started = False


async def start_worker():
    global _worker_started
    if not _worker_started:
        _worker_started = True
        asyncio.create_task(_worker())


async def _worker():
    while True:
        job_id, influencer_id, db_factory = await _job_queue.get()
        db = db_factory()
        try:
            await _run_scrape(job_id, influencer_id, db)
        except Exception as e:
            logger.error("Unhandled error in scrape worker: %s", e)
        finally:
            db.close()
            _job_queue.task_done()


async def enqueue_scrape(influencer_id: int, db: Session, db_factory) -> ScrapeJob:
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise ValueError(f"Influencer {influencer_id} not found")

    job = ScrapeJob(influencer_id=influencer_id, status="queued")
    db.add(job)
    influencer.scrape_status = "pending"
    db.commit()
    db.refresh(job)

    await _job_queue.put((job.id, influencer_id, db_factory))
    return job


async def _run_scrape(job_id: int, influencer_id: int, db: Session):
    job = db.get(ScrapeJob, job_id)
    influencer = db.get(Influencer, influencer_id)
    if not job or not influencer:
        return

    job.status = "running"
    influencer.scrape_status = "scraping"
    db.commit()

    try:
        if influencer.platform == "instagram":
            data = await ig_scraper.scrape_profile(influencer.username, settings)
        else:
            data = await tt_scraper.scrape_profile(influencer.username, settings)

        _update_influencer(influencer, data, db)

        job.status = "success"
        job.completed_at = datetime.now(timezone.utc)
        influencer.scrape_status = "success"
        influencer.last_scraped_at = datetime.now(timezone.utc)
        influencer.scrape_error = None
        db.commit()

        # Auto-link if same username exists on the other platform and neither is linked yet
        _try_auto_link(influencer, db)

        logger.info("Scrape succeeded for @%s (%s)", influencer.username, influencer.platform)

    except Exception as e:
        logger.error("Scrape failed for @%s: %s", influencer.username, e)
        job.status = "failed"
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = str(e)
        influencer.scrape_status = "error"
        influencer.scrape_error = str(e)
        db.commit()


def _try_auto_link(influencer: Influencer, db: Session):
    if influencer.linked_influencer_id is not None:
        return  # already linked — don't override
    other_platform = "tiktok" if influencer.platform == "instagram" else "instagram"
    match = (
        db.query(Influencer)
        .filter_by(platform=other_platform, username=influencer.username)
        .first()
    )
    if match and match.linked_influencer_id is None:
        influencer.linked_influencer_id = match.id
        match.linked_influencer_id = influencer.id
        db.commit()
        logger.info("Auto-linked @%s IG↔TT (ids %d ↔ %d)", influencer.username, influencer.id, match.id)


def _update_influencer(influencer: Influencer, data: dict, db: Session):
    influencer.display_name = data.get("display_name", "") or influencer.display_name
    influencer.profile_pic_url = data.get("profile_pic_url", "") or influencer.profile_pic_url
    influencer.bio = data.get("bio", "") or influencer.bio
    influencer.followers = data.get("followers", 0)
    influencer.following = data.get("following", 0)
    influencer.total_posts = data.get("total_posts", 0)
    influencer.is_verified = data.get("is_verified", False)

    posts_raw = data.get("posts", [])
    has_comments = data.get("has_comments_data", True)
    precomputed_avg_likes = data.get("_precomputed_avg_likes")

    if precomputed_avg_likes is not None and influencer.followers > 0:
        # TikTok: avg_likes computed from aggregate heartCount / videoCount
        influencer.avg_likes = precomputed_avg_likes
        influencer.avg_comments = 0.0
        influencer.engagement_rate = round(precomputed_avg_likes / influencer.followers * 100, 2)
        influencer.posts_per_week = 0.0
        influencer.has_comments_data = False
    else:
        kpis = compute_kpis(posts_raw, influencer.followers, has_comments)
        influencer.avg_likes = kpis["avg_likes"]
        influencer.avg_comments = kpis["avg_comments"]
        influencer.engagement_rate = kpis["engagement_rate"]
        influencer.posts_per_week = kpis["posts_per_week"]
        influencer.has_comments_data = kpis["has_comments_data"]

    # Phase 2: hashtags, mentions, niches, reach, media breakdown
    top_hashtags = data.get("top_hashtags", [])
    top_mentions = data.get("top_mentions", [])
    influencer.top_hashtags = json.dumps(top_hashtags)
    influencer.top_mentions = json.dumps(top_mentions)
    influencer.inferred_niches = json.dumps(infer_niches(influencer.bio or "", top_hashtags))
    influencer.estimated_reach = round(influencer.followers * 0.35)
    influencer.estimated_impressions = round(influencer.followers * 0.50)
    influencer.photo_count = sum(1 for p in posts_raw if p.get("media_type") == "photo")
    influencer.video_count = sum(1 for p in posts_raw if p.get("media_type") in ("video", "carousel"))

    # Upsert posts — update existing, insert new; keep latest 30
    existing_map = {post.post_id: post for post in influencer.posts}
    for p in posts_raw:
        post_id = p["post_id"]
        if post_id in existing_map:
            existing = existing_map[post_id]
            existing.likes = p.get("likes", 0)
            existing.comments = p.get("comments", 0)
            existing.thumbnail_url = p.get("thumbnail_url") or existing.thumbnail_url
            existing.caption = p.get("caption")
            existing.media_type = p.get("media_type")
            existing.view_count = p.get("view_count", 0)
        else:
            db.add(Post(
                influencer_id=influencer.id,
                post_id=post_id,
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

    # Trim to 30 most recent
    db.flush()
    all_posts = (
        db.query(Post)
        .filter(Post.influencer_id == influencer.id)
        .order_by(Post.posted_at.desc().nullslast())
        .all()
    )
    for old_post in all_posts[30:]:
        db.delete(old_post)

    # Async thumbnail caching (fire and forget)
    asyncio.create_task(_cache_thumbnails(influencer.id, posts_raw))


async def _cache_thumbnails(influencer_id: int, posts: list):
    thumb_dir = Path(settings.thumbnails_dir) / str(influencer_id)
    thumb_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=15) as client:
        for post in posts[:6]:
            url = post.get("thumbnail_url", "")
            if not url:
                continue
            filename = thumb_dir / f"{post['post_id']}.jpg"
            if filename.exists():
                continue
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    filename.write_bytes(resp.content)
            except Exception as e:
                logger.debug("Could not cache thumbnail %s: %s", url, e)
