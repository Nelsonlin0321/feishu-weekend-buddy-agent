from pathlib import Path
from typing import cast,Literal

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
        runtime: ToolRuntime[FeishuRuntimeContext],
        kind: Literal["document", "event"] = "event",
        mode: Literal["replace", "upsert"]='replace',
    ) -> str:
        """
        Persist user-specific knowledge to the your local memory

        Use this tool when you learn something that should be remembered across turns/sessions, such as:
        preferences (food, activities), constraints (budget, time window), availability, locations, people/group vibe,
        or an activity log of what happened on a specific day.

        How it’s organized:
        - Stored as markdown files, grouped by category (folder) and a slugified name.
        - kind="document": stable file at {category}/{name}.md (good for profile/preferences you update over time).
        - kind="event": timestamped file at {category}/YYYY-MM-DD/HH:MM:SS_{name}.md (good for logs/history).

        Args:
            category: A consistent bucket name. Examples: "profile", "preferences", "availability",
                "constraints", "people", "places", "budgets", "activity_history", "conversation_notes".
                In order to make the category consistent, you may have to read the knowledge tree. 
            name: A descriptive title that makes the file easy to find later. Examples:
                "Alice: food likes/dislikes", "Weekend availability", "Budget constraints", "Last weekend recap".
            content: Markdown body to store. Prefer concrete, structured bullets. Avoid secrets (tokens, passwords).
            kind: "document" or "event". Defaults to "event" in this tool signature.
            mode: For kind="document", controls how updates are written:
                - "replace": overwrite the file content
                - "upsert": append a dated "Update ..." section if the file already exists
                For kind="event", the file is always a new timestamped record. Defaults to "replace" here.

        Returns:
            A confirmation string including the relative path written under the user’s knowledge directory.

        Recommended usage patterns:
        - Long-lived memory (profile/preferences): kind="document" + mode="upsert"
        - Single-shot snapshot (constraints right now): kind="document" + mode="replace"
        - Activity log / what happened: kind="event"
        """
        ctx = runtime.context
        open_id = ctx.open_id
        open_id_safe = sanitize_open_id(open_id)
        path = write_knowledge_record(
            base_dir=base_dir,
            open_id=open_id,
            category=category,
            name=name,
            kind="event" if kind == "event" else "document",
            mode="replace" if mode == "replace" else "upsert",
            content=content,
        )
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
    def knowledge_read(rel_path: str, runtime: ToolRuntime[FeishuRuntimeContext]) -> str:
        """
        Read previously stored knowledge

        Use this tool when you need to recall details that were saved with knowledge_write, such as preferences,
        constraints, availability, or past activity logs.

        Args:
            rel_path: File path relative to the user’s knowledge root. Example:
                - "preferences/alice__food_likes_dislikes.md"
                - "activity_history/2026-04-10/23:15:43_weekend_plan.md"
                Prefer getting valid paths by calling the knowledge_tree tool first.

        Returns:
            The full markdown content of the file.
        """
        ctx = runtime.context
        open_id_safe = sanitize_open_id(ctx.open_id)
        logger.debug("knowledge_read called open_id={} rel_path={}", open_id_safe, rel_path)
        content = read_knowledge_record(base_dir=base_dir, open_id=ctx.open_id, rel_path=rel_path)
        return content

    @tool("knowledge_tree")
    def knowledge_tree(
        runtime: ToolRuntime[FeishuRuntimeContext],
        rel_path: str = ".",
        max_depth: int = 10,
        max_entries: int = 500,
    ) -> str:
        """
        List the current user’s knowledge folder as a readable tree (paths under /memory/{open_id}/knowledge).

        Use this tool to:
        - Discover what the agent has already saved for the user (categories and files).
        - Get the exact rel_path values to pass into knowledge_read.
        - Keep category naming consistent before writing new records with knowledge_write.

        Args:
            rel_path: Starting folder (relative to the user’s knowledge root). Defaults to "." (the root).
                Examples:
                - "." (everything)
                - "preferences"
                - "activity_history/2026-04-10"
            max_depth: How many nested directory levels to include.
            max_entries: Maximum number of lines/entries to return (output will truncate beyond this).

        Returns:
            A newline-separated tree. Directories end with "/". Each file line shows the rel_path you can reuse
            in knowledge_read.
        """
        open_id = runtime.context.open_id
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
