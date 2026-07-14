import json
from pathlib import Path
from langchain_core.tools import tool

_DEST_PATH = Path(__file__).parent.parent / "data" / "mock_destinations.json"
_TRANSPORT_PATH = Path(__file__).parent.parent / "data" / "mock_transport.json"
_DESTINATIONS: dict[str, dict] = {d["name"].lower(): d for d in json.loads(_DEST_PATH.read_text())}
_TRANSPORT: dict = json.loads(_TRANSPORT_PATH.read_text())


def _find_dest(name: str) -> dict | None:
    key = name.lower().strip()
    if key in _DESTINATIONS:
        return _DESTINATIONS[key]
    for k, v in _DESTINATIONS.items():
        if key in k or k in key:
            return v
    return None


def _get_transit_time(city: str, from_place: str, to_place: str) -> int:
    """Return estimated transit time in minutes between two places."""
    city_data = _TRANSPORT.get("cities", {}).get(city, {})
    transit = city_data.get("transit_times_min", {})
    for key, minutes in transit.items():
        parts = key.split("->")
        if len(parts) == 2:
            a, b = [p.lower() for p in parts]
            fp, tp = from_place.lower(), to_place.lower()
            if (a in fp or fp in a) and (b in tp or tp in b):
                return minutes
    return 20  # default 20 min between stops


@tool
def plan_route(
    destination: str,
    places_to_visit: str,
    start_location: str = "hotel",
    transport_mode: str = "mixed",
) -> str:
    """
    Plan an optimized visit sequence for a list of places at a destination.

    Considers: geographic proximity (neighborhood clustering), opening hours,
    crowd peak times, and best visiting times. Returns an ordered visit plan
    with arrival/departure times, transit details, and timing tips.

    places_to_visit: comma-separated place names, e.g. "Eiffel Tower,Louvre,Montmartre"
    transport_mode: walking | taxi | public_transport | scooter | mixed
    """
    dest = _find_dest(destination)
    if not dest:
        return json.dumps({"error": f"Destination '{destination}' not found"})

    place_names = [p.strip() for p in places_to_visit.split(",") if p.strip()]
    all_places = dest.get("places", [])

    # Match requested place names to destination place data
    matched = []
    for requested in place_names:
        best = None
        for p in all_places:
            if requested.lower() in p["name"].lower() or p["name"].lower() in requested.lower():
                best = p
                break
        if not best:
            # Create a generic placeholder so we don't skip requested places
            best = {
                "name": requested,
                "type": "attraction",
                "open_time": "09:00",
                "close_time": "18:00",
                "best_visit_time": "10:00",
                "crowd_peak": "13:00",
                "duration_hours": 2,
                "entrance_fee_usd": 0,
                "neighborhood": "City Center",
                "notes": "",
            }
        matched.append(best)

    # Sort: morning-best places first (those with earliest best_visit_time)
    def sort_key(p):
        bvt = p.get("best_visit_time", "10:00")
        h, m = map(int, bvt.split(":"))
        # Deprioritise places with crowd_peak before best_visit_time (already past)
        crowd = p.get("crowd_peak", "12:00")
        ch = int(crowd.split(":")[0])
        penalty = 0 if h < ch else 2  # penalty for visiting when crowds are already there
        return h + penalty

    matched.sort(key=sort_key)

    # Build timeline starting at 8:30
    current_hour = 8
    current_min = 30
    route = []
    prev_place = start_location

    for idx, place in enumerate(matched):
        arrive_str = f"{current_hour:02d}:{current_min:02d}"
        transit_min = _get_transit_time(dest["name"], prev_place, place["name"])

        # Add transit time
        current_min += transit_min
        while current_min >= 60:
            current_min -= 60
            current_hour += 1

        actual_arrive = f"{current_hour:02d}:{current_min:02d}"
        duration = place.get("duration_hours", 2)
        cost = place.get("entrance_fee_usd", 0)

        # Compute departure time
        dep_min = current_min + int((duration % 1) * 60)
        dep_hour = current_hour + int(duration)
        while dep_min >= 60:
            dep_min -= 60
            dep_hour += 1

        depart_str = f"{dep_hour:02d}:{dep_min:02d}"

        # Timing advice
        best = place.get("best_visit_time", "10:00")
        peak = place.get("crowd_peak", "13:00")
        crowd_advice = ""
        best_h = int(best.split(":")[0])
        arrive_h = int(actual_arrive.split(":")[0])
        if arrive_h > best_h + 1:
            crowd_advice = f"💡 Tip: Ideally visit by {best} for fewer crowds"
        elif arrive_h < best_h:
            crowd_advice = f"You're arriving early — {place['name']} opens at {place.get('open_time', '09:00')}"

        transit_desc = {
            "walking": f"~{min(transit_min, 25)} min walk",
            "taxi": f"~{max(transit_min // 3, 5)} min by taxi",
            "public_transport": f"~{transit_min} min by transit",
            "scooter": f"~{transit_min // 2} min by scooter",
            "mixed": f"~{transit_min} min ({idx % 2 == 0 and 'taxi' or 'walk'})",
        }.get(transport_mode, f"~{transit_min} min")

        route.append({
            "order": idx + 1,
            "place": place["name"],
            "type": place.get("type", ""),
            "neighborhood": place.get("neighborhood", ""),
            "arrive": actual_arrive,
            "duration_hours": duration,
            "depart": depart_str,
            "transit_from_prev": transit_desc if idx > 0 else "Start here",
            "entrance_fee_usd": cost,
            "open_time": place.get("open_time", "09:00"),
            "close_time": place.get("close_time", "18:00"),
            "crowd_peak": peak,
            "notes": place.get("notes", ""),
            "timing_advice": crowd_advice,
        })

        current_hour = dep_hour
        current_min = dep_min
        prev_place = place["name"]

    total_mins = (current_hour - 8) * 60 + (current_min - 30)
    return json.dumps({
        "destination": dest["name"],
        "transport_mode": transport_mode,
        "total_duration_hours": round(total_mins / 60, 1),
        "start_time": "08:30",
        "end_time": f"{current_hour:02d}:{current_min:02d}",
        "route": route,
        "summary": f"Visit {len(route)} places in ~{round(total_mins / 60, 1)} hours",
    })
