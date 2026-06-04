import csv
import io
import json
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.influencer import Influencer, ScrapeJob
from ..schemas.influencer import (
    InfluencerCreate,
    InfluencerBulkCreate,
    InfluencerOut,
    InfluencerDetail,
    InfluencerListResponse,
    LinkedInfluencerOut,
    SponsoredPostOut,
    PostOut,
)
from ..services import scrape_service
from ..services.sponsorship_detector import detect_sponsorships

router = APIRouter(prefix="/api/influencers", tags=["influencers"])


def _extract_handle(link: Optional[str]) -> Optional[str]:
    if not link:
        return None
    link = link.strip().rstrip("/")
    m = re.search(r"(?:instagram|tiktok)\.com/@?([^/?#]+)", link)
    if m:
        return m.group(1).lstrip("@")
    if "/" not in link and "." not in link:
        return link.lstrip("@")
    return None


def _get_db_factory(db: Session = Depends(get_db)):
    from ..database import SessionLocal
    return SessionLocal


def _build_influencer_query(
    db: Session,
    platform: Optional[str] = None,
    min_followers: Optional[int] = None,
    max_followers: Optional[int] = None,
    min_er: Optional[float] = None,
    max_er: Optional[float] = None,
    search: Optional[str] = None,
    niche: Optional[str] = None,
):
    """Shared query builder for list and export endpoints."""
    q = db.query(Influencer)
    if platform:
        q = q.filter(Influencer.platform == platform.lower())
    if min_followers is not None:
        q = q.filter(Influencer.followers >= min_followers)
    if max_followers is not None:
        q = q.filter(Influencer.followers <= max_followers)
    if min_er is not None:
        q = q.filter(Influencer.engagement_rate >= min_er)
    if max_er is not None:
        q = q.filter(Influencer.engagement_rate <= max_er)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            or_(
                Influencer.username.ilike(pattern),
                Influencer.display_name.ilike(pattern),
            )
        )
    if niche:
        # inferred_niches is a JSON TEXT column — use LIKE for SQLite compatibility
        q = q.filter(Influencer.inferred_niches.ilike(f'%"{niche}"%'))
    return q


@router.get("", response_model=InfluencerListResponse)
def list_influencers(
    platform: Optional[str] = Query(None),
    min_followers: Optional[int] = Query(None),
    max_followers: Optional[int] = Query(None),
    min_er: Optional[float] = Query(None),
    max_er: Optional[float] = Query(None),
    sort_by: str = Query("followers"),
    order: str = Query("desc"),
    search: Optional[str] = Query(None),
    niche: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = _build_influencer_query(db, platform, min_followers, max_followers, min_er, max_er, search, niche)

    valid_sorts = {"followers", "engagement_rate", "avg_likes", "last_scraped_at", "created_at"}
    sort_col = getattr(Influencer, sort_by if sort_by in valid_sorts else "followers")
    q = q.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()

    return InfluencerListResponse(
        data=[InfluencerOut.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/export")
def export_influencers_csv(
    platform: Optional[str] = Query(None),
    min_followers: Optional[int] = Query(None),
    max_followers: Optional[int] = Query(None),
    min_er: Optional[float] = Query(None),
    max_er: Optional[float] = Query(None),
    sort_by: str = Query("followers"),
    order: str = Query("desc"),
    search: Optional[str] = Query(None),
    niche: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Export filtered influencer list as a CSV file."""
    q = _build_influencer_query(db, platform, min_followers, max_followers, min_er, max_er, search, niche)

    valid_sorts = {"followers", "engagement_rate", "avg_likes", "last_scraped_at", "created_at"}
    sort_col = getattr(Influencer, sort_by if sort_by in valid_sorts else "followers")
    q = q.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

    items = q.all()

    def generate():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "platform", "username", "display_name", "followers", "following",
            "engagement_rate", "avg_likes", "avg_comments", "posts_per_week",
            "total_posts", "is_verified", "niches", "bio", "last_scraped_at",
        ])
        yield output.getvalue()

        for inf in items:
            output = io.StringIO()
            writer = csv.writer(output)
            niches = inf.inferred_niches if isinstance(inf.inferred_niches, str) else json.dumps(inf.inferred_niches or [])
            try:
                niches_list = json.loads(niches) if isinstance(niches, str) else niches
                niches_str = ", ".join(niches_list)
            except Exception:
                niches_str = ""
            writer.writerow([
                inf.platform, inf.username, inf.display_name or "",
                inf.followers, inf.following,
                round(inf.engagement_rate or 0, 2),
                round(inf.avg_likes or 0, 1),
                round(inf.avg_comments or 0, 1),
                round(inf.posts_per_week or 0, 2),
                inf.total_posts, inf.is_verified,
                niches_str, (inf.bio or "").replace("\n", " "),
                inf.last_scraped_at or "",
            ])
            yield output.getvalue()

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=influencers.csv"},
    )


@router.post("", response_model=InfluencerOut, status_code=201)
async def add_influencer(
    body: InfluencerCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Influencer)
        .filter_by(platform=body.platform, username=body.username)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Influencer already exists")

    influencer = Influencer(platform=body.platform, username=body.username)
    db.add(influencer)
    db.commit()
    db.refresh(influencer)

    from ..database import SessionLocal
    background_tasks.add_task(_trigger_scrape_bg, influencer.id, SessionLocal)
    return InfluencerOut.model_validate(influencer)


async def _trigger_scrape_bg(influencer_id: int, db_factory):
    db = db_factory()
    try:
        await scrape_service.enqueue_scrape(influencer_id, db, db_factory)
    finally:
        db.close()


@router.post("/bulk", response_model=list[InfluencerOut], status_code=201)
async def bulk_add_influencers(
    body: InfluencerBulkCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    created = []
    from ..database import SessionLocal

    for item in body.influencers:
        existing = (
            db.query(Influencer)
            .filter_by(platform=item.platform, username=item.username)
            .first()
        )
        if existing:
            continue
        influencer = Influencer(platform=item.platform, username=item.username)
        db.add(influencer)
        db.commit()
        db.refresh(influencer)
        created.append(influencer)
        background_tasks.add_task(_trigger_scrape_bg, influencer.id, SessionLocal)

    return [InfluencerOut.model_validate(i) for i in created]


@router.delete("", status_code=204)
def delete_all_influencers(db: Session = Depends(get_db)):
    db.query(ScrapeJob).delete()
    db.query(Influencer).delete()
    db.commit()


@router.post("/csv", status_code=201)
async def csv_upload(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    # Auto-detect delimiter: try semicolon first, fall back to comma
    sample = text[:2048]
    delimiter = ";" if sample.count(";") >= sample.count(",") else ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]

    if "username" not in fieldnames:
        raise HTTPException(status_code=422, detail="CSV must have a 'username' column (comma or semicolon separated)")

    has_platform_col = "platform" in fieldnames

    from ..database import SessionLocal

    added: list[dict] = []
    skipped: list[str] = []
    invalid: list[str] = []

    for row in reader:
        normalized = {k.strip().lower(): v.strip() for k, v in row.items() if v}
        username = normalized.get("username", "").lstrip("@").strip()
        # Strip URL query params (e.g. "?g=5" appended to some handles)
        username = username.split("?")[0].strip()
        if not username:
            continue

        platform = normalized.get("platform", "instagram").lower() if has_platform_col else "instagram"
        if platform not in ("instagram", "tiktok"):
            invalid.append(f"{username} (unknown platform '{platform}')")
            continue

        existing = db.query(Influencer).filter_by(platform=platform, username=username).first()
        if existing:
            skipped.append(username)
            continue

        influencer = Influencer(platform=platform, username=username)
        db.add(influencer)
        db.commit()
        db.refresh(influencer)
        added.append({"id": influencer.id, "platform": platform, "username": username})
        background_tasks.add_task(_trigger_scrape_bg, influencer.id, SessionLocal)

    return {"added": len(added), "skipped": len(skipped), "invalid": len(invalid), "items": added}


@router.get("/{influencer_id}", response_model=InfluencerDetail)
def get_influencer(influencer_id: int, db: Session = Depends(get_db)):
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    from ..models.influencer import Post
    from ..models.brand import Brand

    posts = (
        db.query(Post)
        .filter_by(influencer_id=influencer_id)
        .order_by(Post.posted_at.desc().nullslast())
        .limit(6)
        .all()
    )

    detail = InfluencerDetail.model_validate(influencer)
    detail.posts = [PostOut.model_validate(p) for p in posts]

    # Linked cross-platform account
    if influencer.linked_influencer_id:
        linked = db.get(Influencer, influencer.linked_influencer_id)
        if linked:
            detail.linked_influencer = LinkedInfluencerOut.model_validate(linked)

    # Sponsored post detection (compute on-read from all posts, not just top 6)
    all_posts = (
        db.query(Post)
        .filter_by(influencer_id=influencer_id)
        .all()
    )
    brands = db.query(Brand).all()
    brand_names = [b.name for b in brands]
    brand_handles = []
    for b in brands:
        for link in (b.ig_link, b.tt_link):
            h = _extract_handle(link)
            if h:
                brand_handles.append(h)

    raw_sponsorships = detect_sponsorships(all_posts, brand_names, brand_handles)
    detail.detected_sponsorships = [SponsoredPostOut(**s) for s in raw_sponsorships]

    return detail


@router.delete("/{influencer_id}", status_code=204)
def delete_influencer(influencer_id: int, db: Session = Depends(get_db)):
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    db.delete(influencer)
    db.commit()


# --- Multi-platform linking ---

from pydantic import BaseModel as _BaseModel


class _LinkBody(_BaseModel):
    linked_id: int


@router.post("/{influencer_id}/link", response_model=InfluencerDetail)
def link_influencer(influencer_id: int, body: _LinkBody, db: Session = Depends(get_db)):
    """Manually link two influencer profiles (e.g. IG ↔ TikTok). Bidirectional."""
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")
    linked = db.get(Influencer, body.linked_id)
    if not linked:
        raise HTTPException(status_code=404, detail="Linked influencer not found")
    if influencer_id == body.linked_id:
        raise HTTPException(status_code=400, detail="Cannot link an influencer to itself")
    if influencer.platform == linked.platform:
        raise HTTPException(status_code=400, detail="Both influencers are on the same platform")

    # Clear any existing links first (both sides)
    if influencer.linked_influencer_id:
        old_link = db.get(Influencer, influencer.linked_influencer_id)
        if old_link and old_link.linked_influencer_id == influencer_id:
            old_link.linked_influencer_id = None
    if linked.linked_influencer_id:
        old_link2 = db.get(Influencer, linked.linked_influencer_id)
        if old_link2 and old_link2.linked_influencer_id == body.linked_id:
            old_link2.linked_influencer_id = None

    influencer.linked_influencer_id = body.linked_id
    linked.linked_influencer_id = influencer_id
    db.commit()

    return get_influencer(influencer_id, db)


@router.delete("/{influencer_id}/link", status_code=204)
def unlink_influencer(influencer_id: int, db: Session = Depends(get_db)):
    """Remove the cross-platform link. Clears both sides."""
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    if influencer.linked_influencer_id:
        other = db.get(Influencer, influencer.linked_influencer_id)
        if other and other.linked_influencer_id == influencer_id:
            other.linked_influencer_id = None
    influencer.linked_influencer_id = None
    db.commit()
