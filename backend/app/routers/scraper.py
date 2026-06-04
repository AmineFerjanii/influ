from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db, SessionLocal
from ..models.influencer import Influencer, ScrapeJob
from ..schemas.influencer import ScrapeResponse, ScrapeJobOut
from ..services import scrape_service
from ..services.refresh_scheduler import _refresh_all

router = APIRouter(prefix="/api/scrape", tags=["scraper"])


@router.post("/{influencer_id}", response_model=ScrapeResponse)
async def trigger_scrape(
    influencer_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    influencer = db.get(Influencer, influencer_id)
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    from ..database import SessionLocal
    job = await scrape_service.enqueue_scrape(influencer_id, db, SessionLocal)

    return ScrapeResponse(
        job_id=job.id,
        influencer_id=influencer_id,
        status=job.status,
    )


@router.get("/status/{influencer_id}", response_model=ScrapeJobOut)
def get_scrape_status(influencer_id: int, db: Session = Depends(get_db)):
    job = (
        db.query(ScrapeJob)
        .filter_by(influencer_id=influencer_id)
        .order_by(ScrapeJob.triggered_at.desc())
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="No scrape job found for this influencer")
    return ScrapeJobOut.model_validate(job)


@router.get("/jobs", response_model=list[ScrapeJobOut])
def list_recent_jobs(limit: int = 20, db: Session = Depends(get_db)):
    jobs = (
        db.query(ScrapeJob)
        .order_by(ScrapeJob.triggered_at.desc())
        .limit(limit)
        .all()
    )
    return [ScrapeJobOut.model_validate(j) for j in jobs]


@router.post("/refresh-all")
async def trigger_full_refresh(background_tasks: BackgroundTasks):
    """Manually trigger a progressive refresh of all successfully-scraped influencers."""
    background_tasks.add_task(_refresh_all)
    return {"message": "Full refresh started — 5 influencers every 5 minutes"}
