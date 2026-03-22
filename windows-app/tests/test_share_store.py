from pathlib import Path

from transfer_tool.services.share_store import ShareStore


def test_create_share_builds_zip_for_multiple_files(tmp_path: Path) -> None:
    store = ShareStore(tmp_path / "shared.json", tmp_path / "shared_files")
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("one", encoding="utf-8")
    second.write_text("two", encoding="utf-8")

    share = store.create_share([str(first), str(second)])

    assert share["package_kind"] == "zip"
    assert Path(share["download_path"]).exists()
    assert share["file_count"] == 2
