from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from transfer_tool.networking.protocol import DEFAULT_PORT
from transfer_tool.services.network_utils import get_hostname


@dataclass(slots=True)
class AppSettings:
    device_name: str
    port: int = DEFAULT_PORT


class SettingsStore:
    def __init__(self, settings_path: Path) -> None:
        self.settings_path = settings_path

    def load(self) -> AppSettings:
        if not self.settings_path.exists():
            settings = AppSettings(device_name=get_hostname())
            self.save(settings)
            return settings
        payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        return AppSettings(
            device_name=str(payload.get("device_name") or get_hostname()),
            port=int(payload.get("port") or DEFAULT_PORT),
        )

    def save(self, settings: AppSettings) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(asdict(settings), indent=2), encoding="utf-8")

