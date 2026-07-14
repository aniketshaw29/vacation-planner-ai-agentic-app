import json
from pathlib import Path
from langchain_core.tools import tool

_FOOD_PATH = Path(__file__).parent.parent / "data" / "mock_food.json"
_DEST_PATH = Path(__file__).parent.parent / "data" / "mock_destinations.json"
_TRANSPORT_PATH = Path(__file__).parent.parent / "data" / "mock_transport.json"

_FOOD: dict = json.loads(_FOOD_PATH.read_text())
_DEST_COSTS: dict[str, dict] = {d["name"].lower(): d["estimated_daily_cost_usd"] for d in json.loads(_DEST_PATH.read_text())}
_TRANSPORT: dict = json.loads(_TRANSPORT_PATH.read_text())


def _find_food_city(name: str) -> dict | None:
    key = name.lower().strip()
    for city_key in _FOOD:
        if key in city_key.lower() or city_key.lower() in key:
            return _FOOD[city_key]
    return None


def _find_dest_cost(name: str) -> dict:
    key = name.lower().strip()
    for city_key, costs in _DEST_COSTS.items():
        if key in city_key or city_key in key:
            return costs
    return {"budget": 40, "moderate": 80, "comfortable": 150, "luxury": 300}


@tool
def suggest_food(
    destination: str,
    price_tier: str = "all",
    meal_type: str = "all",
    dietary_restrictions: str = "none",
    num_people: int = 2,
) -> str:
    """
    Suggest food options and restaurants at a destination with price tiers.

    Returns JSON grouped by tier: street_food, budget, mid_range, fine_dining.
    Each entry has: name, cuisine, specialty, avg_cost_per_person_usd, avg_cost_inr,
    must_try, open/close times, reservation info, vegetarian options, and local tips.

    price_tier: street_food | budget | mid_range | fine_dining | all
    meal_type: breakfast | lunch | dinner | snacks | all
    dietary_restrictions: vegetarian | vegan | halal | gluten_free | none
    """
    city_food = _find_food_city(destination)

    if not city_food:
        return json.dumps({
            "destination": destination,
            "message": "Detailed food data not available. This destination has great local cuisine — explore the central market or main street for authentic local food.",
            "general_tips": [
                "Eat where locals eat — look for full tables and local language menus",
                "Markets and street stalls usually offer the most authentic and affordable meals",
                "Ask your hotel or hostel staff for their personal recommendations",
            ],
        })

    restrict_lower = dietary_restrictions.lower()
    tiers = ["street_food", "budget", "mid_range", "fine_dining"]
    if price_tier != "all":
        tiers = [price_tier.lower().replace("-", "_").replace(" ", "_")]

    result = {}
    for tier in tiers:
        if tier not in city_food:
            continue
        entries = city_food[tier]
        filtered = []
        for entry in entries:
            if restrict_lower not in ("none", "all", ""):
                if restrict_lower == "vegetarian" and not entry.get("vegetarian"):
                    continue
            avg_cost_usd = entry.get("avg_cost_usd", 15)
            filtered.append({
                "name": entry["name"],
                "cuisine": entry.get("cuisine", "Local"),
                "specialty": entry.get("specialty", ""),
                "avg_cost_per_person_usd": avg_cost_usd,
                "avg_cost_inr": round(avg_cost_usd * 84),
                "cost_for_group_usd": round(avg_cost_usd * num_people),
                "must_try": entry.get("must_try", []),
                "open": entry.get("open", "09:00"),
                "close": entry.get("close", "22:00"),
                "reservation_required": entry.get("reservation", False),
                "reservation_notes": entry.get("reservation_notes", ""),
                "rating": entry.get("rating", 4.0),
                "vegetarian_options": entry.get("vegetarian", False),
                "notes": entry.get("notes", ""),
            })
        if filtered:
            result[tier] = filtered

    result["destination"] = destination
    result["notes"] = city_food.get("food_notes", "")
    result["num_people"] = num_people
    return json.dumps(result)


@tool
def calculate_budget_breakdown(
    destination: str,
    trip_duration_days: int,
    num_people: int,
    accommodation_cost_usd: float,
    flight_cost_usd: float,
    travel_style: str = "moderate",
    currency: str = "INR",
) -> str:
    """
    Calculate a complete itemized budget breakdown for a trip.

    Returns JSON with: total_usd, per_person_usd, daily_spending_budget_usd,
    and itemized breakdown by category: flights, accommodation, food, local_transport,
    activities, shopping, emergency_fund (10%). Also returns money_saving_tips.
    When currency is INR, all monetary values are also returned in INR.

    travel_style: budget | moderate | comfortable | luxury
    accommodation_cost_usd: total accommodation cost for entire trip
    flight_cost_usd: total flight cost for all people (round-trip)
    currency: INR or USD — determines whether INR-converted values are included in output
    """
    INR_PER_USD = 84

    dest_costs = _find_dest_cost(destination)
    city_transport = _TRANSPORT.get("cities", {})
    transport_data = None
    for key in city_transport:
        if destination.lower() in key.lower() or key.lower() in destination.lower():
            transport_data = city_transport[key]
            break

    style = travel_style.lower()
    if style not in ("budget", "moderate", "comfortable", "luxury"):
        style = "moderate"

    # Daily food cost per person by style
    food_daily_per_person = {
        "budget": dest_costs.get("budget", 35) * 0.35,
        "moderate": dest_costs.get("moderate", 80) * 0.30,
        "comfortable": dest_costs.get("comfortable", 140) * 0.28,
        "luxury": dest_costs.get("luxury", 300) * 0.25,
    }[style]

    # Daily local transport per person
    transport_daily = {
        "budget": (transport_data or {}).get("daily_transport_budget_usd", {}).get("budget", 5),
        "moderate": (transport_data or {}).get("daily_transport_budget_usd", {}).get("moderate", 12),
        "comfortable": (transport_data or {}).get("daily_transport_budget_usd", {}).get("comfortable", 25),
        "luxury": (transport_data or {}).get("daily_transport_budget_usd", {}).get("comfortable", 25) * 2,
    }[style]

    # Activities/entrance fees per person per day
    activities_daily = {
        "budget": 8,
        "moderate": 18,
        "comfortable": 30,
        "luxury": 60,
    }[style]

    # Shopping allowance per person for whole trip
    shopping = {
        "budget": 50,
        "moderate": 150,
        "comfortable": 300,
        "luxury": 700,
    }[style]

    food_total = round(food_daily_per_person * trip_duration_days * num_people)
    transport_total = round(transport_daily * trip_duration_days * num_people)
    activities_total = round(activities_daily * trip_duration_days * num_people)
    shopping_total = round(shopping * num_people)

    subtotal = flight_cost_usd + accommodation_cost_usd + food_total + transport_total + activities_total + shopping_total
    emergency = round(subtotal * 0.10)
    total = subtotal + emergency

    tips_by_style = {
        "budget": [
            f"Eat at street stalls and markets — often the best food at 10% of restaurant prices",
            "Use public transport instead of taxis — usually 5-10x cheaper",
            "Book accommodation 3-4 weeks ahead for best hostel/budget hotel rates",
            "Visit free museums on their free-entry days (most museums have one)",
            "Cook simple meals at your accommodation a few times per week",
        ],
        "moderate": [
            "Book flights 6-8 weeks ahead for best prices — midweek flights are 20-30% cheaper",
            "Eat lunch at fine-dining restaurants — same kitchen, half the price of dinner",
            "Use city transport passes (day/weekly) instead of per-ride tickets",
            "Book tours directly through local operators instead of hotel desks",
            "Mix street food lunches with mid-range dinners to balance food budget",
        ],
        "comfortable": [
            "Book hotels with breakfast included — quality breakfast often costs $20+ separately",
            "Use Grab/Uber over taxis — more transparent pricing",
            "Combine 1-2 splurge meals with mid-range options to keep food costs balanced",
            "Check credit cards with no foreign transaction fees before traveling",
            "Research free or low-cost alternatives to expensive tourist attractions",
        ],
        "luxury": [
            "Book luxury hotels 3+ months ahead — last-minute prices can be 40% higher",
            "Use hotel concierge for restaurant reservations — they often secure better tables",
            "Consider private airport transfers — removes stress and often only $20-40 more",
            "Michelin star restaurants at lunch offer the same menu for 30-40% less",
            "Travel insurance covering luxury items (cameras, jewelry) is essential at this spend level",
        ],
    }

    breakdown = {
        "flights": round(flight_cost_usd),
        "accommodation": round(accommodation_cost_usd),
        "food": food_total,
        "local_transport": transport_total,
        "activities_and_entrance_fees": activities_total,
        "shopping_and_souvenirs": shopping_total,
        "emergency_fund_10pct": emergency,
    }

    result = {
        "destination": destination,
        "travel_style": style,
        "trip_duration_days": trip_duration_days,
        "num_people": num_people,
        "currency": currency.upper(),
        "exchange_rate": f"1 USD = {INR_PER_USD} INR",
        "total_usd": total,
        "per_person_usd": round(total / num_people),
        "daily_spending_budget_usd": round((total - flight_cost_usd) / trip_duration_days / num_people),
        "breakdown": breakdown,
        "breakdown_per_person": {k: round(v / num_people) for k, v in breakdown.items()},
        "food_detail": {
            "daily_per_person_usd": round(food_daily_per_person),
            "street_food_budget": round(food_daily_per_person * 0.3),
            "restaurant_budget": round(food_daily_per_person * 0.7),
        },
        "money_saving_tips": tips_by_style.get(style, tips_by_style["moderate"]),
    }

    if currency.upper() == "INR":
        result["total_inr"] = round(total * INR_PER_USD)
        result["per_person_inr"] = round((total / num_people) * INR_PER_USD)
        result["daily_spending_budget_inr"] = round(((total - flight_cost_usd) / trip_duration_days / num_people) * INR_PER_USD)
        result["breakdown_inr"] = {k: round(v * INR_PER_USD) for k, v in breakdown.items()}
        result["breakdown_per_person_inr"] = {k: round((v / num_people) * INR_PER_USD) for k, v in breakdown.items()}
        result["food_detail"]["daily_per_person_inr"] = round(food_daily_per_person * INR_PER_USD)
        result["food_detail"]["street_food_budget_inr"] = round(food_daily_per_person * 0.3 * INR_PER_USD)
        result["food_detail"]["restaurant_budget_inr"] = round(food_daily_per_person * 0.7 * INR_PER_USD)

    return json.dumps(result)
