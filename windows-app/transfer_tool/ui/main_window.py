from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from transfer_tool.ui.theme import build_stylesheet


def _format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    amount = float(value)
    unit_index = 0
    while amount >= 1024 and unit_index < len(units) - 1:
        amount /= 1024
        unit_index += 1
    precision = 0 if amount >= 10 or unit_index == 0 else 1
    return f"{amount:.{precision}f} {units[unit_index]}"


class MainWindow(QMainWindow):
    def __init__(self, state) -> None:
        super().__init__()
        self.state = state
        self._shares: list[dict] = []
        self.setWindowTitle("Transfer Tool")
        self.resize(1120, 780)
        self._set_window_icon()
        self._build_ui()
        self._wire_signals()
        self.state.refresh_receive_mode()

    def _set_window_icon(self) -> None:
        icon_path = self.state.paths.icon_path
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("appRoot")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(24, 22, 24, 18)
        outer.setSpacing(18)
        outer.addWidget(self._build_header())

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_dashboard_tab(), "Overview")
        self.tabs.addTab(self._build_shares_tab(), "Shared Files")
        self.tabs.addTab(self._build_history_tab(), "History")
        self.tabs.addTab(self._build_diagnostics_tab(), "Diagnostics")
        outer.addWidget(self.tabs)

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())

    def _build_header(self) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        icon_label = QLabel()
        icon_label.setFixedSize(52, 52)
        icon_png = self.state.paths.icon_path.with_suffix(".png")
        if icon_png.exists():
            pixmap = QPixmap(str(icon_png)).scaled(52, 52, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)

        text_column = QVBoxLayout()
        text_column.setContentsMargins(0, 0, 0, 0)
        text_column.setSpacing(3)
        title = QLabel("Transfer Tool")
        title.setObjectName("headerTitle")
        subtitle = QLabel("A simple local file bridge between your Windows PC and Safari on iPhone or iPad.")
        subtitle.setObjectName("headerSubtitle")
        subtitle.setWordWrap(True)
        text_column.addWidget(title)
        text_column.addWidget(subtitle)

        self.header_badge = self._make_badge("Pairing ready", "ready")
        layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(text_column, 1)
        layout.addWidget(self.header_badge, 0, Qt.AlignmentFlag.AlignTop)
        return wrapper

    def _build_dashboard_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)
        grid.addWidget(self._build_access_card(), 0, 0)
        grid.addWidget(self._build_settings_card(), 0, 1)
        grid.addWidget(self._build_activity_card(), 1, 0, 1, 2)
        layout.addLayout(grid)
        layout.addStretch()
        return widget

    def _build_access_card(self) -> QFrame:
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addWidget(self._section_heading("Open on iPhone or iPad", "Use the local address below in Safari."))

        url_row = QHBoxLayout()
        url_row.setSpacing(10)
        self.local_url_value = QLabel("-")
        self.local_url_value.setObjectName("urlValue")
        self.local_url_value.setWordWrap(True)
        open_button = self._make_button("Open in Browser", "primary")
        open_button.clicked.connect(self._open_local_url)
        copy_button = self._make_button("Copy", "subtle")
        copy_button.clicked.connect(self._copy_local_url)
        url_row.addWidget(self.local_url_value, 1)
        url_row.addWidget(open_button)
        url_row.addWidget(copy_button)
        layout.addLayout(url_row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(12)
        self.local_ip_value = self._make_value("-")
        self.port_value = self._make_value("-")
        self.pairing_value = QLabel("-")
        self.pairing_value.setObjectName("pairingValue")
        self.pairing_expiry_value = QLabel("-")
        self.pairing_expiry_value.setObjectName("sectionSubtitle")
        self.receive_folder_value = self._make_value("-")
        self.receive_folder_value.setWordWrap(True)

        grid.addWidget(self._make_label("LAN IP"), 0, 0)
        grid.addWidget(self.local_ip_value, 1, 0)
        grid.addWidget(self._make_label("Port"), 0, 1)
        grid.addWidget(self.port_value, 1, 1)
        grid.addWidget(self._make_label("Pairing code"), 2, 0)
        grid.addWidget(self.pairing_value, 3, 0)
        grid.addWidget(self._make_label("Expires"), 2, 1)
        grid.addWidget(self.pairing_expiry_value, 3, 1)
        grid.addWidget(self._make_label("Receive folder"), 4, 0, 1, 2)
        grid.addWidget(self.receive_folder_value, 5, 0, 1, 2)
        layout.addLayout(grid)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        open_folder = self._make_button("Open Receive Folder", "subtle")
        open_folder.clicked.connect(self._open_receive_folder)
        refresh_pairing = self._make_button("Refresh Pairing Code", "subtle")
        refresh_pairing.clicked.connect(self.state.refresh_receive_mode)
        button_row.addWidget(open_folder)
        button_row.addWidget(refresh_pairing)
        button_row.addStretch()
        layout.addLayout(button_row)
        return card

    def _build_settings_card(self) -> QFrame:
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        layout.addWidget(self._section_heading("This Windows PC", "Keep the host name simple and easy to recognize."))

        form = QFormLayout()
        form.setSpacing(12)
        self.device_name_edit = QLineEdit()
        self.device_name_edit.setPlaceholderText("Matt's PC")
        form.addRow("Device name", self.device_name_edit)
        layout.addLayout(form)

        self.pairing_state_badge = self._make_badge("Ready to pair", "ready")
        layout.addWidget(self.pairing_state_badge, 0, Qt.AlignmentFlag.AlignLeft)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)
        save_button = self._make_button("Save Name", "primary")
        save_button.clicked.connect(lambda: self.state.set_device_name(self.device_name_edit.text()))
        disable_button = self._make_button("Disable Pairing", "warning")
        disable_button.clicked.connect(self.state.disable_receive_mode)
        shares_button = self._make_button("Go to Shared Files", "subtle")
        shares_button.clicked.connect(lambda: self.tabs.setCurrentIndex(1))
        button_row.addWidget(save_button)
        button_row.addWidget(disable_button)
        button_row.addWidget(shares_button)
        button_row.addStretch()
        layout.addLayout(button_row)
        layout.addStretch()
        return card

    def _build_activity_card(self) -> QFrame:
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(self._section_heading("Latest activity", "A quick summary of what just happened."))
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        self.activity_value = QLabel("Waiting for activity")
        self.activity_value.setObjectName("activityValue")
        self.activity_value.setWordWrap(True)
        self.activity_badge = self._make_badge("Idle", "neutral")
        top_row.addWidget(self.activity_value, 1)
        top_row.addWidget(self.activity_badge, 0, Qt.AlignmentFlag.AlignTop)
        self.activity_note = QLabel("Uploads and downloads will show up here as they happen.")
        self.activity_note.setObjectName("sectionSubtitle")
        self.activity_note.setWordWrap(True)
        layout.addLayout(top_row)
        layout.addWidget(self.activity_note)
        return card

    def _build_shares_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)
        layout.addWidget(self._section_heading("Shared files", "Choose files on Windows and make them available in Safari."))

        self.shares_table = QTableWidget(0, 5)
        self.shares_table.setHorizontalHeaderLabels(["Created", "Download", "Files", "Size", "Downloads"])
        self.shares_table.horizontalHeader().setStretchLastSection(True)
        self.shares_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.shares_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.shares_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.shares_table.verticalHeader().setVisible(False)
        self.shares_table.setShowGrid(False)
        self.shares_table.setMinimumHeight(420)

        button_row = QHBoxLayout()
        add_button = self._make_button("Share Files", "primary")
        add_button.clicked.connect(self._add_share_files)
        remove_button = self._make_button("Remove Selected", "subtle")
        remove_button.clicked.connect(self._remove_selected_share)
        button_row.addWidget(add_button)
        button_row.addWidget(remove_button)
        button_row.addStretch()

        layout.addWidget(self.shares_table)
        layout.addLayout(button_row)
        return widget

    def _build_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)
        layout.addWidget(self._section_heading("History", "Recent completed transfers stay here for quick reference."))

        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["Time", "Direction", "Peer", "Status", "Files"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setShowGrid(False)
        self.history_table.setMinimumHeight(420)
        layout.addWidget(self.history_table)
        return widget

    def _build_diagnostics_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(14)
        layout.addWidget(self._section_heading("Diagnostics", "Helpful details if something goes wrong."))
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(430)
        layout.addWidget(self.log_view)
        return widget

    def _wire_signals(self) -> None:
        self.state.receive_mode_changed.connect(self._update_receive_mode)
        self.state.shares_changed.connect(self._update_shares)
        self.state.history_changed.connect(self._update_history)
        self.state.web_activity_changed.connect(self._update_activity)
        self.state.status_changed.connect(self.statusBar().showMessage)
        self.state.log_message.connect(self.log_view.appendPlainText)

    def _make_card(self) -> QFrame:
        frame = QFrame()
        frame.setProperty("card", True)
        return frame

    def _section_heading(self, title: str, subtitle: str) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("sectionSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        return wrapper

    def _make_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _make_value(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldValue")
        return label

    def _make_badge(self, text: str, role: str) -> QLabel:
        label = QLabel(text)
        self._set_badge(label, text, role)
        return label

    def _set_badge(self, label: QLabel, text: str, role: str) -> None:
        label.setText(text)
        label.setProperty("badgeRole", role)
        label.style().unpolish(label)
        label.style().polish(label)

    def _make_button(self, text: str, variant: str) -> QPushButton:
        button = QPushButton(text)
        button.setProperty("variant", variant)
        return button

    def _copy_local_url(self) -> None:
        text = self.local_url_value.text().strip()
        if not text or text == "-":
            QMessageBox.information(self, "Copy URL", "The local URL is not ready yet.")
            return
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage("Local URL copied")

    def _open_local_url(self) -> None:
        url = self.local_url_value.text().strip()
        if url and url != "-":
            QDesktopServices.openUrl(QUrl(url))

    def _open_receive_folder(self) -> None:
        path_text = self.receive_folder_value.text().strip()
        if path_text and path_text != "-":
            QDesktopServices.openUrl(QUrl.fromLocalFile(path_text))

    def _add_share_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose files to share with Safari")
        if paths:
            self.state.create_share(paths)

    def _remove_selected_share(self) -> None:
        row = self.shares_table.currentRow()
        if row < 0 or row >= len(self._shares):
            QMessageBox.information(self, "Remove Share", "Choose a shared file batch first.")
            return
        self.state.remove_share(self._shares[row]["share_id"])

    def _update_receive_mode(self, payload: dict) -> None:
        enabled = bool(payload.get("enabled"))
        self.device_name_edit.setText(payload.get("device_name", ""))
        self.local_url_value.setText(payload.get("local_url", "-"))
        self.local_ip_value.setText(payload.get("ip_address", "-"))
        self.port_value.setText(str(payload.get("port", "-")))
        self.pairing_value.setText(payload.get("pairing_code", "Disabled") or "Disabled")
        self.pairing_expiry_value.setText(payload.get("expires_at", "-"))
        self.receive_folder_value.setText(payload.get("receive_folder", "-"))
        badge_text = "Pairing ready" if enabled else "Pairing off"
        badge_role = "ready" if enabled else "warning"
        self._set_badge(self.header_badge, badge_text, badge_role)
        self._set_badge(self.pairing_state_badge, badge_text, badge_role)

    def _update_shares(self, shares: list[dict]) -> None:
        self._shares = shares
        self.shares_table.setRowCount(len(shares))
        for row, item in enumerate(shares):
            self.shares_table.setItem(row, 0, QTableWidgetItem(item["created_at"]))
            self.shares_table.setItem(row, 1, QTableWidgetItem(item["download_name"]))
            self.shares_table.setItem(row, 2, QTableWidgetItem(str(item["file_count"])))
            self.shares_table.setItem(row, 3, QTableWidgetItem(_format_bytes(int(item["total_bytes"]))))
            self.shares_table.setItem(row, 4, QTableWidgetItem(str(item.get("downloads_count", 0))))
        self.shares_table.resizeColumnsToContents()

    def _update_history(self, entries: list[dict]) -> None:
        self.history_table.setRowCount(len(entries))
        for row, item in enumerate(entries):
            self.history_table.setItem(row, 0, QTableWidgetItem(item["timestamp"]))
            self.history_table.setItem(row, 1, QTableWidgetItem(item["direction"].title()))
            self.history_table.setItem(row, 2, QTableWidgetItem(item["peer_device_name"]))
            self.history_table.setItem(row, 3, QTableWidgetItem(item["status"].title()))
            self.history_table.setItem(row, 4, QTableWidgetItem(", ".join(item["filenames"])))
        self.history_table.resizeColumnsToContents()

    def _update_activity(self, payload: dict) -> None:
        message = payload.get("message", "Waiting for activity")
        status = payload.get("status", "idle")
        self.activity_value.setText(message)
        self.activity_note.setText(f"Status: {status}")
        role = "ready" if status in {"success", "ready", "sending", "receiving"} else "neutral"
        if status in {"failed", "error"}:
            role = "warning"
        self._set_badge(self.activity_badge, status.title(), role)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.state.shutdown()
        super().closeEvent(event)


def run_app(state) -> int:
    app = QApplication([])
    app.setStyleSheet(build_stylesheet())
    icon_path = state.paths.icon_path
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = MainWindow(state)
    window.show()
    return app.exec()
