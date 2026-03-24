from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QProgressBar,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from transfer_tool.services.qr_code_service import build_qr_png_bytes
from transfer_tool.ui.file_drop_zone import FileDropZone
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
        self._trusted_devices: list[dict] = []
        self._nav_buttons: dict[str, QPushButton] = {}
        self.setWindowTitle("Transfer Tool")
        self.resize(1180, 820)
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
        shell = QHBoxLayout(root)
        shell.setContentsMargins(18, 18, 18, 18)
        shell.setSpacing(18)
        shell.addWidget(self._build_sidebar())
        shell.addWidget(self._build_main_area(), 1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(188)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        icon_label = QLabel()
        icon_label.setFixedSize(30, 30)
        icon_png = self.state.paths.icon_path.with_suffix(".png")
        if icon_png.exists():
            pixmap = QPixmap(str(icon_png)).scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        title = QLabel("Transfer Tool")
        title.setObjectName("sidebarBrand")
        brand_row.addWidget(icon_label)
        brand_row.addWidget(title, 1)
        layout.addLayout(brand_row)

        layout.addWidget(self._make_nav_button("overview", "Overview"))
        layout.addWidget(self._make_nav_button("files", "Shared Files"))
        layout.addWidget(self._make_nav_button("history", "History"))
        layout.addWidget(self._make_nav_button("diagnostics", "Diagnostics"))
        layout.addStretch()
        return sidebar

    def _build_main_area(self) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.addWidget(self._build_header())

        self.page_stack = QStackedWidget()
        self.page_stack.addWidget(self._build_overview_page())
        self.page_stack.addWidget(self._build_files_page())
        self.page_stack.addWidget(self._build_history_page())
        self.page_stack.addWidget(self._build_diagnostics_page())
        layout.addWidget(self.page_stack, 1)

        self._set_page("overview")
        return wrapper

    def _build_header(self) -> QFrame:
        card = self._make_card("pageHeader")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(6)
        self.page_kicker = QLabel("Overview")
        self.page_kicker.setObjectName("pageKicker")
        self.page_title = QLabel("Connect Your Device")
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel("Use the QR code or local URL below to connect your iPhone or iPad.")
        self.page_subtitle.setObjectName("pageSubtitle")
        self.page_subtitle.setWordWrap(True)
        layout.addWidget(self.page_kicker)
        layout.addWidget(self.page_title)
        layout.addWidget(self.page_subtitle)
        return card

    def _build_overview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        top = QGridLayout()
        top.setHorizontalSpacing(16)
        top.setVerticalSpacing(16)
        top.addWidget(self._build_pairing_card(), 0, 0, 1, 2)
        top.addWidget(self._build_qr_card(), 0, 2)
        layout.addLayout(top)
        layout.addWidget(self._build_connection_card())
        return page

    def _build_pairing_card(self) -> QFrame:
        card = self._make_card("heroCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)
        self.pairing_state_badge = self._make_badge("Ready to pair", "ready")
        layout.addWidget(self.pairing_state_badge, 0, Qt.AlignmentFlag.AlignLeft)
        note = QLabel("Use the current pairing code or scan the QR code for direct trusted pairing.")
        note.setObjectName("sectionSubtitle")
        note.setWordWrap(True)
        layout.addWidget(note)

        digits_row = QHBoxLayout()
        digits_row.setSpacing(10)
        self.pairing_digit_labels: list[QLabel] = []
        for _ in range(6):
            label = QLabel("-")
            label.setObjectName("pairDigit")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFixedSize(56, 66)
            self.pairing_digit_labels.append(label)
            digits_row.addWidget(label)
        digits_row.addStretch()
        layout.addLayout(digits_row)

        self.pairing_expiry_value = QLabel("-")
        self.pairing_expiry_value.setObjectName("sectionSubtitle")
        layout.addWidget(self.pairing_expiry_value)
        return card

    def _build_qr_card(self) -> QFrame:
        card = self._make_card("qrCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        self.qr_preview = QLabel()
        self.qr_preview.setObjectName("qrPreview")
        self.qr_preview.setFixedSize(160, 200)
        self.qr_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel("Scan with Camera")
        title.setObjectName("sectionTitleCompact")
        note = QLabel("Opens the mobile page and pairs that browser automatically.")
        note.setObjectName("sectionSubtitle")
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.qr_preview, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(note)
        return card

    def _build_connection_card(self) -> QFrame:
        card = self._make_card()
        layout = QGridLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(12)

        self.local_url_value = QLabel("-")
        self.local_url_value.setObjectName("urlValue")
        self.local_url_value.setWordWrap(True)
        self.ip_value = QLabel("-")
        self.ip_value.setObjectName("fieldValue")
        self.port_value = QLabel("-")
        self.port_value.setObjectName("fieldValue")
        self.host_value = QLabel("-")
        self.host_value.setObjectName("fieldValue")
        self.receive_folder_value = QLabel("-")
        self.receive_folder_value.setObjectName("folderValue")
        self.receive_folder_value.setWordWrap(True)
        self.receive_folder_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addWidget(self._make_field("Local URL", self.local_url_value), 0, 0, 1, 3)
        layout.addWidget(self._make_field("IP Address", self.ip_value), 1, 0)
        layout.addWidget(self._make_field("Port", self.port_value), 1, 1)
        layout.addWidget(self._make_field("Device Name", self.host_value), 1, 2)
        layout.addWidget(self._make_field("Receive Folder", self.receive_folder_value), 2, 0, 1, 3)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        open_button = self._make_button("Open in Browser", "primary")
        open_button.clicked.connect(self._open_local_url)
        copy_url = self._make_button("Copy URL", "subtle")
        copy_url.clicked.connect(self._copy_local_url)
        open_folder = self._make_button("Open Receive Folder", "subtle")
        open_folder.clicked.connect(self._open_receive_folder)
        copy_path = self._make_button("Copy Path", "subtle")
        copy_path.clicked.connect(self._copy_receive_folder)
        refresh = self._make_button("Refresh Pairing Code", "subtle")
        refresh.clicked.connect(self.state.refresh_receive_mode)
        for widget in (open_button, copy_url, open_folder, copy_path, refresh):
            button_row.addWidget(widget)
        button_row.addStretch()
        layout.addLayout(button_row, 3, 0, 1, 3)
        return card

    def _build_files_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self.drop_zone = FileDropZone()
        self.drop_zone.files_selected.connect(self._handle_share_paths)
        self.drop_zone.browse_requested.connect(self._add_share_files)
        layout.addWidget(self.drop_zone)

        card = self._make_card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(14)
        header = QHBoxLayout()
        title = QLabel("Shared Files")
        title.setObjectName("sectionTitle")
        add_button = self._make_button("Add Files", "primary")
        add_button.clicked.connect(self._add_share_files)
        remove_button = self._make_button("Remove Selected", "subtle")
        remove_button.clicked.connect(self._remove_selected_share)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_button)
        header.addWidget(remove_button)
        self.shares_table = QTableWidget(0, 5)
        self.shares_table.setHorizontalHeaderLabels(["Created", "Download", "Files", "Size", "Downloads"])
        self.shares_table.horizontalHeader().setStretchLastSection(True)
        self.shares_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.shares_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.shares_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.shares_table.verticalHeader().setVisible(False)
        self.shares_table.setShowGrid(False)
        self.shares_table.setMinimumHeight(420)
        card_layout.addLayout(header)
        card_layout.addWidget(self.shares_table)
        layout.addWidget(card)
        return page

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        active_card = self._make_card()
        active_layout = QVBoxLayout(active_card)
        active_layout.setContentsMargins(22, 20, 22, 20)
        active_layout.setSpacing(10)
        top = QHBoxLayout()
        self.activity_value = QLabel("Waiting for activity")
        self.activity_value.setObjectName("sectionTitle")
        self.activity_badge = self._make_badge("Idle", "neutral")
        top.addWidget(self.activity_value, 1)
        top.addWidget(self.activity_badge)
        self.activity_note = QLabel("Transfers will appear here as they happen.")
        self.activity_note.setObjectName("sectionSubtitle")
        self.activity_note.setWordWrap(True)
        self.activity_progress = QProgressBar()
        self.activity_progress.setRange(0, 100)
        self.activity_progress.setValue(0)
        active_layout.addLayout(top)
        active_layout.addWidget(self.activity_note)
        active_layout.addWidget(self.activity_progress)
        layout.addWidget(active_card)

        history_card = self._make_card()
        history_layout = QVBoxLayout(history_card)
        history_layout.setContentsMargins(22, 20, 22, 20)
        history_layout.setSpacing(14)
        title = QLabel("Recent History")
        title.setObjectName("sectionTitle")
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["Time", "Direction", "Peer", "Status", "Files"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setShowGrid(False)
        self.history_table.setMinimumHeight(360)
        history_layout.addWidget(title)
        history_layout.addWidget(self.history_table)
        layout.addWidget(history_card)
        return page

    def _build_diagnostics_page(self) -> QWidget:
        page = QWidget()
        layout = QGridLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(16)
        layout.addWidget(self._build_trusted_devices_card(), 0, 0)
        layout.addWidget(self._build_host_settings_card(), 0, 1)
        layout.addWidget(self._build_logs_card(), 1, 0, 1, 2)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return page

    def _build_trusted_devices_card(self) -> QFrame:
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        title = QLabel("Trusted Devices")
        title.setObjectName("sectionTitle")
        self.trusted_devices_table = QTableWidget(0, 3)
        self.trusted_devices_table.setHorizontalHeaderLabels(["Device", "Last Seen", "Trusted Until"])
        self.trusted_devices_table.horizontalHeader().setStretchLastSection(True)
        self.trusted_devices_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.trusted_devices_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.trusted_devices_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.trusted_devices_table.verticalHeader().setVisible(False)
        self.trusted_devices_table.setShowGrid(False)
        self.trusted_devices_table.setMinimumHeight(240)
        revoke_button = self._make_button("Revoke Selected", "warning")
        revoke_button.clicked.connect(self._revoke_selected_trusted_device)
        layout.addWidget(title)
        layout.addWidget(self.trusted_devices_table)
        layout.addWidget(revoke_button, 0, Qt.AlignmentFlag.AlignLeft)
        return card

    def _build_host_settings_card(self) -> QFrame:
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        title = QLabel("Host Settings")
        title.setObjectName("sectionTitle")
        self.device_name_edit = QLineEdit()
        self.device_name_edit.setPlaceholderText("Matt's PC")
        save_button = self._make_button("Save Name", "primary")
        save_button.clicked.connect(lambda: self.state.set_device_name(self.device_name_edit.text()))
        disable_button = self._make_button("Disable Pairing", "subtle")
        disable_button.clicked.connect(self.state.disable_receive_mode)
        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        button_row.addWidget(save_button)
        button_row.addWidget(disable_button)
        button_row.addStretch()
        layout.addWidget(title)
        layout.addWidget(self.device_name_edit)
        layout.addLayout(button_row)
        layout.addStretch()
        return card

    def _build_logs_card(self) -> QFrame:
        card = self._make_card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)
        title = QLabel("Diagnostics Log")
        title.setObjectName("sectionTitle")
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(240)
        layout.addWidget(title)
        layout.addWidget(self.log_view)
        return card

    def _make_card(self, name: str | None = None) -> QFrame:
        frame = QFrame()
        frame.setProperty("card", True)
        if name:
            frame.setObjectName(name)
        return frame

    def _make_nav_button(self, page_name: str, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setProperty("navButton", True)
        button.setProperty("activeNav", False)
        button.clicked.connect(lambda: self._set_page(page_name))
        self._nav_buttons[page_name] = button
        return button

    def _make_button(self, text: str, variant: str) -> QPushButton:
        button = QPushButton(text)
        button.setProperty("variant", variant)
        return button

    def _make_badge(self, text: str, role: str) -> QLabel:
        label = QLabel(text)
        self._set_badge(label, text, role)
        return label

    def _set_badge(self, label: QLabel, text: str, role: str) -> None:
        label.setText(text)
        label.setProperty("badgeRole", role)
        label.style().unpolish(label)
        label.style().polish(label)

    def _make_field(self, label_text: str, value_label: QLabel) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(label_text)
        label.setObjectName("fieldLabel")
        layout.addWidget(label)
        layout.addWidget(value_label)
        return wrapper

    def _wire_signals(self) -> None:
        self.state.receive_mode_changed.connect(self._update_receive_mode)
        self.state.shares_changed.connect(self._update_shares)
        self.state.history_changed.connect(self._update_history)
        self.state.trusted_devices_changed.connect(self._update_trusted_devices)
        self.state.web_activity_changed.connect(self._update_activity)
        self.state.status_changed.connect(self.statusBar().showMessage)
        self.state.log_message.connect(self.log_view.appendPlainText)

    def _set_page(self, page_name: str) -> None:
        pages = {
            "overview": (0, "Overview", "Connect Your Device", "Use the QR code or local URL below to connect your iPhone or iPad."),
            "files": (1, "Shared Files", "Shared Files", "Add files here and they become available to Safari immediately."),
            "history": (2, "History", "Recent Activity", "Review current transfer state and recent file activity."),
            "diagnostics": (3, "Diagnostics", "Diagnostics", "Manage trusted devices and view runtime logs."),
        }
        index, kicker, title, subtitle = pages[page_name]
        self.page_stack.setCurrentIndex(index)
        self.page_kicker.setText(kicker)
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)
        for name, button in self._nav_buttons.items():
            active = name == page_name
            button.setProperty("activeNav", active)
            button.style().unpolish(button)
            button.style().polish(button)

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

    def _copy_receive_folder(self) -> None:
        path_text = self.receive_folder_value.text().strip()
        if not path_text or path_text == "-":
            QMessageBox.information(self, "Copy Path", "The receive folder is not ready yet.")
            return
        QApplication.clipboard().setText(path_text)
        self.statusBar().showMessage("Receive folder path copied")

    def _add_share_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose files to share with Safari")
        if paths:
            self._handle_share_paths(paths)

    def _handle_share_paths(self, paths: list[str]) -> None:
        self.state.create_share(paths)
        self._set_page("files")

    def _remove_selected_share(self) -> None:
        row = self.shares_table.currentRow()
        if row < 0 or row >= len(self._shares):
            QMessageBox.information(self, "Remove Share", "Choose a shared file batch first.")
            return
        self.state.remove_share(self._shares[row]["share_id"])

    def _revoke_selected_trusted_device(self) -> None:
        row = self.trusted_devices_table.currentRow()
        if row < 0 or row >= len(self._trusted_devices):
            QMessageBox.information(self, "Revoke Trusted Device", "Choose a trusted device first.")
            return
        self.state.revoke_trusted_device(self._trusted_devices[row].get("device_id", ""))

    def _update_receive_mode(self, payload: dict) -> None:
        enabled = bool(payload.get("enabled"))
        self.local_url_value.setText(payload.get("local_url", "-"))
        self.ip_value.setText(payload.get("ip_address", "-"))
        self.port_value.setText(str(payload.get("port", "-")))
        self.host_value.setText(payload.get("device_name", "-"))
        self.device_name_edit.setText(payload.get("device_name", ""))
        receive_folder = payload.get("receive_folder", "-")
        self.receive_folder_value.setText(receive_folder)
        self.receive_folder_value.setToolTip(receive_folder)
        self.pairing_expiry_value.setText(f"Expires: {payload.get('expires_at', '-')}")

        pairing_code = (payload.get("pairing_code", "") or "------").ljust(6, "-")[:6]
        for index, digit_label in enumerate(self.pairing_digit_labels):
            digit_label.setText(pairing_code[index])

        badge_text = "Ready to pair" if enabled else "Pairing off"
        badge_role = "ready" if enabled else "warning"
        self._set_badge(self.pairing_state_badge, badge_text, badge_role)

        qr_data = build_qr_png_bytes(payload.get("qr_pair_url", payload.get("local_url", "")))
        qr_pixmap = QPixmap()
        qr_pixmap.loadFromData(qr_data, "PNG")
        self.qr_preview.setPixmap(
          qr_pixmap.scaled(120, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )

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

    def _update_trusted_devices(self, devices: list[dict]) -> None:
        self._trusted_devices = devices
        self.trusted_devices_table.setRowCount(len(devices))
        for row, item in enumerate(devices):
            self.trusted_devices_table.setItem(row, 0, QTableWidgetItem(item.get("device_name", "iPhone/iPad")))
            self.trusted_devices_table.setItem(row, 1, QTableWidgetItem(item.get("last_seen_at", "-")))
            self.trusted_devices_table.setItem(row, 2, QTableWidgetItem(item.get("trust_expires_at", "-")))
        self.trusted_devices_table.resizeColumnsToContents()

    def _update_activity(self, payload: dict) -> None:
        message = payload.get("message", "Waiting for activity")
        status = payload.get("status", "idle")
        detail = payload.get("detail") or payload.get("current_file") or f"Status: {status}"
        self.activity_value.setText(message)
        self.activity_note.setText(detail)
        role = "ready" if status in {"success", "ready", "sending", "receiving", "paired"} else "neutral"
        if status in {"failed", "error"}:
            role = "warning"
        self._set_badge(self.activity_badge, status.title(), role)
        if status in {"sending", "receiving"}:
            self.activity_progress.setRange(0, 0)
        elif status in {"success", "ready", "paired"}:
            self.activity_progress.setRange(0, 100)
            self.activity_progress.setValue(100)
        else:
            self.activity_progress.setRange(0, 100)
            self.activity_progress.setValue(0)

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
