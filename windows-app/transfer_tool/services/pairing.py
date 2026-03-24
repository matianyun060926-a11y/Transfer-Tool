from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from transfer_tool.models.transfer import PairingSession


@dataclass(slots=True)
class ReceiveModeSnapshot:
    enabled: bool
    pairing_code: str
    expires_at: str
    qr_pair_token: str


class PairingManager:
    def __init__(self, code_ttl_minutes: int = 10, session_ttl_minutes: int = 10) -> None:
        self.code_ttl_minutes = code_ttl_minutes
        self.session_ttl_minutes = session_ttl_minutes
        self._lock = threading.Lock()
        self._enabled = False
        self._pairing_code = ""
        self._code_expires_at = datetime.now(UTC)
        self._qr_pair_token = ""
        self._sessions: dict[str, PairingSession] = {}

    def enable_receive_mode(self) -> ReceiveModeSnapshot:
        with self._lock:
            self._enabled = True
            self._pairing_code = f"{secrets.randbelow(1_000_000):06d}"
            self._code_expires_at = datetime.now(UTC) + timedelta(minutes=self.code_ttl_minutes)
            self._qr_pair_token = secrets.token_urlsafe(24)
            return self.snapshot()

    def disable_receive_mode(self) -> ReceiveModeSnapshot:
        with self._lock:
            self._enabled = False
            self._pairing_code = ""
            self._qr_pair_token = ""
            self._sessions.clear()
            return self.snapshot()

    def snapshot(self) -> ReceiveModeSnapshot:
        enabled = self._enabled and datetime.now(UTC) < self._code_expires_at
        code = self._pairing_code if enabled else ""
        qr_pair_token = self._qr_pair_token if enabled else ""
        return ReceiveModeSnapshot(
            enabled=enabled,
            pairing_code=code,
            expires_at=self._code_expires_at.isoformat(),
            qr_pair_token=qr_pair_token,
        )

    def create_session(self, sender_device_id: str, sender_device_name: str, pairing_code: str) -> PairingSession:
        with self._lock:
            self._validate_receive_mode(pairing_code=pairing_code)
            return self._issue_session(sender_device_id, sender_device_name)

    def create_session_from_qr(self, sender_device_id: str, sender_device_name: str, qr_pair_token: str) -> PairingSession:
        with self._lock:
            self._validate_receive_mode(qr_pair_token=qr_pair_token)
            self._qr_pair_token = ""
            return self._issue_session(sender_device_id, sender_device_name)

    def create_trusted_session(self, sender_device_id: str, sender_device_name: str) -> PairingSession:
        with self._lock:
            return self._issue_session(sender_device_id, sender_device_name)

    def validate_session(self, token: str) -> PairingSession | None:
        with self._lock:
            session = self._sessions.get(token)
            if session is None:
                return None
            if datetime.now(UTC) >= session.expires_at:
                self._sessions.pop(token, None)
                return None
            return session

    def revoke_sessions_for_device(self, sender_device_id: str) -> None:
        with self._lock:
            for token, session in list(self._sessions.items()):
                if session.sender_device_id == sender_device_id:
                    self._sessions.pop(token, None)

    def _issue_session(self, sender_device_id: str, sender_device_name: str) -> PairingSession:
        now = datetime.now(UTC)
        token = secrets.token_urlsafe(24)
        session = PairingSession(
            session_token=token,
            sender_device_id=sender_device_id,
            sender_device_name=sender_device_name,
            created_at=now,
            expires_at=now + timedelta(minutes=self.session_ttl_minutes),
        )
        self._sessions[token] = session
        return session

    def _validate_receive_mode(self, pairing_code: str = "", qr_pair_token: str = "") -> None:
        now = datetime.now(UTC)
        if not self._enabled:
            raise ValueError("This device is not ready to receive right now")
        if now >= self._code_expires_at:
            raise ValueError("Pairing code expired. Refresh receive mode and try again")
        if pairing_code:
            if pairing_code != self._pairing_code:
                raise ValueError("Pairing code did not match")
            return
        if qr_pair_token:
            if qr_pair_token != self._qr_pair_token:
                raise ValueError("QR pairing link is no longer valid. Refresh it on Windows and try again")
            return
        raise ValueError("A pairing code or QR pairing token is required")
