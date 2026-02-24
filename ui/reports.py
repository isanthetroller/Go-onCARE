"""Reporting & Analytics page with summary cards and tables."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QComboBox, QTabWidget, QGraphicsDropShadowEffect, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from ui.styles import configure_table


_REVENUE_DATA = [
    ("2026-02-22", "General Checkup",  "Maria Santos",   "Dr. Reyes", "Cash",        "₱ 800.00"),
    ("2026-02-22", "Follow-up Visit",  "Juan Dela Cruz", "Dr. Tan",   "GCash",       "₱ 500.00"),
    ("2026-02-21", "Lab Tests (CBC)",  "Ana Reyes",      "Dr. Reyes", "Credit Card", "₱ 1,200.00"),
    ("2026-02-21", "Dental Cleaning",  "Carlos Garcia",  "Dr. Lim",   "Insurance",   "₱ 2,500.00"),
    ("2026-02-20", "X-Ray",            "Roberto Cruz",   "Dr. Reyes", "Cash",        "₱ 1,500.00"),
    ("2026-02-20", "Physical Therapy", "Lea Mendoza",    "Dr. Tan",   "Maya",        "₱ 1,800.00"),
]

_PATIENT_STATS = [
    ("January 2026",  "42",  "38",  "4",  "90.5%"),
    ("February 2026", "34",  "30",  "4",  "88.2%"),
    ("December 2025", "55",  "50",  "5",  "90.9%"),
    ("November 2025", "48",  "44",  "4",  "91.7%"),
]

_DOCTOR_PERF = [
    ("Dr. Reyes",  "156", "148", "₱ 125,600", "4.8 / 5"),
    ("Dr. Tan",    "132", "128", "₱ 108,400", "4.7 / 5"),
    ("Dr. Lim",    "98",  "94",  "₱ 92,300",  "4.9 / 5"),
    ("Dr. Santos", "87",  "82",  "₱ 78,500",  "4.6 / 5"),
]


class ReportsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner)
        lay.setSpacing(20)
        lay.setContentsMargins(28, 28, 28, 28)

        # ── Header ─────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        tc = QVBoxLayout()
        title = QLabel("Reports & Analytics")
        title.setObjectName("pageTitle")
        sub = QLabel("Revenue, patient statistics, and doctor performance")
        sub.setObjectName("sectionSubtitle")
        tc.addWidget(title); tc.addWidget(sub)
        hdr.addLayout(tc); hdr.addStretch()

        export_btn = QPushButton("Export Report")
        export_btn.setObjectName("secondaryBtn")
        export_btn.setMinimumHeight(42)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        hdr.addWidget(export_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(hdr)

        # ── Summary cards ──────────────────────────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        summaries = [
            ("Monthly Revenue",   "₱ 482,300",  "+12.4%", "#388087"),
            ("Total Patients",    "1,248",       "+3.2%",  "#5CB85C"),
            ("Appointments",      "473",         "+8.1%",  "#6FB3B8"),
            ("Avg. Visit / Day",  "15.8",        "+1.5%",  "#388087"),
        ]
        for label, value, change, color in summaries:
            cards_row.addWidget(self._summary_card(label, value, change, color))
        lay.addLayout(cards_row)

        # ── Date range filter ──────────────────────────────────────────
        range_bar = QHBoxLayout()
        range_bar.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate(2026, 2, 1))
        self.from_date.setObjectName("formCombo")
        self.from_date.setMinimumHeight(38)
        range_bar.addWidget(self.from_date)
        range_bar.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setObjectName("formCombo")
        self.to_date.setMinimumHeight(38)
        range_bar.addWidget(self.to_date)
        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("secondaryBtn")
        apply_btn.setMinimumHeight(38)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        range_bar.addWidget(apply_btn)
        range_bar.addStretch()
        lay.addLayout(range_bar)

        # ── Tabs ───────────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.addTab(self._revenue_tab(),  "Revenue")
        tabs.addTab(self._patient_tab(),  "Patient Stats")
        tabs.addTab(self._doctor_tab(),   "Doctor Performance")
        lay.addWidget(tabs)

        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

    # ── Summary card ───────────────────────────────────────────────────
    @staticmethod
    def _summary_card(label, value, change, color) -> QFrame:
        card = QFrame(); card.setObjectName("card"); card.setMinimumHeight(120)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 18); vbox.setSpacing(4)
        strip = QFrame(); strip.setFixedHeight(4)
        strip.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        vbox.addWidget(strip)

        val_row = QHBoxLayout()
        v = QLabel(value); v.setObjectName("statValue")
        ch = QLabel(change)
        ch_color = "#5CB85C" if change.startswith("+") else "#D9534F"
        ch.setStyleSheet(f"color: {ch_color}; font-size: 13px; font-weight: bold;")
        val_row.addWidget(v); val_row.addStretch(); val_row.addWidget(ch)
        vbox.addLayout(val_row)

        l = QLabel(label); l.setObjectName("statLabel")
        vbox.addWidget(l)
        return card

    # ── Revenue tab ────────────────────────────────────────────────────
    def _revenue_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(12); lay.setContentsMargins(16, 16, 16, 16)

        cols = ["Date", "Service", "Patient", "Doctor", "Payment", "Amount"]
        tbl = self._make_table(cols, _REVENUE_DATA)
        lay.addWidget(tbl)

        # Total row
        total_row = QHBoxLayout()
        total_row.addStretch()
        tl = QLabel("Total Revenue:  ₱ 8,300.00")
        tl.setObjectName("totalLabel")
        total_row.addWidget(tl)
        lay.addLayout(total_row)
        return page

    # ── Patient stats tab ──────────────────────────────────────────────
    def _patient_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(12); lay.setContentsMargins(16, 16, 16, 16)
        cols = ["Month", "Total Visits", "Completed", "Cancelled", "Completion Rate"]
        tbl = self._make_table(cols, _PATIENT_STATS)
        lay.addWidget(tbl)
        return page

    # ── Doctor performance tab ─────────────────────────────────────────
    def _doctor_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(12); lay.setContentsMargins(16, 16, 16, 16)
        cols = ["Doctor", "Total Appts", "Completed", "Revenue", "Rating"]
        tbl = self._make_table(cols, _DOCTOR_PERF)
        lay.addWidget(tbl)
        return page

    # ── Table helper ───────────────────────────────────────────────────
    @staticmethod
    def _make_table(headers, rows) -> QTableWidget:
        tbl = QTableWidget(len(rows), len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(min(len(rows) * 48 + 48, 360))
        tbl.verticalHeader().setDefaultSectionSize(48)
        configure_table(tbl)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                tbl.setItem(r, c, QTableWidgetItem(val))
        return tbl
