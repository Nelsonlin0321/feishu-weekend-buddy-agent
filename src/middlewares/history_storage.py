from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


Role = Literal["user", "bot"]


@dataclass(frozen=True, slots=True)
class StoredMessage:
    role: Role
    content: object
    timestamp: str
    path: Path


_OPEN_ID_SAFE = re.compile(r"[^a-zA-Z0-9_\-]")


def sanitize_open_id(open_id: str) -> str:
    return _OPEN_ID_SAFE.sub("_", open_id).strip("_") or "unknown"


def now_timestamp() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def messages_dir(*, base_dir: Path, open_id: str) -> Path:
    return base_dir / sanitize_open_id(open_id) / "messages"


def message_path(*, base_dir: Path, open_id: str, role: Role, timestamp: str) -> Path:
    prefix = "user" if role == "user" else "bot"
    return messages_dir(base_dir=base_dir, open_id=open_id) / f"{prefix}_{timestamp}"


def _coerce_jsonable(value: object) -> object:
    try:
        json.dumps(value, ensure_ascii=False)
        return value
    except (TypeError, ValueError):
        return str(value)


def write_message(
    *,
    base_dir: Path,
    open_id: str,
    role: Role,
    content: object,
    timestamp: str | None = None,
) -> Path:
    ts = timestamp or now_timestamp()
    path = message_path(base_dir=base_dir, open_id=open_id, role=role, timestamp=ts)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"role": role, "content": _coerce_jsonable(content), "timestamp": ts}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _infer_role_from_filename(name: str) -> Role | None:
    if name.startswith("user_"):
        return "user"
    if name.startswith("bot_"):
        return "bot"
    return None


def _infer_timestamp_from_filename(name: str) -> str | None:
    if name.startswith("user_"):
        return name[len("user_") :]
    if name.startswith("bot_"):
        return name[len("bot_") :]
    return None


def read_recent_messages(*, base_dir: Path, open_id: str, limit: int) -> list[StoredMessage]:
    if limit <= 0:
        return []

    directory = messages_dir(base_dir=base_dir, open_id=open_id)
    if not directory.exists() or not directory.is_dir():
        return []

    candidates: list[Path] = []
    for entry in directory.iterdir():
        if not entry.is_file():
            continue
        if _infer_role_from_filename(entry.name) is None:
            continue
        candidates.append(entry)

    candidates.sort(key=lambda p: p.name)
    selected = candidates[-limit:]

    results: list[StoredMessage] = []
    for path in selected:
        raw = path.read_text(encoding="utf-8")
        role = _infer_role_from_filename(path.name) or "user"
        timestamp = _infer_timestamp_from_filename(path.name) or ""
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                parsed_role = obj.get("role")
                if parsed_role in ("user", "bot"):
                    role = parsed_role
                parsed_ts = obj.get("timestamp")
                if isinstance(parsed_ts, str) and parsed_ts:
                    timestamp = parsed_ts
                content = obj.get("content", "")
                results.append(StoredMessage(role=role, content=content, timestamp=timestamp, path=path))
                continue
        except (TypeError, json.JSONDecodeError, ValueError):
            pass

        results.append(StoredMessage(role=role, content=raw, timestamp=timestamp, path=path))

    return results

