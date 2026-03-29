from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer, QUrl
from PySide6.QtGui import QCursor, QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from transfer_tool.services.qr_code_service import build_qr_png_bytes
from transfer_tool.ui.custom_title_bar import CustomTitleBar
from transfer_tool.ui.file_drop_zone import FileDropZone
from transfer_tool.ui.theme import build_stylesheet

WM_GETMINMAXINFO = 0x0024
MONITOR_DEFAULTTONEAREST = 2


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


class MINMAXINFO(ctypes.Structure):
    _fields_ = [
        ("ptReserved", POINT),
        ("ptMaxSize", POINT),
        ("ptMaxPosition", POINT),
        ("ptMinTrackSize", POINT),
        ("ptMaxTrackSize", POINT),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", ctypes.c_ulong),
    ]


_USER32 = ctypes.windll.user32 if sys.platform == "win32" else None


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
        self._window_border = 8
        self._window_margin = 14
        self._use_custom_title_bar = sys.platform == "win32"
        self._shadow_effect: QGraphicsDropShadowEffect | None = None
        self.title_bar: CustomTitleBar | None = None
        self._window_canvas: QWidget | None = None
        self.window_surface: QFrame | None = None
        self.window_canvas_layout: QVBoxLayout | None = None
        self.window_footer: QFrame | None = None
        self.window_status_bar: QStatusBar | None = None
        self._window_handle_signals_bound = False
        self._pending_window_maximized: bool | None = None
        self._pending_maximize_retry_used = False

        if self._use_custom_title_bar:
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setWindowTitle("Transfer Tool")
        self.setMinimumSize(1020, 720)
        self.resize(1180, 820)
        self._set_window_icon()
        self._build_ui()
        self._wire_signals()
        self.windowTitleChanged.connect(self._handle_window_title_changed)
        self._sync_window_chrome()
        self.state.refresh_receive_mode()

    def _set_window_icon(self) -> None:
        icon_path = self.state.paths.icon_path
        if not icon_path.exists():
            return
        icon = QIcon(str(icon_path))
        self.setWindowIcon(icon)
        if self.title_bar is not None:
            self.title_bar.set_window_icon(icon)

    def _build_ui(self) -> None:
        canvas = QWidget()
        canvas.setObjectName("windowCanvas")
        canvas.setMouseTracking(True)
        if self._use_custom_title_bar:
            canvas.installEventFilter(self)
        self._window_canvas = canvas
        self.window_canvas_layout = QVBoxLayout(canvas)
        self.window_canvas_layout.setContentsMargins(
            self._window_margin,
            self._window_margin,
            self._window_margin,
            self._window_margin,
        )
        self.window_canvas_layout.setSpacing(0)

        self.window_surface = QFrame()
        self.window_surface.setObjectName("windowSurface")
        self.window_surface.setProperty("windowMaximized", False)
        self.window_canvas_layout.addWidget(self.window_surface)

        if self._use_custom_title_bar:
            self._shadow_effect = QGraphicsDropShadowEffect(self.window_surface)
            self._shadow_effect.setBlurRadius(34)
            self._shadow_effect.setOffset(0, 10)
            self._shadow_effect.setColor(self._shadow_effect.color().darker(160))
            self.window_surface.setGraphicsEffect(self._shadow_effect)

        surface_layout = QVBoxLayout(self.window_surface)
        surface_layout.setContentsMargins(0, 0, 0, 0)
        surface_layout.setSpacing(0)

        if self._use_custom_title_bar:
            self.title_bar = CustomTitleBar(self.windowTitle(), self.windowIcon())
            self.title_bar.minimize_requested.connect(self.showMinimized)
            self.title_bar.maximize_requested.connect(self._toggle_maximize_restore)
            self.title_bar.close_requested.connect(self.close)
            surface_layout.addWidget(self.title_bar)

        root = QWidget()
        root.setObjectName("appRoot")
        shell = QHBoxLayout(root)
        shell.setContentsMargins(18, 18, 18, 18)
        shell.setSpacing(18)
        shell.addWidget(self._build_sidebar())
        shell.addWidget(self._build_main_area(), 1)
        surface_layout.addWidget(root, 1)

        self.window_footer = QFrame()
        self.window_footer.setObjectName("windowFooter")
        self.window_footer.setProperty("windowMaximized", False)
        footer_layout = QVBoxLayout(self.window_footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(0)

        self.window_status_bar = QStatusBar()
        self.window_status_bar.setObjectName("windowStatusBar")
        self.window_status_bar.setSizeGripEnabled(False)
        self.window_status_bar.setProperty("windowMaximized", False)
        footer_layout.addWidget(self.window_status_bar)
        surface_layout.addWidget(self.window_footer)

        self.setCentralWidget(canvas)

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
            pixmap = QPixmap(str(icon_png)).scaled(
                30,
                30,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
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
        if self.window_status_bar is not None:
            self.state.status_changed.connect(self.window_status_bar.showMessage)
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
        self._show_status_message("Local URL copied")

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
        self._show_status_message("Receive folder path copied")

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
            qr_pixmap.scaled(
                120,
                160,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
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

    def _handle_window_title_changed(self, title: str) -> None:
        if self.title_bar is not None:
            self.title_bar.set_window_title(title)

    def _toggle_maximize_restore(self) -> None:
        self._set_window_maximized(not self.isMaximized())

    def _set_window_maximized(self, maximized: bool) -> None:
        self._bind_window_handle_signals()
        self._pending_window_maximized = maximized
        self._pending_maximize_retry_used = False

        if maximized == self.isMaximized():
            self._pending_window_maximized = None
            return

        if maximized:
            self.showMaximized()
        else:
            self.showNormal()
        QTimer.singleShot(0, self._finalize_pending_window_state)

    def _show_status_message(self, message: str) -> None:
        if self.window_status_bar is not None:
            self.window_status_bar.showMessage(message)

    def _sync_window_chrome(self) -> None:
        if self.window_surface is None or self.window_canvas_layout is None:
            return

        maximized = self.isMaximized()
        outer_margin = 0 if self._use_custom_title_bar and maximized else self._window_margin
        self.window_canvas_layout.setContentsMargins(outer_margin, outer_margin, outer_margin, outer_margin)

        for widget in (self.window_surface, self.window_footer, self.window_status_bar):
            if widget is None:
                continue
            widget.setProperty("windowMaximized", maximized)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        if self.title_bar is not None:
            self.title_bar.set_maximized(maximized)

        if self._shadow_effect is not None:
            self._shadow_effect.setEnabled(not maximized)

        if maximized:
            self._clear_resize_cursor()

    def _bind_window_handle_signals(self) -> None:
        if self._window_handle_signals_bound:
            return
        handle = self.windowHandle()
        if handle is None:
            return
        handle.windowStateChanged.connect(self._handle_window_state_changed)
        self._window_handle_signals_bound = True

    def _handle_window_state_changed(self, _state) -> None:
        if self._pending_window_maximized is not None:
            QTimer.singleShot(0, self._finalize_pending_window_state)
            return
        self._sync_window_chrome()

    def _finalize_pending_window_state(self) -> None:
        target = self._pending_window_maximized
        if target is None:
            self._sync_window_chrome()
            return

        if self.isMaximized() == target:
            self._pending_window_maximized = None
            self._pending_maximize_retry_used = False
            self._sync_window_chrome()
            return

        if target and not self._pending_maximize_retry_used:
            self._pending_maximize_retry_used = True
            self.showMaximized()
            QTimer.singleShot(0, self._finalize_pending_window_state)
            return

        self._pending_window_maximized = None
        self._pending_maximize_retry_used = False
        self._sync_window_chrome()

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            if self._pending_window_maximized is not None:
                QTimer.singleShot(0, self._finalize_pending_window_state)
            else:
                self._sync_window_chrome()

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if self._use_custom_title_bar:
            QTimer.singleShot(0, self._bind_window_handle_signals)
            QTimer.singleShot(0, self._sync_window_chrome)

    def restore_from_title_bar_drag(self, local_pos: QPoint, global_pos: QPoint) -> None:
        if not self.isMaximized():
            return

        normal_geometry = self.normalGeometry()
        restored_width = max(normal_geometry.width(), self.minimumWidth())
        restored_height = max(normal_geometry.height(), self.minimumHeight())
        title_width = self.title_bar.width() if self.title_bar is not None else self.width()
        horizontal_ratio = 0.5 if title_width <= 0 else min(max(local_pos.x() / title_width, 0.0), 1.0)
        title_height = self.title_bar.height() if self.title_bar is not None else restored_height
        title_offset = min(local_pos.y(), max(title_height - 1, 0))
        target_x = global_pos.x() - int(restored_width * horizontal_ratio)
        target_y = global_pos.y() - max(title_offset, 8)

        self._pending_window_maximized = None
        self._pending_maximize_retry_used = False
        self.showNormal()
        self._sync_window_chrome()
        self.resize(restored_width, restored_height)
        self.move(target_x, target_y)

    def _resize_edges_at(self, global_pos: QPoint) -> Qt.Edges:
        if not self._use_custom_title_bar or self.isMaximized():
            return Qt.Edges()

        local_pos = self.mapFromGlobal(global_pos)
        if not self.rect().contains(local_pos):
            return Qt.Edges()

        edges = Qt.Edges()
        if local_pos.x() < self._window_border:
            edges |= Qt.Edge.LeftEdge
        elif local_pos.x() >= self.width() - self._window_border:
            edges |= Qt.Edge.RightEdge

        if local_pos.y() < self._window_border:
            edges |= Qt.Edge.TopEdge
        elif local_pos.y() >= self.height() - self._window_border:
            edges |= Qt.Edge.BottomEdge

        return edges

    def _cursor_for_edges(self, edges: Qt.Edges) -> Qt.CursorShape | None:
        on_left = bool(edges & Qt.Edge.LeftEdge)
        on_right = bool(edges & Qt.Edge.RightEdge)
        on_top = bool(edges & Qt.Edge.TopEdge)
        on_bottom = bool(edges & Qt.Edge.BottomEdge)

        if (on_left and on_top) or (on_right and on_bottom):
            return Qt.CursorShape.SizeFDiagCursor
        if (on_right and on_top) or (on_left and on_bottom):
            return Qt.CursorShape.SizeBDiagCursor
        if on_left or on_right:
            return Qt.CursorShape.SizeHorCursor
        if on_top or on_bottom:
            return Qt.CursorShape.SizeVerCursor
        return None

    def _clear_resize_cursor(self) -> None:
        if self._window_canvas is not None:
            self._window_canvas.unsetCursor()
        self.unsetCursor()

    def _update_resize_cursor(self, global_pos: QPoint | None = None) -> None:
        if not self._use_custom_title_bar or self.isMaximized():
            self._clear_resize_cursor()
            return

        if global_pos is None:
            global_pos = QCursor.pos()

        cursor_shape = self._cursor_for_edges(self._resize_edges_at(global_pos))
        if cursor_shape is None:
            self._clear_resize_cursor()
            return

        if self._window_canvas is not None:
            self._window_canvas.setCursor(cursor_shape)
        self.setCursor(cursor_shape)

    def _start_system_resize(self, edges: Qt.Edges) -> bool:
        if not edges or self.isMaximized():
            return False
        handle = self.windowHandle()
        if handle is None:
            return False
        return handle.startSystemResize(edges)

    def eventFilter(self, watched, event):  # noqa: N802
        if watched is self._window_canvas and self._use_custom_title_bar:
            event_type = event.type()
            if event_type == QEvent.Type.MouseMove:
                if event.buttons() == Qt.MouseButton.NoButton:
                    self._update_resize_cursor(event.globalPosition().toPoint())
            elif event_type == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    edges = self._resize_edges_at(event.globalPosition().toPoint())
                    if edges and self._start_system_resize(edges):
                        self._update_resize_cursor(event.globalPosition().toPoint())
                        event.accept()
                        return True
            elif event_type == QEvent.Type.MouseButtonRelease:
                self._update_resize_cursor(event.globalPosition().toPoint())
            elif event_type == QEvent.Type.Leave:
                self._clear_resize_cursor()

        return super().eventFilter(watched, event)

    def nativeEvent(self, event_type, message):  # noqa: N802
        if not self._use_custom_title_bar or _USER32 is None:
            return super().nativeEvent(event_type, message)

        if event_type not in {b"windows_generic_MSG", "windows_generic_MSG"}:
            return super().nativeEvent(event_type, message)

        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_GETMINMAXINFO:
            self._update_maximized_metrics(msg.hWnd, msg.lParam)
            return True, 0

        return super().nativeEvent(event_type, message)

    def _update_maximized_metrics(self, hwnd, l_param: int) -> None:
        if _USER32 is None:
            return
        monitor = _USER32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
        if not monitor:
            return

        monitor_info = MONITORINFO()
        monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
        if not _USER32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
            return

        max_info = MINMAXINFO.from_address(l_param)
        max_info.ptMaxPosition.x = monitor_info.rcWork.left - monitor_info.rcMonitor.left
        max_info.ptMaxPosition.y = monitor_info.rcWork.top - monitor_info.rcMonitor.top
        max_info.ptMaxSize.x = monitor_info.rcWork.right - monitor_info.rcWork.left
        max_info.ptMaxSize.y = monitor_info.rcWork.bottom - monitor_info.rcWork.top
        max_info.ptMaxTrackSize.x = max_info.ptMaxSize.x
        max_info.ptMaxTrackSize.y = max_info.ptMaxSize.y

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
