from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable


class LoggingService:
    def __init__(self, log_path: Path, callback: Callable[[str], None] | None = None) -> None:
        self.log_path = log_path
        self.callback = callback
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = logging.getLogger(f"transfer_tool.{id(self)}")
        self._logger.setLevel(logging.INFO)
        self._logger.handlers.clear()
        handler = logging.FileHandler(self.log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        self._logger.addHandler(handler)

    def info(self, message: str) -> None:
        self._logger.info(message)
        if self.callback is not None:
            self.callback(message)

    def error(self, message: str) -> None:
        self._logger.error(message)
        if self.callback is not None:
            self.callback(f"ERROR: {message}")
