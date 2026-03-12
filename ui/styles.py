# Color palette, style helpers, and UI factory functions
#
# Colors:
# Primary:   #388087  (dark teal)
# Accent:    #6FB3B8  (medium teal)
# Highlight: #BADFE7  (light blue)
# Mint:      #C2EDCE  (light green)
# BG:        #F6F6F2  (off-white)
# Card:      #FFFFFF
# Text:      #2C3E50
# Muted:     #7F8C8D
# Warning:   #E8B931
# Danger:    #D9534F
#
# QSS files are in ui/styles/ folder

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

# ── Centralised status → colour maps ──────────────────────────────────
STATUS_COLORS = {
    # Entity statuses
    "Active": "#5CB85C", "On Leave": "#E8B931", "Inactive": "#D9534F",
    # Appointment / queue statuses
    "Completed": "#5CB85C", "Confirmed": "#388087", "Pending": "#E8B931",
    "Cancelled": "#D9534F", "In Progress": "#6FB3B8", "Waiting": "#E8B931",
    "Triaged": "#3498DB",
    # Leave request statuses
    "Approved": "#5CB85C", "Declined": "#D9534F",
    # Invoice statuses
    "Paid": "#5CB85C", "Unpaid": "#D9534F", "Partial": "#E8B931", "Voided": "#7F8C8D",
    # Billing
    "No Invoice": "#7F8C8D",
    # Paycheck statuses
    "Rejected": "#D9534F", "Disbursed": "#3498DB",
}

ACTION_COLORS = {
    "Login": "#388087", "Created": "#5CB85C", "Edited": "#E8B931",
    "Deleted": "#D9534F", "Voided": "#D9534F", "Merged": "#6FB3B8",
    "Requested": "#9B59B6", "Approved": "#27AE60", "Declined": "#C0392B",
    "Rejected": "#C0392B", "Disbursed": "#3498DB",
}

# ── QSS loader ────────────────────────────────────────────────────────
_STYLES_DIR = _os.path.join(_os.path.dirname(__file__), "styles")


def _load_qss(filename: str) -> str:
    """Read a .qss file from the ui/styles/ directory and return its contents."""
    path = _os.path.join(_STYLES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Resolve relative url(./) refs to absolute paths so images load correctly
    abs_dir = _STYLES_DIR.replace("\\", "/")
    content = content.replace("url(./", f"url({abs_dir}/")
    return content


# ── Public stylesheet strings (loaded once at import) ─────────────────
AUTH_STYLE: str = _load_qss("auth.qss")
MAIN_STYLE: str = _load_qss("main.qss")


# ── Table palette helper ──────────────────────────────────────────────

_active_colors = COLORS  # start with light


def set_active_palette(dark: bool = False):
    global _active_colors
    _active_colors = COLORS


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


# ══════════════════════════════════════════════════════════════════════
#  UI Factory Functions — eliminate repeated boilerplate across pages
# ══════════════════════════════════════════════════════════════════════

def make_page_layout():
    """Create the standard scrollable page wrapper used by every page.

    Returns (scroll_widget, content_layout) — add widgets to *content_layout*,
    then set *scroll_widget* as the child of an outer QVBoxLayout on self.
    """
    from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QFrame
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    inner = QWidget()
    inner.setObjectName("pageInner")
    lay = QVBoxLayout(inner)
    lay.setSpacing(20)
    lay.setContentsMargins(28, 28, 28, 28)
    scroll.setWidget(inner)
    return scroll, lay


def finish_page(page_widget, scroll):
    """Set the scroll area as the only child of *page_widget*."""
    from PyQt6.QtWidgets import QVBoxLayout
    wrapper = QVBoxLayout(page_widget)
    wrapper.setContentsMargins(0, 0, 0, 0)
    wrapper.addWidget(scroll)


def make_card(min_height: int = 0):
    """Return a styled QFrame card with a subtle drop-shadow."""
    from PyQt6.QtWidgets import QFrame, QGraphicsDropShadowEffect
    from PyQt6.QtGui import QColor
    card = QFrame()
    card.setObjectName("card")
    if min_height:
        card.setMinimumHeight(min_height)
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(18)
    shadow.setOffset(0, 3)
    shadow.setColor(QColor(0, 0, 0, 12))
    card.setGraphicsEffect(shadow)
    return card


def make_banner(title_text: str, subtitle_text: str,
                btn_text: str = "", btn_slot=None):
    """Build a standard page banner (teal header bar).

    Returns a wrapper QWidget that holds the banner QFrame.
    If *btn_text* is given a bannerBtn is added to the right side
    (connected to *btn_slot*).
    """
    from PyQt6.QtWidgets import (QWidget, QFrame, QHBoxLayout, QVBoxLayout,
                                 QLabel, QPushButton)
    from PyQt6.QtCore import Qt

    # Outer wrapper prevents QGraphicsDropShadowEffect from clipping text
    wrapper = QWidget()
    wrapper.setContentsMargins(0, 0, 0, 0)
    wrapper_lay = QVBoxLayout(wrapper)
    wrapper_lay.setContentsMargins(0, 0, 0, 0)

    banner = QFrame()
    banner.setObjectName("pageBanner")
    banner.setMinimumHeight(100)

    banner_lay = QHBoxLayout(banner)
    banner_lay.setContentsMargins(32, 24, 32, 24)
    banner_lay.setSpacing(0)
    tc = QVBoxLayout()
    tc.setSpacing(6)
    t = QLabel(title_text)
    t.setObjectName("bannerTitle")
    s = QLabel(subtitle_text)
    s.setObjectName("bannerSubtitle")
    tc.addWidget(t)
    tc.addWidget(s)
    banner_lay.addLayout(tc)
    banner_lay.addStretch()

    if btn_text and btn_slot:
        btn = QPushButton(btn_text)
        btn.setObjectName("bannerBtn")
        btn.setMinimumHeight(42)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setToolTip(btn_text.replace("\uff0b", "").replace("+", "").strip())
        btn.clicked.connect(btn_slot)
        banner_lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    wrapper_lay.addWidget(banner)
    return wrapper


def make_read_only_table(headers: list[str], *, min_h: int = 420,
                         max_h: int = 0, row_h: int = 48):
    """Create and return a fully-configured read-only QTableWidget.

    Handles: column headers, stretch mode, no edit/select, alternating rows,
    row height, palette, and minimum height.
    """
    from PyQt6.QtWidgets import QTableWidget, QHeaderView
    from PyQt6.QtCore import Qt
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setStretchLastSection(True)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.setAlternatingRowColors(True)
    table.setMinimumHeight(min_h)
    if max_h:
        table.setMaximumHeight(max_h)
    table.verticalHeader().setDefaultSectionSize(row_h)
    configure_table(table)
    return table


def make_interactive_table(headers: list[str], *, min_h: int = 160,
                          max_h: int = 0, row_h: int = 40):
    """Create a row-selectable table (for edit/delete workflows).

    SingleSelection + SelectRows + StrongFocus so the user can pick a row
    before clicking an action button.
    """
    from PyQt6.QtWidgets import QTableWidget, QHeaderView
    from PyQt6.QtCore import Qt
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setStretchLastSection(True)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    table.setAlternatingRowColors(True)
    table.setMinimumHeight(min_h)
    if max_h:
        table.setMaximumHeight(max_h)
    table.verticalHeader().setDefaultSectionSize(row_h)
    configure_table(table)
    return table


def make_action_table(headers: list[str], *, min_h: int = 420,
                     row_h: int = 48, action_col_width: int = 160):
    """Create a display table whose last column holds action-button widgets.

    NoSelection + NoFocus like read-only tables, but the last column is
    fixed-width instead of stretched so View/Edit buttons have room.
    """
    from PyQt6.QtWidgets import QTableWidget, QHeaderView
    from PyQt6.QtCore import Qt
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.horizontalHeader().setSectionResizeMode(
        len(headers) - 1, QHeaderView.ResizeMode.Fixed)
    table.setColumnWidth(len(headers) - 1, action_col_width)
    table.horizontalHeader().setStretchLastSection(False)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
    table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    table.setAlternatingRowColors(True)
    table.setMinimumHeight(min_h)
    table.verticalHeader().setDefaultSectionSize(row_h)
    configure_table(table)
    return table


def make_stat_card(key: str, title: str, color: str, labels_dict: dict):
    """Build a KPI card (color strip + value + label). Stores the value QLabel
    in *labels_dict[key]*. Returns the card QFrame."""
    from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
    card = make_card(min_height=100)
    cl = QVBoxLayout(card)
    cl.setContentsMargins(18, 14, 18, 14)
    cl.setSpacing(4)
    strip = QFrame()
    strip.setFixedHeight(3)
    strip.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
    v = QLabel("0")
    v.setObjectName("statValue")
    labels_dict[key] = v
    l = QLabel(title)
    l.setObjectName("statLabel")
    cl.addWidget(strip)
    cl.addWidget(v)
    cl.addWidget(l)
    return card


def format_timedelta(td) -> str:
    """Convert a MySQL TIME / timedelta to 'HH:MM' string."""
    if hasattr(td, "total_seconds"):
        total = int(td.total_seconds())
        h, m = divmod(total // 60, 60)
        return f"{h:02d}:{m:02d}"
    if hasattr(td, "strftime"):
        return td.strftime("%H:%M")
    return str(td) if td else ""


def status_color(status: str) -> str:
    """Look up the colour for a status string, with a sensible fallback."""
    return STATUS_COLORS.get(status, COLORS["text"])


def fmt_peso(amount) -> str:
    """Format a number as Philippine Peso string."""
    return f"₱ {float(amount):,.0f}"


# ── Tab button styling (used by appointments + clinical) ─────────────
_TAB_STYLE = (
    "QPushButton {{ background: {bg}; color: {fg}; border: {bd};"
    " border-radius: 8px; padding: 8px 20px;"
    " font-size: 13px; font-weight: bold; }}"
    " QPushButton:hover {{ background: {hv}; }}"
)
TAB_ACTIVE = _TAB_STYLE.format(bg="#388087", fg="#FFFFFF", hv="#2C6A70", bd="none")
TAB_INACTIVE = _TAB_STYLE.format(bg="#FFFFFF", fg="#2C3E50", hv="#BADFE7", bd="1.5px solid #CADCE0")


# ── Loading cursor context manager ────────────────────────────────────
from contextlib import contextmanager


@contextmanager
def busy_cursor():
    """Show a wait cursor while a block of code runs, then restore."""
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    try:
        yield
    finally:
        QApplication.restoreOverrideCursor()


# ── Table button helper ───────────────────────────────────────────────

def make_table_btn(text: str) -> "QPushButton":
    """Create a compact QPushButton for use inside table cells."""
    from PyQt6.QtWidgets import QPushButton, QSizePolicy
    from PyQt6.QtCore import Qt
    btn = QPushButton(text)
    btn.setObjectName("tblActionBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedHeight(26)
    btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    return btn


def make_table_btn_danger(text: str) -> "QPushButton":
    """Create a compact danger QPushButton for use inside table cells."""
    from PyQt6.QtWidgets import QPushButton, QSizePolicy
    from PyQt6.QtCore import Qt
    btn = QPushButton(text)
    btn.setObjectName("tblDangerBtn")
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setFixedHeight(26)
    btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
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


def make_action_cell(*buttons) -> "QWidget":
    """Return a QWidget containing horizontally-centred action buttons.

    Usage: ``tbl.setCellWidget(r, col, make_action_cell(btn1, btn2))``
    """
    from PyQt6.QtWidgets import QWidget, QHBoxLayout
    from PyQt6.QtCore import Qt
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(8, 0, 8, 0)
    lay.setSpacing(8)
    lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
    for b in buttons:
        lay.addWidget(b)
    return w
