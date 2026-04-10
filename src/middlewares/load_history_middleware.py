from __future__ import annotations

import json
from pathlib import Path

from langchain.agents.middleware.types import AgentMiddleware, AgentState
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

from src.middlewares.history_storage import read_recent_messages
from src.middlewares.runtime_context import FeishuRuntimeContext


def _content_for_message(value: object) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(value)


def _open_id_from_runtime(runtime: Runtime[FeishuRuntimeContext]) -> str | None:
    context = runtime.context
    if context is None:
        return None
    if isinstance(context, FeishuRuntimeContext):
        return context.open_id
    open_id = getattr(context, "open_id", None)
    return open_id if isinstance(open_id, str) and open_id else None


def _history_to_load_from_runtime(
    runtime: Runtime[FeishuRuntimeContext], default: int
) -> int:
    context = runtime.context
    if context is None:
        return default
    if isinstance(context, FeishuRuntimeContext):
        return context.history_to_load
    raw = getattr(context, "history_to_load", None)
    if isinstance(raw, int):
        return raw
    return default


class LoadHistoryMiddleware(AgentMiddleware[AgentState[object], FeishuRuntimeContext]):
    def __init__(self, *, base_dir: Path, default_history_to_load: int = 20) -> None:
        self._base_dir = base_dir
        self._default_history_to_load = default_history_to_load

    def before_agent(
        self, state: AgentState[object], runtime: Runtime[FeishuRuntimeContext]
    ) -> dict[str, object] | None:
        open_id = _open_id_from_runtime(runtime)
        if open_id is None:
            return None

        limit = _history_to_load_from_runtime(runtime, self._default_history_to_load)
        stored = read_recent_messages(base_dir=self._base_dir, open_id=open_id, limit=limit)
        if not stored:
            return None

        history_messages = [
            HumanMessage(content=_content_for_message(m.content))
            if m.role == "user"
            else AIMessage(content=_content_for_message(m.content))
            for m in stored
        ]

        current_messages = list(state.get("messages", []))
        new_messages = [*history_messages, *current_messages]

        return {"messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages]}
