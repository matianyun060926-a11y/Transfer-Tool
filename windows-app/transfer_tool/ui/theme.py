from __future__ import annotations


def build_stylesheet() -> str:
    return """
    QWidget {
        background: #f4f7f8;
        color: #22313a;
        font-family: "Segoe UI", "Aptos", sans-serif;
        font-size: 14px;
    }

    QWidget#appRoot {
        background: #f4f7f8;
    }

    QFrame[card="true"] {
        background: #ffffff;
        border: 1px solid #dde7ea;
        border-radius: 18px;
    }

    QLabel#headerTitle {
        color: #203139;
        font-size: 26px;
        font-weight: 700;
    }

    QLabel#headerSubtitle {
        color: #6e8189;
        font-size: 14px;
    }

    QLabel#sectionTitle {
        color: #22323a;
        font-size: 18px;
        font-weight: 700;
    }

    QLabel#sectionSubtitle {
        color: #768992;
        font-size: 13px;
    }

    QLabel#fieldLabel {
        color: #7b8c94;
        font-size: 11px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    QLabel#fieldValue {
        color: #22313a;
        font-size: 15px;
        font-weight: 600;
    }

    QLabel#urlValue {
        color: #1e6f86;
        font-size: 17px;
        font-weight: 700;
    }

    QLabel#pairingValue {
        color: #1d6173;
        font-size: 30px;
        font-weight: 700;
        letter-spacing: 3px;
    }

    QLabel#activityValue {
        color: #203139;
        font-size: 16px;
        font-weight: 600;
    }

    QLabel[badgeRole="neutral"] {
        background: #eef4f6;
        color: #69808a;
        border: 1px solid #dce8eb;
        border-radius: 999px;
        padding: 5px 10px;
        font-weight: 600;
    }

    QLabel[badgeRole="ready"] {
        background: #e9f8f7;
        color: #20727c;
        border: 1px solid #caece9;
        border-radius: 999px;
        padding: 5px 10px;
        font-weight: 600;
    }

    QLabel[badgeRole="warning"] {
        background: #fff5e8;
        color: #8a6b32;
        border: 1px solid #f1e1bf;
        border-radius: 999px;
        padding: 5px 10px;
        font-weight: 600;
    }

    QLineEdit, QPlainTextEdit, QTableWidget {
        background: #fbfcfc;
        border: 1px solid #d9e5e8;
        border-radius: 14px;
        padding: 10px 12px;
        color: #22313a;
        selection-background-color: #d9f1f2;
        selection-color: #203139;
    }

    QLineEdit:focus, QPlainTextEdit:focus, QTableWidget:focus {
        border: 1px solid #9bcfd4;
    }

    QPushButton {
        background: #f7fbfb;
        color: #29404a;
        border: 1px solid #d7e5e8;
        border-radius: 12px;
        padding: 10px 15px;
        font-weight: 600;
    }

    QPushButton:hover {
        background: #eef7f7;
        border-color: #bddadd;
    }

    QPushButton:pressed {
        background: #e8f1f2;
    }

    QPushButton[variant="primary"] {
        background: #d9f1f2;
        color: #225461;
        border: 1px solid #bfdfdf;
        font-weight: 700;
    }

    QPushButton[variant="subtle"] {
        background: #ffffff;
    }

    QPushButton[variant="warning"] {
        background: #fff4ea;
        color: #7a5a24;
        border: 1px solid #edd9bf;
    }

    QTabWidget::pane {
        border: none;
        margin-top: 16px;
    }

    QTabBar::tab {
        background: transparent;
        color: #7a8b93;
        border: none;
        padding: 10px 14px;
        margin-right: 14px;
        font-weight: 600;
    }

    QTabBar::tab:selected {
        color: #225866;
        border-bottom: 2px solid #7ebec4;
    }

    QHeaderView::section {
        background: #f7fafb;
        color: #6b7f88;
        border: none;
        border-bottom: 1px solid #dbe6e9;
        padding: 11px 10px;
        font-weight: 700;
    }

    QTableWidget {
        gridline-color: #eef3f4;
        outline: none;
    }

    QTableCornerButton::section {
        background: #f7fafb;
        border: none;
    }

    QStatusBar {
        background: #f8fbfb;
        color: #72858d;
        border-top: 1px solid #dde7ea;
    }
    """

