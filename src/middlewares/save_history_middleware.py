from __future__ import annotations

from pathlib import Path

from langchain.agents.middleware.types import AgentMiddleware, AgentState
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.runtime import Runtime

from src.middlewares.history_storage import write_message
from src.types.context import FeishuRuntimeContext


def _open_id_from_runtime(runtime: Runtime[FeishuRuntimeContext]) -> str | None:
    context = runtime.context
    if context is None:
        return None
    if isinstance(context, FeishuRuntimeContext):
        return context.open_id
    open_id = getattr(context, "open_id", None)
    return open_id if isinstance(open_id, str) and open_id else None


class SaveHistoryMiddleware(AgentMiddleware[AgentState[object], FeishuRuntimeContext]):
    def __init__(self, *, base_dir: Path) -> None:
        self._base_dir = base_dir

    def before_agent(
        self, state: AgentState[object], runtime: Runtime[FeishuRuntimeContext]
    ) -> dict[str, object] | None:
        open_id = _open_id_from_runtime(runtime)
        if open_id is None:
            return None

        messages = state.get("messages", [])
        last = messages[-1] if messages else None
        if isinstance(last, HumanMessage):
            write_message(
                base_dir=self._base_dir,
                open_id=open_id,
                role="user",
                content=last.content,
            )
        return None

    def after_agent(
        self, state: AgentState[object], runtime: Runtime[FeishuRuntimeContext]
    ) -> dict[str, object] | None:
        open_id = _open_id_from_runtime(runtime)
        if open_id is None:
            return None

        messages = state.get("messages", [])
        last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
        if isinstance(last_ai, AIMessage):
            write_message(
                base_dir=self._base_dir,
                open_id=open_id,
                role="bot",
                content=last_ai.content,
            )
        return None
