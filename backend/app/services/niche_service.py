NICHE_KEYWORDS: dict[str, list[str]] = {
    "Fashion": ["fashion", "style", "outfit", "ootd", "clothing", "wear", "look", "mode", "tenue", "vêtement", "moda"],
    "Beauty": ["beauty", "makeup", "skincare", "cosmetics", "lipstick", "glam", "sephora", "beauté", "maquillage", "soins"],
    "Food & Beverage": ["food", "recipe", "cook", "baking", "restaurant", "eat", "cuisine", "nourriture", "recette", "gastronomie", "chef"],
    "Travel": ["travel", "explore", "adventure", "wanderlust", "trip", "destination", "voyage", "tourisme", "explore", "vacances"],
    "Fitness": ["fitness", "gym", "workout", "training", "sport", "health", "yoga", "run", "musculation", "coaching", "nutrition"],
    "Lifestyle": ["lifestyle", "life", "daily", "vlog", "family", "home", "living", "vie", "quotidien", "famille"],
    "Tech": ["tech", "technology", "coding", "software", "gaming", "digital", "dev", "informatique", "programmation"],
    "Business": ["entrepreneur", "business", "startup", "marketing", "finance", "invest", "entrepreneur", "affaires"],
    "Art & Culture": ["art", "design", "photography", "creative", "culture", "museum", "photo", "artiste", "culture"],
    "Entertainment": ["comedy", "humor", "music", "dance", "entertainment", "fun", "comédie", "musique", "danse"],
    "Education": ["education", "learn", "knowledge", "teacher", "school", "cours", "apprendre", "formation", "étude"],
    "Environment": ["eco", "green", "sustainable", "environment", "nature", "climate", "plastic", "plastique", "durable", "écologie", "nomoreplastic"],
}


def infer_niches(bio: str, top_hashtags: list, top_mentions=None) -> list:
    """Keyword-match bio + hashtags to infer up to 3 content niches."""
    tag_text = " ".join(h["tag"].lower() for h in top_hashtags)
    text = (bio or "").lower() + " " + tag_text

    scores: dict[str, int] = {}
    for niche, keywords in NICHE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[niche] = score

    return [n for n, _ in sorted(scores.items(), key=lambda x: -x[1])][:3]
