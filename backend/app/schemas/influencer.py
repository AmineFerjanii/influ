import json
from datetime import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, field_validator


class PostOut(BaseModel):
    id: int
    post_id: str
    thumbnail_url: Optional[str] = None
    local_thumbnail: Optional[str] = None
    post_url: Optional[str] = None
    likes: int = 0
    comments: int = 0
    posted_at: Optional[datetime] = None
    is_video: bool = False
    caption: Optional[str] = None
    media_type: Optional[str] = None
    view_count: int = 0

    model_config = {"from_attributes": True}


class InfluencerBase(BaseModel):
    platform: str
    username: str

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("instagram", "tiktok"):
            raise ValueError("platform must be 'instagram' or 'tiktok'")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        return v.strip().lstrip("@")


class InfluencerCreate(InfluencerBase):
    pass


class InfluencerBulkCreate(BaseModel):
    influencers: List[InfluencerCreate]


class InfluencerOut(BaseModel):
    id: int
    platform: str
    username: str
    display_name: Optional[str] = None
    profile_pic_url: Optional[str] = None
    bio: Optional[str] = None
    followers: int = 0
    following: int = 0
    total_posts: int = 0
    is_verified: bool = False
    avg_likes: float = 0.0
    avg_comments: float = 0.0
    engagement_rate: float = 0.0
    posts_per_week: float = 0.0
    has_comments_data: bool = True
    top_hashtags: List[Any] = []
    top_mentions: List[Any] = []
    inferred_niches: List[str] = []
    estimated_reach: float = 0.0
    estimated_impressions: float = 0.0
    photo_count: int = 0
    video_count: int = 0
    last_scraped_at: Optional[datetime] = None
    scrape_status: str = "pending"
    scrape_error: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @field_validator("top_hashtags", "top_mentions", mode="before")
    @classmethod
    def _parse_json_list_of_dicts(cls, v: Any) -> List[Any]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []

    @field_validator("inferred_niches", mode="before")
    @classmethod
    def _parse_json_list_of_str(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []


class LinkedInfluencerOut(BaseModel):
    id: int
    platform: str
    username: str
    display_name: Optional[str] = None
    profile_pic_url: Optional[str] = None
    followers: int = 0
    engagement_rate: float = 0.0
    scrape_status: str = "pending"

    model_config = {"from_attributes": True}


class SponsoredPostOut(BaseModel):
    post_id: str
    post_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    matched_tags: List[str] = []
    matched_brands: List[str] = []
    caption_snippet: Optional[str] = None


class InfluencerDetail(InfluencerOut):
    posts: List[PostOut] = []
    linked_influencer: Optional[LinkedInfluencerOut] = None
    detected_sponsorships: List[SponsoredPostOut] = []


class InfluencerListResponse(BaseModel):
    data: List[InfluencerOut]
    total: int
    page: int
    page_size: int


class ScrapeJobOut(BaseModel):
    id: int
    influencer_id: Optional[int] = None
    status: str
    triggered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class ScrapeResponse(BaseModel):
    job_id: int
    influencer_id: int
    status: str
