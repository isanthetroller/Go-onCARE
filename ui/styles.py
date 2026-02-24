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
#
# Stylesheets are stored as .qss files under ui/styles/ and loaded
# at import time by the helper function _load_qss().

import os as _os

# ── Colour constants (shared with Python code) ────────────────────────
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

# ── QSS loader ────────────────────────────────────────────────────────
_STYLES_DIR = _os.path.join(_os.path.dirname(__file__), "styles")


def _load_qss(filename: str) -> str:
    """Read a .qss file from the ui/styles/ directory and return its contents."""
    path = _os.path.join(_STYLES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ── Public stylesheet strings (loaded once at import) ─────────────────
AUTH_STYLE: str = _load_qss("auth.qss")
MAIN_STYLE: str = _load_qss("main.qss")


# ── Table palette helper ──────────────────────────────────────────────

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


# ── Table button helper ───────────────────────────────────────────────

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
