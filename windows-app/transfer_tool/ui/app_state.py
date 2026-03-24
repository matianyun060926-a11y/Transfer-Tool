from __future__ import annotations

from uuid import uuid4

from PySide6.QtCore import QObject, Signal

from transfer_tool.networking.http_server import TransferServer
from transfer_tool.networking.protocol import DEFAULT_PORT
from transfer_tool.services.app_settings import AppSettings, SettingsStore
from transfer_tool.services.file_store import FileStore
from transfer_tool.services.history_store import HistoryStore
from transfer_tool.services.logging_service import LoggingService
from transfer_tool.services.network_utils import get_preferred_lan_ip
from transfer_tool.services.pairing import PairingManager
from transfer_tool.services.runtime_paths import resolve_app_paths
from transfer_tool.services.share_store import ShareStore
from transfer_tool.services.trusted_device_store import TrustedDeviceStore
from transfer_tool.services.web_transfer_service import WebTransferService


class AppState(QObject):
    receive_mode_changed = Signal(dict)
    shares_changed = Signal(list)
    history_changed = Signal(list)
    trusted_devices_changed = Signal(list)
    web_activity_changed = Signal(dict)
    status_changed = Signal(str)
    log_message = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.paths = resolve_app_paths()
        self.repo_root = self.paths.project_root
        self.runtime_root = self.paths.runtime_root
        self.web_root = self.paths.web_root
        self.settings_store = SettingsStore(self.runtime_root / "app_settings.json")
        self.settings = self.settings_store.load()
        self.settings.port = self.settings.port or DEFAULT_PORT
        self.logger = LoggingService(self.runtime_root / "logs" / "windows-app.log", self.log_message.emit)
        self.history_store = HistoryStore(self.runtime_root / "transfer_history" / "windows_history.json")
        self.trusted_device_store = TrustedDeviceStore(self.runtime_root / "transfer_history" / "trusted_devices.json")
        self.file_store = FileStore(self.runtime_root / "received_files")
        self.share_store = ShareStore(
            self.runtime_root / "transfer_history" / "shared_files.json",
            self.runtime_root / "shared_files",
        )
        self.pairing_manager = PairingManager()
        self.desktop_device_id = uuid4().hex
        self.transfer_service = WebTransferService(
            file_store=self.file_store,
            share_store=self.share_store,
            history_store=self.history_store,
            trusted_device_store=self.trusted_device_store,
            logger=self.logger,
            event_callback=self._handle_web_event,
        )
        self.server = TransferServer(
            device_payload_provider=self.device_payload,
            pairing_manager=self.pairing_manager,
            transfer_service=self.transfer_service,
            logger=self.logger,
            web_root=self.web_root,
            port=self.settings.port,
        )
        self.server.start()
        self.refresh_receive_mode()
        self.emit_shares()
        self.emit_history()
        self.emit_trusted_devices()

    def shutdown(self) -> None:
        self.server.stop()

    def local_ip(self) -> str:
        return get_preferred_lan_ip()

    def local_url(self) -> str:
        return f"http://{self.local_ip()}:{self.settings.port}/"

    def device_payload(self) -> dict:
        receive_mode = self.pairing_manager.snapshot()
        return {
            "device_id": self.desktop_device_id,
            "device_name": self.settings.device_name,
            "platform": "windows-hosted-web",
            "ready_to_receive": receive_mode.enabled,
            "port": self.settings.port,
        }

    def refresh_receive_mode(self) -> None:
        snapshot = self.pairing_manager.enable_receive_mode()
        self.receive_mode_changed.emit(
            {
                "enabled": snapshot.enabled,
                "pairing_code": snapshot.pairing_code,
                "expires_at": snapshot.expires_at,
                "qr_pair_url": f"{self.local_url()}?pair_token={snapshot.qr_pair_token}",
                "port": self.settings.port,
                "ip_address": self.local_ip(),
                "device_name": self.settings.device_name,
                "receive_folder": str(self.file_store.receive_root),
                "local_url": self.local_url(),
            }
        )
        self.status_changed.emit("Pairing code refreshed")

    def disable_receive_mode(self) -> None:
        snapshot = self.pairing_manager.disable_receive_mode()
        self.receive_mode_changed.emit(
            {
                "enabled": snapshot.enabled,
                "pairing_code": snapshot.pairing_code,
                "expires_at": snapshot.expires_at,
                "qr_pair_url": "",
                "port": self.settings.port,
                "ip_address": self.local_ip(),
                "device_name": self.settings.device_name,
                "receive_folder": str(self.file_store.receive_root),
                "local_url": self.local_url(),
            }
        )
        self.status_changed.emit("Pairing disabled")

    def set_device_name(self, name: str) -> None:
        cleaned = name.strip() or self.settings.device_name
        self.settings = AppSettings(device_name=cleaned, port=self.settings.port)
        self.settings_store.save(self.settings)
        self.refresh_receive_mode()

    def create_share(self, file_paths: list[str]) -> None:
        try:
            self.transfer_service.create_share(file_paths)
            self.emit_shares()
            self.status_changed.emit("Shared files are ready for Safari")
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"Failed to prepare shared files: {exc}")
            self.status_changed.emit(f"Failed to prepare shared files: {exc}")

    def remove_share(self, share_id: str) -> None:
        try:
            self.transfer_service.remove_share(share_id)
            self.emit_shares()
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"Failed to remove shared files: {exc}")
            self.status_changed.emit(f"Failed to remove shared files: {exc}")

    def emit_shares(self) -> None:
        self.shares_changed.emit(self.transfer_service.list_shares())

    def emit_history(self) -> None:
        self.history_changed.emit(self.transfer_service.list_history())

    def emit_trusted_devices(self) -> None:
        self.trusted_devices_changed.emit(self.transfer_service.list_trusted_devices())

    def revoke_trusted_device(self, device_id: str) -> None:
        try:
            if not self.transfer_service.revoke_trusted_device(device_id):
                self.status_changed.emit("That trusted device was already removed")
                return
            self.pairing_manager.revoke_sessions_for_device(device_id)
            self.emit_trusted_devices()
            self.status_changed.emit("Trusted device revoked")
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"Failed to revoke trusted device: {exc}")
            self.status_changed.emit(f"Failed to revoke trusted device: {exc}")

    def _handle_web_event(self, payload: dict) -> None:
        self.web_activity_changed.emit(payload)
        self.emit_history()
        self.emit_shares()
        self.emit_trusted_devices()
