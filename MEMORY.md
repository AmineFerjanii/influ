# Influencer Platform — Full Project Knowledge Transfer

> This document captures the complete history, design decisions, architecture, and current
> state of the platform. It is intended for onboarding, handoff, or continuing work in a
> new session with no prior context.

---

## 1. Project Goal

Build a **locally-runnable** influencer discovery and KPI tracking tool for Tunisian
influencers on Instagram and TikTok. The benchmark is Modash (marketer.modash.io).

- **No paid APIs.** Everything is scraped from public profile pages.
- **Fully local.** SQLite database, no cloud services required.
- **Primary use case:** Discover influencers, view KPIs, filter by platform/followers/
  engagement rate, and eventually match influencers to brand campaigns.

---

## 2. Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI 0.115 + Uvicorn |
| Database | SQLite (WAL mode) via SQLAlchemy 2.0 |
| Data validation | Pydantic 2.8 |
| Instagram scraper | httpx (Instagram mobile API) |
| TikTok scraper | Playwright 1.47 + playwright-stealth + httpx fallback |
| Frontend | React 18 + TypeScript 5 + Vite 5 |
| State (server) | TanStack React Query v5 |
| State (UI filters) | Zustand 4 |
| HTTP client | Axios |
| UI components | Radix UI (Dialog, Slider, Select, Toast) |
| Styling | Tailwind CSS 3 |
| Icons | Lucide React |

---

## 3. Build History

### Phase 5 — Category Filter + Export Shortlist (complete)
Implemented two features requested by Mayssen Ghalloub (Mmediahub):
- **Category filter** — Sidebar chip buttons for all 12 inferred niches. Selecting a chip filters the grid instantly. Implemented as a `niche` query param on the list + export endpoints using `ILIKE '%"<niche>"%'` on the JSON TEXT column — no DB migration needed.
- **Export shortlist** — "Export" button in TopBar downloads the current filtered + sorted view as `influencers.csv` (14 columns). Backend streams via `StreamingResponse`; frontend triggers download via `window.location.href`. The `/export` route is declared before `/{influencer_id}` in the router to avoid path collision.
- Remaining requests from that feedback: multi-platform detection (moderate), brand collaboration history detection (moderate), audience demographics + fake followers (blocked — requires paid API).

### Phase 1 — KPI Tracking (complete)
Built from scratch. Key features:
- Add influencers by username (Instagram or TikTok)
- Background async scrape queue (serial, prevents SQLite write conflicts)
- KPI display: followers, avg likes, avg comments, engagement rate, posts/week
- Sidebar filters: platform, follower range, ER range, free-text search, sort
- InfluencerCard grid with color-coded ER badges
- InfluencerModal with KPI row + top 6 post grid
- Add Influencer modal → auto-triggers scrape on creation
- Scrape polling: POST scrape → job_id → poll every 3s → React Query cache invalidation

### Phase 4 — CSV Import & Bulk Scraping (complete)
- **CSV upload endpoint**: `POST /api/influencers/csv` — multipart, auto-detects `,` or `;` delimiter, strips URL junk from handles, skips duplicates, returns summary stats
- **Delete all endpoint**: `DELETE /api/influencers` — wipes all influencers + scrape jobs
- **AddInfluencerModal tabs**: Manual (single handle) + CSV Upload (file picker with result summary: added / skipped / invalid counts)
- **TopBar "Clear All" button**: appears only when influencers exist; destructive confirm dialog
- **Standalone scraper** (`backend/scrape_csv.py`): reads CSV, upserts directly to SQLite, skips already-scraped handles, **auto-retries on Instagram 401 rate limit** (waits 5 min, up to 10 retries per handle) — never stops mid-run
- First real import: `Influencer CSV.csv` — 126 unique handles, 121 scraped successfully, 6 private/deleted (404)

### Phase 3 — Brand Matching (complete)
Added a full Brands section alongside the Influencers grid:
- **Brand model** — `brands` + `collaborations` tables. Brand stores name, description, IG/TikTok profile links, inferred platform, budget tier, min ER, niche categories.
- **Platform auto-inference** — `platform` is derived from which links are set (IG only → instagram, TikTok only → tiktok, both → both, neither → both). Never stored manually.
- **IG profile picture** — `POST /api/brands/{id}/fetch-ig` calls the existing Instagram mobile API scraper, stores the profile pic URL. Called fire-and-forget after brand creation if an IG link is provided.
- **Matching algorithm** — 0–100 score: niche overlap (40 pts) + follower tier match (30 pts) + ER threshold (30 pts). Partial credit for one-tier-off follower counts and ER within 50% of threshold.
- **Collaboration pipeline** — per brand–influencer pair: Potential → Contacted → In Progress → Done. Status editable in BrandModal's Pipeline tab.
- **TopBar tab toggle** — `useViewStore` (Zustand) switches `activeView: 'influencers' | 'brands'`. Sidebar hidden in brands view.
- **Critical bug fixed** — `MatchResult.model_validate(orm_obj)` crashes (match_score is required but not on ORM). Must convert via `InfluencerOut.model_validate(orm).model_dump()` first.

### Phase 2 — Rich Analytics (complete)
Extended the platform with Modash-style analytics:
- **Popular Hashtags** — extracted from post captions via `Counter(re.findall(#\w+))`
- **Popular Mentions** — extracted from post captions via `Counter(re.findall(@\w+))`
- **Niche Inference** — keyword match on bio + hashtags, 12 categories, top 3 returned
- **Media Type Breakdown** — photo_count / video_count from `__typename` per post
- **Estimated Reach** — `followers × 0.35` (industry average organic reach rate)
- **Estimated Impressions** — `followers × 0.50`
- **Post-level data** — caption, media_type, view_count now stored and returned
- **Audience Data** — explicitly shown as "locked" (requires Instagram Business API + consent)

---

## 4. Scraper Design Decisions

### Instagram: Why not Instaloader?
Instaloader uses Instagram's old GraphQL endpoint (`/graphql/query`), which started returning
403 for unauthenticated requests. Switched to the **Instagram mobile API**:

```
GET https://i.instagram.com/api/v1/users/web_profile_info/?username={username}
```

Headers required:
```
User-Agent: Instagram 219.0.0.12.117 Android (33/13; 420dpi; ...)
x-ig-app-id: 936619743392459
Accept-Language: en-US,en;q=0.9
origin: https://www.instagram.com
referer: https://www.instagram.com/
```

This endpoint returns the full profile JSON including the last ~12 posts with captions,
`__typename` (GraphImage/GraphVideo/GraphSidecar), `video_view_count`, likes, comments.
No authentication required for public profiles.

### TikTok: Playwright + Stealth
TikTok's web app embeds all profile data in a `<script>` tag as
`__UNIVERSAL_DATA_FOR_REHYDRATION__`. Playwright (headless Chromium) loads the page and
extracts this JSON blob.

**Critical stealth API** (wrong versions cause ImportError or TypeError):
```python
from playwright_stealth import Stealth
await Stealth().apply_stealth_async(page)   # correct
# NOT: stealth_async(page)                  # ImportError
# NOT: stealth(page)                        # TypeError (sync function)
```

Headless mode must be `--headless=new` (the legacy headless is more detectable).

**TikTok per-video data:** The `item_list` API requires authentication and returns an empty
body even with cookies in headless mode. Solution: use `heartCount / videoCount` as
`avg_likes` estimate. `has_comments_data = False` is set so the UI shows "N/A" for comments
and annotates ER as likes-only.

### Image Proxy: Why needed?
Instagram CDN (fbcdn.net, cdninstagram.com) and TikTok CDN serve images with CORS headers
that block browser requests from localhost. The backend acts as a proxy:

```
GET /api/proxy-image?url=<encoded_cdn_url>
```

The frontend `proxyImage()` utility in `src/utils/formatters.ts` automatically rewrites any
CDN URL to go through this endpoint. Applied on all avatar images, post thumbnails.

---

## 5. Brand & Collaboration Schema

### `brands`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | VARCHAR(200) | UNIQUE |
| description | TEXT | |
| ig_link | TEXT | Full Instagram URL |
| tt_link | TEXT | Full TikTok URL |
| profile_pic_url | TEXT | Fetched via fetch-ig endpoint |
| categories | TEXT | JSON list of niche strings |
| platform | VARCHAR(20) | Auto-computed from links: instagram/tiktok/both |
| budget_tier | VARCHAR(20) | nano/micro/macro/mega |
| min_er | REAL | Min ER % required, default 0 |
| created_at / updated_at | DATETIME | |

### `collaborations`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| brand_id | FK → brands CASCADE | |
| influencer_id | FK → influencers CASCADE | |
| status | VARCHAR(20) | potential/contacted/in_progress/done |
| notes | TEXT | |
| UNIQUE(brand_id, influencer_id) | | |

---

## 6. Influencer Database Schema

### `influencers`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | auto-increment |
| platform | VARCHAR(20) | 'instagram' or 'tiktok' |
| username | VARCHAR(100) | |
| display_name | VARCHAR(200) | |
| profile_pic_url | TEXT | CDN URL |
| bio | TEXT | |
| followers | INTEGER | |
| following | INTEGER | |
| total_posts | INTEGER | |
| is_verified | BOOLEAN | |
| avg_likes | FLOAT | |
| avg_comments | FLOAT | |
| engagement_rate | FLOAT | % |
| posts_per_week | FLOAT | |
| has_comments_data | BOOLEAN | False for TikTok |
| top_hashtags | TEXT | JSON: `[{"tag": "#fashion", "count": 8}]` |
| top_mentions | TEXT | JSON: `[{"mention": "@brand", "count": 3}]` |
| inferred_niches | TEXT | JSON: `["Fashion", "Travel"]` |
| estimated_reach | REAL | followers × 0.35 |
| estimated_impressions | REAL | followers × 0.50 |
| photo_count | INTEGER | of last scraped posts |
| video_count | INTEGER | of last scraped posts |
| last_scraped_at | DATETIME | |
| scrape_status | VARCHAR(20) | pending/scraping/success/error |
| scrape_error | TEXT | last error message |
| created_at | DATETIME | |
| updated_at | DATETIME | |

Constraints: UNIQUE(platform, username), CHECK platform IN ('instagram','tiktok')

### `posts`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| influencer_id | INTEGER FK | CASCADE DELETE |
| post_id | VARCHAR(200) | shortcode (IG) or video ID |
| thumbnail_url | TEXT | CDN URL |
| local_thumbnail | TEXT | cached path if downloaded |
| post_url | TEXT | |
| likes | INTEGER | |
| comments | INTEGER | |
| posted_at | DATETIME | |
| is_video | BOOLEAN | |
| caption | TEXT | full caption text |
| media_type | TEXT | photo / video / carousel |
| view_count | INTEGER | video views (0 for photos) |
| created_at | DATETIME | |

Constraints: UNIQUE(influencer_id, post_id). Max 30 posts kept per influencer.

### `scrape_jobs`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| influencer_id | INTEGER FK | CASCADE DELETE |
| status | VARCHAR(20) | queued/running/success/failed |
| triggered_at | DATETIME | |
| completed_at | DATETIME | |
| error_message | TEXT | |

---

## 6. API Endpoint Reference

### Brands
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/brands` | List all brands |
| POST | `/api/brands` | Create brand (platform auto-computed from links) |
| GET | `/api/brands/{id}` | Brand detail + collaborations |
| PATCH | `/api/brands/{id}` | Update brand fields |
| DELETE | `/api/brands/{id}` | Delete brand + all collaborations |
| GET | `/api/brands/{id}/matches` | Ranked influencer match list (score desc) |
| POST | `/api/brands/{id}/fetch-ig` | Fetch IG profile pic → store in profile_pic_url |
| POST | `/api/brands/{id}/collaborations` | Add influencer to pipeline |
| PATCH | `/api/brands/{id}/collaborations/{inf_id}` | Update collab status/notes |
| DELETE | `/api/brands/{id}/collaborations/{inf_id}` | Remove from pipeline |

### Influencers
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/influencers` | List with filters + pagination |
| POST | `/api/influencers` | Add one influencer (triggers auto-scrape) |
| POST | `/api/influencers/bulk` | Seed from `backend/seed/influencers.json` |
| POST | `/api/influencers/csv` | Bulk import from uploaded CSV file |
| DELETE | `/api/influencers` | Delete ALL influencers + scrape jobs |
| GET | `/api/influencers/{id}` | Full detail + posts |
| DELETE | `/api/influencers/{id}` | Remove influencer + posts |

**GET /api/influencers query params:**
- `platform`: instagram | tiktok
- `min_followers`, `max_followers`: integer bounds
- `min_er`, `max_er`: float % bounds
- `search`: partial match on username or display_name
- `niche`: one of the 12 niche categories (exact string match inside JSON column)
- `sort_by`: followers | engagement_rate | avg_likes | posts_per_week | created_at
- `order`: asc | desc
- `page`, `page_size`

**GET /api/influencers/export** — accepts same params as list (except page/page_size), returns CSV StreamingResponse. Route declared before `/{influencer_id}` to avoid path collision.

### Scraping
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/scrape/{influencer_id}` | Queue a scrape job → returns `{job_id, status}` |
| GET | `/api/scrape/status/{influencer_id}` | Latest job status for that influencer |

### Utility
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/proxy-image?url=<url>` | Proxy CDN image to bypass CORS |
| GET | `/api/health` | `{"status": "ok"}` |

---

## 7. Frontend Architecture

### State Model
```
Zustand (filterStore)
  platform: 'instagram' | 'tiktok' | ''
  minFollowers, maxFollowers: number | ''
  minEr, maxEr: number | ''
  sortBy: string
  order: 'asc' | 'desc'
  search: string
  niche: string          ← added Phase 5
  page: number

React Query
  useInfluencers()       → GET /api/influencers with filter params
  useInfluencer(id)      → GET /api/influencers/{id}
  useScrape(id)          → POST /api/scrape/{id}, then polls /api/scrape/status/{id} every 3s
  useBrands()            → GET /api/brands
  useBrandMatches(id)    → GET /api/brands/{id}/matches (enabled only when id != null)
  useCollaboration(brandId) → mutations: add / update / remove collaborations

Zustand
  useFilterStore   → platform, followers range, ER range, search, sort, page (influencer filters)
  useViewStore     → activeView: 'influencers' | 'brands'
```

### Component Tree
```
App
├── TopBar
│   ├── View toggle (Influencers | Brands) → useViewStore
│   ├── Search input (influencers view only) → filterStore.search
│   └── Add button (label changes per view)
├── Sidebar (influencers view only)
│   ├── Platform radio buttons
│   ├── Follower range slider (Radix Slider)
│   ├── ER range slider
│   └── Sort select
├── InfluencerGrid (activeView === 'influencers')
│   ├── InfluencerCard (×N)
│   │   ├── NicheTagList (inferred_niches chips)
│   │   └── KPI summary row
│   └── InfluencerModal (Radix Dialog)
│       ├── Profile header + bio
│       ├── KPI badge row (7 metrics)
│       ├── PostGrid (top 6 posts)
│       ├── Estimated Performance section
│       └── Creator Intelligence section (2×2 grid)
│           ├── HashtagMentionPanel (hashtags + mentions)
│           ├── NicheTagList (creator interests)
│           └── AudienceLockedPanel (demographics placeholder)
└── BrandGrid (activeView === 'brands')
    ├── BrandCard (×N) — avatar (IG pic), name, IG/TikTok badges, tier, niche chips
    └── BrandModal (Radix Dialog)
        ├── Header: avatar, name, description, IG/TikTok links, tier, min ER, niche chips
        ├── "Matched Influencers" tab
        │   └── MatchedInfluencerRow (×N) — avatar, name, score bar, reasons, Add button
        └── "Pipeline" tab
            └── PipelineRow (×N) — name, status dropdown, remove button
```

### Key Utilities (`src/utils/formatters.ts`)
- `formatNumber(n)` — 1234567 → "1.2M", 12345 → "12.3K"
- `formatEngagementRate(er)` — "3.45%"
- `erColor(er)` — returns Tailwind classes: gray <1%, yellow 1–3%, green 3–6%, blue >6%
- `erLabel(er)` — "Low" / "Average" / "Good" / "Excellent"
- `proxyImage(url)` — rewrites CDN URLs to `/api/proxy-image?url=...`
- `timeAgo(dateStr)` — "3 days ago", "just now"

---

## 8. Brand Matching Details

File: `backend/app/services/brand_matcher.py`

### Scoring (0–100)
| Dimension | Max | Logic |
|-----------|-----|-------|
| Niche overlap | 40 | `len(matched) / len(brand.categories) × 40`; 0 if brand has no categories → full 40 pts |
| Follower tier | 30 | +30 exact tier match; +15 if one tier away; 0 otherwise |
| Engagement rate | 30 | +30 if ER ≥ min_er; proportional partial if ER ≥ min_er×0.5; if min_er=0 → full 30 pts |

Budget tier → follower ranges:
- `nano`: 0 – 9,999
- `micro`: 10,000 – 99,999
- `macro`: 100,000 – 999,999
- `mega`: 1,000,000+

### Platform Filtering
If `brand.platform != 'both'`, only influencers on that platform are scored.
Platform is auto-derived from ig_link / tt_link (see Brand model notes).

### MatchResult Serialization (critical gotcha)
The `/matches` endpoint must construct MatchResult from a dict, not directly from the ORM object:
```python
# Correct pattern
inf_dict = InfluencerOut.model_validate(orm_influencer).model_dump()
inf_dict["match_score"] = score
inf_dict["match_reasons"] = reasons
inf_dict["collaboration"] = collab_or_none
MatchResult.model_validate(inf_dict)
```
Direct `MatchResult.model_validate(orm_influencer)` will raise a Pydantic validation error
because `match_score: float` (required) is not on the ORM object.

---

## 9. Niche Inference Details

File: `backend/app/services/niche_service.py`

Text searched: `bio.lower() + " " + " ".join(hashtag["tag"].lower() for hashtag in top_hashtags)`

12 categories and their keyword lists:
| Category | Sample Keywords |
|----------|----------------|
| Fashion | fashion, style, outfit, ootd, clothing, wear, look, mode, tenue, moda |
| Beauty | beauty, makeup, skincare, cosmetics, lipstick, glam, sephora, beauté |
| Food & Beverage | food, recipe, cook, baking, restaurant, eat, cuisine, nourriture |
| Travel | travel, explore, adventure, wanderlust, trip, destination, voyage |
| Fitness | fitness, gym, workout, training, sport, health, yoga, run, musculation |
| Lifestyle | lifestyle, life, daily, vlog, family, home, living, vie, quotidien |
| Tech | tech, technology, coding, software, gaming, digital, dev, informatique |
| Business | entrepreneur, business, startup, marketing, finance, invest, affaires |
| Art & Culture | art, design, photography, creative, culture, museum, photo, artiste |
| Entertainment | comedy, humor, music, dance, entertainment, fun, comédie, musique |
| Education | education, learn, knowledge, teacher, school, cours, apprendre |
| Environment | eco, green, sustainable, environment, nature, climate, plastic, plastique |

Accuracy notes:
- Tunisian Arabic is not covered yet
- Niche is only as good as the captions/bio language
- Re-runs on every scrape, so adding keywords takes effect on next refresh

---

## 9. What Is and Isn't Feasible Without Official API

| Feature | Status | Reason |
|---------|--------|--------|
| Follower count | ✅ Available | Public profile |
| Avg likes | ✅ Available | Per-post data (IG) / aggregate estimate (TikTok) |
| Avg comments | ✅ IG / ❌ TikTok | TikTok requires auth for per-video comment counts |
| Top hashtags | ✅ Available | Extracted from captions |
| Top mentions | ✅ Available | Extracted from captions |
| Niche inference | ✅ Available | Keyword matching |
| Media type breakdown | ✅ Available | `__typename` from IG API |
| Estimated reach/impressions | ✅ Estimated | Industry average formula |
| Audience gender/age/country | ❌ Not feasible | Instagram Business API + influencer consent |
| Follower interests | ❌ Not feasible | Requires audience-level data |
| Fake followers % | ❌ Not feasible | Requires HypeAuditor or similar paid service |
| Stories data | ❌ Not feasible | Private platform data |

---

## 10. Known Limitations & Workarounds

**Instagram rate limits**
- Unauthenticated: ~10–20 scrapes per session before soft-blocking
- Fix: add `IG_USERNAME` and `IG_PASSWORD` to `.env` (uses session login)
- For bulk imports: use `scrape_csv.py` which auto-waits 5 min and retries on 401 — never needs manual restart

**TikTok bot detection**
- Playwright-stealth significantly reduces detection risk
- If still blocked, the httpx fallback attempts a direct API call
- Headless must be `--headless=new` (legacy mode is more fingerprinted)

**SQLite concurrency**
- SQLite only supports one writer at a time
- The `asyncio.Queue` in `scrape_service.py` serializes all jobs
- Never run multiple uvicorn workers — use a single process

**Python version compatibility**
- Codebase targets Python 3.9+
- Do NOT use `X | Y` union syntax (requires 3.10+) — use `Optional[X]` from `typing`

**CDN image expiry**
- Instagram/TikTok CDN URLs expire after hours/days
- Thumbnails are cached locally to `data/thumbnails/{influencer_id}/{post_id}.jpg`
- Served via FastAPI's StaticFiles mount at `/static/thumbnails/`
- If a cached thumbnail exists, PostGrid prefers it over the CDN URL

---

## 11. Setup Instructions (Verbose)

### Prerequisites
- Python 3.9+
- Node.js 18+
- ~400 MB disk space (Playwright Chromium binary)

### First-time setup
```bash
# Clone / open project root
cd "Influencer Platform"

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium       # Downloads ~130 MB Chromium binary

# Optional: create .env for Instagram credentials
cp .env.example .env              # if it exists, else create manually
# Edit .env with IG_USERNAME, IG_PASSWORD if you have them

# Start backend (SQLite DB auto-created on first run)
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd ../frontend
npm install
npm run dev
# Open http://localhost:5173
```

### Adding influencers
1. Click "Add Influencer" in the UI → enter platform + username → Save
2. Auto-scrape triggers immediately; card shows spinner while scraping
3. Or: seed from JSON — edit `backend/seed/influencers.json` then POST `/api/influencers/bulk`

### Re-scraping
- Click the refresh icon on any card or modal
- Or: `curl -X POST http://localhost:8000/api/scrape/{id}`
- Scrape typically completes in 5–20 seconds for Instagram, 15–40s for TikTok

---

## 12. Potential Next Features (Prioritized)

### Tier 1 — High value, low effort
- [x] **Niche filter in sidebar** — ✅ Done (Phase 5): chip buttons for all 12 categories, `niche` query param, ILIKE on JSON column
- [x] **Export to CSV** — ✅ Done (Phase 5): Export button in TopBar, streams current filtered view, 14 columns
- [ ] **Bulk re-scrape** — "Refresh All" button that queues all influencers
- [ ] **Arabic keyword expansion** for niche inference
- [ ] **Brand sidebar filters** — filter brand grid by tier, platform, niche
- [x] **CSV bulk import** — ✅ Done (Phase 4): upload CSV, auto-detect delimiter, dedup, queue scraping
- [x] **Auto-retry scraper** — ✅ Done (Phase 4): `scrape_csv.py` waits 5 min on 401, retries up to 10×

### Tier 2 — Medium value, medium effort
- [x] **Brand matching** — ✅ Done (Phase 3): brands with IG/TikTok links, scoring 0–100, pipeline tracking
- [ ] **Multi-platform detection** — show if a creator is active on both IG + TikTok; needs manual linking UI or fuzzy username matching across platforms
- [ ] **Brand collaboration detection** — detect sponsored posts from scraped captions (#ad, #sponsored, @brand mentions); surface in influencer modal as "Recent Partnerships"
- [ ] **Campaign tracker** — associate influencers with campaigns, track deliverables + deadlines
- [ ] **Engagement trend** — store historical ER over time, show sparkline
- [ ] **TikTok per-video data** — requires authenticated session via cookie injection
- [ ] **Brand edit modal** — currently brands can only be deleted, not edited in the UI

### Tier 3 — High value, high effort
- [ ] **Audience demographics** — requires Instagram Business API + influencer OAuth consent
- [ ] **Fake follower detection** — integrate HypeAuditor API or build ratio heuristic
- [ ] **AI-powered bio analysis** — use Claude API to classify niche more accurately
- [ ] **Multi-user / team mode** — replace SQLite with PostgreSQL, add auth
