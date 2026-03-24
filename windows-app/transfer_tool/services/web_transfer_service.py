from __future__ import annotations

from pathlib import Path
from typing import Callable

from transfer_tool.models.history import HistoryEntry


ProgressEvent = Callable[[dict], None]


class WebTransferService:
    def __init__(
        self,
        file_store,
        share_store,
        history_store,
        trusted_device_store,
        logger,
        event_callback: ProgressEvent | None = None,
    ) -> None:
        self.file_store = file_store
        self.share_store = share_store
        self.history_store = history_store
        self.trusted_device_store = trusted_device_store
        self.logger = logger
        self.event_callback = event_callback

    def create_share(self, source_paths: list[str]) -> dict:
        share = self.share_store.create_share(source_paths)
        self.logger.info(f"Prepared {share['file_count']} file(s) for mobile download")
        self._emit(
            {
                "status": "ready",
                "message": f"Prepared {share['file_count']} file(s) for Safari download",
                "share_id": share["share_id"],
                "detail": share["download_name"],
            }
        )
        return share

    def list_shares(self) -> list[dict]:
        return self.share_store.load()

    def remove_share(self, share_id: str) -> None:
        self.share_store.remove_share(share_id)
        self.logger.info("Removed shared file batch")
        self._emit({"status": "removed", "message": "Removed shared file batch", "share_id": share_id})

    def save_uploaded_files(self, uploaded_files: list, mobile_device_name: str) -> dict:
        batch = self.file_store.create_batch_dir()
        saved_names: list[str] = []
        saved_paths: list[str] = []
        total_bytes = 0
        for upload in uploaded_files:
            safe_name = self.file_store.resolve_unique_name(batch.batch_dir, upload.filename or "upload")
            target_path = batch.batch_dir / safe_name
            upload.save(target_path)
            saved_names.append(safe_name)
            saved_paths.append(str(target_path))
            total_bytes += target_path.stat().st_size
            self._emit(
                {
                    "status": "receiving",
                    "message": f"Saved {safe_name}",
                    "current_file": safe_name,
                    "detail": f"Receiving from {mobile_device_name or 'iPhone/iPad'}",
                }
            )
        entry = HistoryEntry(
            direction="incoming",
            peer_device_name=mobile_device_name or "iPhone/iPad",
            filenames=saved_names,
            total_bytes=total_bytes,
            status="success",
            details=f"Saved to {batch.batch_dir}",
            saved_paths=saved_paths,
        )
        self.history_store.add_entry(entry)
        self.logger.info(f"Received {len(saved_names)} file(s) from {mobile_device_name or 'iPhone/iPad'}")
        self._emit(
            {
                "status": "success",
                "message": f"Received {len(saved_names)} file(s) from {mobile_device_name or 'iPhone/iPad'}",
                "detail": f"Saved to {batch.batch_dir}",
            }
        )
        return {
            "saved_files": saved_names,
            "saved_to": str(batch.batch_dir),
            "total_bytes": total_bytes,
        }

    def list_history(self) -> list[dict]:
        return [entry.to_dict() for entry in self.history_store.load()]

    def issue_trusted_device(self, device_id: str, device_name: str) -> dict:
        trusted_token, record = self.trusted_device_store.issue_trust(device_id, device_name)
        self._emit(
            {
                "status": "paired",
                "message": f"Paired with {device_name or 'iPhone/iPad'}",
                "trusted_device_name": device_name or "iPhone/iPad",
                "detail": f"Trusted until {record['trust_expires_at']}",
            }
        )
        return {
            "trusted_device_token": trusted_token,
            "trusted_until": record["trust_expires_at"],
        }

    def restore_trusted_device(self, trusted_token: str, device_id: str, device_name: str) -> dict | None:
        record = self.trusted_device_store.restore_trust(trusted_token, device_id, device_name)
        if record is not None:
            self._emit(
                {
                    "status": "ready",
                    "message": f"Restored trusted access for {record['device_name']}",
                    "detail": f"Trusted until {record['trust_expires_at']}",
                }
            )
        return record

    def list_trusted_devices(self) -> list[dict]:
        return self.trusted_device_store.list_devices()

    def revoke_trusted_device(self, device_id: str) -> bool:
        revoked = self.trusted_device_store.revoke_device(device_id)
        if revoked:
            self._emit(
                {
                    "status": "ready",
                    "message": "Trusted device revoked",
                    "detail": device_id,
                }
            )
        return revoked

    def get_download_payload(self, share_id: str, mobile_device_name: str) -> dict:
        share = self.share_store.get_share(share_id)
        path = Path(share["download_path"])
        if not path.exists():
            raise ValueError("Shared file package is no longer available")
        updated_share = self.share_store.record_download(share_id)
        entry = HistoryEntry(
            direction="outgoing",
            peer_device_name=mobile_device_name or "iPhone/iPad",
            filenames=[file_item["name"] for file_item in share["files"]],
            total_bytes=int(share["total_bytes"]),
            status="success",
            details=f"Downloaded as {share['download_name']}",
            saved_paths=[str(path)],
        )
        self.history_store.add_entry(entry)
        self.logger.info(
            f"Mobile download started for {share['download_name']} by {mobile_device_name or 'iPhone/iPad'}"
        )
        self._emit(
            {
                "status": "sending",
                "message": f"Serving {share['download_name']} to {mobile_device_name or 'iPhone/iPad'}",
                "share_id": share_id,
                "downloads_count": updated_share["downloads_count"],
                "detail": f"Download count: {updated_share['downloads_count']}",
            }
        )
        return {
            "path": path,
            "download_name": share["download_name"],
            "total_bytes": int(share["total_bytes"]),
            "mimetype": "application/zip" if share["package_kind"] == "zip" else "application/octet-stream",
        }

    def _emit(self, payload: dict) -> None:
        if self.event_callback is not None:
            self.event_callback(payload)
