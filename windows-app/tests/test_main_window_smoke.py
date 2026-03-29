import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication

from transfer_tool.ui.main_window import MainWindow


class DummyState(QObject):
    receive_mode_changed = Signal(dict)
    shares_changed = Signal(list)
    history_changed = Signal(list)
    trusted_devices_changed = Signal(list)
    web_activity_changed = Signal(dict)
    status_changed = Signal(str)
    log_message = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        project_root = Path(__file__).resolve().parents[2]
        self.paths = type(
            "Paths",
            (),
            {"icon_path": project_root / "windows-app" / "resources" / "transfer-tool.ico"},
        )()
        self.shutdown_called = False

    def refresh_receive_mode(self) -> None:
        self.receive_mode_changed.emit(
            {
                "enabled": True,
                "pairing_code": "123456",
                "expires_at": "2099-01-01 12:00",
                "qr_pair_url": "http://127.0.0.1:8877/?pair_token=test",
                "port": 8877,
                "ip_address": "127.0.0.1",
                "device_name": "Test Device",
                "receive_folder": "C:/Temp/TransferTool",
                "local_url": "http://127.0.0.1:8877/",
            }
        )

    def set_device_name(self, _name: str) -> None:
        return

    def disable_receive_mode(self) -> None:
        return

    def create_share(self, _paths: list[str]) -> None:
        return

    def remove_share(self, _share_id: str) -> None:
        return

    def revoke_trusted_device(self, _device_id: str) -> None:
        return

    def shutdown(self) -> None:
        self.shutdown_called = True


@pytest.fixture
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_main_window_smoke_custom_chrome_sync(app: QApplication) -> None:
    state = DummyState()
    window = MainWindow(state)

    try:
        window.show()
        app.processEvents()

        assert window._use_custom_title_bar is True
        assert window.title_bar is not None
        assert window.window_footer is not None

        window.title_bar._maximize_button.click()
        app.processEvents()
        app.processEvents()
        assert window.isMaximized() is True
        assert window.window_surface.property("windowMaximized") == window.isMaximized()
        assert window.window_footer.property("windowMaximized") == window.isMaximized()
        assert window.title_bar.property("windowMaximized") == window.isMaximized()
        margins = window.window_canvas_layout.contentsMargins()
        assert margins.left() == 0
        assert margins.top() == 0

        window.title_bar._maximize_button.click()
        app.processEvents()
        app.processEvents()
        assert window.isMaximized() is False
        assert window.window_surface.property("windowMaximized") == window.isMaximized()
        assert window.window_footer.property("windowMaximized") == window.isMaximized()
        assert window.title_bar.property("windowMaximized") == window.isMaximized()
        margins = window.window_canvas_layout.contentsMargins()
        assert margins.left() == window._window_margin
        assert margins.top() == window._window_margin

        top_left_edges = window._resize_edges_at(window.mapToGlobal(QPoint(1, 1)))
        bottom_right_edges = window._resize_edges_at(
            window.mapToGlobal(QPoint(window.width() - 2, window.height() - 2))
        )
        center_edges = window._resize_edges_at(window.mapToGlobal(window.rect().center()))

        assert top_left_edges == (Qt.Edge.TopEdge | Qt.Edge.LeftEdge)
        assert bottom_right_edges == (Qt.Edge.BottomEdge | Qt.Edge.RightEdge)
        assert not center_edges
    finally:
        window.close()
        app.processEvents()

    assert state.shutdown_called is True
