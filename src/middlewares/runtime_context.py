from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeishuRuntimeContext:
    open_id: str
    history_to_load: int = 20

