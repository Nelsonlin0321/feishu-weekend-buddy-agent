from pathlib import Path
from src.tools.knowledge_paths import _safe_knowledge_path, knowledge_dir, safe_knowledge_path, slugify
from src.tools.knowledge_records import list_knowledge_tree, read_knowledge_record, write_knowledge_record
from src.tools.knowledge_tools import build_knowledge_tools
from src.tools.knowledge_types import KnowledgeRecordKind, KnowledgeWriteMode

__all__ = [
    "KnowledgeRecordKind",
    "KnowledgeWriteMode",
    "_safe_knowledge_path",
    "build_knowledge_tools",
    "knowledge_dir",
    "list_knowledge_tree",
    "read_knowledge_record",
    "safe_knowledge_path",
    "slugify",
    "write_knowledge_record",
]


if __name__ == "__main__":

    base_dir = Path("./memory")
    print(base_dir.absolute())
    open_id = "ou_test_user_123"

    doc_path = write_knowledge_record(
        base_dir=base_dir,
        open_id=open_id,
        category="preferences",
        name="Alice: food likes/dislikes",
        kind="document",
        content="Likes: spicy Sichuan\nDislikes: cilantro",
        mode="replace",
    )
    assert doc_path.exists()

    doc_path_2 = write_knowledge_record(
        base_dir=base_dir,
        open_id=open_id,
        category="preferences",
        name="Alice: food likes/dislikes",
        kind="document",
        content="Also likes: hotpot",
        mode="upsert",
    )
    assert doc_path_2 == doc_path

    root = knowledge_dir(base_dir=base_dir, open_id=open_id).resolve()
    doc_rel = str(doc_path.relative_to(root))
    doc_content = read_knowledge_record(base_dir=base_dir, open_id=open_id, rel_path=doc_rel)
    assert "Likes: spicy Sichuan" in doc_content
    assert "Also likes: hotpot" in doc_content

    event_path = write_knowledge_record(
        base_dir=base_dir,
        open_id=open_id,
        category="activity_history",
        name="Weekend plan",
        kind="event",
        content="Went to a board game cafe with friends.",
        mode="replace",
    )
    assert event_path.exists()

    event_rel = str(event_path.relative_to(root))
    event_content = read_knowledge_record(base_dir=base_dir, open_id=open_id, rel_path=event_rel)
    assert "Went to a board game cafe with friends." in event_content

    print("doc_rel:", doc_rel)
    print("event_rel:", event_rel)
    print()
    print("tree:")
    print(list_knowledge_tree(base_dir=base_dir, open_id=open_id, rel_path="."))
