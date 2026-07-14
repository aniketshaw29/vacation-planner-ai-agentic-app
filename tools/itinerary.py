import json
from pathlib import Path
from langchain_core.tools import tool

_DATA_PATH = Path(__file__).parent.parent / "data" / "mock_destinations.json"
_DESTINATIONS: dict[str, dict] = {d["name"].lower(): d for d in json.loads(_DATA_PATH.read_text())}

_ACTIVITY_TEMPLATES = {
    "morning": ["Explore {place} — {notes}", "Visit {place} (opens {open_time})", "{place} — best visited in the morning"],
    "afternoon": ["{place} — {duration}hr visit, budget ${cost}", "Discover {place} in the afternoon", "Head to {place}"],
    "evening": ["Dinner near {place}", "{place} at sunset — {notes}", "Evening at {place}"],
}


def _find_destination(name: str) -> dict | None:
    key = name.lower().strip()
    if key in _DESTINATIONS:
        return _DESTINATIONS[key]
    for k, v in _DESTINATIONS.items():
        if key in k or k in key:
            return v
    return None


def _slot_places(places: list[dict]) -> list[tuple[str, dict]]:
    """Sort places into morning/afternoon/evening slots based on best_visit_time."""
    morning, afternoon, evening = [], [], []
    for p in places:
        best = p.get("best_visit_time", "10:00")
        hour = int(best.split(":")[0])
        if hour < 12:
            morning.append(p)
        elif hour < 17:
            afternoon.append(p)
        else:
            evening.append(p)
    return morning, afternoon, evening


@tool
def build_itinerary(
    destination: str,
    trip_duration_days: int,
    travel_style: str,
    group_size: int,
    interests: str,
) -> str:
    """
    Build a detailed day-by-day itinerary for a vacation destination.

    Returns a JSON list of days. Each day has: day_number, theme, morning, afternoon,
    and evening slots. Each slot has: activity, place, time, duration_hours, cost_usd,
    open_time, close_time, notes, and transit_hint.

    interests: comma-separated string, e.g. "temples,food,beaches,hiking,markets"
    travel_style: adventure | relaxation | cultural | foodie | beach | city | nature | romance | balanced
    """
    dest = _find_destination(destination)
    if not dest:
        return json.dumps({"error": f"Destination '{destination}' not found in database"})

    interest_list = [i.strip().lower() for i in interests.split(",") if i.strip()]
    places = dest.get("places", [])

    # Score places by interest match
    scored_places = []
    for place in places:
        score = 0
        ptype = place.get("type", "").lower()
        for interest in interest_list:
            if interest in ptype or ptype in interest:
                score += 2
        # Prioritize by travel style
        style = travel_style.lower()
        if style == "cultural" and ptype in ("cultural", "historical", "museum"):
            score += 3
        elif style == "beach" and ptype == "beach":
            score += 3
        elif style == "foodie" and ptype in ("food", "market"):
            score += 3
        elif style == "adventure" and ptype in ("adventure", "nature"):
            score += 3
        scored_places.append((score, place))

    scored_places.sort(key=lambda x: x[0], reverse=True)
    available = [p for _, p in scored_places]

    morning_pool, afternoon_pool, evening_pool = _slot_places(available)

    itinerary = []
    used = set()
    place_index = 0

    theme_by_day = [
        "Arrival & Orientation", "Main Highlights", "Off the Beaten Path",
        "Food & Culture", "Nature & Adventure", "Local Life", "Leisure Day",
        "Shopping & Markets", "Day Trip", "Farewell Day"
    ]

    for day_num in range(1, trip_duration_days + 1):
        theme = theme_by_day[min(day_num - 1, len(theme_by_day) - 1)]

        def pick(pool, fallback_pool=None):
            for p in pool:
                if p["name"] not in used:
                    used.add(p["name"])
                    return p
            if fallback_pool:
                for p in fallback_pool:
                    if p["name"] not in used:
                        used.add(p["name"])
                        return p
            return None

        m = pick(morning_pool, available)
        a = pick(afternoon_pool, available)
        e = pick(evening_pool, available)

        def make_slot(p, slot_time):
            if not p:
                return {"activity": "Free time / rest", "place": "Hotel area", "time": slot_time, "duration_hours": 2, "cost_usd": 0, "notes": "Relax and explore at your own pace"}
            return {
                "activity": f"Visit {p['name']}",
                "place": p["name"],
                "type": p.get("type", ""),
                "time": p.get("best_visit_time", slot_time),
                "open_time": p.get("open_time", "09:00"),
                "close_time": p.get("close_time", "18:00"),
                "duration_hours": p.get("duration_hours", 2),
                "cost_usd": p.get("entrance_fee_usd", 0) * group_size,
                "neighborhood": p.get("neighborhood", ""),
                "notes": p.get("notes", ""),
                "transit_hint": f"~{10 + place_index * 5} min from previous stop",
            }

        itinerary.append({
            "day": day_num,
            "theme": theme,
            "morning": make_slot(m, "09:00"),
            "afternoon": make_slot(a, "14:00"),
            "evening": make_slot(e, "18:30"),
            "daily_cost_estimate_usd": sum([
                (m or {}).get("entrance_fee_usd", 0) * group_size if m else 0,
                (a or {}).get("entrance_fee_usd", 0) * group_size if a else 0,
                (e or {}).get("entrance_fee_usd", 0) * group_size if e else 0,
            ]) + 20 * group_size,  # +$20 per person for meals/transit
        })

    return json.dumps(itinerary)
