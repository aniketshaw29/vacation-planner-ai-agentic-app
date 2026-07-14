from tools.destinations import suggest_destinations
from tools.itinerary import build_itinerary
from tools.flights_hotels import search_flights, search_hotels
from tools.route_planner import plan_route
from tools.travel_modes import compare_travel_modes, estimate_rental_costs
from tools.food_budget import suggest_food, calculate_budget_breakdown

ALL_TOOLS = [
    suggest_destinations,
    build_itinerary,
    search_flights,
    search_hotels,
    plan_route,
    compare_travel_modes,
    estimate_rental_costs,
    suggest_food,
    calculate_budget_breakdown,
]

__all__ = ["ALL_TOOLS"]
