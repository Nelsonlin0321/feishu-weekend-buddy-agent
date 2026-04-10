import re
from pathlib import Path

from src.middlewares.history_storage import sanitize_open_id

_SLUG_SAFE = re.compile(r"[^a-zA-Z0-9_\\-]")


def knowledge_dir(*, base_dir: Path, open_id: str) -> Path:
    return base_dir / sanitize_open_id(open_id) / "knowledge"


def slugify(value: str) -> str:
    return _SLUG_SAFE.sub("_", value.strip().lower()).strip("_") or "untitled"


def safe_knowledge_path(*, base_dir: Path, open_id: str, rel_path: str) -> Path:
    root = knowledge_dir(base_dir=base_dir, open_id=open_id)
    if not rel_path or rel_path.startswith("/"):
        raise ValueError("rel_path must be a non-empty relative path under knowledge/")

    candidate = (root / rel_path).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("rel_path must stay within knowledge/ directory")
    return candidate


_safe_knowledge_path = safe_knowledge_path
