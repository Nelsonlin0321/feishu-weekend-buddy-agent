import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, cast

from langchain.tools import ToolRuntime, tool
from langchain_core.tools import BaseTool

from src.types.context import FeishuRuntimeContext
from src.middlewares.history_storage import _coerce_jsonable, now_timestamp, sanitize_open_id

KnowledgeWriteMode = Literal["upsert", "replace"]
KnowledgeRecordKind = Literal["document", "event"]


def knowledge_dir(*, base_dir: Path, open_id: str) -> Path:
    return base_dir / sanitize_open_id(open_id) / "knowledge"


_SLUG_SAFE = re.compile(r"[^a-zA-Z0-9_\-]")


def slugify(value: str) -> str:
    return _SLUG_SAFE.sub("_", value.strip().lower()).strip("_") or "untitled"


def _safe_knowledge_path(*, base_dir: Path, open_id: str, rel_path: str) -> Path:
    root = knowledge_dir(base_dir=base_dir, open_id=open_id)
    if not rel_path or rel_path.startswith("/"):
        raise ValueError("rel_path must be a non-empty relative path under knowledge/")

    candidate = (root / rel_path).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("rel_path must stay within knowledge/ directory")
    return candidate


def write_knowledge_record(
    *,
    base_dir: Path,
    open_id: str,
    category: str,
    name: str,
    kind: KnowledgeRecordKind,
    content: object,
    mode: KnowledgeWriteMode = "upsert",
    timestamp: str | None = None,
    event_date: str | None = None,
) -> Path:
    ts = timestamp or now_timestamp()
    category_slug = slugify(category)
    name_slug = slugify(name)

    root = knowledge_dir(base_dir=base_dir, open_id=open_id)
    if kind == "event":
        day = event_date or datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        month = day[:7]
        rel = f"{category_slug}/{month}/{day}_{name_slug}_{ts}.json"
    else:
        rel = f"{category_slug}/{name_slug}.json"

    path = _safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=rel)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, object] = {
        "kind": kind,
        "category": category_slug,
        "name": name_slug,
        "timestamp": ts,
        "content": _coerce_jsonable(content),
    }

    if mode == "upsert" and path.exists():
        try:
            existing_raw = path.read_text(encoding="utf-8")
            existing_obj = json.loads(existing_raw)
            if isinstance(existing_obj, dict):
                existing_obj.update(payload)
                payload = existing_obj
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def read_knowledge_record(*, base_dir: Path, open_id: str, rel_path: str) -> object:
    path = _safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=rel_path)
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        return raw


def list_knowledge_tree(
    *,
    base_dir: Path,
    open_id: str,
    rel_path: str = ".",
    max_depth: int = 4,
    max_entries: int = 200,
) -> str:
    root = knowledge_dir(base_dir=base_dir, open_id=open_id)
    root_resolved = root.resolve()
    start = _safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=rel_path)
    if not start.exists():
        return f"(empty) {start.relative_to(root_resolved)} does not exist"

    lines: list[str] = [str(start.relative_to(root_resolved)) + ("/" if start.is_dir() else "")]
    count = 0

    def walk(current: Path, depth: int) -> None:
        nonlocal count
        if count >= max_entries:
            return
        if depth > max_depth:
            return
        if not current.is_dir():
            return

        entries = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        for entry in entries:
            if count >= max_entries:
                return
            prefix = "  " * depth
            rel = entry.relative_to(root_resolved)
            lines.append(f"{prefix}- {rel}" + ("/" if entry.is_dir() else ""))
            count += 1
            if entry.is_dir():
                walk(entry, depth + 1)

    walk(start, 1)
    if count >= max_entries:
        lines.append("... (truncated)")
    return "\n".join(lines)


def build_knowledge_tools(*, base_dir: Path) -> list[BaseTool]:
    @tool("knowledge_write")
    def knowledge_write(
        category: str,
        name: str,
        content: object,
        tool_runtime: ToolRuntime[FeishuRuntimeContext],
        kind: str = "document",
        mode: str = "upsert",
        event_date: str | None = None,
    ) -> str:
        """Write long-term knowledge to /memory/{open_id}/knowledge.

        Args:
            category: High-level folder name (e.g., "preferences", "schedule", "activity_history", "profile").
            name: Human-readable name used in the file name.
            content: JSON-serializable content to store.
            kind: "document" (stable file) or "event" (timestamped file under YYYY-MM/).
            mode: "upsert" (merge into existing JSON) or "replace" (overwrite).
            event_date: Optional YYYY-MM-DD for kind="event".
        """
        ctx = tool_runtime.context
        open_id = ctx.open_id
        path = write_knowledge_record(
            base_dir=base_dir,
            open_id=open_id,
            category=category,
            name=name,
            kind="event" if kind == "event" else "document",
            mode="replace" if mode == "replace" else "upsert",
            content=content,
            event_date=event_date,
        )
        root = knowledge_dir(base_dir=base_dir, open_id=open_id)
        return str(path.relative_to(root))

    @tool("knowledge_read")
    def knowledge_read(rel_path: str, tool_runtime: ToolRuntime) -> str:
        """Read a knowledge file by relative path under /memory/{open_id}/knowledge."""
        ctx = cast(FeishuRuntimeContext, tool_runtime.context)
        open_id = ctx.open_id
        obj = read_knowledge_record(base_dir=base_dir, open_id=open_id, rel_path=rel_path)
        try:
            import json

            return json.dumps(obj, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return str(obj)

    @tool("knowledge_tree")
    def knowledge_tree(
        tool_runtime: ToolRuntime,
        rel_path: str = ".",
        max_depth: int = 4,
        max_entries: int = 200,
    ) -> str:
        """Show knowledge folder structure (tree) under /memory/{open_id}/knowledge."""
        ctx = cast(FeishuRuntimeContext, tool_runtime.context)
        open_id = ctx.open_id
        return list_knowledge_tree(
            base_dir=base_dir,
            open_id=open_id,
            rel_path=rel_path,
            max_depth=max_depth,
            max_entries=max_entries,
        )

    return [
        cast(BaseTool, knowledge_write),
        cast(BaseTool, knowledge_read),
        cast(BaseTool, knowledge_tree),
    ]
