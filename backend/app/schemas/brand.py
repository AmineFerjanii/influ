import json
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, field_validator

from .influencer import InfluencerOut


class BrandCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ig_link: Optional[str] = None
    tt_link: Optional[str] = None
    categories: List[str] = []
    budget_tier: str = "micro"
    min_er: float = 0.0

    @field_validator("budget_tier")
    @classmethod
    def validate_budget_tier(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("nano", "micro", "macro", "mega"):
            raise ValueError("budget_tier must be 'nano', 'micro', 'macro', or 'mega'")
        return v

    @field_validator("min_er")
    @classmethod
    def validate_min_er(cls, v: float) -> float:
        if v < 0:
            raise ValueError("min_er must be >= 0")
        return v


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ig_link: Optional[str] = None
    tt_link: Optional[str] = None
    profile_pic_url: Optional[str] = None
    categories: Optional[List[str]] = None
    budget_tier: Optional[str] = None
    min_er: Optional[float] = None


class CollaborationOut(BaseModel):
    id: int
    brand_id: int
    influencer_id: int
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CollaborationCreate(BaseModel):
    influencer_id: int
    status: str = "potential"
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("potential", "contacted", "in_progress", "done"):
            raise ValueError("status must be potential, contacted, in_progress, or done")
        return v


class CollaborationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("potential", "contacted", "in_progress", "done"):
            raise ValueError("status must be potential, contacted, in_progress, or done")
        return v


class BrandOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    ig_link: Optional[str] = None
    tt_link: Optional[str] = None
    profile_pic_url: Optional[str] = None
    categories: List[str] = []
    platform: str
    budget_tier: str
    min_er: float = 0.0
    collaboration_count: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_validator("categories", mode="before")
    @classmethod
    def _parse_categories(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []


class BrandDetail(BrandOut):
    collaborations: List[CollaborationOut] = []


class MatchResult(InfluencerOut):
    match_score: float
    match_reasons: List[str] = []
    collaboration: Optional[CollaborationOut] = None
