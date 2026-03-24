from pathlib import Path

import pytest
import requests

pytest.importorskip("flask")

from transfer_tool.networking.http_server import TransferServer
from transfer_tool.services.file_store import FileStore
from transfer_tool.services.history_store import HistoryStore
from transfer_tool.services.logging_service import LoggingService
from transfer_tool.services.pairing import PairingManager
from transfer_tool.services.share_store import ShareStore
from transfer_tool.services.trusted_device_store import TrustedDeviceStore
from transfer_tool.services.web_transfer_service import WebTransferService


def test_web_flow_smoke(tmp_path: Path) -> None:
    web_root = tmp_path / "web"
    assets_root = web_root / "assets"
    assets_root.mkdir(parents=True)
    (web_root / "index.html").write_text("<html><body>ok</body></html>", encoding="utf-8")
    (assets_root / "app.js").write_text("console.log('ok');", encoding="utf-8")

    logger = LoggingService(tmp_path / "logs" / "app.log")
    history = HistoryStore(tmp_path / "history.json")
    file_store = FileStore(tmp_path / "received")
    share_store = ShareStore(tmp_path / "shared.json", tmp_path / "shared_files")
    trusted_devices = TrustedDeviceStore(tmp_path / "trusted_devices.json")
    pairing = PairingManager()
    service = WebTransferService(file_store, share_store, history, trusted_devices, logger)

    def device_payload() -> dict:
        snapshot = pairing.snapshot()
        return {
            "device_id": "device123",
            "device_name": "Receiver",
            "platform": "windows-hosted-web",
            "ready_to_receive": snapshot.enabled,
            "port": 8877,
        }

    server = TransferServer(
        device_payload_provider=device_payload,
        pairing_manager=pairing,
        transfer_service=service,
        logger=logger,
        web_root=web_root,
        host="127.0.0.1",
        port=8877,
    )
    server.start()
    try:
        snapshot = pairing.enable_receive_mode()
        pair_response = requests.post(
            "http://127.0.0.1:8877/api/pair/direct",
            json={
                "sender_device_id": "mobile-1",
                "sender_device_name": "Test iPhone",
                "pair_token": snapshot.qr_pair_token,
            },
            timeout=5,
        )
        pair_response.raise_for_status()
        pair_payload = pair_response.json()
        token = pair_payload["session_token"]

        trusted_session_response = requests.post(
            "http://127.0.0.1:8877/api/trusted-session",
            json={
                "trusted_device_token": pair_payload["trusted_device_token"],
                "sender_device_id": "mobile-1",
                "sender_device_name": "Test iPhone",
            },
            timeout=5,
        )
        trusted_session_response.raise_for_status()
        trusted_token = trusted_session_response.json()["session_token"]

        trusted_response = requests.get(
            "http://127.0.0.1:8877/api/trusted-devices",
            headers={"X-Session-Token": token},
            timeout=5,
        )
        trusted_response.raise_for_status()
        assert trusted_response.json()["items"][0]["device_name"] == "Test iPhone"

        upload_response = requests.post(
            "http://127.0.0.1:8877/api/uploads",
            headers={"X-Session-Token": trusted_token},
            files={"files": ("hello.txt", b"hello world")},
            timeout=10,
        )
        upload_response.raise_for_status()
        assert history.load()[0].direction == "incoming"

        source_file = tmp_path / "source.txt"
        source_file.write_text("from windows", encoding="utf-8")
        share = service.create_share([str(source_file)])
        shares_response = requests.get(
            "http://127.0.0.1:8877/api/shares",
            headers={"X-Session-Token": token},
            timeout=5,
        )
        shares_response.raise_for_status()
        assert shares_response.json()["items"][0]["share_id"] == share["share_id"]

        download_response = requests.get(
            f"http://127.0.0.1:8877/api/downloads/{share['share_id']}",
            headers={"X-Session-Token": token},
            timeout=10,
        )
        download_response.raise_for_status()
        assert download_response.content == b"from windows"
        assert history.load()[0].direction == "outgoing"
    finally:
        server.stop()
