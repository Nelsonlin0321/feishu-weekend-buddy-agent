from pathlib import Path
import shutil
from typing import cast,Literal

from langchain.tools import ToolRuntime, tool
from langchain_core.tools import BaseTool
from loguru import logger

from src.middlewares.history_storage import sanitize_open_id
from src.tools.knowledge_paths import knowledge_dir, safe_knowledge_path, slugify
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
        or an activity log of what happened on a specific day. Before calling this tool, check the knowledge tree to avoid duplicates.

        How it’s organized:
        - Stored as markdown files, grouped by category (folder) and a slugified name.
        - kind="document": stable file at {category}/YYYY-MM-DD/{name}.md (good for profile/preferences you update over time).
        - kind="event": timestamped file at {category}/YYYY-MM-DD/HH:MM:SS_{name}.md (good for logs/history).

        Args:
            category: A consistent bucket name. Examples: "profile", "preferences", "availability",
                "constraints", "people", "places", "budgets", "activity_history", "conversation_notes", etc
                You can create a new category if your knowledge is not fit in any existing category to capture the any user intent.
                In order to make the category consistent, you may have to read the knowledge tree first. 
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

    @tool("knowledge_rename")
    def knowledge_rename(
        src_rel_path: str,
        dst_rel_path: str,
        runtime: ToolRuntime[FeishuRuntimeContext],
        overwrite: bool = False,
    ) -> str:
        """
        Rename or move a stored knowledge file/folder.

        Use this tool when you want to:
        - Fix a category folder name
        - Re-organize stored knowledge
        - Rename a single file to a better title

        Args:
            src_rel_path: Source path relative to the user’s knowledge root.
                Prefer getting valid paths by calling knowledge_tree first.
            dst_rel_path: Destination path relative to the user’s knowledge root.
                If dst_rel_path points to an existing directory, the source will be moved into it.
            overwrite: If true, replace an existing destination file/folder. Default false.

        Returns:
            A confirmation string including the final destination relative path.
        """
        ctx = runtime.context
        open_id = ctx.open_id
        open_id_safe = sanitize_open_id(open_id)

        root = knowledge_dir(base_dir=base_dir, open_id=open_id).resolve()
        src = safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=src_rel_path)
        dst = safe_knowledge_path(base_dir=base_dir, open_id=open_id, rel_path=dst_rel_path)

        if src.resolve() == root:
            raise ValueError("src_rel_path cannot be the knowledge root")
        if dst.resolve() == root:
            raise ValueError("dst_rel_path cannot be the knowledge root")
        if not src.exists():
            raise FileNotFoundError(f"Source does not exist: {src_rel_path}")

        final_dst = dst
        if dst.exists() and dst.is_dir():
            final_dst = dst / src.name

        if final_dst.exists():
            if not overwrite:
                rel_final = str(final_dst.relative_to(root))
                raise FileExistsError(f"Destination already exists: {rel_final}")
            if final_dst.is_dir():
                shutil.rmtree(final_dst)
            else:
                final_dst.unlink()

        final_dst.parent.mkdir(parents=True, exist_ok=True)
        moved_to = Path(shutil.move(str(src), str(final_dst))).resolve()
        rel_moved = moved_to.relative_to(root)
        logger.debug(
            "knowledge_rename success open_id={} src={} dst={}",
            open_id_safe,
            src_rel_path,
            str(rel_moved),
        )
        return f"Renamed to {rel_moved} successfully"

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

    @tool("invite_send_mock")
    def invite_send_mock(
        to_open_id: str,
        text: str,
        runtime: ToolRuntime[FeishuRuntimeContext],
        purpose: Literal["invite", "reminder", "confirmation"] = "invite",
        title: str = "",
    ) -> str:
        """
        Sending an invite message to someone (no real Feishu API call).

        Use this tool to outbound coordination messages. It logs the "sent"
        invite into the user's local knowledge store as an event record.

        Args:
            to_open_id: Recipient's Feishu open_id, ask the user to provide this.
            text: Message content you would send.
            purpose: Message type. One of: "invite", "reminder", "confirmation".
            title: Optional short label to help later browsing/searching.

        Returns:
            A confirmation string including the relative path where the invite was logged.
        """
        ctx = runtime.context
        from_open_id = ctx.open_id
        from_open_id_safe = sanitize_open_id(from_open_id)
        to_open_id_safe = sanitize_open_id(to_open_id)

        name_parts: list[str] = [purpose, "to", to_open_id_safe]
        if title.strip():
            name_parts.append(title.strip())
        name = " ".join(name_parts)

        content = "\n".join(
            [
                f"- purpose: {purpose}",
                f"- from_open_id: {from_open_id_safe}",
                f"- to_open_id: {to_open_id_safe}",
                "",
                "## Message",
                "",
                text.strip(),
                "",
            ]
        ).strip()

        path = write_knowledge_record(
            base_dir=base_dir,
            open_id=from_open_id,
            category="invites",
            name=name,
            kind="event",
            content=content,
            mode="replace",
        )
        root = knowledge_dir(base_dir=base_dir, open_id=from_open_id)
        rel_path = path.relative_to(root)
        logger.debug(
            "invite_send_mock success from_open_id={} to_open_id={} rel_path={} bytes={}",
            from_open_id_safe,
            to_open_id_safe,
            str(rel_path),
            path.stat().st_size,
        )
        return f"Invite logged to {rel_path} successfully"

    return [
        cast(BaseTool, knowledge_write),
        cast(BaseTool, knowledge_read),
        cast(BaseTool, knowledge_rename),
        cast(BaseTool, knowledge_tree),
        cast(BaseTool, invite_send_mock),
    ]
