from __future__ import annotations

import json
import threading
from pathlib import Path

from transfer_tool.models.history import HistoryEntry


class HistoryStore:
    def __init__(self, history_path: Path, limit: int = 20) -> None:
        self.history_path = history_path
        self.limit = limit
        self._lock = threading.Lock()
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.history_path.exists():
            self.history_path.write_text("[]", encoding="utf-8")

    def load(self) -> list[HistoryEntry]:
        with self._lock:
            payload = json.loads(self.history_path.read_text(encoding="utf-8") or "[]")
        return [HistoryEntry.from_dict(item) for item in payload]

    def save_all(self, entries: list[HistoryEntry]) -> None:
        trimmed = entries[: self.limit]
        with self._lock:
            self.history_path.write_text(
                json.dumps([entry.to_dict() for entry in trimmed], indent=2),
                encoding="utf-8",
            )

    def add_entry(self, entry: HistoryEntry) -> list[HistoryEntry]:
        entries = [entry, *self.load()]
        self.save_all(entries)
        return self.load()

