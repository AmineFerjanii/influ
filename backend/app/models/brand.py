from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, UniqueConstraint, CheckConstraint, func,
)
from sqlalchemy.orm import relationship
from ..database import Base


class Brand(Base):
    __tablename__ = "brands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    ig_link = Column(Text)            # e.g. https://www.instagram.com/vitalait
    tt_link = Column(Text)            # e.g. https://www.tiktok.com/@vitalait
    profile_pic_url = Column(Text)    # fetched from Instagram
    categories = Column(Text, default="[]")   # JSON: ["Fashion", "Lifestyle"]
    platform = Column(String(20), nullable=False, default="both")  # auto-computed from links
    budget_tier = Column(String(20), nullable=False, default="micro")
    min_er = Column(Float, default=0.0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    collaborations = relationship("Collaboration", back_populates="brand", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("platform IN ('instagram', 'tiktok', 'both')", name="ck_brand_platform"),
        CheckConstraint("budget_tier IN ('nano', 'micro', 'macro', 'mega')", name="ck_budget_tier"),
    )


class Collaboration(Base):
    __tablename__ = "collaborations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    influencer_id = Column(Integer, ForeignKey("influencers.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="potential")
    notes = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    brand = relationship("Brand", back_populates="collaborations")
    influencer = relationship("Influencer")

    __table_args__ = (
        UniqueConstraint("brand_id", "influencer_id", name="uq_brand_influencer"),
        CheckConstraint(
            "status IN ('potential', 'contacted', 'in_progress', 'done')",
            name="ck_collab_status",
        ),
    )
