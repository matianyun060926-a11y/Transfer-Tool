from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QMouseEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class FileDropZone(QFrame):
    files_selected = Signal(list)
    browse_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("fileDropZone")
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._active = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(8)

        title = QLabel("Drop files here")
        title.setObjectName("dropZoneTitle")
        subtitle = QLabel("Drag one or more files into this box, or click anywhere here to choose files.")
        subtitle.setObjectName("dropZoneSubtitle")
        subtitle.setWordWrap(True)
        hint = QLabel("Files are shared immediately and will appear below as ready for Safari download.")
        hint.setObjectName("dropZoneHint")
        hint.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(hint)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if self._extract_paths(event):
            self._set_active(True)
            event.acceptProposedAction()
            return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._set_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        paths = self._extract_paths(event)
        self._set_active(False)
        if paths:
            self.files_selected.emit(paths)
            event.acceptProposedAction()
            return
        event.ignore()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.browse_requested.emit()
        super().mousePressEvent(event)

    def _extract_paths(self, event) -> list[str]:
        if not event.mimeData().hasUrls():
            return []
        return [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]

    def _set_active(self, active: bool) -> None:
        if self._active == active:
            return
        self._active = active
        self.setProperty("activeDrop", active)
        self.style().unpolish(self)
        self.style().polish(self)
