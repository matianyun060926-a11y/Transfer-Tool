from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(slots=True)
class PeerDevice:
    device_id: str
    device_name: str
    platform: str
    app_version: str
    ready_to_receive: bool
    host: str
    port: int


@dataclass(slots=True)
class LocalFile:
    path: str
    name: str
    size_bytes: int


@dataclass(slots=True)
class PairingSession:
    session_token: str
    sender_device_id: str
    sender_device_name: str
    created_at: datetime
    expires_at: datetime


@dataclass(slots=True)
class ActiveTransfer:
    transfer_id: str
    direction: str
    peer_device_name: str
    peer_host: str
    created_at: str = field(default_factory=utc_now_iso)
    status: str = "queued"
    total_bytes: int = 0
    transferred_bytes: int = 0
    current_file_index: int = -1
    file_count: int = 0
    detail: str = ""

