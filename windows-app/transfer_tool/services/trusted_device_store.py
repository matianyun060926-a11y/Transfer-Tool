from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from transfer_tool.models.transfer import utc_now_iso


def _utc_now() -> datetime:
    return datetime.now(UTC)


class TrustedDeviceStore:
    def __init__(self, store_path: Path, trust_days: int = 30, limit: int = 12) -> None:
        self.store_path = store_path
        self.trust_days = trust_days
        self.limit = limit
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self.store_path.write_text("[]", encoding="utf-8")

    def list_devices(self) -> list[dict[str, Any]]:
        return [self._sanitize(record) for record in self._load_active_records()]

    def issue_trust(self, device_id: str, device_name: str) -> tuple[str, dict[str, Any]]:
        records = self._load_raw()
        active_records = self._filter_active(records)
        existing = next((item for item in active_records if item.get("device_id") == device_id), None)
        token = secrets.token_urlsafe(32)
        now = _utc_now()
        trust_expires_at = now + timedelta(days=self.trust_days)

        record = existing or {
            "device_id": device_id,
            "pair_count": 0,
        }
        record["device_name"] = device_name or "iPhone/iPad"
        record["pair_count"] = int(record.get("pair_count", 0)) + 1
        record["last_paired_at"] = now.isoformat()
        record["last_seen_at"] = now.isoformat()
        record["trust_expires_at"] = trust_expires_at.isoformat()
        record["trusted_token_hash"] = self._hash_token(token)

        remaining = [item for item in active_records if item.get("device_id") != device_id]
        remaining.insert(0, record)
        self._save_raw(remaining[: self.limit])
        return token, self._sanitize(record)

    def restore_trust(self, trusted_token: str, device_id: str, device_name: str) -> dict[str, Any] | None:
        if not trusted_token:
            return None
        records = self._load_active_records()
        token_hash = self._hash_token(trusted_token)
        now = _utc_now()
        matched: dict[str, Any] | None = None
        updated_records: list[dict[str, Any]] = []

        for item in records:
            if item.get("trusted_token_hash") == token_hash:
                if device_id and item.get("device_id") != device_id:
                    return None
                item["device_name"] = device_name or item.get("device_name") or "iPhone/iPad"
                item["last_seen_at"] = now.isoformat()
                item["trust_expires_at"] = (now + timedelta(days=self.trust_days)).isoformat()
                matched = item
                updated_records.insert(0, item)
            else:
                updated_records.append(item)

        if matched is None:
            return None

        self._save_raw(updated_records[: self.limit])
        return self._sanitize(matched)

    def revoke_device(self, device_id: str) -> bool:
        active_records = self._load_active_records()
        updated_records = [item for item in active_records if item.get("device_id") != device_id]
        changed = len(updated_records) != len(active_records)
        if changed:
            self._save_raw(updated_records[: self.limit])
        return changed

    def _load_raw(self) -> list[dict[str, Any]]:
        payload = json.loads(self.store_path.read_text(encoding="utf-8") or "[]")
        return [dict(item) for item in payload]

    def _save_raw(self, entries: list[dict[str, Any]]) -> None:
        self.store_path.write_text(json.dumps(entries[: self.limit], indent=2), encoding="utf-8")

    def _load_active_records(self) -> list[dict[str, Any]]:
        active_records = self._filter_active(self._load_raw())
        self._save_raw(active_records[: self.limit])
        return active_records

    def _filter_active(self, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        now = _utc_now()
        active_records = []
        for item in entries:
            expires_at_text = str(item.get("trust_expires_at", ""))
            try:
                expires_at = datetime.fromisoformat(expires_at_text)
            except ValueError:
                continue
            if expires_at <= now:
                continue
            active_records.append(item)
        active_records.sort(key=lambda item: str(item.get("last_seen_at", utc_now_iso())), reverse=True)
        return active_records

    def _sanitize(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "device_id": str(record.get("device_id", "")),
            "device_name": str(record.get("device_name", "iPhone/iPad")),
            "pair_count": int(record.get("pair_count", 0)),
            "last_paired_at": str(record.get("last_paired_at", "")),
            "last_seen_at": str(record.get("last_seen_at", "")),
            "trust_expires_at": str(record.get("trust_expires_at", "")),
        }

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
