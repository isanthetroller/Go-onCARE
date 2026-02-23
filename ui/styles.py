# ── CareCRUD Design System ─────────────────────────────────────────────
# Palette from user reference:
#
# Primary:   #388087  (dark teal)
# Accent:    #6FB3B8  (medium teal)
# Highlight: #BADFE7  (light blue)
# Mint:      #C2EDCE  (light green)
# BG:        #F6F6F2  (warm off-white)
# Card:      #FFFFFF
# Text:      #2C3E50  (dark blue-gray)
# Muted:     #7F8C8D
# Warning:   #E8B931  (amber)
# Danger:    #D9534F  (red)

COLORS = {
    "primary":    "#388087",
    "primary_lt": "#BADFE7",
    "primary_dk": "#2C6A70",
    "accent":     "#6FB3B8",
    "success":    "#5CB85C",
    "warning":    "#E8B931",
    "danger":     "#D9534F",
    "bg":         "#F6F6F2",
    "card":       "#FFFFFF",
    "text":       "#2C3E50",
    "muted":      "#7F8C8D",
    "border":     "#BADFE7",
    "sidebar_bg": "#FFFFFF",
    "sidebar_hv": "#BADFE7",
    "sidebar_sel": "#388087",
    "mint":       "#C2EDCE",
}


def configure_table(table):
    """Set palette directly on a QTableWidget so alternating rows use our palette."""
    from PyQt6.QtGui import QPalette, QColor
    pal = table.palette()
    pal.setColor(QPalette.ColorRole.Base, QColor(COLORS["card"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS["card"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(COLORS["text"]))
    pal.setColor(QPalette.ColorRole.Window, QColor(COLORS["card"]))
    table.setPalette(pal)
    table.setAutoFillBackground(True)


_TBL_BTN_STYLE = (
    "QPushButton { background-color: #388087; color: #FFFFFF; border: none;"
    " border-radius: 4px; padding: 5px 14px; font-size: 11px; font-weight: bold; }"
    " QPushButton:hover { background-color: #2C6A70; }"
)


def make_table_btn(text: str) -> "QPushButton":
    """Create a compact QPushButton for use inside table cells."""
    from PyQt6.QtWidgets import QPushButton
    from PyQt6.QtCore import Qt
    btn = QPushButton(text)
    btn.setStyleSheet(_TBL_BTN_STYLE)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


AUTH_STYLE = """
/* ── Auth background ────────────────────────── */
QMainWindow, QWidget#authBg {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #2C6A70, stop:0.5 #388087, stop:1 #6FB3B8
    );
}

/* ── Card ────────────────────────────────────── */
QWidget#cardWidget {
    background-color: #FFFFFF;
    border-radius: 20px;
}

/* ── Typography ──────────────────────────────── */
QLabel#titleLabel {
    color: #388087;
    font-size: 30px;
    font-weight: bold;
    font-family: 'Segoe UI', sans-serif;
}
QLabel#subtitleLabel {
    color: #7F8C8D;
    font-size: 14px;
    font-family: 'Segoe UI', sans-serif;
}
QLabel#switchLabel {
    color: #7F8C8D;
    font-size: 13px;
}

/* ── Inputs ──────────────────────────────────── */
QLineEdit {
    padding: 14px 18px;
    border: 2px solid #BADFE7;
    border-radius: 12px;
    font-size: 14px;
    font-family: 'Segoe UI', sans-serif;
    background-color: #F6F6F2;
    color: #2C3E50;
    selection-background-color: #388087;
}
QLineEdit:focus {
    border: 2px solid #388087;
    background-color: #FFFFFF;
}
QLineEdit:hover {
    border: 2px solid #6FB3B8;
}

/* ── Primary button ──────────────────────────── */
QPushButton#primaryBtn {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #388087, stop:1 #6FB3B8
    );
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    padding: 14px 28px;
    font-size: 15px;
    font-weight: bold;
    font-family: 'Segoe UI', sans-serif;
}
QPushButton#primaryBtn:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #2C6A70, stop:1 #388087
    );
}
QPushButton#primaryBtn:pressed {
    background-color: #245558;
}

/* ── Link button ─────────────────────────────── */
QPushButton#linkBtn {
    background: none;
    border: none;
    color: #388087;
    font-size: 13px;
    font-weight: bold;
    padding: 4px;
}
QPushButton#linkBtn:hover {
    color: #2C6A70;
}

/* ── Separator ───────────────────────────────── */
QFrame#separator {
    background-color: #BADFE7;
    max-height: 1px;
}
"""


MAIN_STYLE = """
/* ── Global ─────────────────────────────────── */
* {
    font-family: 'Segoe UI', sans-serif;
}
QMainWindow {
    background-color: #F6F6F2;
}

/* ── Top header bar ─────────────────────────── */
QWidget#topBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #BADFE7;
}
QLineEdit#topSearch {
    padding: 10px 16px 10px 38px;
    border: 2px solid #BADFE7;
    border-radius: 20px;
    font-size: 13px;
    background-color: #F6F6F2;
    color: #2C3E50;
    min-width: 280px;
}
QLineEdit#topSearch:focus {
    border: 2px solid #388087;
    background-color: #FFFFFF;
}
QLabel#topUserName {
    color: #2C3E50;
    font-size: 14px;
    font-weight: bold;
}
QLabel#topUserEmail {
    color: #7F8C8D;
    font-size: 11px;
}
QPushButton#topIconBtn {
    background: transparent;
    border: none;
    border-radius: 20px;
    padding: 8px;
    font-size: 18px;
    color: #7F8C8D;
    min-width: 40px;
    min-height: 40px;
}
QPushButton#topIconBtn:hover {
    background-color: #BADFE7;
    color: #388087;
}

/* ── Sidebar (light) ────────────────────────── */
QWidget#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #BADFE7;
}
QWidget#logoFrame {
    background-color: #BADFE7;
    border-radius: 16px;
}
QLabel#logoIcon {
    color: #388087;
    font-size: 28px;
    font-weight: bold;
}
QLabel#brandLabel {
    color: #388087;
    font-size: 22px;
    font-weight: bold;
}
QLabel#brandSubLabel {
    color: #6FB3B8;
    font-size: 11px;
}
QPushButton#navBtn {
    text-align: left;
    padding: 11px 16px;
    border: none;
    border-radius: 10px;
    color: #2C3E50;
    font-size: 14px;
    font-weight: 500;
    background: transparent;
    margin: 2px 0px;
}
QPushButton#navBtn:hover {
    background-color: #BADFE7;
    color: #2C3E50;
}
QPushButton#navBtnActive {
    text-align: left;
    padding: 11px 16px;
    border: none;
    border-radius: 10px;
    color: #2C3E50;
    font-size: 14px;
    font-weight: bold;
    background-color: #BADFE7;
    border-left: 3px solid #388087;
    margin: 2px 0px;
}
QPushButton#logoutBtn {
    text-align: left;
    padding: 11px 16px;
    border: none;
    border-radius: 10px;
    color: #D9534F;
    font-size: 14px;
    font-weight: 500;
    background: transparent;
}
QPushButton#logoutBtn:hover {
    background-color: #FDECEA;
    color: #D9534F;
}
QLabel#sidebarSection {
    color: #7F8C8D;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    padding-left: 4px;
}

/* ── Content area ───────────────────────────── */
QWidget#contentArea {
    background-color: #F6F6F2;
}

/* ── Cards ──────────────────────────────────── */
QWidget#card, QFrame#card {
    background-color: #FFFFFF;
    border-radius: 16px;
    border: 1px solid #BADFE7;
}

/* ── Stat cards ─────────────────────────────── */
QLabel#statValue {
    font-size: 30px;
    font-weight: bold;
    color: #2C3E50;
}
QLabel#statLabel {
    font-size: 13px;
    color: #7F8C8D;
    font-weight: 500;
}

/* ── Section headers ────────────────────────── */
QLabel#sectionTitle {
    font-size: 18px;
    font-weight: bold;
    color: #2C3E50;
}
QLabel#sectionSubtitle {
    font-size: 14px;
    color: #7F8C8D;
}
QLabel#pageTitle {
    font-size: 26px;
    font-weight: bold;
    color: #2C3E50;
}
QLabel#cardTitle {
    font-size: 16px;
    font-weight: bold;
    color: #2C3E50;
}

/* ── Tables ─────────────────────────────────── */
QTableWidget {
    background-color: #FFFFFF;
    alternate-background-color: #FFFFFF;
    border: none;
    border-radius: 0px;
    gridline-color: #E8E8E4;
    font-size: 13px;
    color: #2C3E50;
    outline: none;
}
QTableWidget::item {
    padding: 10px 14px;
    border-bottom: 1px solid #E8E8E4;
}
QTableWidget::item:selected {
    background-color: #BADFE7;
    color: #2C3E50;
}
QTableWidget::item:hover {
    background-color: #F6F6F2;
}
QHeaderView::section {
    background-color: #FFFFFF;
    color: #7F8C8D;
    font-weight: bold;
    font-size: 12px;
    padding: 12px 14px;
    border: none;
    border-bottom: 2px solid #BADFE7;
}

/* ── Table action buttons (compact) ─────────── */
QPushButton#tblActionBtn {
    background-color: #BADFE7;
    color: #2C3E50;
    border: none;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#tblActionBtn:hover {
    background-color: #A8D4DE;
}
QPushButton#tblDangerBtn {
    background-color: #BADFE7;
    color: #2C3E50;
    border: none;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#tblDangerBtn:hover {
    background-color: #A8D4DE;
}
QPushButton#tblSuccessBtn {
    background-color: #BADFE7;
    color: #2C3E50;
    border: none;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#tblSuccessBtn:hover {
    background-color: #A8D4DE;
}
QPushButton#tblSecondaryBtn {
    background-color: #BADFE7;
    color: #2C3E50;
    border: none;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#tblSecondaryBtn:hover {
    background-color: #A8D4DE;
}

/* ── Action buttons ─────────────────────────── */
QPushButton#actionBtn {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #388087, stop:1 #6FB3B8
    );
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#actionBtn:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #2C6A70, stop:1 #388087
    );
}
QPushButton#secondaryBtn {
    background-color: #BADFE7;
    color: #388087;
    border: 2px solid #6FB3B8;
    border-radius: 10px;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#secondaryBtn:hover {
    background-color: #A8D4DE;
    border-color: #388087;
}
QPushButton#dangerBtn {
    background-color: #FDECEA;
    color: #D9534F;
    border: none;
    border-radius: 10px;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#dangerBtn:hover {
    background-color: #F9D6D5;
}
QPushButton#successBtn {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #4CAE4C, stop:1 #5CB85C
    );
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 10px 22px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#successBtn:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #3D9140, stop:1 #4CAE4C
    );
}
QPushButton#viewBtn {
    background-color: transparent;
    color: #2C3E50;
    border: 1px solid #BADFE7;
    border-radius: 12px;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: bold;
}
QPushButton#viewBtn:hover {
    background-color: #BADFE7;
    color: #2C3E50;
}

/* ── Status badges ──────────────────────────── */
QLabel#badgePending {
    background-color: #FFF3CD;
    color: #856404;
    border-radius: 10px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: bold;
}
QLabel#badgeComplete {
    background-color: #C2EDCE;
    color: #2D6A3F;
    border-radius: 10px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: bold;
}
QLabel#badgeActive {
    background-color: #BADFE7;
    color: #2C6A70;
    border-radius: 10px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: bold;
}

/* ── Form inputs (content area) ─────────────── */
QLineEdit#formInput, QTextEdit#formInput {
    padding: 10px 14px;
    border: 2px solid #BADFE7;
    border-radius: 10px;
    font-size: 13px;
    background-color: #F6F6F2;
    color: #2C3E50;
}
QLineEdit#formInput:focus, QTextEdit#formInput:focus {
    border: 2px solid #388087;
    background-color: #FFFFFF;
}
QComboBox#formCombo {
    padding: 10px 14px;
    border: 2px solid #BADFE7;
    border-radius: 10px;
    font-size: 13px;
    background-color: #F6F6F2;
    color: #2C3E50;
}
QComboBox#formCombo:focus {
    border: 2px solid #388087;
}
QComboBox#formCombo::drop-down {
    border: none;
    width: 30px;
}

/* ── Search bar ─────────────────────────────── */
QLineEdit#searchBar {
    padding: 12px 16px 12px 40px;
    border: 2px solid #BADFE7;
    border-radius: 12px;
    font-size: 14px;
    background-color: #FFFFFF;
    color: #2C3E50;
}
QLineEdit#searchBar:focus {
    border: 2px solid #388087;
    background-color: #FFFFFF;
}
QLineEdit#searchBar:hover {
    border: 2px solid #6FB3B8;
}

/* ── Tab widget ──────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #BADFE7;
    border-radius: 12px;
    background-color: #FFFFFF;
    margin-top: -1px;
}
QTabBar::tab {
    padding: 12px 28px;
    font-size: 13px;
    font-weight: bold;
    color: #7F8C8D;
    border: none;
    border-bottom: 3px solid transparent;
    background: transparent;
    margin-right: 4px;
}
QTabBar::tab:selected {
    color: #388087;
    border-bottom: 3px solid #388087;
}
QTabBar::tab:hover {
    color: #2C3E50;
    background-color: #F6F6F2;
}

/* ── Calendar ────────────────────────────────── */
QCalendarWidget {
    background-color: #FFFFFF;
    border: 1px solid #BADFE7;
    border-radius: 12px;
}
QCalendarWidget QToolButton {
    color: #2C3E50;
    font-weight: bold;
    font-size: 14px;
    padding: 4px;
}
QCalendarWidget QAbstractItemView:enabled {
    color: #2C3E50;
    selection-background-color: #388087;
    selection-color: #FFFFFF;
}

/* ── Scroll bars ─────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    border-radius: 3px;
    margin: 4px 2px;
}
QScrollBar::handle:vertical {
    background: #6FB3B8;
    border-radius: 3px;
    min-height: 40px;
}
QScrollBar::handle:vertical:hover {
    background: #388087;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #6FB3B8;
    border-radius: 3px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ── Tooltips ────────────────────────────────── */
QToolTip {
    background-color: #2C3E50;
    color: #FFFFFF;
    border: none;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
}

/* ── Message card items ─────────────────────── */
QWidget#msgItem {
    border-bottom: 1px solid #F6F6F2;
}
QLabel#msgName {
    color: #2C3E50;
    font-size: 13px;
    font-weight: bold;
}
QLabel#msgPreview {
    color: #7F8C8D;
    font-size: 12px;
}
QLabel#msgTime {
    color: #7F8C8D;
    font-size: 11px;
}
"""
