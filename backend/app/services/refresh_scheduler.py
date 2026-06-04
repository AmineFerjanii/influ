import asyncio
import logging
from datetime import datetime

from ..database import SessionLocal
from ..models.influencer import Influencer
from . import scrape_service

logger = logging.getLogger(__name__)

# Configurable: how many influencers per batch and how long to wait between batches
BATCH_SIZE = 5
BATCH_INTERVAL_SECONDS = 5 * 60  # 5 minutes


def _seconds_until_next_run() -> float:
    """Return seconds until 02:00 on the 1st of next month."""
    now = datetime.now()
    year = now.year + 1 if now.month == 12 else now.year
    month = 1 if now.month == 12 else now.month + 1
    next_run = datetime(year, month, 1, 2, 0, 0)
    return max((next_run - now).total_seconds(), 0)


async def _refresh_all():
    db = SessionLocal()
    try:
        influencer_ids = [
            row.id
            for row in db.query(Influencer.id)
            .filter(Influencer.scrape_status == "success")
            .all()
        ]
    finally:
        db.close()

    total = len(influencer_ids)
    logger.info("Monthly refresh: %d influencers to update", total)

    for batch_start in range(0, total, BATCH_SIZE):
        batch = influencer_ids[batch_start : batch_start + BATCH_SIZE]
        for inf_id in batch:
            db = SessionLocal()
            try:
                await scrape_service.enqueue_scrape(inf_id, db, SessionLocal)
            except Exception as e:
                logger.warning("Could not enqueue influencer %d: %s", inf_id, e)
            finally:
                db.close()

        batch_num = batch_start // BATCH_SIZE + 1
        batches_total = (total + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info("Monthly refresh: batch %d/%d queued", batch_num, batches_total)

        if batch_start + BATCH_SIZE < total:
            await asyncio.sleep(BATCH_INTERVAL_SECONDS)

    logger.info("Monthly refresh: all batches enqueued")


async def start_refresh_scheduler():
    async def _loop():
        while True:
            delay = _seconds_until_next_run()
            logger.info(
                "Monthly refresh scheduler: next run in %.1f hours (1st of next month at 02:00)",
                delay / 3600,
            )
            await asyncio.sleep(delay)
            try:
                await _refresh_all()
            except Exception as e:
                logger.error("Monthly refresh failed: %s", e)

    asyncio.create_task(_loop())
