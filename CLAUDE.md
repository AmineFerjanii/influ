# Influencer Platform — Claude Code Context

## What this is
A locally-runnable influencer discovery and KPI tracking platform for Tunisian influencers
on Instagram and TikTok, modeled after Modash. No paid APIs required. Stack: Python FastAPI
+ React (TypeScript) + SQLite.

---

## Setup & Run

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium        # one-time, ~130 MB
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # → http://localhost:5173
```

### Optional: create a `.env` in `backend/` for Instagram credentials
```
IG_USERNAME=your_ig_username
IG_PASSWORD=your_ig_password
```

---

## Key Commands (curl)
```bash
# List all influencers
curl http://localhost:8000/api/influencers

# Trigger re-scrape for influencer ID 1
curl -X POST http://localhost:8000/api/scrape/1

# Poll scrape job status
curl http://localhost:8000/api/scrape/status/1

# Add a new influencer
curl -X POST http://localhost:8000/api/influencers \
  -H "Content-Type: application/json" \
  -d '{"platform": "instagram", "username": "azzaslimene"}'

# Bulk seed from backend/seed/influencers.json
curl -X POST http://localhost:8000/api/influencers/bulk

# Import influencers from a CSV file (comma or semicolon delimited)
curl -X POST http://localhost:8000/api/influencers/csv \
  -F "file=@path/to/influencers.csv"

# Delete ALL influencers (and their scrape jobs)
curl -X DELETE http://localhost:8000/api/influencers
```

## Bulk CSV Scraper (standalone script)
For scraping large batches without hitting the API queue, use `backend/scrape_csv.py`:
```bash
cd backend
source venv/bin/activate
python scrape_csv.py "../Influencer CSV.csv"   # logs to stdout
# or run in background:
nohup python scrape_csv.py "../Influencer CSV.csv" > /tmp/scraper.log 2>&1 &
tail -f /tmp/scraper.log
```
- Auto-detects comma or semicolon delimiter
- Strips URL junk from usernames (e.g. `?g=5`)
- Skips already-scraped influencers (status = success)
- **Auto-retries on 401 rate limit**: waits 5 min, retries up to 10× per handle
- Upserts directly into SQLite (bypasses the API queue)

---

## Architecture

```
backend/app/
  main.py            FastAPI app, CORS, /api/proxy-image endpoint, static file mount
  config.py          Pydantic Settings — reads from .env
  database.py        SQLAlchemy engine (SQLite WAL mode), session factory
  models/
    influencer.py    ORM: Influencer, Post, ScrapeJob
  schemas/
    influencer.py    Pydantic I/O schemas; field_validators parse JSON TEXT columns
  routers/
    influencers.py   CRUD + filter/search/pagination + CSV upload + delete-all endpoints
    scraper.py       POST /api/scrape/{id}, GET /api/scrape/status/{id}
  services/
    scrape_service.py   Async serial job queue, dispatches scrapers, updates DB
    kpi_calculator.py   engagement_rate, avg_likes, avg_comments, posts_per_week
    niche_service.py    Keyword-match bio + hashtags → inferred niches (12 categories)
  scrapers/
    instagram.py     httpx → Instagram mobile API (no auth needed for public profiles)
    tiktok.py        Playwright + playwright-stealth → httpx fallback
  scrape_csv.py      Standalone bulk scraper — reads CSV, upserts DB directly, auto-retries on 401

frontend/src/
  api/client.ts      Axios typed API client (base URL /api)
  store/             Zustand: platform, followers range, ER range, search, niche, sort, page
  hooks/             React Query wrappers — useInfluencers, useInfluencer, useScrape
  components/
    layout/          TopBar (search + Clear All button), Sidebar (filters)
    common/          Badge, KPIBadge, LoadingSpinner, EmptyState
    influencer/      InfluencerCard, InfluencerGrid, InfluencerModal, PostGrid
                     HashtagMentionPanel, NicheTagList, AudienceLockedPanel
                     AddInfluencerModal (Manual tab + CSV Upload tab)
  types/index.ts     All TypeScript interfaces
  utils/formatters.ts  formatNumber, formatEngagementRate, erColor, proxyImage
```

---

## Instagram Scraper
- Endpoint: `https://i.instagram.com/api/v1/users/web_profile_info/?username={username}`
- Headers: Android User-Agent + `x-ig-app-id: 936619743392459`
- No login required for public profiles
- Extracts: followers, bio, posts (caption, media_type from `__typename`, view_count,
  likes, comments, shortcode)
- Aggregates top 10 hashtags and mentions across all post captions via `Counter(re.findall(...))`
- Rate limit: ~10–20 unauthenticated scrapes per session; add credentials to `.env` for more

## TikTok Scraper
- Uses Playwright (headless chromium) + playwright-stealth to bypass bot detection
- Extracts `__UNIVERSAL_DATA_FOR_REHYDRATION__` JSON blob from the page HTML
- Profile path: `__DEFAULT_SCOPE__['webapp.user-detail']['userInfo']`
- Per-video stats unavailable without auth → uses `heartCount / videoCount` as avg_likes
- Falls back to httpx if Playwright fails
- Correct stealth import: `from playwright_stealth import Stealth`
  Usage: `await Stealth().apply_stealth_async(page)`
- Headless mode: `args=["--headless=new"]`

## Image Proxy
- Instagram/TikTok CDN URLs (fbcdn.net, cdninstagram.com, tiktokcdn.com) are CORS-blocked
  in the browser
- Solution: `GET /api/proxy-image?url=<encoded_url>` on the FastAPI backend
- Frontend `proxyImage()` in `utils/formatters.ts` automatically routes CDN URLs through it
- Applied in: InfluencerCard, InfluencerModal, PostGrid

---

## Database: JSON Columns
`Influencer.top_hashtags`, `top_mentions`, `inferred_niches` are stored as TEXT (JSON strings).
Pydantic schemas use `@field_validator(mode="before")` to parse them into Python lists on read.
Never mutate these with raw SQL — always go through the ORM + service layer.

## Niche Inference (12 categories)
`niche_service.py` keyword-matches `bio.lower() + hashtag_text` against:
Fashion, Beauty, Food & Beverage, Travel, Fitness, Lifestyle, Tech, Business,
Art & Culture, Entertainment, Education, Environment.
Returns top 3 by keyword hit count. Re-runs on every scrape.

## KPI Formulas
```
engagement_rate  = (avg_likes + avg_comments) / followers * 100
posts_per_week   = post_count / max(date_span_weeks, 1)
estimated_reach  = followers * 0.35
estimated_impressions = followers * 0.50
```
TikTok: `has_comments_data = False` → ER uses likes only.

---

## Scrape Job Flow
1. `POST /api/scrape/{id}` → creates ScrapeJob (status=queued), returns `job_id`
2. Background `asyncio.Queue` worker picks up job, sets status=running
3. Calls `ig_scraper.scrape_profile()` or `tt_scraper.scrape_profile()`
4. `_update_influencer()` writes all fields, upserts posts, fires thumbnail caching task
5. Job → status=success; frontend polls `/api/scrape/status/{id}` every 3s until done
6. React Query cache invalidated → UI updates

---

## Server Deployment (Agency)

The platform can run on a shared agency server instead of locally on each machine.

### What needs changing before deploying
- **Auth**: No login system exists. Add nginx basic auth at minimum, or a JWT layer.
- **CORS**: Update allowed origins in `backend/app/main.py` (currently hardcoded to `localhost:5173`).
- **Frontend**: Run `npm run build` and serve as static files via nginx.
- **Process manager**: Run uvicorn via systemd (single worker only — never `--workers > 1`).
- **Instagram rate limits**: All agency users share one server IP → limits hit faster; add `IG_USERNAME`/`IG_PASSWORD` in `.env`.
- **SQLite**: Fine for 2–10 concurrent users. Migrate to PostgreSQL for larger teams.

### VPS Cost Estimate (as of May 2026)
| Provider | Spec | Monthly |
|----------|------|---------|
| Hetzner CX22 | 2 vCPU, 4 GB RAM | ~$6–7 |
| DigitalOcean Basic | 2 vCPU, 4 GB RAM | ~$18 |
| AWS Lightsail | 2 vCPU, 4 GB RAM | ~$20 |
| Render.com (managed) | — | ~$25–35 |

**Minimum spec:** 2 GB RAM (Playwright needs ~500 MB per scrape), 20 GB storage.
**Recommended:** Hetzner CX22 (~$6/mo) + nginx + systemd = ~$80–100/year total.
**Other costs:** Domain ~$12/year, SSL free via Let's Encrypt.

---

---

## Brand Section

### Architecture
```
backend/app/
  models/brand.py          ORM: Brand, Collaboration
  schemas/brand.py         Pydantic I/O schemas for brands/collaborations/match results
  services/brand_matcher.py  Scoring engine: rank_matches(), score_influencer()
  routers/brands.py        8 endpoints — CRUD + matching + collaborations

frontend/src/
  store/viewStore.ts        Zustand: activeView 'influencers' | 'brands'
  hooks/
    useBrands.ts            GET /api/brands
    useBrandMatches.ts      GET /api/brands/{id}/matches (enabled only when brand selected)
    useCollaboration.ts     POST/PATCH/DELETE collaborations mutations
  components/brand/
    BrandCard.tsx           Grid card with platform badges, tier, niche chips, avatar
    BrandGrid.tsx           Card grid (same layout as InfluencerGrid)
    AddBrandModal.tsx       Form: name, description, IG link, TikTok link, niches, tier, min ER
    BrandModal.tsx          Detail modal: Matched Influencers tab + Pipeline tab
    MatchedInfluencerRow.tsx  Score bar + match reasons + Add to Pipeline button
```

### Brand Model (`brands` table)
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | VARCHAR(200) | UNIQUE |
| description | TEXT | |
| ig_link | TEXT | Full IG URL — drives profile pic fetch + platform inference |
| tt_link | TEXT | Full TikTok URL — drives platform inference |
| profile_pic_url | TEXT | Fetched from Instagram via `POST /api/brands/{id}/fetch-ig` |
| categories | TEXT | JSON list of niche strings e.g. `["Fashion","Lifestyle"]` |
| platform | VARCHAR(20) | Auto-computed: 'instagram' \| 'tiktok' \| 'both' |
| budget_tier | VARCHAR(20) | 'nano' \| 'micro' \| 'macro' \| 'mega' |
| min_er | REAL | Minimum engagement rate %, default 0 |
| created_at / updated_at | DATETIME | |

**`collaborations` table**
| Column | Type | Notes |
|--------|------|-------|
| brand_id | FK → brands | CASCADE DELETE |
| influencer_id | FK → influencers | CASCADE DELETE |
| status | VARCHAR(20) | 'potential' \| 'contacted' \| 'in_progress' \| 'done' |
| notes | TEXT | |
| UNIQUE(brand_id, influencer_id) | | |

### Platform Auto-Inference
`platform` is computed from links — never set manually:
- IG link only → `'instagram'`
- TikTok link only → `'tiktok'`
- Both links → `'both'`
- Neither → `'both'` (no restriction)

### Brand Matching Algorithm (`brand_matcher.py`)
Scoring (0–100 total):
| Dimension | Max pts | Logic |
|-----------|---------|-------|
| Niche overlap | 40 | `matched_niches / len(brand.categories) × 40` |
| Follower tier | 30 | +30 exact match; +15 one tier away |
| Engagement rate | 30 | +30 if ER ≥ min_er; partial if ER ≥ min_er×0.5 |

Budget tier → follower ranges: nano <10K, micro 10K–100K, macro 100K–1M, mega >1M.
Platform filter applied first: if `brand.platform != 'both'`, only that platform's influencers are scored.

### Brand API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/brands` | List all brands |
| POST | `/api/brands` | Create brand (platform auto-computed) |
| GET | `/api/brands/{id}` | Brand detail + collaborations |
| PATCH | `/api/brands/{id}` | Update brand fields |
| DELETE | `/api/brands/{id}` | Delete brand + collaborations |
| GET | `/api/brands/{id}/matches` | Scored influencer list (desc by score) |
| POST | `/api/brands/{id}/fetch-ig` | Fetch IG profile pic and store in profile_pic_url |
| POST | `/api/brands/{id}/collaborations` | Add influencer to pipeline |
| PATCH | `/api/brands/{id}/collaborations/{inf_id}` | Update status/notes |
| DELETE | `/api/brands/{id}/collaborations/{inf_id}` | Remove from pipeline |

### MatchResult serialization (critical)
`GET /api/brands/{id}/matches` must build MatchResult from a dict, NOT from the ORM object directly:
```python
# CORRECT
inf_dict = InfluencerOut.model_validate(orm_influencer).model_dump()
inf_dict["match_score"] = score
inf_dict["match_reasons"] = reasons
result = MatchResult.model_validate(inf_dict)

# WRONG — crashes with Pydantic validation error (match_score missing)
result = MatchResult.model_validate(orm_influencer)
```

### DB Migration for New Columns
`_migrate_brands_columns()` in `main.py` lifespan runs `ALTER TABLE brands ADD COLUMN`
for any new columns added to the model. Wrapped in try/except so it's idempotent.
Add new brand columns here whenever the Brand model gains fields.

### TopBar Tab Toggle
`useViewStore` (Zustand) controls `activeView: 'influencers' | 'brands'`.
TopBar reads this to show the tab pills and change the "Add" button label.
Sidebar is hidden when `activeView === 'brands'` (brands have no filter sidebar yet).

---

## Influencer API Endpoints (full list)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/influencers` | List with filters + pagination |
| GET | `/api/influencers/export` | Export filtered list as CSV download |
| POST | `/api/influencers` | Add one (auto-scrape triggered) |
| POST | `/api/influencers/bulk` | Seed from `backend/seed/influencers.json` |
| POST | `/api/influencers/csv` | Import from uploaded CSV file (multipart/form-data) |
| DELETE | `/api/influencers` | Delete ALL influencers + scrape jobs |
| GET | `/api/influencers/{id}` | Full detail + posts |
| DELETE | `/api/influencers/{id}` | Remove single influencer |

## CSV Import
- Endpoint: `POST /api/influencers/csv` — multipart upload, field name `file`
- Accepts comma **or** semicolon delimited files (auto-detected)
- Required column: `username`; optional column: `platform` (defaults to `instagram`)
- Strips `@` prefix and URL query params (e.g. `?g=5`) from handles automatically
- Skips duplicates; returns `{ added, skipped, invalid, items }`
- Frontend: "Add Influencer" modal has a **CSV Upload** tab with file picker + result summary

## Clear All (UI)
- TopBar shows a **"Clear All"** red button when influencers exist in the influencer view
- Calls `DELETE /api/influencers` after a confirmation dialog
- Deletes all scrape jobs first (FK constraint), then all influencers

## Category Filter (Sidebar)
- Sidebar has a **Category** section with 12 chip buttons (toggle — one active at a time)
- Categories: Fashion, Beauty, Food & Beverage, Travel, Fitness, Lifestyle, Tech, Business, Art & Culture, Entertainment, Education, Environment
- Filter param: `niche=<category>` on `GET /api/influencers` and `GET /api/influencers/export`
- Backend uses `ILIKE '%"<niche>"%'` on the `inferred_niches` JSON TEXT column (SQLite-safe, no migration needed)
- Store: `niche` + `setNiche()` in `filterStore.ts`; clicking active chip deselects it

## Export Shortlist (TopBar)
- **Export** button appears in TopBar whenever influencers are present (influencer view only)
- Exports the **current filtered + sorted view** — respects platform, niche, followers range, ER range, search, and sort
- Endpoint: `GET /api/influencers/export` → `StreamingResponse` with `Content-Disposition: attachment; filename=influencers.csv`
- 14 columns: platform, username, display_name, followers, following, engagement_rate, avg_likes, avg_comments, posts_per_week, total_posts, is_verified, niches, bio, last_scraped_at
- Frontend: `influencerApi.exportCsv()` in `api/client.ts` triggers download via `window.location.href` (no axios needed — lets browser handle the file)
- Route `/export` is declared before `/{influencer_id}` in the router to avoid path-param collision

## Standalone Bulk Scraper (`backend/scrape_csv.py`)
- Reads a CSV, upserts influencers directly into SQLite (bypasses the API job queue)
- Skips handles already at `scrape_status = success`
- **Auto-retry on 401**: waits `RATE_LIMIT_COOLDOWN = 5 min`, retries up to `RATE_LIMIT_MAX_RETRIES = 10` times per handle before marking as error
- Private/deleted profiles (404) are logged as ✗ and skipped immediately, script continues
- Logs to stdout; run with `nohup … > /tmp/scraper.log 2>&1 &` for background execution

---

## Multi-platform Linking

### How it works
- `linked_influencer_id` (nullable FK → influencers.id) on the `Influencer` model
- **Auto-link**: after a successful scrape, `_try_auto_link()` in `scrape_service.py` checks if the same `username` exists on the other platform with no existing link — if so, links both rows bidirectionally
- **Manual override**: two endpoints in `influencers.py` router let users link/unlink manually

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/influencers/{id}/link` | Body: `{"linked_id": int}` — links both sides; replaces any existing link |
| DELETE | `/api/influencers/{id}/link` | Clears link on both sides |

### Schema / Frontend
- `InfluencerDetail.linked_influencer: Optional[LinkedInfluencerOut]` (lightweight — id, platform, username, followers, ER)
- `LinkedAccountPanel.tsx` in `InfluencerModal.tsx` header: shows linked account chip + unlink button, or search-to-link if unlinked
- Platform constraint: can only link IG ↔ TikTok (same platform blocked at API level)

---

## Sponsored Post Detection

### How it works
Detection runs **on-read** in `GET /api/influencers/{id}` — no extra DB column needed. Scans all stored post captions using three sources:

1. **Disclosure hashtags** (`backend/app/services/sponsorship_detector.py`): `#ad`, `#sponsored`, `#partnership`, `#collab`, `#collaboration`, `#publicite`, `#partenariat`, `#publi`, `#brandpartner`, `#paidpartnership`
2. **Brand names**: cross-references caption text against all `Brand.name` values in the DB (case-insensitive substring match)
3. **@mentions**: extracts `@handles` from captions, matches against brand IG/TikTok handles extracted from `Brand.ig_link` / `Brand.tt_link`

> Note: The official Meta Branded Content API requires approved app credentials — not available without a Meta Business Manager approval flow.

### Schema
```python
class SponsoredPostOut(BaseModel):
    post_id: str
    post_url: Optional[str]
    thumbnail_url: Optional[str]
    matched_tags: List[str]    # e.g. ["#ad"]
    matched_brands: List[str]  # e.g. ["Carrefour", "@carrefourtn"]
    caption_snippet: Optional[str]  # first 120 chars
```
`InfluencerDetail.detected_sponsorships: List[SponsoredPostOut]`

### Frontend
- `SponsorshipPanel.tsx` replaces `AudienceLockedPanel` in the Creator Intelligence 2×2 grid
- Shows count badge, thumbnail + caption snippet + matched tag/brand chips per post
- Empty state: "No sponsored content detected"

---

## Known Limitations & Gotchas
- **Python 3.9 compat**: avoid `X | Y` union syntax in type hints — use `Optional[X]` instead
- **SQLite single-writer**: serial asyncio.Queue prevents write conflicts; never bypass it
- **Instagram rate limits**: ~10–20 unauthenticated scrapes per session; `scrape_csv.py` auto-waits and retries
- **TikTok per-video data**: unavailable in headless; avg_likes is an aggregate estimate
- **Niche inference**: keyword list covers English + French; Tunisian Arabic not yet included
- **CDN URL expiry**: thumbnails cached locally at scrape time to handle expired URLs

## .env Reference
```
DATABASE_URL=sqlite:///./data/influencers.db
THUMBNAILS_DIR=data/thumbnails
IG_USERNAME=
IG_PASSWORD=
IG_MIN_DELAY=8
IG_MAX_DELAY=15
TT_PAGE_WAIT=12
POSTS_PER_PROFILE=30
```
