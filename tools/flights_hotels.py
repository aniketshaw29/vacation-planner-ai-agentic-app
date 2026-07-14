import json
import re
from pathlib import Path
from langchain_core.tools import tool
from tools.currency import to_inr, INR_PER_USD

_FLIGHTS_PATH = Path(__file__).parent.parent / "data" / "mock_flights.json"
_HOTELS_PATH = Path(__file__).parent.parent / "data" / "mock_hotels.json"
_FLIGHTS: dict = json.loads(_FLIGHTS_PATH.read_text())
_HOTELS: dict = json.loads(_HOTELS_PATH.read_text())

_DESTINATIONS_PATH = Path(__file__).parent.parent / "data" / "mock_destinations.json"
_DEST_NAMES: dict[str, str] = {}
for _d in json.loads(_DESTINATIONS_PATH.read_text()):
    _DEST_NAMES[_d["name"].lower()] = _d["name"]


def _normalize_city(name: str) -> str:
    """Return the canonical city name used as dict key."""
    name = name.strip()
    # Check known destinations
    lower = name.lower()
    if lower in _DEST_NAMES:
        return _DEST_NAMES[lower]
    # Common aliases
    aliases = {
        "nyc": "New York", "new york city": "New York",
        "bkk": "Bangkok", "kix": "Kyoto", "osaka": "Kyoto",
        "rio": "Rio de Janeiro",
    }
    return aliases.get(lower, name)


def _season_from_date(date_str: str) -> str:
    try:
        month = int(date_str.split("-")[1])
    except Exception:
        return "summer"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


@tool
def search_flights(
    origin_city: str,
    destination: str,
    departure_date: str,
    return_date: str,
    num_passengers: int,
    cabin_class: str = "economy",
) -> str:
    """
    Search for available flights between two cities.

    Returns a JSON list of flight options sorted by price. Each option includes:
    airline, flight_number, departure_time, arrival_time (estimated), duration_hours,
    stops, stop_cities, price_per_person_usd, total_price_usd, baggage_kg, rating.

    departure_date / return_date format: YYYY-MM-DD
    cabin_class: economy | business | first
    """
    origin = _normalize_city(origin_city).upper()
    dest = _normalize_city(destination).upper()
    route_key = f"{origin}->{dest}"

    routes = _FLIGHTS.get("routes", {})
    flights = routes.get(route_key)

    if not flights:
        # Try reverse or partial match
        for key, value in routes.items():
            if dest in key:
                flights = value
                break

    if not flights:
        # Return a generic placeholder
        flights = [{
            "airline": "International Airways",
            "flight_number": "IA001",
            "price_usd_economy": 600,
            "price_usd_business": 1800,
            "duration_hours": 12,
            "stops": 1,
            "stop_cities": ["Hub City"],
            "departure_times": ["08:00", "18:00"],
            "baggage_kg": 23,
            "rating": 4.0,
        }]

    season = _season_from_date(departure_date)
    multiplier = _FLIGHTS.get("price_multipliers", {}).get(season, 1.0)
    group_discount = 1.0
    disc = _FLIGHTS.get("group_discounts", {})
    if num_passengers >= 10 and "10" in disc:
        group_discount = 1 - disc["10"]
    elif num_passengers >= 5 and "5" in disc:
        group_discount = 1 - disc["5"]

    price_field = f"price_usd_{cabin_class}" if cabin_class != "first" else "price_usd_business"

    results = []
    for f in flights:
        base = f.get(price_field, f.get("price_usd_economy", 500))
        per_person = round(base * multiplier * group_discount)
        total = per_person * num_passengers
        dep = f["departure_times"][0] if f.get("departure_times") else "08:00"
        # Estimate arrival from departure + duration
        dep_h, dep_m = map(int, dep.split(":"))
        duration_h = f.get("duration_hours", 10)
        arr_h = (dep_h + int(duration_h)) % 24
        arrival = f"{arr_h:02d}:{dep_m:02d}"

        results.append({
            "airline": f["airline"],
            "flight_number": f["flight_number"],
            "departure_time": dep,
            "arrival_time": arrival,
            "duration_hours": duration_h,
            "stops": f.get("stops", 0),
            "stop_cities": f.get("stop_cities", []),
            "cabin_class": cabin_class,
            "price_per_person_inr": to_inr(per_person),
            "total_price_inr": to_inr(total),
            "baggage_kg": f.get("baggage_kg", 23),
            "rating": f.get("rating", 4.0),
            "season_note": f"Prices adjusted for {season} travel",
        })

    results.sort(key=lambda x: x["price_per_person_inr"])
    return json.dumps(results)


@tool
def search_hotels(
    destination: str,
    check_in_date: str,
    check_out_date: str,
    num_guests: int,
    accommodation_type: str = "any",
    max_price_per_night_usd: int = 500,
) -> str:
    """
    Search for accommodation options at the destination.

    Returns a JSON list of hotels sorted by price. Each option includes:
    name, type, stars, neighborhood, price_per_night_usd, total_price_usd,
    amenities, distance_to_center_km, guest_rating, description.

    accommodation_type: hotel | hostel | airbnb | resort | boutique | villa | ryokan | any
    max_price_per_night_usd: upper limit; pass 9999 to see all options
    """
    city = _normalize_city(destination)
    hotels = _HOTELS.get(city)

    if not hotels:
        # Fallback search
        for key in _HOTELS:
            if city.lower() in key.lower() or key.lower() in city.lower():
                hotels = _HOTELS[key]
                break

    if not hotels:
        return json.dumps({"error": f"No hotel data for destination '{destination}'"})

    try:
        ci_parts = check_in_date.split("-")
        co_parts = check_out_date.split("-")
        nights = abs(int(co_parts[2]) - int(ci_parts[2])) or 7
        # Rough cross-month: if same month, use day diff; otherwise estimate
        if ci_parts[1] != co_parts[1]:
            nights = max(1, nights)
    except Exception:
        nights = 7

    filtered = []
    for h in hotels:
        htype = h.get("type", "").lower()
        if accommodation_type != "any" and htype != accommodation_type.lower():
            continue
        price = h["price_per_night_usd"]
        if price > max_price_per_night_usd:
            continue
        filtered.append({
            **h,
            "price_per_night_inr": to_inr(price),
            "total_price_inr": to_inr(price * nights),
            "nights": nights,
            "guests": num_guests,
        })

    if not filtered:
        # Relax type filter if nothing matches
        for h in hotels:
            price = h["price_per_night_usd"]
            if price <= max_price_per_night_usd:
                filtered.append({**h, "total_price_usd": price * nights, "nights": nights})

    filtered.sort(key=lambda x: x["price_per_night_usd"])
    return json.dumps(filtered[:6])
