from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

from .transfer import utc_now_iso


@dataclass(slots=True)
class HistoryEntry:
    entry_id: str = field(default_factory=lambda: uuid4().hex)
    timestamp: str = field(default_factory=utc_now_iso)
    direction: str = ""
    peer_device_name: str = ""
    peer_host: str = ""
    peer_port: int = 8765
    filenames: list[str] = field(default_factory=list)
    total_bytes: int = 0
    status: str = ""
    details: str = ""
    source_paths: list[str] = field(default_factory=list)
    saved_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HistoryEntry":
        return cls(
            entry_id=str(payload.get("entry_id", uuid4().hex)),
            timestamp=str(payload.get("timestamp", utc_now_iso())),
            direction=str(payload.get("direction", "")),
            peer_device_name=str(payload.get("peer_device_name", "")),
            peer_host=str(payload.get("peer_host", "")),
            peer_port=int(payload.get("peer_port", 8765)),
            filenames=[str(item) for item in payload.get("filenames", [])],
            total_bytes=int(payload.get("total_bytes", 0)),
            status=str(payload.get("status", "")),
            details=str(payload.get("details", "")),
            source_paths=[str(item) for item in payload.get("source_paths", [])],
            saved_paths=[str(item) for item in payload.get("saved_paths", [])],
        )
