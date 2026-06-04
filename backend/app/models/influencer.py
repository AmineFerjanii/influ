from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, CheckConstraint, UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from ..database import Base


class Influencer(Base):
    __tablename__ = "influencers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(20), nullable=False)
    username = Column(String(100), nullable=False)
    display_name = Column(String(200))
    profile_pic_url = Column(Text)
    bio = Column(Text)

    followers = Column(Integer, default=0)
    following = Column(Integer, default=0)
    total_posts = Column(Integer, default=0)
    is_verified = Column(Boolean, default=False)

    avg_likes = Column(Float, default=0.0)
    avg_comments = Column(Float, default=0.0)
    engagement_rate = Column(Float, default=0.0)
    posts_per_week = Column(Float, default=0.0)
    has_comments_data = Column(Boolean, default=True)

    # Phase 2: Rich analytics
    top_hashtags = Column(Text, default="[]")        # JSON: [{"tag": "#fashion", "count": 8}]
    top_mentions = Column(Text, default="[]")        # JSON: [{"mention": "@brand", "count": 3}]
    inferred_niches = Column(Text, default="[]")     # JSON: ["Fashion", "Lifestyle"]
    estimated_reach = Column(Float, default=0.0)
    estimated_impressions = Column(Float, default=0.0)
    photo_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)

    linked_influencer_id = Column(Integer, ForeignKey("influencers.id", ondelete="SET NULL"), nullable=True)

    last_scraped_at = Column(DateTime)
    scrape_status = Column(String(20), default="pending")
    scrape_error = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    posts = relationship("Post", back_populates="influencer", cascade="all, delete-orphan")
    scrape_jobs = relationship("ScrapeJob", back_populates="influencer", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("platform", "username", name="uq_platform_username"),
        CheckConstraint("platform IN ('instagram', 'tiktok')", name="ck_platform"),
        CheckConstraint(
            "scrape_status IN ('pending', 'scraping', 'success', 'error')",
            name="ck_scrape_status",
        ),
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    influencer_id = Column(Integer, ForeignKey("influencers.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(String(200), nullable=False)
    thumbnail_url = Column(Text)
    local_thumbnail = Column(Text)
    post_url = Column(Text)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    posted_at = Column(DateTime)
    is_video = Column(Boolean, default=False)

    # Phase 2: Rich post data
    caption = Column(Text)
    media_type = Column(String(20))   # photo | video | carousel
    view_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=func.now())

    influencer = relationship("Influencer", back_populates="posts")

    __table_args__ = (
        UniqueConstraint("influencer_id", "post_id", name="uq_influencer_post"),
    )


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    influencer_id = Column(Integer, ForeignKey("influencers.id", ondelete="CASCADE"))
    status = Column(String(20), default="queued")
    triggered_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    error_message = Column(Text)

    influencer = relationship("Influencer", back_populates="scrape_jobs")

    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'success', 'failed')",
            name="ck_job_status",
        ),
    )
