from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .config import settings
from .database import Base, engine
from .models import influencer as _models  # ensure models are registered
from .models import brand as _brand_models  # ensure brand models are registered
from .routers.influencers import router as influencers_router
from .routers.scraper import router as scraper_router
from .routers.brands import router as brands_router
from .routers.discover import router as discover_router
from .services.scrape_service import start_worker
from .services.refresh_scheduler import start_refresh_scheduler


def _migrate_brands_columns():
    """Add new columns to the brands table if they don't exist yet (SQLite ALTER TABLE)."""
    new_cols = [
        ("ig_link", "TEXT"),
        ("tt_link", "TEXT"),
        ("profile_pic_url", "TEXT"),
    ]
    with engine.connect() as conn:
        for col, col_type in new_cols:
            try:
                conn.execute(text(f"ALTER TABLE brands ADD COLUMN {col} {col_type}"))
                conn.commit()
            except Exception:
                pass  # column already exists


def _migrate_influencer_columns():
    """Add new columns to the influencers table if they don't exist yet."""
    with engine.connect() as conn:
        try:
            conn.execute(text(
                "ALTER TABLE influencers ADD COLUMN linked_influencer_id INTEGER "
                "REFERENCES influencers(id) ON DELETE SET NULL"
            ))
            conn.commit()
        except Exception:
            pass  # column already exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    Base.metadata.create_all(bind=engine)
    # Add any new columns to existing tables
    _migrate_brands_columns()
    _migrate_influencer_columns()
    # Ensure thumbnails dir exists
    Path(settings.thumbnails_dir).mkdir(parents=True, exist_ok=True)
    # Start background scrape worker
    await start_worker()
    # Start monthly refresh scheduler (runs at 02:00 on the 1st of each month)
    await start_refresh_scheduler()
    yield


app = FastAPI(title="Influencer Platform API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.allowed_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(influencers_router)
app.include_router(scraper_router)
app.include_router(brands_router)
app.include_router(discover_router)

# Serve cached thumbnails as static files
thumbnails_path = Path(settings.thumbnails_dir)
thumbnails_path.mkdir(parents=True, exist_ok=True)
app.mount("/static/thumbnails", StaticFiles(directory=str(thumbnails_path)), name="thumbnails")


@app.get("/api/health")
def health():
    return {"status": "ok"}


_PROXY_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    "Referer": "https://www.instagram.com/",
}

_proxy_client = httpx.AsyncClient(timeout=15, follow_redirects=True, headers=_PROXY_HEADERS)


@app.get("/api/proxy-image")
async def proxy_image(url: str = Query(...)):
    """Server-side proxy for CDN images (bypasses browser CORS on Instagram/TikTok CDNs)."""
    allowed = ("fbcdn.net", "cdninstagram.com", "tiktokcdn.com", "tiktok.com", "instagram.com")
    if not any(d in url for d in allowed):
        raise HTTPException(status_code=400, detail="URL not from an allowed CDN")
    try:
        r = await _proxy_client.get(url)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail="CDN fetch failed")
        content_type = r.headers.get("content-type", "image/jpeg")
        return Response(content=r.content, media_type=content_type)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=str(e))
