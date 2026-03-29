from __future__ import annotations

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QApplication, QAbstractButton, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class WindowControlButton(QPushButton):
    def __init__(self, role: str) -> None:
        super().__init__()
        self._role = role
        self._window_is_maximized = False
        self.setObjectName("titleBarButton")
        self.setProperty("windowControlRole", role)
        self.setProperty("titleBarInteractive", True)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(44, 32)
        tooltips = {
            "minimize": "Minimize",
            "maximize": "Maximize or restore",
            "close": "Close",
        }
        self.setToolTip(tooltips.get(role, "Window control"))

    def set_window_maximized(self, maximized: bool) -> None:
        if self._window_is_maximized == maximized:
            return
        self._window_is_maximized = maximized
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(44, 32)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(self._icon_color(), 1.45, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))

        if self._role == "minimize":
            self._paint_minimize_icon(painter)
        elif self._role == "maximize":
            self._paint_maximize_icon(painter)
        elif self._role == "close":
            self._paint_close_icon(painter)

    def _paint_minimize_icon(self, painter: QPainter) -> None:
        center_y = self.height() / 2 + 2
        painter.drawLine(QPoint(15, int(center_y)), QPoint(self.width() - 15, int(center_y)))

    def _paint_maximize_icon(self, painter: QPainter) -> None:
        rect = self.rect().adjusted(14, 9, -14, -9)
        if self._window_is_maximized:
            back_rect = self.rect().adjusted(13, 8, -17, -12)
            front_rect = self.rect().adjusted(17, 12, -13, -8)
            painter.drawRect(back_rect)
            painter.drawRect(front_rect)
            return
        painter.drawRect(rect)

    def _paint_close_icon(self, painter: QPainter) -> None:
        painter.drawLine(QPoint(15, 11), QPoint(self.width() - 15, self.height() - 11))
        painter.drawLine(QPoint(15, self.height() - 11), QPoint(self.width() - 15, 11))

    def _icon_color(self) -> QColor:
        if self._role == "close" and (self.isDown() or self.underMouse()):
            return QColor("#fff9f5")
        return QColor("#6a5645")


class CustomTitleBar(QFrame):
    minimize_requested = Signal()
    maximize_requested = Signal()
    close_requested = Signal()

    def __init__(self, window_title: str, window_icon: QIcon | None = None) -> None:
        super().__init__()
        self.setObjectName("customTitleBar")
        self.setProperty("windowMaximized", False)
        self.setFixedHeight(62)
        self._drag_pending = False
        self._drag_start_pos = QPoint()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 14, 14, 12)
        layout.setSpacing(12)

        brand = QWidget()
        brand.setObjectName("titleBarBrand")
        brand.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(0, 0, 0, 0)
        brand_layout.setSpacing(12)

        self._icon_label = QLabel()
        self._icon_label.setObjectName("titleBarIcon")
        self._icon_label.setFixedSize(20, 20)
        self._icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        brand_layout.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignTop)

        text_stack = QVBoxLayout()
        text_stack.setContentsMargins(0, 0, 0, 0)
        text_stack.setSpacing(1)

        self._title_label = QLabel(window_title)
        self._title_label.setObjectName("titleBarTitle")
        self._title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._subtitle_label = QLabel("Desktop transfer hub")
        self._subtitle_label.setObjectName("titleBarSubtitle")
        self._subtitle_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        text_stack.addWidget(self._title_label)
        text_stack.addWidget(self._subtitle_label)
        brand_layout.addLayout(text_stack)

        layout.addWidget(brand, 1)

        controls = QWidget()
        controls.setObjectName("titleBarControls")
        controls.setProperty("titleBarInteractive", True)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)

        self._minimize_button = WindowControlButton("minimize")
        self._maximize_button = WindowControlButton("maximize")
        self._close_button = WindowControlButton("close")
        self._minimize_button.clicked.connect(self.minimize_requested.emit)
        self._maximize_button.clicked.connect(self.maximize_requested.emit)
        self._close_button.clicked.connect(self.close_requested.emit)

        controls_layout.addWidget(self._minimize_button)
        controls_layout.addWidget(self._maximize_button)
        controls_layout.addWidget(self._close_button)
        layout.addWidget(controls, 0, Qt.AlignmentFlag.AlignRight)

        self.set_window_icon(window_icon)

    def is_draggable_area(self, local_pos: QPoint) -> bool:
        if not self.rect().contains(local_pos):
            return False
        widget = self.childAt(local_pos)
        while widget is not None and widget is not self:
            if isinstance(widget, QAbstractButton):
                return False
            if bool(widget.property("titleBarInteractive")):
                return False
            widget = widget.parentWidget()
        return True

    def set_window_icon(self, icon: QIcon | None) -> None:
        if not icon or icon.isNull():
            self._icon_label.clear()
            return
        self._icon_label.setPixmap(icon.pixmap(QSize(20, 20)))

    def set_window_title(self, title: str) -> None:
        self._title_label.setText(title or "Transfer Tool")

    def set_maximized(self, maximized: bool) -> None:
        self.setProperty("windowMaximized", maximized)
        self.style().unpolish(self)
        self.style().polish(self)
        self._maximize_button.set_window_maximized(maximized)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.is_draggable_area(event.position().toPoint()):
            self._drag_pending = True
            self._drag_start_pos = event.globalPosition().toPoint()
            event.accept()
            return
        self._drag_pending = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._drag_pending and event.buttons() & Qt.MouseButton.LeftButton:
            if (event.globalPosition().toPoint() - self._drag_start_pos).manhattanLength() >= QApplication.startDragDistance():
                self._start_window_drag(event)
                event.accept()
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._drag_pending = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.is_draggable_area(event.position().toPoint()):
            self._drag_pending = False
            self.maximize_requested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def _start_window_drag(self, event: QMouseEvent) -> None:
        self._drag_pending = False
        window = self.window()
        handle = window.windowHandle()
        if handle is None:
            return

        local_pos = event.position().toPoint()
        global_pos = event.globalPosition().toPoint()

        if window.isMaximized():
            restore_drag = getattr(window, "restore_from_title_bar_drag", None)
            if callable(restore_drag):
                restore_drag(local_pos, global_pos)
            else:
                normal_geometry = window.normalGeometry()
                restored_width = max(normal_geometry.width(), window.minimumWidth())
                restored_height = max(normal_geometry.height(), window.minimumHeight())
                horizontal_ratio = 0.5 if self.width() <= 0 else min(max(local_pos.x() / self.width(), 0.0), 1.0)
                target_x = global_pos.x() - int(restored_width * horizontal_ratio)
                title_offset = min(local_pos.y(), self.height() - 1)
                target_y = global_pos.y() - max(title_offset, 8)
                window.showNormal()
                window.resize(restored_width, restored_height)
                window.move(target_x, target_y)
            handle = window.windowHandle()
            if handle is None:
                return

        handle.startSystemMove()
