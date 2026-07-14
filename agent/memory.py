from collections import defaultdict
from langchain_core.messages import HumanMessage, AIMessage

_MAX_TURNS = 20  # keep last N human+AI pairs per session


class SessionMemory:
    def __init__(self) -> None:
        self._sessions: dict[str, list] = defaultdict(list)

    def add_turn(self, session_id: str, human: str, ai: str) -> None:
        history = self._sessions[session_id]
        history.append(HumanMessage(content=human))
        history.append(AIMessage(content=ai))
        # Trim to last _MAX_TURNS pairs (2 messages each)
        cutoff = _MAX_TURNS * 2
        if len(history) > cutoff:
            self._sessions[session_id] = history[-cutoff:]

    def get_history(self, session_id: str) -> list:
        return list(self._sessions.get(session_id, []))

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def turn_count(self, session_id: str) -> int:
        return len(self._sessions.get(session_id, [])) // 2


session_memory = SessionMemory()
