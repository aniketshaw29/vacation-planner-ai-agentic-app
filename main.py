import os
import json
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# ── Models ────────────────────────────────────────────────────────────────────

class UserPreferences(BaseModel):
    budget_usd: int = 3000
    trip_duration_days: int = 7
    group_size: int = 2
    season: str = "summer"
    travel_style: str = "balanced"
    accommodation_type: str = "hotel"
    food_tier: list[str] = ["mid_range", "street_food"]
    dietary_restrictions: str = "none"
    transport_modes: list[str] = ["flight", "train", "bus", "scooter"]
    origin_city: str = "New York"

    @property
    def budget_per_person(self) -> int:
        return self.budget_usd // max(self.group_size, 1)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1, max_length=100)
    provider: str = "gemini"
    preferences: UserPreferences = Field(default_factory=UserPreferences)


# ── App setup ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate at least one provider is configured
    from agent.providers import available_providers, default_provider
    providers = available_providers()
    if not providers:
        raise RuntimeError(
            "No LLM API key found. Set at least one of: "
            "GOOGLE_API_KEY, GROQ_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY in .env"
        )
    print(f"✓ Vacation Planner started | Available providers: {providers} | Default: {default_provider()}")

    # Pre-load tools to catch import errors at startup
    from tools import ALL_TOOLS
    print(f"✓ {len(ALL_TOOLS)} tools loaded")
    yield


app = FastAPI(
    title="Vacation Planner AI",
    description="AI-powered vacation planner — connect any LLM (Gemini, Groq, OpenAI, Anthropic)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── SSE stream generator ──────────────────────────────────────────────────────

async def _sse_generator(request: ChatRequest):
    from agent.agent import run_agent_stream

    prefs_dict = request.preferences.model_dump()
    prefs_dict["budget_per_person_usd"] = request.preferences.budget_per_person

    async for chunk in run_agent_stream(
        message=request.message,
        session_id=request.session_id,
        preferences=prefs_dict,
        provider=request.provider,
    ):
        yield chunk


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat(request: ChatRequest):
    from agent.providers import available_providers
    if request.provider not in available_providers():
        raise HTTPException(400, detail=f"Provider '{request.provider}' not available. Configure the API key first.")

    return StreamingResponse(
        _sse_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/health")
async def health():
    from agent.providers import available_providers
    providers = available_providers()
    return {
        "status": "ok",
        "providers": providers,
        "default_provider": providers[0] if providers else None,
    }


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    from agent.memory import session_memory
    return {
        "session_id": session_id,
        "turn_count": session_memory.turn_count(session_id),
    }


@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    from agent.memory import session_memory
    session_memory.clear(session_id)
    return {"status": "cleared", "session_id": session_id}


# ── Static files ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Mount static assets (CSS/JS if needed in future)
import os as _os
if _os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(_os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
