import json
from typing import AsyncGenerator

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.prompts import SYSTEM_PROMPT_TEMPLATE
from agent.memory import session_memory
from agent.providers import get_llm

# Lazy import to avoid circular deps — tools imported on first call
_executor_cache: dict[str, AgentExecutor] = {}


def build_agent_executor(provider: str = "groq") -> AgentExecutor:
    """Build (or return cached) AgentExecutor for the given provider."""
    if provider in _executor_cache:
        return _executor_cache[provider]

    from tools import ALL_TOOLS

    llm = get_llm(provider)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT_TEMPLATE),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}\n\n<user_preferences>\n{preferences_json}\n</user_preferences>"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=False,
        max_iterations=10,
        max_execution_time=120,
        handle_parsing_errors=True,
        return_intermediate_steps=False,
    )

    _executor_cache[provider] = executor
    return executor


async def run_agent_stream(
    message: str,
    session_id: str,
    preferences: dict,
    provider: str = "groq",
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
    executor = build_agent_executor(provider)
    history = session_memory.get_history(session_id)

    inputs = {
        "input": message,
        "chat_history": history,
        "preferences_json": json.dumps(preferences, ensure_ascii=False),
    }

    full_response = []

    try:
        async for event in executor.astream_events(inputs, version="v2"):
            kind = event.get("event", "")

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                # Content can be str or list of dicts depending on the model
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
        # Persist conversation turn to memory
        if full_response:
            session_memory.add_turn(session_id, message, "".join(full_response))
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
