import json
from pathlib import Path
from langchain_core.tools import tool
from tools.currency import to_inr

_TRANSPORT_PATH = Path(__file__).parent.parent / "data" / "mock_transport.json"
_TRANSPORT: dict = json.loads(_TRANSPORT_PATH.read_text())


def _city_transport(city: str) -> dict:
    cities = _TRANSPORT.get("cities", {})
    for key in cities:
        if city.lower() in key.lower() or key.lower() in city.lower():
            return cities[key]
    return {}


@tool
def compare_travel_modes(
    origin: str,
    destination: str,
    num_people: int = 1,
    days_needed: int = 1,
    distance_km: float = None,
) -> str:
    """
    Compare all available travel modes between two cities or for getting around a destination.

    Returns a JSON list of transport options sorted from cheapest to most expensive.
    Each mode includes: mode, availability, total_cost_usd, cost_per_person_usd,
    duration_hours (one-way), comfort (1-5), flexibility (1-5), eco_rating (1-5),
    best_for description, and notes.

    Use this when the user asks: "How should we get around?", "Is renting a scooter worth it?",
    "How do I get from X to Y?", "Compare transport options"
    """
    city_data = _city_transport(destination)
    modes_data = city_data.get("modes", {})

    results = []

    if not modes_data:
        # Use inter-city defaults
        inter = _TRANSPORT.get("inter_city", {})
        costs = inter.get("approx_costs_per_100km_usd", {})
        dist = distance_km or 500
        for mode, cost_per_100 in costs.items():
            total = round(cost_per_100 * dist / 100 * num_people)
            results.append({
                "mode": mode.replace("_", " ").title(),
                "available": True,
                "total_cost_usd": total,
                "cost_per_person_usd": round(total / num_people),
                "duration_hours": round(dist / {"flight": 900, "train": 200, "bus": 80, "car_rental_split_2": 100, "budget_airline": 900}.get(mode, 100), 1),
                "comfort": {"flight": 4, "train": 4, "bus": 2, "car_rental_split_2": 3, "budget_airline": 3}.get(mode, 3),
                "flexibility": {"flight": 2, "train": 3, "bus": 2, "car_rental_split_2": 5, "budget_airline": 2}.get(mode, 3),
                "eco_rating": {"flight": 1, "train": 5, "bus": 4, "car_rental_split_2": 3, "budget_airline": 2}.get(mode, 3),
                "best_for": "Inter-city travel",
                "notes": "",
            })
        results.sort(key=lambda x: x["total_cost_usd"])
        return json.dumps(results)

    # Local transport modes
    mode_meta = {
        "scooter_rental": {"comfort": 2, "flexibility": 5, "eco": 4, "best_for": "Flexible sightseeing, getting off the beaten path"},
        "bicycle_rental": {"comfort": 2, "flexibility": 5, "eco": 5, "best_for": "Short distances, flat cities, eco-conscious travelers"},
        "taxi_ride_share": {"comfort": 4, "flexibility": 4, "eco": 2, "best_for": "Airport transfers, late night, direct routes"},
        "private_driver": {"comfort": 5, "flexibility": 4, "eco": 2, "best_for": "Day trips, families with luggage, comfort seekers"},
        "subway_bus": {"comfort": 3, "flexibility": 3, "eco": 5, "best_for": "Budget travelers, locals, frequent short trips"},
        "tram_metro": {"comfort": 3, "flexibility": 3, "eco": 5, "best_for": "City sightseeing, frequent short trips"},
        "metro": {"comfort": 3, "flexibility": 3, "eco": 5, "best_for": "City sightseeing, frequent short trips"},
        "bus": {"comfort": 2, "flexibility": 2, "eco": 5, "best_for": "Cheapest option, good for long waits"},
        "bts_skytrain": {"comfort": 4, "flexibility": 3, "eco": 5, "best_for": "Avoiding Bangkok traffic jams"},
        "jr_pass_subway": {"comfort": 4, "flexibility": 3, "eco": 5, "best_for": "Comprehensive Japan transit"},
        "rental_car": {"comfort": 4, "flexibility": 5, "eco": 2, "best_for": "Countries/regions (Iceland, rural areas), families"},
        "motorbike_rental": {"comfort": 2, "flexibility": 5, "eco": 4, "best_for": "Experienced riders, mountain roads"},
        "walking": {"comfort": 3, "flexibility": 5, "eco": 5, "best_for": "City centers, sightseeing on foot"},
        "canal_boat": {"comfort": 4, "flexibility": 3, "eco": 4, "best_for": "Scenic city exploration"},
        "water_taxi": {"comfort": 3, "flexibility": 3, "eco": 3, "best_for": "Crossing waterways quickly"},
        "boat": {"comfort": 3, "flexibility": 3, "eco": 3, "best_for": "River travel, island hopping"},
        "grab": {"comfort": 4, "flexibility": 4, "eco": 2, "best_for": "Convenient door-to-door, cashless"},
        "tuk_tuk": {"comfort": 2, "flexibility": 4, "eco": 3, "best_for": "Short hops, local experience, bargaining"},
        "organized_tour": {"comfort": 4, "flexibility": 1, "eco": 4, "best_for": "First-timers, Northern Lights tours, day trips"},
        "speedboat": {"comfort": 3, "flexibility": 3, "eco": 2, "best_for": "Island transfers"},
        "seaplane": {"comfort": 4, "flexibility": 2, "eco": 1, "best_for": "Remote resort transfers, spectacular views"},
        "dhoni_boat": {"comfort": 3, "flexibility": 3, "eco": 4, "best_for": "Island hopping, local experience"},
        "cable_car": {"comfort": 4, "flexibility": 1, "eco": 4, "best_for": "Sugarloaf, scenic viewpoints"},
        "mrt_subway": {"comfort": 4, "flexibility": 3, "eco": 5, "best_for": "Singapore city travel"},
        "colectivos": {"comfort": 2, "flexibility": 3, "eco": 4, "best_for": "Cheapest Mexico peninsula travel"},
        "bus_ado": {"comfort": 3, "flexibility": 2, "eco": 4, "best_for": "Mexico city-to-city travel"},
    }

    for mode_key, mode_info in modes_data.items():
        meta = mode_meta.get(mode_key, {"comfort": 3, "flexibility": 3, "eco": 3, "best_for": "General use"})

        # Calculate cost for the given number of days/people
        daily = mode_info.get("daily_usd") or mode_info.get("daily_rate_usd")
        weekly = mode_info.get("weekly_usd") or mode_info.get("weekly_rate_usd")
        per_ride = mode_info.get("per_ride_usd")
        day_pass = mode_info.get("day_pass_usd")
        half_day = mode_info.get("half_day_usd")
        full_day = mode_info.get("full_day_usd")

        if daily:
            if weekly and days_needed >= 6:
                base_cost = weekly
            else:
                base_cost = daily * days_needed
            fuel = mode_info.get("fuel_per_day_usd", 0) * days_needed
            deposit = mode_info.get("deposit_usd", 0)
            total = round((base_cost + fuel) * max(num_people // 2 if "rental" in mode_key else num_people, 1))
        elif day_pass:
            total = round(day_pass * days_needed * num_people)
        elif per_ride:
            total = round(per_ride * 8 * days_needed * num_people)  # assume 8 rides/day
        elif full_day:
            total = round(full_day * days_needed)  # shared vehicle
        elif half_day:
            total = round(half_day * 2 * days_needed)
        elif mode_info.get("avg_city_ride_usd"):
            total = round(mode_info["avg_city_ride_usd"] * 6 * days_needed * num_people)  # 6 rides/day
        elif mode_info.get("transfer_usd"):
            total = mode_info["transfer_usd"] * num_people
        else:
            total = 0

        results.append({
            "mode": mode_key.replace("_", " ").title(),
            "mode_key": mode_key,
            "available": mode_info.get("available", True),
            "total_cost_inr": to_inr(total),
            "cost_per_person_inr": to_inr(round(total / max(num_people, 1))),
            "duration_hours": 0,
            "comfort": meta["comfort"],
            "flexibility": meta["flexibility"],
            "eco_rating": meta["eco"],
            "best_for": meta["best_for"],
            "notes": mode_info.get("notes", ""),
            "deposit_inr": to_inr(mode_info.get("deposit_usd", 0)),
            "license_required": mode_info.get("license_required", False),
        })

    results.sort(key=lambda x: x["total_cost_inr"])
    return json.dumps(results)


@tool
def estimate_rental_costs(
    destination: str,
    rental_type: str,
    rental_days: int,
    num_units: int = 1,
) -> str:
    """
    Estimate rental costs for bikes, scooters, or motorbikes at a destination.

    Returns JSON with: daily_rate_usd, weekly_rate_usd, total_cost_usd, deposit_usd,
    fuel_cost_usd (for motorised), license_required, helmet_included,
    available_types (list), tips for renting locally.

    rental_type: bicycle | electric_bicycle | scooter | motorbike
    rental_days: number of days you need the rental
    num_units: number of bikes/scooters to rent
    """
    city_data = _city_transport(destination)
    modes = city_data.get("modes", {})

    type_map = {
        "bicycle": ["bicycle_rental"],
        "electric_bicycle": ["bicycle_rental"],
        "scooter": ["scooter_rental"],
        "motorbike": ["motorbike_rental", "scooter_rental"],
    }
    keys_to_try = type_map.get(rental_type.lower(), ["scooter_rental", "bicycle_rental"])

    rental_data = None
    for key in keys_to_try:
        if key in modes:
            rental_data = modes[key]
            break

    if not rental_data:
        return json.dumps({
            "rental_type": rental_type,
            "destination": destination,
            "available": False,
            "message": f"No {rental_type} rental data found for {destination}. Check local tour operators.",
        })

    daily = rental_data.get("daily_usd", rental_data.get("daily_rate_usd", 10))
    weekly = rental_data.get("weekly_usd", rental_data.get("weekly_rate_usd", daily * 6))
    electric_daily = rental_data.get("electric_daily_usd", rental_data.get("electric_daily_rate_usd"))

    if rental_days >= 6 and weekly:
        base_cost = weekly
        weeks = 1
        extra_days = max(0, rental_days - 7)
        base_cost += extra_days * daily
    else:
        base_cost = daily * rental_days

    base_cost *= num_units
    fuel = rental_data.get("fuel_per_day_usd", 0) * rental_days * num_units
    deposit = rental_data.get("deposit_usd", 0) * num_units

    result = {
        "rental_type": rental_type,
        "destination": destination,
        "available": True,
        "daily_rate_inr": to_inr(daily),
        "weekly_rate_inr": to_inr(weekly),
        "electric_daily_rate_inr": to_inr(electric_daily) if electric_daily else None,
        "total_cost_inr": to_inr(round(base_cost + fuel)),
        "fuel_cost_inr": to_inr(round(fuel)),
        "deposit_inr": to_inr(deposit),
        "license_required": rental_data.get("license_required", False),
        "license_type": rental_data.get("license_type", "Driver's license"),
        "helmet_included": rental_data.get("helmet_included", True),
        "num_units": num_units,
        "rental_days": rental_days,
        "cost_breakdown": f"₹{to_inr(daily)}/day × {rental_days} days × {num_units} unit(s)"
                          + (f" + ₹{to_inr(fuel)} fuel" if fuel else "")
                          + f" = ₹{to_inr(round(base_cost + fuel))}",
        "tips": rental_data.get("notes", ""),
    }
    return json.dumps(result)
