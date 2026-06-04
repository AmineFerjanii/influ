import json
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.brand import Brand, Collaboration
from ..models.influencer import Influencer
from ..schemas.brand import (
    BrandCreate, BrandUpdate, BrandOut, BrandDetail,
    CollaborationCreate, CollaborationUpdate, CollaborationOut,
    MatchResult,
)
from ..schemas.influencer import InfluencerOut
from ..services.brand_matcher import rank_matches
from ..scrapers.instagram import scrape_profile as ig_scrape


def _platform_from_links(ig_link: Optional[str], tt_link: Optional[str]) -> str:
    """Compute platform filter from which profile links are provided."""
    has_ig = bool(ig_link and ig_link.strip())
    has_tt = bool(tt_link and tt_link.strip())
    if has_ig and has_tt:
        return "both"
    if has_ig:
        return "instagram"
    if has_tt:
        return "tiktok"
    return "both"  # no links = no restriction


def _extract_ig_username(ig_link: str) -> Optional[str]:
    """Extract username from an IG URL or return the string as-is if it's already a username."""
    if not ig_link:
        return None
    ig_link = ig_link.strip().rstrip("/")
    # Handle full URLs
    m = re.search(r"instagram\.com/([^/?#]+)", ig_link)
    if m:
        return m.group(1).lstrip("@")
    # Plain username (no URL)
    if "/" not in ig_link and "." not in ig_link:
        return ig_link.lstrip("@")
    return None

router = APIRouter(prefix="/api/brands", tags=["brands"])


def _brand_out(brand: Brand, db: Session) -> BrandOut:
    count = db.query(Collaboration).filter(Collaboration.brand_id == brand.id).count()
    out = BrandOut.model_validate(brand)
    out.collaboration_count = count
    return out


# --- CRUD ---

@router.get("", response_model=List[BrandOut])
def list_brands(db: Session = Depends(get_db)):
    brands = db.query(Brand).order_by(Brand.created_at.desc()).all()
    return [_brand_out(b, db) for b in brands]


@router.post("", response_model=BrandOut, status_code=201)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)):
    existing = db.query(Brand).filter(Brand.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="A brand with this name already exists")

    brand = Brand(
        name=payload.name,
        description=payload.description,
        ig_link=payload.ig_link,
        tt_link=payload.tt_link,
        categories=json.dumps(payload.categories),
        platform=_platform_from_links(payload.ig_link, payload.tt_link),
        budget_tier=payload.budget_tier,
        min_er=payload.min_er,
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return _brand_out(brand, db)


@router.get("/{brand_id}", response_model=BrandDetail)
def get_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    out = BrandDetail.model_validate(brand)
    out.collaboration_count = len(brand.collaborations)
    return out


@router.patch("/{brand_id}", response_model=BrandOut)
def update_brand(brand_id: int, payload: BrandUpdate, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    if payload.name is not None:
        brand.name = payload.name
    if payload.description is not None:
        brand.description = payload.description
    if payload.ig_link is not None:
        brand.ig_link = payload.ig_link
    if payload.tt_link is not None:
        brand.tt_link = payload.tt_link
    if payload.profile_pic_url is not None:
        brand.profile_pic_url = payload.profile_pic_url
    if payload.categories is not None:
        brand.categories = json.dumps(payload.categories)
    if payload.budget_tier is not None:
        brand.budget_tier = payload.budget_tier
    if payload.min_er is not None:
        brand.min_er = payload.min_er
    # Recompute platform from current links
    brand.platform = _platform_from_links(brand.ig_link, brand.tt_link)

    db.commit()
    db.refresh(brand)
    return _brand_out(brand, db)


@router.post("/{brand_id}/fetch-ig", response_model=BrandOut)
async def fetch_ig_profile(brand_id: int, db: Session = Depends(get_db)):
    """Fetch the Instagram profile picture for a brand using its ig_link."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    username = _extract_ig_username(brand.ig_link or "")
    if not username:
        raise HTTPException(status_code=400, detail="Brand has no valid Instagram link set")

    try:
        profile = await ig_scrape(username)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    brand.profile_pic_url = profile.get("profile_pic_url") or brand.profile_pic_url
    db.commit()
    db.refresh(brand)
    return _brand_out(brand, db)


@router.delete("/{brand_id}", status_code=204)
def delete_brand(brand_id: int, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    db.delete(brand)
    db.commit()


# --- Matching ---

@router.get("/{brand_id}/matches", response_model=List[MatchResult])
def get_matches(brand_id: int, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    influencers = db.query(Influencer).filter(Influencer.followers > 0).all()
    collabs = db.query(Collaboration).filter(Collaboration.brand_id == brand_id).all()
    collab_map = {c.influencer_id: CollaborationOut.model_validate(c) for c in collabs}

    ranked = rank_matches(brand, influencers, collab_map)

    results = []
    for entry in ranked:
        inf_dict = InfluencerOut.model_validate(entry["influencer"]).model_dump()
        inf_dict["match_score"] = entry["score"]
        inf_dict["match_reasons"] = entry["match_reasons"]
        inf_dict["collaboration"] = entry["collaboration"]
        results.append(MatchResult.model_validate(inf_dict))

    return results


# --- Collaborations ---

@router.post("/{brand_id}/collaborations", response_model=CollaborationOut, status_code=201)
def add_collaboration(brand_id: int, payload: CollaborationCreate, db: Session = Depends(get_db)):
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    influencer = db.query(Influencer).filter(Influencer.id == payload.influencer_id).first()
    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    existing = db.query(Collaboration).filter(
        Collaboration.brand_id == brand_id,
        Collaboration.influencer_id == payload.influencer_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Collaboration already exists")

    collab = Collaboration(
        brand_id=brand_id,
        influencer_id=payload.influencer_id,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(collab)
    db.commit()
    db.refresh(collab)
    return collab


@router.patch("/{brand_id}/collaborations/{influencer_id}", response_model=CollaborationOut)
def update_collaboration(
    brand_id: int,
    influencer_id: int,
    payload: CollaborationUpdate,
    db: Session = Depends(get_db),
):
    collab = db.query(Collaboration).filter(
        Collaboration.brand_id == brand_id,
        Collaboration.influencer_id == influencer_id,
    ).first()
    if not collab:
        raise HTTPException(status_code=404, detail="Collaboration not found")

    if payload.status is not None:
        collab.status = payload.status
    if payload.notes is not None:
        collab.notes = payload.notes

    db.commit()
    db.refresh(collab)
    return collab


@router.delete("/{brand_id}/collaborations/{influencer_id}", status_code=204)
def delete_collaboration(brand_id: int, influencer_id: int, db: Session = Depends(get_db)):
    collab = db.query(Collaboration).filter(
        Collaboration.brand_id == brand_id,
        Collaboration.influencer_id == influencer_id,
    ).first()
    if not collab:
        raise HTTPException(status_code=404, detail="Collaboration not found")

    db.delete(collab)
    db.commit()
