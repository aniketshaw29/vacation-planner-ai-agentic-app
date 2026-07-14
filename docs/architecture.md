# Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                                  │
│                                                                      │
│  ┌─────────────────────┐    ┌────────────────────────────────────┐  │
│  │     SIDEBAR          │    │         MAIN CHAT AREA             │  │
│  │                      │    │                                    │  │
│  │  Budget slider       │    │  Chat messages (streaming)         │  │
│  │  Duration picker     │    │  Tool call indicators              │  │
│  │  Group size          │    │                                    │  │
│  │  Season chips        │    │  ── Result Panels ──               │  │
│  │  Travel style        │    │  Destination cards                 │  │
│  │  Accommodation       │    │  Itinerary timeline                │  │
│  │  Food tiers          │    │  Route sequence                    │  │
│  │  Dietary prefs       │    │  Cost breakdown table              │  │
│  │  Transport modes     │    │  Food cards                        │  │
│  │  AI model select     │    │                                    │  │
│  │                      │    │  ── Input Bar ──                   │  │
│  │  [Apply Prefs]       │    │  [Type message...] [Send]          │  │
│  └─────────────────────┘    └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                │ POST /api/chat (SSE)
                ▼
┌──────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND (main.py)                 │
│                                                              │
│  POST /api/chat  ─────────►  AgentExecutor.astream_events()  │
│  GET  /api/health           SSE stream back to browser       │
│  GET  /api/session/{id}                                      │
│  DEL  /api/session/{id}                                      │
│  GET  /  ─────────────────► static/index.html                │
└──────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│                    LANGCHAIN AGENT LAYER                      │
│                                                              │
│  agent/agent.py                                              │
│    create_tool_calling_agent(llm, ALL_TOOLS, prompt)         │
│    AgentExecutor(agent, tools, max_iterations=10)            │
│                                                              │
│  agent/providers.py                                          │
│    get_llm("groq" | "gemini" | "openai")                     │
│                                                              │
│  agent/memory.py                                             │
│    SessionMemory { session_id → [HumanMsg, AIMsg, ...] }     │
│                                                              │
│  agent/prompts.py                                            │
│    SYSTEM_PROMPT_TEMPLATE (static, cache-friendly)           │
└──────────────────────────────────────────────────────────────┘
                │ calls tools
                ▼
┌──────────────────────────────────────────────────────────────┐
│                      TOOLS LAYER                              │
│                                                              │
│  suggest_destinations      → reads mock_destinations.json    │
│  build_itinerary           → reads mock_destinations.json    │
│  search_flights            → reads mock_flights.json         │
│  search_hotels             → reads mock_hotels.json          │
│  plan_route                → reads mock_transport.json       │
│  compare_travel_modes      → reads mock_transport.json       │
│  estimate_rental_costs     → reads mock_transport.json       │
│  suggest_food              → reads mock_food.json            │
│  calculate_budget_breakdown → reads all mocks                │
└──────────────────────────────────────────────────────────────┘
                │ reads
                ▼
┌──────────────────────────────────────────────────────────────┐
│                       DATA LAYER                              │
│                                                              │
│  data/mock_destinations.json   (20+ destinations)            │
│  data/mock_flights.json        (routes × airlines × times)   │
│  data/mock_hotels.json         (hotels × cities × types)     │
│  data/mock_food.json           (restaurants × cities × tier) │
│  data/mock_transport.json      (modes × costs × durations)   │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow: User Message → Agent Response

```
1. USER TYPES MESSAGE + ADJUSTS SIDEBAR
   └─ JS collects all sidebar values into preferences object

2. SEND
   └─ POST /api/chat
      {
        message: "Plan a beach trip for 2",
        session_id: "uuid-xxx",
        provider: "groq",
        preferences: {
          budget_usd: 3000,
          trip_duration_days: 7,
          group_size: 2,
          season: "summer",
          travel_style: ["beach", "relaxation"],
          ...
        }
      }

3. FASTAPI HANDLER
   ├─ Validate ChatRequest (Pydantic)
   ├─ Get chat history from SessionMemory[session_id]
   ├─ Get LLM from providers.get_llm(provider)
   └─ Build agent input:
      {
        input: "Plan a beach trip for 2\n\n<user_preferences>{json}</user_preferences>",
        chat_history: [HumanMessage(...), AIMessage(...), ...],
        agent_scratchpad: []
      }

4. LANGCHAIN AGENT LOOP
   ├─ LLM receives: system_prompt + chat_history + user_message_with_prefs
   ├─ LLM decides: call suggest_destinations(budget=1500, style="beach", season="summer", ...)
   ├─ Tool executes: filters mock_destinations.json → returns top 5 matches as JSON
   ├─ LLM receives tool result, decides: call search_flights(origin="New York", dest="Bali", ...)
   ├─ Tool executes: looks up mock_flights.json → returns options
   └─ LLM generates final response with structured tags

5. SSE STREAM BACK TO BROWSER
   ├─ {"type": "tool_start", "tool": "suggest_destinations"}  → show spinner
   ├─ {"type": "tool_end", "tool": "suggest_destinations"}    → checkmark
   ├─ {"type": "token", "content": "Here are"}               → append text
   ├─ {"type": "token", "content": " some great"}            → append text
   ├─ ... (hundreds of token events)
   └─ {"type": "done"}                                         → parse result panels

6. FRONTEND RENDERS
   ├─ Parses <destinations_data>[...]</destinations_data> → destination cards
   ├─ Parses <itinerary_data>[...]</itinerary_data> → timeline
   ├─ Parses <budget_data>[...]</budget_data> → cost table
   └─ Saves full response to memory → ready for next turn
```

---

## Session Memory Design

**In-memory only** (no database). Resets on server restart/Render sleep. Fine for a vacation planner — no sensitive data, sessions are short-lived.

```python
# Structure in memory.py
_sessions = {
  "uuid-abc": [
    HumanMessage("I want to go to Bali"),
    AIMessage("Great choice! Bali is perfect for..."),
    HumanMessage("What hotels are available there?"),
    AIMessage("Here are some hotels in Bali..."),
  ],
  "uuid-xyz": [...]
}
```

- Max 20 turns (40 messages) per session — older turns dropped
- No persistence needed: vacation planning sessions are naturally short
- Sessions identified by UUID generated in the browser on page load

---

## Suggestion Engine Logic

### How `suggest_destinations` Works

```
Input: budget_per_person, travel_style, season, group_size, trip_duration

Step 1: Load mock_destinations.json (20+ destinations, loaded once at import)

Step 2: Hard filter
  - estimated_daily_cost_usd[style] × duration ≤ budget_per_person × 0.6
    (60% of budget for accommodation+food, 40% reserved for flights)
  - season ∈ destination.best_seasons

Step 3: Score remaining destinations (0–100)
  score = 0
  + 40 pts: travel_style overlap (styles_matched / total_styles × 40)
  + 30 pts: budget fit (closer to ideal spend = higher score)
  + 20 pts: season match quality (primary vs secondary season)
  + 10 pts: trip_duration fit (typical_stay_days proximity)

Step 4: Return top 5 sorted by score, as JSON
```

### How `plan_route` Works (visit sequencing)

```
Input: destination, places_to_visit (comma-separated), transport_mode

Step 1: Load place metadata from mock_destinations.json
  - Each place has: open_time, close_time, best_visit_time, duration_hours,
    lat/lon (approximate), crowd_peak_hours

Step 2: Cluster by geographic proximity (simple distance grouping)

Step 3: Within each cluster, sort by:
  1. Morning-only places first (temples, markets that close at noon)
  2. Flexible places mid-day
  3. Evening places last (sunset spots, night markets)

Step 4: Add transit time between stops (from mock_transport.json lookup)

Step 5: Build timeline with arrival time, duration, departure time, transit to next

Step 6: Return ordered sequence as JSON
```

### How Budget Calculation Works

```
Input: destination, duration, group_size, accommodation_cost, flight_cost, style

Categories:
  flights         = flight_cost (provided)
  accommodation   = accommodation_cost × duration
  food            = daily_food_cost[style][destination] × duration × group_size
  local_transport = transport_daily[destination] × duration × group_size
  activities      = activity_budget[style] × duration × group_size
  shopping        = shopping_allowance[style] × group_size
  emergency       = subtotal × 0.10  (10% buffer)

  TOTAL = sum of all categories
  per_person = TOTAL / group_size
  daily_budget = TOTAL / duration / group_size
```

---

## LLM Provider Abstraction

```
providers.py
  get_llm(provider: str) → BaseChatModel
    "groq"   → ChatGroq(model="llama-3.1-70b-versatile")  [FREE, default]
    "gemini" → ChatGoogleGenerativeAI(model="gemini-1.5-flash")  [paid, optional]
    "openai" → ChatOpenAI(model="gpt-4o-mini")  [paid, optional]

Available providers detected at startup:
  available = ["groq"]  # always
  if GOOGLE_API_KEY in env: available.append("gemini")
  if OPENAI_API_KEY in env: available.append("openai")

Returned in /api/health response → frontend builds dropdown dynamically
```
