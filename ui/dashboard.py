"""Dashboard – clean overview with greeting, tables, messages, and chart."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QGraphicsDropShadowEffect,
    QScrollArea, QPushButton, QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from ui.styles import configure_table


# ── Sample data ────────────────────────────────────────────────────────

_UPCOMING_APPTS = [
    ("09:00 AM", "Maria Santos",   "Dr. Reyes",    "General Checkup",  "Confirmed"),
    ("09:30 AM", "Juan Dela Cruz", "Dr. Tan",      "Follow-up Visit",       "Confirmed"),
    ("10:00 AM", "Ana Reyes",      "Dr. Reyes",    "Lab Results Review",    "Pending"),
    ("10:30 AM", "Carlos Garcia",  "Dr. Lim",      "Dental Cleaning",  "Confirmed"),
    ("11:00 AM", "Lea Mendoza",    "Dr. Tan",      "Consultation",     "Pending"),
]

_BIRTH_DETAILS = [
    ("Jan", 42), ("Feb", 38), ("Mar", 55), ("Apr", 47),
    ("May", 62), ("Jun", 50),
]


class _BarChartWidget(QWidget):
    """Simple horizontal bar chart painted via QPainter."""

    def __init__(self, data: list[tuple[str, int]], parent=None):
        super().__init__(parent)
        self._data = data
        self._max = max(v for _, v in data) if data else 1
        self.setMinimumHeight(len(data) * 38 + 10)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        bar_h = 22
        spacing = 38
        label_w = 36
        padding_r = 40

        for i, (label, value) in enumerate(self._data):
            y = i * spacing + 6

            painter.setPen(QColor("#7F8C8D"))
            painter.setFont(self.font())
            painter.drawText(0, y, label_w, bar_h, Qt.AlignmentFlag.AlignVCenter, label)

            bar_x = label_w + 8
            max_bar_w = w - bar_x - padding_r
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#F6F6F2"))
            painter.drawRoundedRect(bar_x, y + 2, int(max_bar_w), bar_h - 4, 6, 6)

            fill_w = int(max_bar_w * value / self._max) if self._max else 0
            grad = QLinearGradient(bar_x, 0, bar_x + fill_w, 0)
            grad.setColorAt(0, QColor("#388087"))
            grad.setColorAt(1, QColor("#6FB3B8"))
            painter.setBrush(grad)
            painter.drawRoundedRect(bar_x, y + 2, fill_w, bar_h - 4, 6, 6)

            painter.setPen(QColor("#2C3E50"))
            painter.drawText(
                bar_x + int(max_bar_w) + 6, y, 34, bar_h,
                Qt.AlignmentFlag.AlignVCenter, str(value),
            )

        painter.end()


class DashboardPage(QWidget):
    def __init__(self, user_name: str = "Admin"):
        super().__init__()
        self._user_name = user_name
        self._build()

        # Update time every minute
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(60_000)

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #F6F6F2; }")
        inner = QWidget()
        inner.setObjectName("pageInner")
        inner.setStyleSheet("QWidget#pageInner { background-color: #F6F6F2; }")
        lay = QVBoxLayout(inner)
        lay.setSpacing(20)
        lay.setContentsMargins(28, 28, 28, 28)

        # ── Greeting Banner ────────────────────────────────────────────
        banner = QFrame()
        banner.setObjectName("card")
        banner.setMinimumHeight(120)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)
        banner.setStyleSheet(
            "#card { background: qlineargradient("
            "x1:0, y1:0, x2:1, y2:0,"
            "stop:0 #388087, stop:1 #6FB3B8);"
            "border-radius: 12px; }"
        )

        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(32, 24, 32, 24)
        banner_lay.setSpacing(0)

        # Left side: greeting + date
        greet_col = QVBoxLayout()
        greet_col.setSpacing(6)

        now = datetime.now()
        hour = now.hour
        if hour < 12:
            greeting = "Good Morning"
        elif hour < 17:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"

        self._greeting_label = QLabel(f"{greeting}, {self._user_name}!")
        self._greeting_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #FFFFFF; background: transparent;"
        )
        greet_col.addWidget(self._greeting_label)

        self._date_label = QLabel(now.strftime("%I:%M %p  •  %B %d, %Y"))
        self._date_label.setStyleSheet(
            "font-size: 14px; color: rgba(255,255,255,0.85); background: transparent;"
        )
        greet_col.addWidget(self._date_label)

        welcome_sub = QLabel("Here's what's happening at the hospital today.")
        welcome_sub.setStyleSheet(
            "font-size: 13px; color: rgba(255,255,255,0.7); background: transparent; margin-top: 4px;"
        )
        greet_col.addWidget(welcome_sub)

        banner_lay.addLayout(greet_col)
        banner_lay.addStretch()

        # Right side: quick stats
        quick_stats = QHBoxLayout()
        quick_stats.setSpacing(24)
        for val, label in [("1,248", "Patients"), ("34", "Today's Appts"), ("₱ 482K", "Revenue")]:
            stat_col = QVBoxLayout()
            stat_col.setSpacing(2)
            stat_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v = QLabel(val)
            v.setStyleSheet(
                "font-size: 20px; font-weight: bold; color: #FFFFFF; background: transparent;"
            )
            v.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l = QLabel(label)
            l.setStyleSheet(
                "font-size: 11px; color: rgba(255,255,255,0.75); background: transparent;"
            )
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stat_col.addWidget(v)
            stat_col.addWidget(l)
            quick_stats.addLayout(stat_col)
        banner_lay.addLayout(quick_stats)

        lay.addWidget(banner)

        # ── Row 1: Upcoming Appointments (full width) ──────────────────
        lay.addWidget(self._appointments_card())

        # ── Row 2: Patient Statistics chart (full width) ────────────
        lay.addWidget(self._chart_card())

        lay.addStretch()
        scroll.setWidget(inner)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

    # ── Update time ────────────────────────────────────────────────────
    def _update_time(self):
        now = datetime.now()
        self._date_label.setText(now.strftime("%I:%M %p  •  %B %d, %Y"))

        hour = now.hour
        if hour < 12:
            greeting = "Good Morning"
        elif hour < 17:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
        self._greeting_label.setText(f"{greeting}, {self._user_name}!")

    # ── Upcoming Appointments card ─────────────────────────────────────
    def _appointments_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 12))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14)
        vbox.setSpacing(12)

        hdr_row = QHBoxLayout()
        title = QLabel("Upcoming Appointments")
        title.setObjectName("cardTitle")
        hdr_row.addWidget(title)
        hdr_row.addStretch()
        count_badge = QLabel(f"{len(_UPCOMING_APPTS)} scheduled")
        count_badge.setStyleSheet(
            "background-color: #BADFE7; color: #388087; border-radius: 10px;"
            "padding: 3px 10px; font-size: 11px; font-weight: bold;"
        )
        hdr_row.addWidget(count_badge)
        vbox.addLayout(hdr_row)

        tbl = QTableWidget(len(_UPCOMING_APPTS), 5)
        tbl.setHorizontalHeaderLabels(
            ["Time", "Patient", "Doctor", "Purpose", "Status"]
        )
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setMinimumHeight(len(_UPCOMING_APPTS) * 44 + 44)
        tbl.verticalHeader().setDefaultSectionSize(44)
        tbl.setShowGrid(False)
        tbl.setAlternatingRowColors(True)
        configure_table(tbl)

        for r, row_data in enumerate(_UPCOMING_APPTS):
            for c, cell in enumerate(row_data):
                item = QTableWidgetItem(cell)
                if c == 4:
                    if cell == "Confirmed":
                        item.setForeground(QColor("#5CB85C"))
                    else:
                        item.setForeground(QColor("#E8B931"))
                tbl.setItem(r, c, item)

        vbox.addWidget(tbl)
        return card

    # ── Chart card ─────────────────────────────────────────────────────
    def _chart_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 12))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14)
        vbox.setSpacing(12)

        hdr_row = QHBoxLayout()
        title = QLabel("Patient Statistics")
        title.setObjectName("cardTitle")
        hdr_row.addWidget(title)
        hdr_row.addStretch()
        period = QLabel("Last 6 Months")
        period.setStyleSheet("color: #7F8C8D; font-size: 12px;")
        hdr_row.addWidget(period)
        vbox.addLayout(hdr_row)

        chart = _BarChartWidget(_BIRTH_DETAILS)
        vbox.addWidget(chart, 1)

        summary = QHBoxLayout()
        summary.setSpacing(20)
        for lbl_text, val_text, clr in [
            ("Total", "294", "#2C3E50"),
            ("Average", "49", "#388087"),
            ("Peak", "62", "#5CB85C"),
        ]:
            col = QVBoxLayout()
            col.setSpacing(2)
            v = QLabel(val_text)
            v.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {clr};")
            l = QLabel(lbl_text)
            l.setStyleSheet("font-size: 11px; color: #7F8C8D;")
            col.addWidget(v)
            col.addWidget(l)
            summary.addLayout(col)
        summary.addStretch()
        vbox.addLayout(summary)

        return card
