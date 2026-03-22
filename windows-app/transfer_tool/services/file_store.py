from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable
from uuid import uuid4


@dataclass(slots=True)
class IncomingBatch:
    transfer_id: str
    batch_dir: Path


class FileStore:
    def __init__(self, receive_root: Path) -> None:
        self.receive_root = receive_root
        self.receive_root.mkdir(parents=True, exist_ok=True)

    def create_batch_dir(self, transfer_id: str | None = None) -> IncomingBatch:
        transfer_id = transfer_id or uuid4().hex
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = self.receive_root / f"{stamp}_{transfer_id[:8]}"
        batch_dir.mkdir(parents=True, exist_ok=True)
        return IncomingBatch(transfer_id=transfer_id, batch_dir=batch_dir)

    def resolve_unique_name(self, batch_dir: Path, file_name: str) -> str:
        candidate = Path(file_name).name or "unnamed"
        stem = Path(candidate).stem
        suffix = Path(candidate).suffix
        if not (batch_dir / candidate).exists():
            return candidate
        counter = 1
        while True:
            renamed = f"{stem} ({counter}){suffix}"
            if not (batch_dir / renamed).exists():
                return renamed
            counter += 1

    def prepare_files(self, batch_dir: Path, files: Iterable[dict]) -> list[dict]:
        prepared: list[dict] = []
        for index, item in enumerate(files):
            original_name = Path(str(item.get("name", "unnamed"))).name
            size_bytes = int(item.get("size_bytes", 0))
            if size_bytes < 0:
                raise ValueError("File sizes must be zero or greater")
            stored_name = self.resolve_unique_name(batch_dir, original_name)
            prepared.append(
                {
                    "index": index,
                    "original_name": original_name,
                    "stored_name": stored_name,
                    "size_bytes": size_bytes,
                    "path": str(batch_dir / stored_name),
                }
            )
        if not prepared:
            raise ValueError("At least one file is required")
        return prepared

