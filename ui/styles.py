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


# ── Dark colour constants ──────────────────────────────────────────────
DARK_COLORS = {
    "primary":    "#6FB3B8",
    "primary_lt": "#3A4A5C",
    "primary_dk": "#A0D7DB",
    "accent":     "#388087",
    "success":    "#5CB85C",
    "warning":    "#E8B931",
    "danger":     "#D9534F",
    "bg":         "#1E1E2E",
    "card":       "#2A2A3C",
    "text":       "#E0E0E0",
    "muted":      "#8899AA",
    "border":     "#3A4A5C",
    "sidebar_bg": "#252538",
    "sidebar_hv": "#3A4A5C",
    "sidebar_sel": "#6FB3B8",
    "mint":       "#3A5A40",
}

# ── Public stylesheet strings (loaded once at import) ─────────────────
AUTH_STYLE: str = _load_qss("auth.qss")
MAIN_STYLE: str = _load_qss("main.qss")

# Build dark variant by swapping colors in QSS
def _build_dark_style() -> str:
    """Generate dark QSS by replacing light colours in the main stylesheet."""
    dark = MAIN_STYLE
    _swaps = [
        ("#F6F6F2", DARK_COLORS["bg"]),
        ("#FFFFFF", DARK_COLORS["card"]),
        ("#BADFE7", DARK_COLORS["border"]),
        ("#2C3E50", DARK_COLORS["text"]),
        ("#7F8C8D", DARK_COLORS["muted"]),
    ]
    for old, new in _swaps:
        dark = dark.replace(old, new)
    return dark


DARK_MAIN_STYLE: str = _build_dark_style()


# ── Table palette helper ──────────────────────────────────────────────

_active_colors = COLORS  # start with light


def set_active_palette(dark: bool = False):
    global _active_colors
    _active_colors = DARK_COLORS if dark else COLORS


def configure_table(table):
    """Set palette directly on a QTableWidget so alternating rows use our palette."""
    from PyQt6.QtGui import QPalette, QColor
    pal = table.palette()
    pal.setColor(QPalette.ColorRole.Base, QColor(_active_colors["card"]))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(_active_colors["card"]))
    pal.setColor(QPalette.ColorRole.Text, QColor(_active_colors["text"]))
    pal.setColor(QPalette.ColorRole.Window, QColor(_active_colors["card"]))
    table.setPalette(pal)
    table.setAutoFillBackground(True)


# ── Table button helper ───────────────────────────────────────────────

_TBL_BTN_STYLE = (
    "QPushButton { background-color: #388087; color: #FFFFFF; border: none;"
    " border-radius: 5px; padding: 3px 10px; font-size: 11px; font-weight: bold; }"
    " QPushButton:hover { background-color: #2C6A70; }"
)


def make_table_btn(text: str) -> "QPushButton":
    """Create a compact QPushButton for use inside table cells."""
    from PyQt6.QtWidgets import QPushButton
    from PyQt6.QtCore import Qt
    btn = QPushButton(text)
    btn.setStyleSheet(_TBL_BTN_STYLE)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedHeight(24)
    btn.setMinimumWidth(40)
    return btn


_TBL_BTN_DANGER_STYLE = (
    "QPushButton { background-color: #D9534F; color: #FFFFFF; border: none;"
    " border-radius: 5px; padding: 3px 10px; font-size: 11px; font-weight: bold; }"
    " QPushButton:hover { background-color: #C9302C; }"
)


def make_table_btn_danger(text: str) -> "QPushButton":
    """Create a compact danger QPushButton for use inside table cells."""
    from PyQt6.QtWidgets import QPushButton
    from PyQt6.QtCore import Qt
    btn = QPushButton(text)
    btn.setStyleSheet(_TBL_BTN_DANGER_STYLE)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedHeight(24)
    btn.setMinimumWidth(40)
    return btn


def style_dialog_btns(btns) -> None:
    """Apply consistent Save/Cancel styling to a QDialogButtonBox."""
    from PyQt6.QtWidgets import QDialogButtonBox
    from PyQt6.QtCore import Qt
    save = btns.button(QDialogButtonBox.StandardButton.Save) or btns.button(QDialogButtonBox.StandardButton.Ok)
    cancel = btns.button(QDialogButtonBox.StandardButton.Cancel)
    if save:
        save.setObjectName("dialogSaveBtn")
        save.setCursor(Qt.CursorShape.PointingHandCursor)
    if cancel:
        cancel.setObjectName("dialogCancelBtn")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
