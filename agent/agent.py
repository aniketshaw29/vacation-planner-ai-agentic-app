import json
from typing import AsyncGenerator

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from agent.prompts import SYSTEM_PROMPT_TEMPLATE
from agent.memory import session_memory
from agent.providers import get_llm

_agent_cache: dict[str, object] = {}


def build_agent_executor(provider: str = "gemini"):
    """Build (or return cached) LangGraph react agent for the given provider."""
    if provider in _agent_cache:
        return _agent_cache[provider]

    from tools import ALL_TOOLS

    llm = get_llm(provider)

    # create_react_agent accepts a plain string as the system prompt
    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT_TEMPLATE,
    )

    _agent_cache[provider] = agent
    return agent


async def run_agent_stream(
    message: str,
    session_id: str,
    preferences: dict,
    provider: str = "gemini",
) -> AsyncGenerator[str, None]:
    """
    Run the agent and yield SSE-formatted JSON strings.

    Event types:
      {"type": "token",      "content": "..."}
      {"type": "tool_start", "tool": "..."}
      {"type": "tool_end",   "tool": "...", "output": "..."}
      {"type": "error",      "message": "..."}
      {"type": "done"}
    """
    agent = build_agent_executor(provider)
    history = session_memory.get_history(session_id)

    # Inject current preferences into the human turn
    human_content = (
        f"{message}\n\n"
        f"<user_preferences>\n{json.dumps(preferences, ensure_ascii=False)}\n</user_preferences>"
    )

    messages = history + [HumanMessage(content=human_content)]
    full_response = []

    try:
        async for event in agent.astream_events(
            {"messages": messages},
            version="v2",
        ):
            kind = event.get("event", "")

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if isinstance(chunk.content, str) and chunk.content:
                    full_response.append(chunk.content)
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk.content})}\n\n"
                elif isinstance(chunk.content, list):
                    for part in chunk.content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            text = part.get("text", "")
                            if text:
                                full_response.append(text)
                                yield f"data: {json.dumps({'type': 'token', 'content': text})}\n\n"

            elif kind == "on_tool_start":
                tool_name = event.get("name", "tool")
                yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name})}\n\n"

            elif kind == "on_tool_end":
                tool_name = event.get("name", "tool")
                output = str(event["data"].get("output", ""))[:400]
                yield f"data: {json.dumps({'type': 'tool_end', 'tool': tool_name, 'output': output})}\n\n"

    except Exception as exc:
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
    finally:
        if full_response:
            session_memory.add_turn(session_id, message, "".join(full_response))
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
