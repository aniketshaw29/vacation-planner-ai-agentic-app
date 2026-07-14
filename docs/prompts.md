# Prompt Design

## System Prompt (`agent/prompts.py`)

The system prompt is **static** — it never changes per request. This is intentional: it allows the LLM provider to cache it, reducing latency and cost. User preferences are injected into the **human turn** instead.

```
SYSTEM_PROMPT_TEMPLATE = """
You are an expert vacation planner AI with deep knowledge of global destinations,
travel logistics, local cuisine, budget management, and route optimization.

## Your Capabilities
You help users plan perfect vacations by:
1. Suggesting destinations matched to their preferences
2. Building day-by-day itineraries with specific timings and visit order
3. Finding flights and hotels within budget
4. Planning optimal visit sequences based on opening hours and travel time
5. Comparing all transport options with real costs
6. Recommending food spots with price tiers for every budget
7. Providing complete budget breakdowns with money-saving tips

## Tool Usage Rules
- ALWAYS use your tools to get specific data — never guess prices, timings, or availability
- Call multiple tools in sequence when needed (e.g., destinations → flights → hotels → budget)
- Use user preferences from the <user_preferences> block to filter tool parameters
- If a user asks a follow-up question about a previous destination, reuse that destination in tool calls

## Response Formatting Rules
- After using tools, present results in a clear, friendly, conversational tone
- Wrap structured data in XML tags so the UI can render them as visual panels:

  For destination suggestions:
  <destinations_data>[{"name": "...", "country": "...", "match_score": 92, ...}]</destinations_data>

  For itinerary:
  <itinerary_data>[{"day": 1, "morning": {...}, "afternoon": {...}, "evening": {...}}]</itinerary_data>

  For route plan:
  <route_data>[{"order": 1, "place": "...", "arrive": "09:00", "duration": 2, "transit_to_next": "..."}]</route_data>

  For budget breakdown:
  <budget_data>{"total_usd": 3200, "per_person_usd": 1600, "breakdown": {...}}</budget_data>

  For food suggestions:
  <food_data>{"street_food": [...], "budget": [...], "mid_range": [...], "fine_dining": [...]}</food_data>

  For travel mode comparison:
  <transport_data>[{"mode": "flight", "cost_usd": 850, "duration_hours": 14, ...}]</transport_data>

- Always include a brief conversational summary above the structured data
- End with 1–2 actionable suggestions or follow-up questions to keep the conversation going

## Tone
- Friendly and enthusiastic but professional
- Specific and detailed — include real place names, neighborhoods, timing tips
- Proactively mention insider tips the user wouldn't know to ask about
"""
```

---

## Human Turn Template

Each user message is augmented with the current preference state:

```
Human: {user_message}

<user_preferences>
{
  "budget_usd": 3000,
  "budget_per_person_usd": 1500,
  "trip_duration_days": 7,
  "group_size": 2,
  "season": "summer",
  "travel_style": ["beach", "relaxation"],
  "accommodation_type": "hotel",
  "food_tier": ["mid_range", "street_food"],
  "dietary_restrictions": "none",
  "transport_modes": ["flight", "train", "bus", "scooter"],
  "origin_city": "New York",
  "provider": "groq"
}
</user_preferences>
```

**Why this design:**
- Preferences are always fresh — no stale state from previous turns
- Changing a slider and resending immediately updates the agent's behavior
- System prompt stays static → eligible for prompt caching

---

## Prompt for Each Tool (docstrings)

LangChain reads the function docstring as the tool description for the LLM. These must be clear and precise so the LLM calls the right tool with the right arguments.

### `suggest_destinations`
```
Suggest vacation destinations based on user preferences.
Returns a JSON list of top 5 destination cards with: name, country, description,
travel_styles, estimated_daily_cost_usd (by style), best_seasons, weather_summary,
highlight_activities, must_see_places, and match_score (0-100).

Use user preferences from <user_preferences> to fill parameters.
travel_style: one of adventure, relaxation, cultural, foodie, beach, city, nature, romance
season: spring, summer, autumn, winter
```

### `build_itinerary`
```
Build a detailed day-by-day itinerary for a specific destination.
Returns JSON: list of days, each with morning/afternoon/evening slots.
Each slot has: activity_name, place_name, description, duration_hours,
open_time, close_time, best_visiting_time, estimated_cost_usd, transit_from_previous.

interests: comma-separated, e.g. "temples,food,beaches,hiking"
```

### `plan_route`
```
Plan an optimized visit sequence for a list of places at a destination.
Considers: geographic proximity, opening hours, crowd peak times, best visiting times.
Returns JSON: ordered visit list with arrival time, time spent, transit to next place,
total trip duration, and timing notes (e.g. "visit before 10am to avoid crowds").

places_to_visit: comma-separated place names from the destination
transport_mode: walking, taxi, public_transport, rental_scooter, mixed
```

### `compare_travel_modes`
```
Compare all travel options between two cities or for a trip.
Evaluates: flight, train, bus, rental_car, bike, scooter.
Returns JSON with each mode: availability, total_cost_usd, cost_per_person_usd,
travel_time_hours, comfort (1-5), flexibility (1-5), eco_rating (1-5), best_for.
Sorted from cheapest to most expensive.
```

### `calculate_budget_breakdown`
```
Calculate a complete itemized budget for a trip.
Returns JSON: total_usd, per_person_usd, daily_spending_budget_usd,
and breakdown by category: flights, accommodation, food (with tiers),
local_transport, activities, shopping, emergency_fund (10%).
Also returns: money_saving_tips (3-5 specific actionable tips).
```

---

## Conversation Flow Examples

### Example 1: First-time user, no preferences set
```
User: "Plan me a vacation"
Agent: → calls suggest_destinations(budget=3000, style="balanced", season="summer", group=2, days=7)
       → returns top 5 destinations
       → asks follow-up: "Which of these catches your eye? Or tell me more about your ideal trip!"
```

### Example 2: User has specific destination in mind
```
User: "I want to go to Bali for 10 days, budget $2000"
Agent: → calls search_flights(origin="New York", dest="Bali", ...)
       → calls search_hotels(dest="Bali", nights=10, ...)
       → calls calculate_budget_breakdown(dest="Bali", duration=10, flight_cost=900, hotel_cost=600)
       → returns full trip cost breakdown
       → asks: "Want me to build a day-by-day itinerary for Bali?"
```

### Example 3: User asks about getting around
```
User: "How should we get around Bali? Is renting a scooter worth it?"
Agent: → calls compare_travel_modes(origin="Bali", dest="within Bali", num_people=2)
       → calls estimate_rental_costs(dest="Bali", type="scooter", days=10, units=1)
       → presents comparison: scooter vs taxi vs private driver
       → includes rental cost breakdown and safety tips
```

### Example 4: Route planning
```
User: "We want to visit Tanah Lot, Uluwatu, and Tegallalang Rice Terraces in one day"
Agent: → calls plan_route(dest="Bali", places="Tanah Lot,Uluwatu,Tegallalang Rice Terraces", ...)
       → returns optimized order: Tegallalang (7am) → Tanah Lot (11am) → Uluwatu (sunset at 6pm)
       → explains WHY this order (avoids crowds, catches sunset at Uluwatu cliff)
```
