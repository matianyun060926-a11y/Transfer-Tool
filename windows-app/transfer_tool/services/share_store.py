from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any
from uuid import uuid4

from transfer_tool.models.transfer import utc_now_iso


class ShareStore:
    def __init__(self, manifest_path: Path, shares_root: Path) -> None:
        self.manifest_path = manifest_path
        self.shares_root = shares_root
        self.packages_root = self.shares_root / "packages"
        self.items_root = self.shares_root / "items"
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.packages_root.mkdir(parents=True, exist_ok=True)
        self.items_root.mkdir(parents=True, exist_ok=True)
        if not self.manifest_path.exists():
            self.manifest_path.write_text("[]", encoding="utf-8")

    def load(self) -> list[dict[str, Any]]:
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8") or "[]")
        return [dict(item) for item in payload]

    def save_all(self, entries: list[dict[str, Any]]) -> None:
        self.manifest_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    def create_share(self, source_paths: list[str]) -> dict[str, Any]:
        if not source_paths:
            raise ValueError("Choose at least one file to share")

        share_id = uuid4().hex
        share_dir = self.items_root / share_id
        files_dir = share_dir / "files"
        files_dir.mkdir(parents=True, exist_ok=True)

        copied_files: list[dict[str, Any]] = []
        for source_path in source_paths:
            source = Path(source_path)
            if not source.exists() or not source.is_file():
                continue
            target_name = self._resolve_unique_name(files_dir, source.name)
            target_path = files_dir / target_name
            shutil.copy2(source, target_path)
            copied_files.append(
                {
                    "name": target_name,
                    "size_bytes": target_path.stat().st_size,
                    "path": str(target_path),
                    "source_path": str(source),
                }
            )
        if not copied_files:
            raise ValueError("None of the selected files were available")

        if len(copied_files) == 1:
            download_name = copied_files[0]["name"]
            download_path = copied_files[0]["path"]
            package_kind = "single"
        else:
            archive_name = f"transfer_{share_id[:8]}.zip"
            archive_path = self.packages_root / archive_name
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for item in copied_files:
                    archive.write(item["path"], arcname=item["name"])
            download_name = archive_name
            download_path = str(archive_path)
            package_kind = "zip"

        entry = {
            "share_id": share_id,
            "created_at": utc_now_iso(),
            "download_name": download_name,
            "download_path": download_path,
            "package_kind": package_kind,
            "file_count": len(copied_files),
            "total_bytes": sum(item["size_bytes"] for item in copied_files),
            "downloads_count": 0,
            "files": copied_files,
        }
        entries = [entry, *self.load()]
        self.save_all(entries)
        return entry

    def remove_share(self, share_id: str) -> None:
        entries = self.load()
        remaining: list[dict[str, Any]] = []
        for entry in entries:
            if entry["share_id"] == share_id:
                share_dir = self.items_root / share_id
                if share_dir.exists():
                    shutil.rmtree(share_dir, ignore_errors=True)
                download_path = Path(entry["download_path"])
                if download_path.exists() and download_path.parent == self.packages_root:
                    download_path.unlink(missing_ok=True)
                continue
            remaining.append(entry)
        self.save_all(remaining)

    def record_download(self, share_id: str) -> dict[str, Any]:
        entries = self.load()
        updated: dict[str, Any] | None = None
        for entry in entries:
            if entry["share_id"] == share_id:
                entry["downloads_count"] = int(entry.get("downloads_count", 0)) + 1
                entry["last_downloaded_at"] = utc_now_iso()
                updated = entry
                break
        self.save_all(entries)
        if updated is None:
            raise ValueError("Unknown shared file batch")
        return updated

    def get_share(self, share_id: str) -> dict[str, Any]:
        for entry in self.load():
            if entry["share_id"] == share_id:
                return entry
        raise ValueError("Unknown shared file batch")

    def _resolve_unique_name(self, directory: Path, file_name: str) -> str:
        candidate = Path(file_name).name or "unnamed"
        stem = Path(candidate).stem
        suffix = Path(candidate).suffix
        if not (directory / candidate).exists():
            return candidate
        counter = 1
        while True:
            renamed = f"{stem} ({counter}){suffix}"
            if not (directory / renamed).exists():
                return renamed
            counter += 1
