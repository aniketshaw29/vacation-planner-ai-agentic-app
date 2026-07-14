# Vacation Planner AI Agent

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg?style=flat-square&logo=python)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.26-green.svg?style=flat-square)](https://python.langchain.com/)
[![Gemini](https://img.shields.io/badge/Gemini-Free%20Tier-4285F4.svg?style=flat-square&logo=google)](https://aistudio.google.com/apikey)
[![Deploy on Render](https://img.shields.io/badge/Render-Deploy-46E3B7.svg?style=flat-square&logo=render)](https://render.com/)

An AI-powered vacation planning assistant built on a **modular LLM architecture** — plug in Gemini, Groq, OpenAI, Anthropic, or any LangChain-compatible model. The default provider is **Google Gemini** (genuinely free: 1,500 requests/day, no credit card). Built with LangChain tool-calling agents and a FastAPI streaming backend; ask anything about destinations, flights, hotels, itineraries, routes, food, or budgets and get rich responses rendered as interactive panels, streamed token-by-token in real time.

> **Connect any LLM** — the provider system auto-detects whichever API keys you set in `.env`. Swap providers without changing a line of code.

---

## Features

### 9 AI Agent Tools
- **suggest_destinations** — Scores and ranks up to 5 destinations from mock data based on budget fit, season, travel style, and trip duration
- **build_itinerary** — Constructs a day-by-day itinerary with morning/afternoon/evening time blocks, entrance fees, and meal cost estimates
- **search_flights** — Queries mock flight data with seasonal price multipliers and group discounts for 5+ or 10+ travelers
- **search_hotels** — Returns up to 6 accommodation options with nightly rates, amenities, and multi-night total pricing
- **plan_route** — Builds a time-sequenced visit plan for a list of attractions, including transit times and crowd-level tips
- **compare_travel_modes** — Compares local and inter-city transport options sorted cheapest-first with full cost breakdowns
- **estimate_rental_costs** — Returns daily and weekly rental costs for bicycles, scooters, and motorbikes with deposit and license details
- **suggest_food** — Filters restaurants and food options by price tier (street food through fine dining) and dietary restrictions
- **calculate_budget_breakdown** — Produces an itemized per-person and per-day budget across accommodation, food, transport, and activities with a 10% emergency buffer

### UI and UX
- **Rich interactive panels** — Destinations, itineraries, routes, budgets, food, and transport results rendered as structured cards parsed from XML-tagged JSON in the LLM stream
- **Sidebar with 10+ preference controls** — Budget slider, trip duration, group size, origin city, season picker, travel style chips, accommodation tier, food tier, dietary restrictions, and preferred transport modes
- **Streaming responses** — Token-by-token output via Server-Sent Events with live tool-call progress indicators
- **Multi-turn conversation memory** — Rolling 20-turn session history so the agent remembers everything you discussed earlier
- **Prompt suggestions** — One-click example prompts to get started instantly
- **Session management** — Each browser tab gets its own session ID; clear history with one click

### Developer and Deployment Friendly
- **Modular LLM providers** — Groq (free, default), Google Gemini, and OpenAI are auto-detected from environment variables at startup; switching providers requires only adding an API key
- **Free deployment** — Deploys to Render's free tier with a single `render.yaml`; no paid infrastructure required
- **Zero external API calls** — All tools read from static mock JSON files, so the app runs fully offline without any travel API subscriptions

---

## Tech Stack

| Layer | Technology | Cost |
|---|---|---|
| LLM (default) | [Google Gemini 2.5 Flash](https://aistudio.google.com/) | Gemini 2.5 Flash — best price-performance for agentic tasks |
| LLM (optional) | Groq LLaMA 3.1 70B | Pay-as-you-go — **no free tier**, requires prepaid balance |
| LLM (optional) | OpenAI GPT-4o Mini | Paid |
| LLM (optional) | Anthropic Claude 3.5 Haiku | Paid |
| Agent Framework | [LangChain](https://python.langchain.com/) 0.3 | Free / open source |
| Backend | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) | Free / open source |
| Frontend | Vanilla HTML/CSS/JS — single static file | Free |
| Data | Static mock JSON files | Free |
| Deployment | [Render](https://render.com/) free web service | Free tier |

> **Any LangChain-compatible model works.** The provider is selected by which API key(s) you set in `.env` — no code changes required.

---

## Project Structure

```
vacationPlannerAgentic/
│
├── main.py                    # FastAPI app — SSE /api/chat endpoint, session routes, provider check at startup
├── requirements.txt           # Core dependencies (Groq default); Gemini/OpenAI providers commented out
├── render.yaml                # Render free-tier deployment config — sets GROQ_API_KEY env var
├── .env.example               # Template listing GROQ_API_KEY (required) and optional paid provider keys
│
├── agent/
│   ├── agent.py               # Builds LangChain AgentExecutor (cached per provider); run_agent_stream yields SSE events
│   ├── providers.py           # get_llm() returns a configured chat model; available_providers() checks env keys
│   ├── memory.py              # In-memory session store — rolling 20-turn window of HumanMessage/AIMessage pairs
│   └── prompts.py             # SYSTEM_PROMPT_TEMPLATE — tool rules, XML tag schemas, response format instructions
│
├── tools/
│   ├── __init__.py            # Aggregates all @tool functions into ALL_TOOLS list for agent registration
│   ├── destinations.py        # suggest_destinations — scored destination recommendations from mock JSON
│   ├── itinerary.py           # build_itinerary — day-by-day time-blocked itinerary builder
│   ├── flights_hotels.py      # search_flights, search_hotels — mock data queries with seasonal pricing
│   ├── route_planner.py       # plan_route — time-sequenced attraction visit plan with transit times
│   ├── travel_modes.py        # compare_travel_modes, estimate_rental_costs — local transport cost tools
│   └── food_budget.py         # suggest_food, calculate_budget_breakdown — food search and trip budget tools
│
├── data/
│   ├── mock_destinations.json # Destination records with places, cost tiers, seasons, travel styles
│   ├── mock_flights.json      # Route-keyed flight data with seasonal multipliers and group discounts
│   ├── mock_hotels.json       # City-keyed hotel listings with nightly rates and amenities
│   ├── mock_food.json         # City-keyed food options segmented by price tier
│   └── mock_transport.json    # City transport modes and inter-city transit times/costs
│
├── static/
│   └── index.html             # Single-page chat UI — SSE client, XML panel renderer, preference sidebar
│
└── docs/
    ├── architecture.md        # Full system architecture, data flow, session design, tool logic overview
    ├── prompts.md             # Prompt design docs — system prompt, human turn template, tool docstrings
    └── data-schema.md         # JSON schemas for all five mock data files with annotated examples
```

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/vacationPlannerAgentic.git
cd vacationPlannerAgentic
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and add your API key. **Google Gemini is recommended** — it has a genuine free tier (1,500 requests/day, no credit card required).

```dotenv
# .env

# Recommended: Gemini free tier — https://aistudio.google.com/apikey
GOOGLE_API_KEY=your_gemini_key_here

# Any of these also work (set as many as you want — all appear in the UI):
# GROQ_API_KEY=...       ⚠ pay-as-you-go, no free tier
# OPENAI_API_KEY=...     paid
# ANTHROPIC_API_KEY=...  paid
```

### 5. Start the Server

```bash
uvicorn main:app --reload --port 4949
```

You should see:

```
INFO:     Started server process
INFO:     Waiting for application startup.
✓ Vacation Planner started | Available providers: ['gemini'] | Default: gemini
✓ 9 tools loaded
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:4949
```

### 6. Open the App

Navigate to [http://localhost:4949](http://localhost:4949) in your browser. The dark-themed chat UI will load automatically.

Try a prompt like:

> "I want to plan a 7-day beach vacation for 2 people with a $3000 budget leaving from New York in July."

---

## Environment Variables

| Variable | Provider | Cost | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | Gemini 2.5 Flash | **Free** (1,500 req/day) | Get at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) — no credit card needed. **Recommended default.** |
| `GROQ_API_KEY` | Groq LLaMA 3.1 70B | Pay-as-you-go | ⚠ **No free tier** — requires a prepaid balance at [console.groq.com](https://console.groq.com) |
| `OPENAI_API_KEY` | GPT-4o Mini | Paid | [platform.openai.com](https://platform.openai.com) |
| `ANTHROPIC_API_KEY` | Claude 3.5 Haiku | Paid | [console.anthropic.com](https://console.anthropic.com) |

Set **at least one** key. The app auto-detects all configured keys at startup and populates the provider dropdown — priority order: Gemini → Groq → OpenAI → Anthropic.

---

## The 9 Agent Tools

| Tool | Description | Key Parameters | Data Source |
|---|---|---|---|
| `suggest_destinations` | Scores destinations by budget, season, style, and duration; returns top 5 | `budget_per_person`, `travel_style`, `season`, `trip_duration_days` | `mock_destinations.json` |
| `build_itinerary` | Builds a day-by-day plan with AM/PM/evening blocks and cost estimates | `destination`, `trip_duration_days`, `travel_style`, `group_size`, `interests` | `mock_destinations.json` |
| `search_flights` | Returns flight options with seasonal price multipliers and group discounts | `origin_city`, `destination`, `departure_date`, `num_passengers` | `mock_flights.json` |
| `search_hotels` | Returns up to 6 hotels with nightly rates and multi-night totals | `destination`, `check_in_date`, `check_out_date`, `num_guests` | `mock_hotels.json` |
| `plan_route` | Creates a time-sequenced visit plan for a list of attractions | `destination`, `places_to_visit`, `transport_mode` | `mock_destinations.json`, `mock_transport.json` |
| `compare_travel_modes` | Compares all local transport options, sorted cheapest-first | `destination`, `days_needed`, `num_people` | `mock_transport.json` |
| `estimate_rental_costs` | Returns daily/weekly rental costs for bicycle, scooter, or motorbike | `destination`, `rental_type`, `rental_days` | `mock_transport.json` |
| `suggest_food` | Filters restaurants by price tier and dietary restrictions | `destination`, `price_tier`, `dietary_restrictions`, `num_people` | `mock_food.json` |
| `calculate_budget_breakdown` | Produces itemized per-person and per-day trip budget with 10% emergency buffer | `destination`, `trip_duration_days`, `num_people`, `travel_style` | `mock_destinations.json`, `mock_transport.json` |

The agent selects and chains these tools automatically based on what you ask. A single message like "Plan my whole Bali trip" may invoke 4–5 tools in sequence.

---

## API Endpoints

| Method | Path | Description | Response |
|---|---|---|---|
| `POST` | `/api/chat` | Main chat endpoint — streams AI response as SSE | `text/event-stream` |
| `GET` | `/api/health` | Health check — returns available LLM providers | `{"status": "ok", "providers": [...]}` |
| `GET` | `/api/session/{session_id}` | Returns turn count for a session | `{"session_id": "...", "turn_count": N}` |
| `DELETE` | `/api/session/{session_id}` | Clears conversation history for a session | `{"status": "cleared"}` |
| `GET` | `/` | Serves `static/index.html` | HTML |

### SSE Event Types (`POST /api/chat`)

The streaming response emits newline-delimited `data:` events, each a JSON object:

| Event type | Payload | Description |
|---|---|---|
| `token` | `{"type": "token", "content": "..."}` | A single LLM output token |
| `tool_start` | `{"type": "tool_start", "tool": "suggest_destinations"}` | Agent is invoking a tool |
| `tool_end` | `{"type": "tool_end", "tool": "suggest_destinations", "output": "..."}` | Tool returned (output truncated to 400 chars) |
| `error` | `{"type": "error", "message": "..."}` | Unhandled exception during streaming |
| `done` | `{"type": "done"}` | Stream complete; session memory updated |

### ChatRequest Schema

```json
{
  "message": "Plan a 7-day trip to Bali",
  "session_id": "abc123",
  "provider": "groq",
  "preferences": {
    "budget_usd": 3000,
    "trip_duration_days": 7,
    "group_size": 2,
    "origin_city": "New York",
    "season": "summer",
    "travel_style": "beach,cultural",
    "accommodation_type": "hotel",
    "food_tier": ["mid_range", "street_food"],
    "dietary_restrictions": "none",
    "transport_modes": ["flight", "scooter", "bus"]
  }
}
```

---

## Frontend Features

### Sidebar Controls

The left sidebar collects your travel preferences and sends them with every message. All controls have sensible defaults so you can start chatting immediately:

| Control | Type | Default |
|---|---|---|
| Total Budget | Slider ($500–$15,000) | $3,000 |
| Trip Duration | Number stepper (1–30 days) | 7 days |
| Group Size | Number stepper (1–20 people) | 2 people |
| Origin City | Text input | New York |
| Season | Radio group (Spring / Summer / Autumn / Winter) | Summer |
| Travel Style | Multi-select chips (Beach, Cultural, Adventure, Foodie, Nature, City, Romance, Nightlife, Budget, Luxury) | Cultural + Foodie |
| Accommodation Type | Radio group (Hotel / Hostel / Airbnb / Resort / Boutique / Villa) | Hotel |
| Food Tier | Multi-select chips (Street Food / Budget / Mid-Range / Fine Dining) | Street Food + Mid-Range |
| Dietary Restrictions | Radio group (None / Vegetarian / Vegan / Halal / Gluten-Free) | None |
| Transport Modes | Multi-select chips (Flight / Train / Bus / Scooter / Bicycle / Car / Taxi) | All enabled |
| AI Model | Dropdown (auto-populated from `/api/health`) | Groq (free) |

### Result Panel Types

When the AI response contains structured XML-tagged data, the frontend strips it from the chat text and renders it as a dedicated visual panel:

| XML Tag | Panel | What it shows |
|---|---|---|
| `<destinations_data>` | Destination Cards | Scored list with match %, budget estimate, season fit, highlights — click any card to auto-ask for a full plan |
| `<itinerary_data>` | Day-by-Day Itinerary | Each day's morning/afternoon/evening slots with times, entrance fees, and daily cost totals |
| `<route_data>` | Route Planner | Time-sequenced stop list with transit times between stops, crowd warnings, and neighborhood info |
| `<budget_data>` | Budget Breakdown | Summary stats (total, per person, per day) + category bar chart + money-saving tips |
| `<food_data>` | Food Suggestions | Restaurant cards grouped by price tier (street food → fine dining) with must-try dishes |
| `<transport_data>` | Transport Comparison | Sorted cheapest-first table with comfort/flexibility/eco ratings per mode |

---

## Deployment to Render

The project ships with a ready-to-use `render.yaml` that deploys for free.

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/your-username/vacationPlannerAgentic.git
git push -u origin main
```

### 2. Create a New Web Service on Render

1. Go to [dashboard.render.com](https://dashboard.render.com/) and click **New > Web Service**
2. Connect your GitHub account and select the `vacationPlannerAgentic` repository
3. Render detects `render.yaml` automatically and pre-fills all settings:
   - **Name:** `vacation-planner`
   - **Runtime:** Python
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

### 3. Add Your API Key

In the Render dashboard for your service, go to **Environment** and add:

| Key | Value |
|---|---|
| `GOOGLE_API_KEY` | Your free Gemini key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |

You can add `GROQ_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY` in the same way to enable those providers too.

### 4. Deploy

Click **Deploy Web Service**. Render will build and start the app in ~2–3 minutes. Your live URL will be:

```
https://vacation-planner.onrender.com
```

> **Note:** Free-tier Render services spin down after 15 minutes of inactivity. The first request after a cold start may take 30–60 seconds to respond.

---

## Adding or Switching LLM Providers

The provider system auto-detects API keys at startup — **no code changes needed**. Just add a key to `.env` and reinstall if needed.

### Google Gemini (Default — Free)

Already included in `requirements.txt`. Just set:
```dotenv
GOOGLE_API_KEY=your_key_here
```
Get a free key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

### Groq (LLaMA 3.1 70B)

> ⚠ **Groq has no free tier.** Despite the fast sign-up flow, API calls require a prepaid balance. Previous promotional credits are no longer offered.

1. Uncomment in `requirements.txt`: `langchain-groq==0.3.2`
2. `pip install -r requirements.txt`
3. Set `GROQ_API_KEY=...` in `.env`

### OpenAI (GPT-4o Mini)

1. Uncomment in `requirements.txt`: `langchain-openai==0.2.14`
2. `pip install -r requirements.txt`
3. Set `OPENAI_API_KEY=...` in `.env`

### Anthropic (Claude 3.5 Haiku)

1. Uncomment in `requirements.txt`: `langchain-anthropic==0.3.15`
2. `pip install -r requirements.txt`
3. Set `ANTHROPIC_API_KEY=...` in `.env`

Once a key is present and the package installed, the provider appears automatically in the **AI Model** dropdown in the sidebar.

---

## Architecture

```
Browser (static/index.html)
        |
        |  POST /api/chat  (JSON — message + preferences + session_id)
        v
┌──────────────────────────────────────┐
│          FastAPI  (main.py)          │
│                                      │
│  • Validates ChatRequest (Pydantic)  │
│  • Injects preferences into message  │
│  • Returns StreamingResponse (SSE)   │
│    Cache-Control: no-cache           │
│    X-Accel-Buffering: no             │
└──────────────┬───────────────────────┘
               |
               |  async generator — run_agent_stream()
               v
┌──────────────────────────────────────┐
│      LangChain Agent (agent.py)      │
│                                      │
│  build_agent_executor(provider)      │
│    ├─ get_llm("groq"|"gemini"|...)   │
│    ├─ SYSTEM_PROMPT_TEMPLATE         │
│    ├─ ALL_TOOLS (9 @tool functions)  │
│    └─ AgentExecutor (cached)         │
│                                      │
│  astream_events(v2) yields:          │
│    ├─ on_chat_model_stream → token   │
│    ├─ on_tool_start → tool_start     │
│    ├─ on_tool_end   → tool_end       │
│    └─ exception     → error          │
│                                      │
│  session_memory.add_turn() on done   │
└──────────────┬───────────────────────┘
               |
               |  @tool invocations
               v
┌──────────────────────────────────────┐
│           Tools Layer                │
│                                      │
│  suggest_destinations                │
│  build_itinerary                     │
│  search_flights  / search_hotels     │
│  plan_route                          │
│  compare_travel_modes                │
│  estimate_rental_costs               │
│  suggest_food                        │
│  calculate_budget_breakdown          │
└──────────────┬───────────────────────┘
               |
               |  JSON file reads (once at import time)
               v
┌──────────────────────────────────────┐
│         data/  (mock JSON)           │
│                                      │
│  mock_destinations.json              │
│  mock_flights.json                   │
│  mock_hotels.json                    │
│  mock_food.json                      │
│  mock_transport.json                 │
└──────────────────────────────────────┘
               |
               |  SSE token stream back to browser
               v
Browser renders:
  • Live token text (streamed character by character)
  • Tool-call progress badges (spinner → checkmark)
  • XML-tagged panels: destinations, itinerary,
    route, budget, food, transport
```

### Session Memory Design

Each browser session is identified by a UUID generated client-side. The server-side `SessionMemory` singleton stores `HumanMessage` / `AIMessage` pairs in a `defaultdict[str, list]` keyed by session ID. History is capped at 20 turns (40 messages) per session — older turns are dropped when the limit is exceeded. Memory is in-process only and does not survive server restarts or Render sleep cycles.

---

## Contributing

Contributions are welcome. To get started:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-improvement`
3. Make your changes
4. Open a pull request with a clear description of what changed and why

Some good first contributions:
- Adding more destinations, routes, or flight data to the mock JSON files
- Implementing the remaining dietary restriction filters in [tools/food_budget.py](tools/food_budget.py) (vegan, halal, gluten-free are accepted inputs but not yet filtered)
- Fixing the cross-month nights calculation in [tools/flights_hotels.py](tools/flights_hotels.py)
- Adding a persistent session storage backend (SQLite or Redis) to [agent/memory.py](agent/memory.py)
- Writing a test suite in `tests/`

---

## License

This project is released under the [MIT License](LICENSE). You are free to use, modify, and distribute it for any purpose.
