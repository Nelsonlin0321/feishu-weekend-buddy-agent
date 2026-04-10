from pathlib import Path
from typing import cast

from langchain.tools import ToolRuntime, tool
from langchain_core.tools import BaseTool
from loguru import logger

from src.middlewares.history_storage import sanitize_open_id
from src.tools.knowledge_paths import knowledge_dir, slugify
from src.tools.knowledge_records import list_knowledge_tree, read_knowledge_record, write_knowledge_record
from src.types.context import FeishuRuntimeContext


def build_knowledge_tools(*, base_dir: Path) -> list[BaseTool]:
    @tool("knowledge_write")
    def knowledge_write(
        category: str,
        name: str,
        content: str,
        tool_runtime: ToolRuntime[FeishuRuntimeContext],
        kind: str = "document",
        mode: str = "upsert",
    ) -> str:
        ctx = tool_runtime.context
        open_id = ctx.open_id
        open_id_safe = sanitize_open_id(open_id)
        category_slug = slugify(category)
        name_slug = slugify(name)
        logger.debug(
            "knowledge_write called open_id={} kind={} mode={} event_date={} category_slug={} name_slug={}",
            open_id_safe,
            kind,
            mode,
            None,
            category_slug,
            name_slug,
        )
        try:
            path = write_knowledge_record(
                base_dir=base_dir,
                open_id=open_id,
                category=category,
                name=name,
                kind="event" if kind == "event" else "document",
                mode="replace" if mode == "replace" else "upsert",
                content=content,
            )
        except Exception:
            logger.exception(
                "knowledge_write failed open_id={} kind={} mode={} event_date={} category_slug={} name_slug={}",
                open_id_safe,
                kind,
                mode,
                None,
                category_slug,
                name_slug,
            )
            raise

        if not path.exists():
            logger.error(
                "knowledge_write post-check failed: file not found open_id={} path={}",
                open_id_safe,
                str(path),
            )
            raise RuntimeError("knowledge_write did not create the expected file")

        root = knowledge_dir(base_dir=base_dir, open_id=open_id)
        rel_path = path.relative_to(root)
        logger.debug(
            "knowledge_write success open_id={} rel_path={} bytes={}",
            open_id_safe,
            str(rel_path),
            path.stat().st_size,
        )
        return f"Written to {rel_path} successfully"

    @tool("knowledge_read")
    def knowledge_read(rel_path: str, tool_runtime: ToolRuntime[FeishuRuntimeContext]) -> str:
        ctx = tool_runtime.context
        open_id_safe = sanitize_open_id(ctx.open_id)
        logger.debug("knowledge_read called open_id={} rel_path={}", open_id_safe, rel_path)
        try:
            content = read_knowledge_record(base_dir=base_dir, open_id=ctx.open_id, rel_path=rel_path)
        except Exception:
            logger.exception("knowledge_read failed open_id={} rel_path={}", open_id_safe, rel_path)
            raise
        logger.debug("knowledge_read success open_id={} rel_path={} chars={}", open_id_safe, rel_path, len(content))
        return content

    @tool("knowledge_tree")
    def knowledge_tree(
        tool_runtime: ToolRuntime[FeishuRuntimeContext],
        rel_path: str = ".",
        max_depth: int = 10,
        max_entries: int = 500,
    ) -> str:
        open_id = tool_runtime.context.open_id
        open_id_safe = sanitize_open_id(open_id)
        logger.debug(
            "knowledge_tree called open_id={} rel_path={} max_depth={} max_entries={}",
            open_id_safe,
            rel_path,
            max_depth,
            max_entries,
        )
        try:
            tree = list_knowledge_tree(
                base_dir=base_dir,
                open_id=open_id,
                rel_path=rel_path,
                max_depth=max_depth,
                max_entries=max_entries,
            )
        except Exception:
            logger.exception(
                "knowledge_tree failed open_id={} rel_path={} max_depth={} max_entries={}",
                open_id_safe,
                rel_path,
                max_depth,
                max_entries,
            )
            raise

        logger.debug("knowledge_tree success open_id={} lines={}", open_id_safe, tree.count("\n") + 1 if tree else 0)
        return tree

    return [
        cast(BaseTool, knowledge_write),
        cast(BaseTool, knowledge_read),
        cast(BaseTool, knowledge_tree),
    ]
