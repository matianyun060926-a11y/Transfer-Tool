from __future__ import annotations

import threading
from http import HTTPStatus
from pathlib import Path
from typing import Callable

from flask import Flask, jsonify, request, send_file, send_from_directory
from werkzeug.serving import make_server

from transfer_tool.networking.protocol import APP_VERSION, DEFAULT_PORT, SESSION_HEADER


class TransferServer:
    def __init__(
        self,
        device_payload_provider: Callable[[], dict],
        pairing_manager,
        transfer_service,
        logger,
        web_root: Path,
        host: str = "0.0.0.0",
        port: int = DEFAULT_PORT,
    ) -> None:
        self.host = host
        self.port = port
        self._device_payload_provider = device_payload_provider
        self._pairing_manager = pairing_manager
        self._transfer_service = transfer_service
        self._logger = logger
        self._web_root = web_root
        self._app = Flask(__name__)
        self._server = None
        self._thread: threading.Thread | None = None
        self._configure_routes()

    def _configure_routes(self) -> None:
        app = self._app

        @app.get("/")
        def index():
            return send_from_directory(self._web_root, "index.html")

        @app.get("/assets/<path:asset_path>")
        def assets(asset_path: str):
            return send_from_directory(self._web_root / "assets", asset_path)

        @app.get("/favicon.ico")
        def favicon():
            return send_from_directory(self._web_root, "favicon.ico")

        @app.get("/favicon.png")
        def favicon_png():
            return send_from_directory(self._web_root, "favicon.png")

        @app.get("/apple-touch-icon.png")
        def apple_touch_icon():
            return send_from_directory(self._web_root, "apple-touch-icon.png")

        @app.get("/icon-192.png")
        def icon_192():
            return send_from_directory(self._web_root, "icon-192.png")

        @app.get("/icon-512.png")
        def icon_512():
            return send_from_directory(self._web_root, "icon-512.png")

        @app.get("/site.webmanifest")
        def site_manifest():
            return send_from_directory(self._web_root, "site.webmanifest")

        @app.get("/api/device")
        def get_device() -> tuple:
            payload = self._device_payload_provider()
            payload["app_version"] = APP_VERSION
            payload["mobile_url"] = f"http://{request.host}/"
            return jsonify(payload), HTTPStatus.OK

        @app.post("/api/pair")
        def pair() -> tuple:
            body = request.get_json(silent=True) or {}
            try:
                session = self._pairing_manager.create_session(
                    sender_device_id=str(body.get("sender_device_id", "mobile-web")),
                    sender_device_name=str(body.get("sender_device_name", "iPhone/iPad")),
                    pairing_code=str(body.get("pairing_code", "")),
                )
            except ValueError as exc:
                return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST
            return (
                jsonify(
                    {
                        "session_token": session.session_token,
                        "expires_at": session.expires_at.isoformat(),
                    }
                ),
                HTTPStatus.OK,
            )

        @app.get("/api/history")
        def history() -> tuple:
            session = self._require_session()
            if session is None:
                return jsonify({"error": "Invalid or expired session"}), HTTPStatus.UNAUTHORIZED
            return jsonify({"items": self._transfer_service.list_history()}), HTTPStatus.OK

        @app.get("/api/shares")
        def shares() -> tuple:
            session = self._require_session()
            if session is None:
                return jsonify({"error": "Invalid or expired session"}), HTTPStatus.UNAUTHORIZED
            return jsonify({"items": self._transfer_service.list_shares()}), HTTPStatus.OK

        @app.post("/api/uploads")
        def uploads() -> tuple:
            session = self._require_session()
            if session is None:
                return jsonify({"error": "Invalid or expired session"}), HTTPStatus.UNAUTHORIZED
            files = request.files.getlist("files")
            if not files:
                return jsonify({"error": "Choose at least one file"}), HTTPStatus.BAD_REQUEST
            result = self._transfer_service.save_uploaded_files(files, session.sender_device_name)
            return jsonify(result), HTTPStatus.OK

        @app.get("/api/downloads/<share_id>")
        def download(share_id: str):
            session = self._require_session()
            if session is None:
                return jsonify({"error": "Invalid or expired session"}), HTTPStatus.UNAUTHORIZED
            try:
                payload = self._transfer_service.get_download_payload(share_id, session.sender_device_name)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), HTTPStatus.BAD_REQUEST
            return send_file(
                payload["path"],
                as_attachment=True,
                download_name=payload["download_name"],
                mimetype=payload["mimetype"],
                conditional=True,
                max_age=0,
            )

    def _require_session(self):
        token = request.headers.get(SESSION_HEADER, "")
        return self._pairing_manager.validate_session(token)

    def start(self) -> None:
        if self._server is not None:
            return
        self._server = make_server(self.host, self.port, self._app)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self._logger.info(f"Listening for desktop + web transfers on {self.host}:{self.port}")

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        self._logger.info("Local transfer server stopped")
