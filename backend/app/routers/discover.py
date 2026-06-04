"""
Discovery endpoint: find new Tunisian Instagram usernames via hashtag search,
optionally auto-adding them to the platform and queuing scrape jobs.
"""
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.influencer import Influencer
from ..schemas.influencer import InfluencerOut
from ..scrapers.instagram_discover import discover_tunisian_usernames
from ..services import scrape_service

router = APIRouter(prefix="/api/discover", tags=["discover"])


async def _enqueue_bg(influencer_id: int, db_factory):
    db = db_factory()
    try:
        await scrape_service.enqueue_scrape(influencer_id, db, db_factory)
    finally:
        db.close()


@router.post("/instagram")
async def discover_instagram(
    background_tasks: BackgroundTasks,
    auto_add: bool = Query(False, description="Immediately create + scrape discovered usernames"),
    extra_hashtags: Optional[str] = Query(None, description="Comma-separated extra hashtags to search"),
    db: Session = Depends(get_db),
):
    """
    Search popular Tunisian Instagram hashtags and return discovered usernames.

    - Without `auto_add`: returns the list of new usernames (preview only).
    - With `auto_add=true`: creates Influencer records for new usernames and queues scrapes.
    """
    extra = [h.strip().lstrip("#") for h in extra_hashtags.split(",")] if extra_hashtags else None
    usernames = await discover_tunisian_usernames(extra_hashtags=extra)

    # Filter out usernames already in the DB
    existing = {
        row.username
        for row in db.query(Influencer.username).filter(Influencer.platform == "instagram").all()
    }
    new_usernames = [u for u in usernames if u not in existing]

    if not auto_add:
        return {
            "found": len(new_usernames),
            "usernames": new_usernames,
            "note": "Pass ?auto_add=true to create these influencers and queue scrapes.",
        }

    # Auto-add: create records and enqueue scrapes
    from ..database import SessionLocal

    created_usernames: List[str] = []
    for username in new_usernames:
        already = (
            db.query(Influencer)
            .filter(Influencer.platform == "instagram", Influencer.username == username)
            .first()
        )
        if already:
            continue
        inf = Influencer(platform="instagram", username=username)
        db.add(inf)
        db.commit()
        db.refresh(inf)
        background_tasks.add_task(_enqueue_bg, inf.id, SessionLocal)
        created_usernames.append(username)

    return {
        "created": len(created_usernames),
        "queued_scrapes": len(created_usernames),
        "usernames": created_usernames,
    }
