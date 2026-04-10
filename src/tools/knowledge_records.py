from datetime import datetime, timezone
from pathlib import Path

from src.tools.knowledge_paths import knowledge_dir, safe_knowledge_path, slugify
from src.tools.knowledge_types import KnowledgeRecordKind, KnowledgeWriteMode


def write_knowledge_record(
    base_dir: Path,
    open_id: str,
    category: str,
    name: str,
    kind: KnowledgeRecordKind,
    content: str,
    mode: KnowledgeWriteMode = "upsert",
) -> Path:
    category_slug = slugify(category)
    name_slug = slugify(name)
    day_and_time = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d:%H:%M:%S")
    day = day_and_time[:10]
    time = day_and_time[11:]
    if kind == "event":
        rel = f"{category_slug}/{day}/{time}_{name_slug}.md"
    else:
        rel = f"{category_slug}/{day}/{name_slug}.md"

    path = safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=rel)
    path.parent.mkdir(parents=True, exist_ok=True)

    body = content.strip()
    frontmatter = "\n".join(
        [
            "---",
            f"kind: {kind}",
            f"category: {category_slug}",
            f"name: {name_slug}",
            f"{day_and_time}",
            "---",
            "",
        ]
    )

    if kind == "document" and mode == "upsert" and path.exists():
        existing = path.read_text(encoding="utf-8")
        updated = "\n".join(
            [
                existing.rstrip(),
                "",
                f"## Update {day_and_time}",
                "",
                body,
                "",
            ]
        )
        path.write_text(updated, encoding="utf-8")
        return path

    markdown = "\n".join(
        [
            frontmatter,
            f"# {category_slug}: {name_slug}",
            "",
            body,
            "",
        ]
    )
    path.write_text(markdown, encoding="utf-8")
    return path


def read_knowledge_record(*, base_dir: Path, open_id: str, rel_path: str) -> str:
    path = safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=rel_path)
    return path.read_text(encoding="utf-8")


def list_knowledge_tree(
    *,
    base_dir: Path,
    open_id: str,
    rel_path: str = ".",
    max_depth: int = 10,
    max_entries: int = 200,
) -> str:
    root = knowledge_dir(base_dir=base_dir, open_id=open_id)
    root_resolved = root.resolve()
    start = safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=rel_path)
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
