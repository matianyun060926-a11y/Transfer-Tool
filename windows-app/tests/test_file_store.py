from pathlib import Path

from transfer_tool.services.file_store import FileStore


def test_resolve_unique_name_avoids_overwrite(tmp_path: Path) -> None:
    store = FileStore(tmp_path)
    batch = store.create_batch_dir("batch1")
    original = batch.batch_dir / "hello.txt"
    original.write_text("first", encoding="utf-8")

    renamed = store.resolve_unique_name(batch.batch_dir, "hello.txt")

    assert renamed == "hello (1).txt"


def test_prepare_files_builds_manifest(tmp_path: Path) -> None:
    store = FileStore(tmp_path)
    batch = store.create_batch_dir("batch2")

    prepared = store.prepare_files(
        batch.batch_dir,
        [
            {"name": "a.txt", "size_bytes": 5},
            {"name": "b.txt", "size_bytes": 12},
        ],
    )

    assert len(prepared) == 2
    assert prepared[0]["stored_name"] == "a.txt"
    assert prepared[1]["size_bytes"] == 12

