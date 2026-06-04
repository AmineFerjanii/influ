from datetime import datetime, timezone
from typing import List, Optional


def compute_kpis(
    posts: List[dict],
    followers: int,
    has_comments: bool = True,
) -> dict:
    if not posts or followers == 0:
        return {
            "avg_likes": 0.0,
            "avg_comments": 0.0,
            "engagement_rate": 0.0,
            "posts_per_week": 0.0,
            "has_comments_data": has_comments,
        }

    avg_likes = sum(p.get("likes", 0) for p in posts) / len(posts)

    if has_comments:
        avg_comments = sum(p.get("comments", 0) for p in posts) / len(posts)
        engagement_rate = (avg_likes + avg_comments) / followers * 100
    else:
        avg_comments = 0.0
        engagement_rate = avg_likes / followers * 100

    posts_per_week = _calc_posting_frequency(posts)

    return {
        "avg_likes": round(avg_likes, 1),
        "avg_comments": round(avg_comments, 1),
        "engagement_rate": round(engagement_rate, 2),
        "posts_per_week": round(posts_per_week, 2),
        "has_comments_data": has_comments,
    }


def _calc_posting_frequency(posts: List[dict]) -> float:
    dates = [p["posted_at"] for p in posts if p.get("posted_at")]
    if len(dates) < 2:
        return 0.0

    dates_aware = []
    for d in dates:
        if isinstance(d, datetime):
            if d.tzinfo is None:
                d = d.replace(tzinfo=timezone.utc)
            dates_aware.append(d)

    if len(dates_aware) < 2:
        return 0.0

    span_days = (max(dates_aware) - min(dates_aware)).days
    span_weeks = max(span_days / 7, 1)
    return len(posts) / span_weeks
