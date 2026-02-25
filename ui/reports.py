"""Reporting page – revenue details, patient stats, doctor performance.

All data is pulled live from the database via the backend so that
reports update in real-time when records change."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QTabWidget, QGraphicsDropShadowEffect, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from ui.styles import configure_table


class ReportsPage(QWidget):
    def __init__(self, backend=None, role: str = "Admin"):
        super().__init__()
        self._backend = backend
        self._role = role
        self._build()

    # ── helpers ─────────────────────────────────────────────────────
    @staticmethod
    def _fmt_peso(amount) -> str:
        return f"\u20b1 {float(amount):,.0f}"

    def _load_data(self):
        if not self._backend:
            return {}
        from_d = self.from_date.date().toString("yyyy-MM-dd") if hasattr(self, "from_date") else None
        to_d = self.to_date.date().toString("yyyy-MM-dd") if hasattr(self, "to_date") else None
        return {
            "stats":       self._backend.get_summary_stats(from_d, to_d),
            "revenue":     self._backend.get_revenue_detail(from_d, to_d),
            "monthly":     self._backend.get_monthly_appointment_stats(6),
            "doctors":     self._backend.get_doctor_performance(),
        }

    # ── build ──────────────────────────────────────────────────────
    def _build(self):
        data = self._load_data()
        stats = data.get("stats", {})

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner)
        lay.setSpacing(20)
        lay.setContentsMargins(28, 28, 28, 28)

        # ── Header ─────────────────────────────────────────────────
        hdr = QHBoxLayout()
        tc = QVBoxLayout()
        title = QLabel("Reports & Analytics")
        title.setObjectName("pageTitle")
        sub = QLabel("Revenue, patient statistics, and doctor performance")
        sub.setObjectName("sectionSubtitle")
        tc.addWidget(title); tc.addWidget(sub)
        hdr.addLayout(tc); hdr.addStretch()

        refresh_btn = QPushButton("\u21bb  Refresh")
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.setMinimumHeight(42)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._on_refresh)
        hdr.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(hdr)

        # ── Summary cards from live data ───────────────────────────
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        total_rev = float(stats.get("total_revenue", 0))
        total_patients = stats.get("total_patients", 0)
        total_appts = stats.get("total_appts", 0)
        avg_per_day = stats.get("avg_per_day", 0)
        summaries = [
            ("Total Revenue",    self._fmt_peso(total_rev),      "#388087"),
            ("Total Patients",   f"{total_patients:,}",          "#5CB85C"),
            ("Appointments",     f"{total_appts:,}",             "#6FB3B8"),
            ("Avg. Visit / Day", f"{avg_per_day}",               "#388087"),
        ]
        for label, value, color in summaries:
            cards_row.addWidget(self._summary_card(label, value, color))
        lay.addLayout(cards_row)

        # ── Date range filter ──────────────────────────────────────
        range_bar = QHBoxLayout()
        range_bar.addWidget(QLabel("From:"))
        if not hasattr(self, "from_date"):
            self.from_date = QDateEdit()
            self.from_date.setCalendarPopup(True)
            self.from_date.setDate(QDate.currentDate().addMonths(-6))
        self.from_date.setObjectName("formCombo")
        self.from_date.setMinimumHeight(38)
        range_bar.addWidget(self.from_date)
        range_bar.addWidget(QLabel("To:"))
        if not hasattr(self, "to_date"):
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
        apply_btn.clicked.connect(self._on_refresh)
        range_bar.addWidget(apply_btn)
        range_bar.addStretch()
        lay.addLayout(range_bar)

        # ── Tabs ───────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.addTab(self._revenue_tab(data.get("revenue", [])),   "Revenue")
        tabs.addTab(self._patient_tab(data.get("monthly", [])),   "Patient Stats")
        tabs.addTab(self._doctor_tab(data.get("doctors", [])),    "Doctor Performance")
        lay.addWidget(tabs)

        lay.addStretch()
        scroll.setWidget(inner)

        wrapper = QVBoxLayout(self) if not self.layout() else self.layout()
        # clear existing layout contents
        while wrapper.count():
            item = wrapper.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

    # ── Refresh handler ────────────────────────────────────────────
    def _on_refresh(self):
        self._build()

    # ── Summary card (no hardcoded change %) ───────────────────────
    @staticmethod
    def _summary_card(label, value, color) -> QFrame:
        card = QFrame(); card.setObjectName("card"); card.setMinimumHeight(110)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(18, 14, 18, 14); vbox.setSpacing(4)
        strip = QFrame(); strip.setFixedHeight(3)
        strip.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
        vbox.addWidget(strip)

        v = QLabel(value); v.setObjectName("statValue")
        vbox.addWidget(v)

        l = QLabel(label); l.setObjectName("statLabel")
        vbox.addWidget(l)
        return card

    # ── Revenue tab (live) ─────────────────────────────────────────
    def _revenue_tab(self, revenue_data: list[dict]) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(12); lay.setContentsMargins(16, 16, 16, 16)

        cols = ["Date", "Service", "Patient", "Doctor", "Payment", "Amount"]
        rows = []
        grand = 0.0
        for r in revenue_data:
            amt = float(r.get("amount", 0))
            grand += amt
            rows.append((
                str(r.get("invoice_date", "")),
                r.get("service_name", ""),
                r.get("patient_name", ""),
                r.get("doctor_name", ""),
                r.get("payment_method", ""),
                self._fmt_peso(amt),
            ))

        tbl = self._make_table(cols, rows)
        lay.addWidget(tbl)

        total_row = QHBoxLayout()
        total_row.addStretch()
        tl = QLabel(f"Total Revenue:  {self._fmt_peso(grand)}")
        tl.setObjectName("totalLabel")
        total_row.addWidget(tl)
        lay.addLayout(total_row)
        return page

    # ── Patient stats tab (live) ───────────────────────────────────
    def _patient_tab(self, monthly: list[dict]) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(12); lay.setContentsMargins(16, 16, 16, 16)

        cols = ["Month", "Total Visits", "Completed", "Cancelled", "Completion Rate"]
        rows = []
        for m in monthly:
            total = m.get("total_appointments", 0)
            completed = m.get("completed", 0)
            cancelled = m.get("cancelled", 0)
            rate = f"{(completed / total * 100):.1f}%" if total else "0.0%"
            rows.append((
                m.get("month_label", ""),
                str(total),
                str(completed),
                str(cancelled),
                rate,
            ))

        tbl = self._make_table(cols, rows)
        lay.addWidget(tbl)
        return page

    # ── Doctor performance tab (live) ──────────────────────────────
    def _doctor_tab(self, doctors: list[dict]) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(12); lay.setContentsMargins(16, 16, 16, 16)

        cols = ["Doctor", "Total Appts", "Completed", "Revenue"]
        rows = []
        for d in doctors:
            name = d.get("doctor_name", "")
            rows.append((
                f"Dr. {name.split()[-1]}" if name else "",
                str(d.get("total_appointments", 0)),
                str(d.get("completed", 0)),
                self._fmt_peso(float(d.get("revenue_generated", 0))),
            ))

        tbl = self._make_table(cols, rows)
        lay.addWidget(tbl)
        return page

    # ── Table helper ───────────────────────────────────────────────
    @staticmethod
    def _make_table(headers, rows) -> QTableWidget:
        tbl = QTableWidget(len(rows), len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(min(max(len(rows), 1) * 48 + 48, 360))
        tbl.verticalHeader().setDefaultSectionSize(48)
        configure_table(tbl)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                tbl.setItem(r, c, QTableWidgetItem(val))
        return tbl
