# Phase-wise Development Plan

## Overview

| Phase | What | Files | Status |
|---|---|---|---|
| 1 | Project Scaffolding | requirements.txt, .env.example, .gitignore, render.yaml | ✅ Done |
| 2 | Mock Data | data/*.json (5 files) | ⬜ Next |
| 3 | Agent Infrastructure | agent/*.py (4 files) | ⬜ |
| 4 | Tools | tools/*.py (7 files, 9 tools) | ⬜ |
| 5 | FastAPI Backend | main.py | ⬜ |
| 6 | Frontend | static/index.html | ⬜ |
| 7 | Tests | tests/*.py | ⬜ |
| 8 | Deploy | Render + GitHub | ⬜ |

---

## Phase 1: Project Scaffolding ✅

**Goal:** Create the empty skeleton so every subsequent phase has a home.

**Files created:**
- `requirements.txt` — all Python deps (Groq, LangChain, FastAPI, etc.)
- `.env.example` — API key template
- `.gitignore` — excludes .env, venv, __pycache__
- `render.yaml` — Render free-tier deploy config
- `docs/` — architecture, prompts, data schema docs
- `dev-plan/` — this file and phase tracker
- Directory structure: `agent/`, `tools/`, `data/`, `static/`, `tests/`

**Verification:**
```bash
ls -la   # all dirs and config files present
```

---

## Phase 2: Mock Data

**Goal:** Create realistic JSON data files so tools return meaningful results without any external API.

**Files to create:**
```
data/
  mock_destinations.json   20+ destinations, rich metadata
  mock_flights.json        Routes keyed by ORIGIN->DEST, multiple airlines
  mock_hotels.json         Hotels keyed by city, multiple types and tiers
  mock_food.json           Restaurants keyed by city, grouped by price tier
  mock_transport.json      Transport modes keyed by city, rental prices
```

**Design principles:**
- Cover diverse destinations: Asia, Europe, Americas, budget to luxury
- Enough variety that preference filters return meaningfully different results
- Consistent schema so tools can trust field names

**Verification:**
```python
import json
data = json.load(open("data/mock_destinations.json"))
assert len(data) >= 20
assert all("estimated_daily_cost_usd" in d for d in data)
```

---

## Phase 3: Agent Infrastructure

**Goal:** Set up the LangChain agent layer — LLM selection, memory, prompts, agent executor.

**Files to create:**
```
agent/
  __init__.py      exports: get_agent_executor, session_memory
  providers.py     get_llm(provider) → ChatGroq | ChatGoogleGenerativeAI | ChatOpenAI
  memory.py        SessionMemory class — dict-backed, 20-turn cap
  prompts.py       SYSTEM_PROMPT_TEMPLATE (static for caching)
  agent.py         build_agent_executor(tools, provider) → AgentExecutor
                   run_agent_stream(message, session_id, preferences, provider) → async generator
```

**Key implementation: `run_agent_stream`**

This is the core function called by `main.py`. It:
1. Gets LLM from `providers.get_llm(provider)`
2. Builds `AgentExecutor` with all tools
3. Prepares input dict with history + preferences injected
4. Calls `astream_events(version="v2")`
5. Yields SSE-formatted JSON strings for each event

**Verification:**
```python
from agent import get_agent_executor
executor = get_agent_executor(provider="groq")
print(type(executor))  # AgentExecutor
```

---

## Phase 4: Tools

**Goal:** Implement all 9 `@tool` functions that read from mock data and return structured JSON.

**Files to create:**
```
tools/
  __init__.py           ALL_TOOLS list — imports all 9 tools
  destinations.py       suggest_destinations(budget, style, season, group, days)
  itinerary.py          build_itinerary(destination, days, style, group, interests)
  flights_hotels.py     search_flights(...), search_hotels(...)
  route_planner.py      plan_route(destination, places, start, transport)
  travel_modes.py       compare_travel_modes(...), estimate_rental_costs(...)
  food_budget.py        suggest_food(...), calculate_budget_breakdown(...)
```

**Tool implementation pattern:**
```python
from langchain_core.tools import tool
import json
from pathlib import Path

# Load once at module import (not per call)
_DATA = json.loads((Path(__file__).parent.parent / "data" / "mock_destinations.json").read_text())

@tool
def suggest_destinations(
    budget_usd_per_person: int,
    travel_style: str,
    season: str,
    group_size: int,
    trip_duration_days: int
) -> str:
    """Suggest vacation destinations based on user preferences. ..."""
    # filter + score logic
    return json.dumps(results)
```

**Verification:**
```python
from tools import ALL_TOOLS
assert len(ALL_TOOLS) == 9
result = ALL_TOOLS[0].invoke({"budget_usd_per_person": 2000, ...})
print(json.loads(result)[0]["name"])  # "Bali" or similar
```

---

## Phase 5: FastAPI Backend

**Goal:** Wire up the HTTP layer — SSE streaming, session management, static file serving.

**File: `main.py`**

Key sections:
1. `lifespan` — load env, validate GROQ_API_KEY present, log available providers
2. `ChatRequest` Pydantic model — validates all inputs, provides defaults
3. `POST /api/chat` — calls `run_agent_stream`, wraps in `StreamingResponse`
4. `GET /api/health` — returns model info + available providers
5. `GET/DEL /api/session/{id}` — memory management
6. `StaticFiles` mount — serves `static/` at `/`

**SSE generator function:**
```python
async def generate_sse(request: ChatRequest):
    try:
        async for event_json in run_agent_stream(...):
            yield f"data: {event_json}\n\n"
    except Exception as e:
        yield f'data: {{"type": "error", "message": "{str(e)}"}}\n\n'
    finally:
        yield f'data: {{"type": "done"}}\n\n'
```

**Verification:**
```bash
uvicorn main:app --reload
curl http://localhost:8000/api/health
# {"status": "ok", "providers": ["groq"], "default_provider": "groq"}
```

---

## Phase 6: Frontend

**Goal:** Build the interactive single-file HTML UI with sidebar, streaming chat, and result panels.

**File: `static/index.html`**

Sections (all in one file):
1. `<style>` — full CSS: layout, sidebar, chat bubbles, panels, cards, responsive
2. `<div id="sidebar">` — all preference controls
3. `<div id="main">` — chat messages area + input bar
4. `<div id="panels">` — hidden until agent returns structured data
5. `<script>` — state management, SSE client, preference collection, result rendering

**Key JS functions:**
```javascript
sendMessage()           // POST to /api/chat, open EventSource
handleSSEEvent(data)    // route token/tool_start/tool_end/done
renderDestinations(arr) // build destination card HTML
renderItinerary(arr)    // build timeline HTML
renderBudget(obj)       // build cost table HTML
renderFood(obj)         // build food card HTML
renderRoute(arr)        // build route sequence HTML
collectPreferences()    // snapshot all sidebar → JS object
```

**Verification:**
- Open `http://localhost:8000` — page loads with sidebar defaults
- Type "Suggest a beach vacation" → see streaming response
- See tool call indicators during response
- See destination cards rendered after response completes

---

## Phase 7: Tests

**Goal:** Basic test coverage for tools and API endpoint.

**Files:**
```
tests/
  test_tools.py       each tool with sample args → valid JSON output
  test_api.py         /api/health, /api/session, /api/chat (mock LLM)
```

**Run:**
```bash
pytest tests/ -v
```

---

## Phase 8: Deploy to Render

**Goal:** Push to GitHub, connect to Render, set env vars, get public URL.

**Steps:**
1. `git init && git add . && git commit -m "initial commit"`
2. Push to GitHub (new public repo)
3. Render dashboard → New Web Service → connect repo
4. Set `GROQ_API_KEY` in Render Environment
5. Deploy → wait ~3 min → get URL like `vacation-planner-abc.onrender.com`

**Verify deployed:**
```
curl https://vacation-planner-abc.onrender.com/api/health
```

---

## Dependencies Between Phases

```
Phase 1 (scaffolding)
    └──► Phase 2 (mock data)
              └──► Phase 4 (tools)
                       └──► Phase 3 (agent) ──► Phase 5 (FastAPI) ──► Phase 6 (frontend)
                                                                            └──► Phase 7 (tests)
                                                                                      └──► Phase 8 (deploy)
```

Phases 2 and 3 can partially overlap (providers/memory/prompts don't need data).
Frontend (Phase 6) can be started before agent is complete — use mock SSE responses.
