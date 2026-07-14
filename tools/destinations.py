import json
from pathlib import Path
from langchain_core.tools import tool

_DATA_PATH = Path(__file__).parent.parent / "data" / "mock_destinations.json"
_DESTINATIONS: list[dict] = json.loads(_DATA_PATH.read_text())

_STYLE_MAP = {
    "adventure": ["adventure", "nature", "outdoor"],
    "relaxation": ["relaxation", "beach", "spa"],
    "cultural": ["cultural", "history", "art"],
    "foodie": ["foodie", "culinary", "food"],
    "beach": ["beach", "island", "coastal"],
    "city": ["city", "urban", "metropolis"],
    "nature": ["nature", "wildlife", "eco"],
    "romance": ["romance", "romantic", "honeymoon"],
    "budget": ["budget", "backpacker"],
    "luxury": ["luxury", "premium"],
    "balanced": [],  # matches all
}


def _score_destination(dest: dict, budget_per_person: int, travel_styles: list[str], season: str, duration: int) -> float:
    score = 0.0
    cost = dest["estimated_daily_cost_usd"]
    ideal_daily = budget_per_person * 0.6 / max(duration, 1)

    # Budget fit (30 pts) — penalise if too expensive, reward if cost is near ideal
    cheapest = cost.get("budget", 9999)
    moderate = cost.get("moderate", 9999)
    if cheapest > budget_per_person * 0.6 / max(duration, 1):
        return 0  # hard filter: too expensive even on budget tier
    if ideal_daily >= moderate:
        score += 30
    elif ideal_daily >= cheapest:
        score += 15 + 15 * (ideal_daily - cheapest) / max(moderate - cheapest, 1)
    else:
        score += 5

    # Season match (25 pts)
    if season in dest.get("best_seasons", []):
        score += 25
    elif season in dest.get("okay_seasons", []):
        score += 12
    elif season not in dest.get("avoid_seasons", []):
        score += 5

    # Travel style overlap (35 pts)
    dest_styles = [s.lower() for s in dest.get("travel_styles", [])]
    matched = 0
    for style in travel_styles:
        aliases = _STYLE_MAP.get(style, [style])
        if style == "balanced":
            matched += 1
            continue
        if style in dest_styles or any(a in dest_styles for a in aliases):
            matched += 1
    if travel_styles:
        score += 35 * matched / len(travel_styles)
    else:
        score += 17

    # Duration fit (10 pts)
    typical = dest.get("typical_stay_days", 7)
    diff = abs(typical - duration)
    score += max(0, 10 - diff * 2)

    return round(score, 1)


@tool
def suggest_destinations(
    budget_usd_per_person: int,
    travel_style: str,
    season: str,
    group_size: int,
    trip_duration_days: int,
) -> str:
    """
    Suggest top vacation destinations based on user preferences.

    Returns a JSON list of up to 5 destination cards with: name, country, description,
    highlights, estimated_daily_cost_usd, best_seasons, insider_tip, and match_score (0-100).

    travel_style: comma-separated list or single value from:
      adventure, relaxation, cultural, foodie, beach, city, nature, romance, budget, luxury, balanced
    season: spring | summer | autumn | winter
    """
    styles = [s.strip().lower() for s in travel_style.split(",")]
    scored = []
    for dest in _DESTINATIONS:
        s = _score_destination(dest, budget_usd_per_person, styles, season.lower(), trip_duration_days)
        if s > 0:
            scored.append((s, dest))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, dest in scored[:5]:
        results.append({
            "name": dest["name"],
            "country": dest["country"],
            "continent": dest["continent"],
            "description": dest["description"],
            "highlights": dest["highlights"][:4],
            "known_for": dest["known_for"][:4],
            "estimated_daily_cost_usd": dest["estimated_daily_cost_usd"],
            "best_seasons": dest["best_seasons"],
            "weather_notes": dest.get("weather_notes", ""),
            "typical_stay_days": dest.get("typical_stay_days", trip_duration_days),
            "insider_tip": dest.get("insider_tip", ""),
            "match_score": min(100, int(score)),
            "airport_code": dest.get("airport_code", ""),
        })
    return json.dumps(results)
