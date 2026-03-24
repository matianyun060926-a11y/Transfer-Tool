from __future__ import annotations


def build_stylesheet() -> str:
    return """
    QWidget {
        background: #f4eee7;
        color: #362a22;
        font-family: "Segoe UI", "Aptos", sans-serif;
        font-size: 14px;
    }

    QWidget#appRoot {
        background: #f4eee7;
    }

    QFrame#sidebar {
        background: #f7f1eb;
        border: 1px solid #e7dbcf;
        border-radius: 26px;
    }

    QFrame#pageHeader,
    QFrame[card="true"] {
        background: #fbf8f4;
        border: 1px solid #eadfd3;
        border-radius: 24px;
    }

    QFrame#fileDropZone {
        background: #f6efe7;
        border: 2px dashed #d1ae89;
        border-radius: 22px;
    }

    QFrame#fileDropZone[activeDrop="true"] {
        background: #f2e5d7;
        border: 2px dashed #b8732b;
    }

    QLabel#sidebarBrand {
        color: #2e241d;
        font-size: 21px;
        font-weight: 700;
    }

    QPushButton[navButton="true"] {
        background: transparent;
        color: #6f5b4b;
        border: none;
        border-radius: 16px;
        padding: 12px 14px;
        text-align: left;
        font-weight: 700;
    }

    QPushButton[navButton="true"][activeNav="true"] {
        background: #fff4e6;
        color: #b26d24;
        border: 1px solid #f0dcc4;
    }

    QLabel#pageKicker,
    QLabel#fieldLabel {
        color: #a07b59;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }

    QLabel#pageTitle {
        color: #2f241d;
        font-size: 34px;
        font-weight: 700;
    }

    QLabel#sectionTitle {
        color: #2f241d;
        font-size: 24px;
        font-weight: 700;
    }

    QLabel#sectionTitleCompact {
        color: #2f241d;
        font-size: 16px;
        font-weight: 700;
    }

    QLabel#pageSubtitle,
    QLabel#sectionSubtitle {
        color: #7b6859;
        font-size: 13px;
    }

    QLabel#urlValue,
    QLabel#fieldValue,
    QLabel#folderValue {
        color: #342920;
        font-size: 18px;
        font-weight: 700;
    }

    QLabel#pairDigit {
        background: #fffaf5;
        color: #7a4d1f;
        border: 1px solid #ead8c7;
        border-radius: 16px;
        font-size: 30px;
        font-weight: 700;
    }

    QLabel#dropZoneTitle {
        color: #3a2c22;
        font-size: 20px;
        font-weight: 700;
        background: transparent;
    }

    QLabel#dropZoneSubtitle,
    QLabel#dropZoneHint {
        color: #86705f;
        font-size: 13px;
        background: transparent;
    }

    QLabel[badgeRole="neutral"] {
        background: #f2ebe4;
        color: #7d6758;
        border: 1px solid #e3d6ca;
        border-radius: 999px;
        padding: 5px 11px;
        font-weight: 700;
    }

    QLabel[badgeRole="ready"] {
        background: #fff0de;
        color: #b26d24;
        border: 1px solid #f0d8b8;
        border-radius: 999px;
        padding: 5px 11px;
        font-weight: 700;
    }

    QLabel[badgeRole="warning"] {
        background: #f8e4de;
        color: #b75640;
        border: 1px solid #efc7bd;
        border-radius: 999px;
        padding: 5px 11px;
        font-weight: 700;
    }

    QLineEdit,
    QPlainTextEdit,
    QTableWidget {
        background: #fffaf6;
        border: 1px solid #eadfd3;
        border-radius: 18px;
        padding: 10px 12px;
        color: #362a22;
        selection-background-color: #e5b37b;
        selection-color: #2b2018;
    }

    QLineEdit:focus,
    QPlainTextEdit:focus,
    QTableWidget:focus {
        border: 1px solid #c88741;
    }

    QPushButton {
        background: #f3ebe3;
        color: #5f4a3b;
        border: 1px solid #e2d6ca;
        border-radius: 16px;
        padding: 11px 16px;
        font-weight: 700;
    }

    QPushButton[variant="primary"] {
        background: #b8732b;
        color: #fff8f2;
        border: 1px solid #b8732b;
    }

    QPushButton[variant="warning"] {
        background: #f6dfd9;
        color: #8f4738;
        border: 1px solid #efc7be;
    }

    QProgressBar {
        background: #ede2d8;
        border: none;
        border-radius: 999px;
        min-height: 8px;
        max-height: 8px;
    }

    QProgressBar::chunk {
        background: #c27a2d;
        border-radius: 999px;
    }

    QHeaderView::section {
        background: #f8f2ec;
        color: #8d7661;
        border: none;
        border-bottom: 1px solid #eadfd3;
        padding: 10px 8px;
        font-weight: 700;
    }

    QTableWidget {
        gridline-color: #f0e5db;
        outline: none;
    }

    QTableCornerButton::section {
        background: #f8f2ec;
        border: none;
    }

    QStatusBar {
        background: #f7f1eb;
        color: #8a755f;
        border-top: 1px solid #eadfd3;
    }
    """
