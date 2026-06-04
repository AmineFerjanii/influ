import json
from typing import List, Optional

TIER_RANGES = {
    "nano":  (0, 9_999),
    "micro": (10_000, 99_999),
    "macro": (100_000, 999_999),
    "mega":  (1_000_000, float("inf")),
}


def _parse_niches(raw) -> List[str]:
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    return raw or []


def score_influencer(brand, influencer) -> dict:
    """
    Score an influencer against a brand's criteria (0–100).

    Dimensions:
      - Niche overlap:   0–40 pts  (proportion of brand categories matched)
      - Follower tier:   0–30 pts  (exact tier match)
      - Engagement rate: 0–30 pts  (meets / partially meets min_er)
    """
    reasons: List[str] = []
    total = 0.0

    # --- Niche overlap (0–40) ---
    brand_cats = _parse_niches(brand.categories)
    influencer_niches = _parse_niches(influencer.inferred_niches)

    if brand_cats:
        matched = [n for n in influencer_niches if n in brand_cats]
        niche_score = (len(matched) / len(brand_cats)) * 40
        total += niche_score
        if matched:
            reasons.append(f"Niche match: {', '.join(matched)}")
    else:
        # Brand has no category preference — give full niche points
        total += 40
        reasons.append("No niche restriction")

    # --- Follower tier (0–30) ---
    followers = influencer.followers or 0
    lo, hi = TIER_RANGES.get(brand.budget_tier, (0, float("inf")))
    if lo <= followers <= hi:
        total += 30
        reasons.append(f"Audience size matches {brand.budget_tier} tier")
    else:
        # Partial credit: 15 pts if one tier away
        tiers = list(TIER_RANGES.keys())
        brand_idx = tiers.index(brand.budget_tier)
        for i, tier in enumerate(tiers):
            tier_lo, tier_hi = TIER_RANGES[tier]
            if tier_lo <= followers <= tier_hi:
                if abs(i - brand_idx) == 1:
                    total += 15
                    reasons.append(f"Audience size close to {brand.budget_tier} tier")
                break

    # --- Engagement rate (0–30) ---
    er = influencer.engagement_rate or 0.0
    min_er = brand.min_er or 0.0
    if min_er == 0.0:
        total += 30
        reasons.append("No minimum ER requirement")
    elif er >= min_er:
        total += 30
        reasons.append(f"ER {er:.1f}% meets minimum {min_er:.1f}%")
    elif er >= min_er * 0.5:
        # Within 50% of threshold — partial credit
        partial = (er / min_er) * 30
        total += partial
        reasons.append(f"ER {er:.1f}% close to minimum {min_er:.1f}%")

    return {
        "score": round(min(total, 100), 1),
        "match_reasons": reasons,
    }


def rank_matches(brand, influencers, collaborations_by_influencer: Optional[dict] = None) -> List[dict]:
    """
    Filter by platform (if brand.platform != 'both'), score each influencer,
    and return list of dicts sorted descending by score.
    """
    collab_map = collaborations_by_influencer or {}
    results = []

    for inf in influencers:
        if brand.platform != "both" and inf.platform != brand.platform:
            continue
        scored = score_influencer(brand, inf)
        results.append({
            "influencer": inf,
            "score": scored["score"],
            "match_reasons": scored["match_reasons"],
            "collaboration": collab_map.get(inf.id),
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
