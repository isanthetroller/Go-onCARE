"""Data Analytics page – V2

New: export PDF/CSV, revenue chart, patient retention, cancellation rate,
doctor filter, date-range KPI, period comparison, drill-down tables."""

import math

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QPushButton, QDateEdit, QComboBox,
)
from PyQt6.QtCore import Qt, QRectF, QDate, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath
from ui.styles import configure_table


# ── Colour palettes ───────────────────────────────────────────────────
_CONDITION_COLORS = ["#388087", "#6FB3B8", "#BADFE7", "#C2EDCE", "#E8B931", "#D9534F", "#7F8C8D"]
_STATUS_COLORS    = {"Completed": "#5CB85C", "Confirmed": "#388087", "Pending": "#E8B931", "Cancelled": "#D9534F"}
_DEPT_COLORS      = ["#388087", "#6FB3B8", "#BADFE7", "#C2EDCE", "#E8B931", "#7F8C8D", "#D9534F", "#5CB85C"]
_DEMO_COLORS      = {"0–17": "#6FB3B8", "18–35": "#388087", "36–50": "#BADFE7", "51–65": "#C2EDCE", "65+": "#E8B931"}
_RETENTION_COLORS = {"new_patients": "#6FB3B8", "returning_patients": "#388087"}


# ── Pie Chart Widget ──────────────────────────────────────────────────
class _PieChartWidget(QWidget):
    def __init__(self, data: list[tuple[str, int, str]], *, donut: bool = True, parent=None):
        super().__init__(parent)
        self._data = data; self._donut = donut
        self._total = sum(v for _, v, _ in data)
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data):
        self._data = data; self._total = sum(v for _, v, _ in data); self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        size = min(self.width(), self.height()) - 20
        x, y = (self.width() - size) / 2, (self.height() - size) / 2
        rect = QRectF(x, y, size, size)
        start = 90 * 16
        for _, value, color in self._data:
            span = int(value / self._total * 360 * 16) if self._total else 0
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawPie(rect, start, -span)
            start -= span
        if self._donut:
            hole = size * 0.52; hx, hy = (self.width()-hole)/2, (self.height()-hole)/2
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(QRectF(hx, hy, hole, hole))
        painter.end()


# ── Horizontal Bar Chart ──────────────────────────────────────────────
class _HBarChartWidget(QWidget):
    def __init__(self, data: list[tuple[str, int, str]], parent=None):
        super().__init__(parent)
        self._data = data
        self._max = max(v for _, v, _ in data) if data else 1
        self.setMinimumHeight(len(data) * 38 + 10)

    def set_data(self, data):
        self._data = data
        self._max = max(v for _, v, _ in data) if data else 1
        self.setMinimumHeight(len(data) * 38 + 10)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bar_h, spacing, label_w, value_w = 22, 38, 130, 60
        bar_area = self.width() - label_w - value_w - 20
        font = QFont(); font.setPointSize(10); painter.setFont(font)
        for i, (label, value, color) in enumerate(self._data):
            y = i * spacing + 8
            painter.setPen(QPen(QColor("#2C3E50")))
            painter.drawText(QRectF(0, y, label_w, bar_h),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, label)
            bar_w = int((value / self._max) * bar_area) if self._max else 0
            path = QPainterPath()
            path.addRoundedRect(QRectF(label_w, y, bar_w, bar_h), 4, 4)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawPath(path)
            painter.setPen(QPen(QColor("#2C3E50")))
            painter.drawText(QRectF(label_w + bar_area + 4, y, value_w, bar_h),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             f"{value:,}")
        painter.end()


# ══════════════════════════════════════════════════════════════════════
#  Analytics Page
# ══════════════════════════════════════════════════════════════════════
class AnalyticsPage(QWidget):
    def __init__(self, backend=None, role: str = "Admin", user_email: str = ""):
        super().__init__()
        self._backend = backend
        self._role = role
        self._user_email = user_email
        self._build()
        # Auto-refresh data every 15 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._on_refresh)
        self._refresh_timer.start(15_000)

    @staticmethod
    def _fmt_peso(amount: float) -> str:
        return f"\u20b1 {amount:,.0f}"

    def _load_data(self):
        if not self._backend:
            return {}
        return {
            "stats":          self._backend.get_summary_stats(),
            "monthly_rev":    self._backend.get_monthly_revenue(6),
            "doctors":        self._backend.get_doctor_performance(),
            "services":       self._backend.get_top_services(),
            "appt_status":    self._backend.get_appointment_status_counts(),
            "conditions":     self._backend.get_patient_condition_counts(),
            "demographics":   self._backend.get_patient_demographics(),
            "dept_revenue":   self._backend.get_revenue_by_department(),
            "active_doctors": self._backend.get_active_doctor_count(),
            "monthly_appts":  self._backend.get_monthly_appointment_stats(6),
            "retention":      self._backend.get_patient_retention(6),
            "cancel_trend":   self._backend.get_cancellation_rate_trend(6),
            "period_cmp":     self._backend.get_period_comparison(),
        }

    # ── Build ─────────────────────────────────────────────────────
    def _build(self):
        data = self._load_data()
        stats = data.get("stats", {})

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget(); inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner); lay.setSpacing(20); lay.setContentsMargins(28, 28, 28, 28)

        # ── Banner ────────────────────────────────────────────────
        banner = QFrame(); banner.setObjectName("pageBanner"); banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(32, 20, 32, 20); banner_lay.setSpacing(0)
        tc = QVBoxLayout(); tc.setSpacing(4)
        tc.addWidget(self._lbl("Data Analytics & Reports", "bannerTitle"))
        tc.addWidget(self._lbl("Hospital performance, revenue, trends, and insights", "bannerSubtitle"))
        banner_lay.addLayout(tc); banner_lay.addStretch()
        lay.addWidget(banner)

        # ── Doctor-only view: own performance & revenue ───────────
        if self._role == "Doctor":
            self._build_doctor_view(lay)
            lay.addStretch()
            scroll.setWidget(inner)
            wrapper = QVBoxLayout(self)
            wrapper.setContentsMargins(0, 0, 0, 0)
            wrapper.addWidget(scroll)
            return

        if self._role == "Admin":
            # ── Period Comparison KPIs ────────────────────────────
            cmp = data.get("period_cmp", {})
            kpi_row = QHBoxLayout(); kpi_row.setSpacing(16)
            self._build_kpi_cards(kpi_row, stats, data, cmp)
            lay.addLayout(kpi_row)

            # ── Row 1: Conditions + Appointment Status ────────────
            row1 = QHBoxLayout(); row1.setSpacing(20)
            cond_data = [(c["condition_name"], c["cnt"],
                          _CONDITION_COLORS[i % len(_CONDITION_COLORS)])
                         for i, c in enumerate(data.get("conditions", []))]
            row1.addWidget(self._pie_card("Patient Conditions",
                                          "Distribution of diagnosed conditions",
                                          cond_data or [("No data", 1, "#CCC")]))
            status_data = [(s["status"], s["cnt"],
                            _STATUS_COLORS.get(s["status"], "#7F8C8D"))
                           for s in data.get("appt_status", [])]
            row1.addWidget(self._pie_card("Appointment Status",
                                          "Current appointment outcomes",
                                          status_data or [("No data", 1, "#CCC")]))
            lay.addLayout(row1)

            # ── Row 2: Revenue by Dept + Demographics ─────────────
            row2 = QHBoxLayout(); row2.setSpacing(20)
            dept_data = [(d["department_name"], int(d["total_revenue"]),
                          _DEPT_COLORS[i % len(_DEPT_COLORS)])
                         for i, d in enumerate(data.get("dept_revenue", []))]
            row2.addWidget(self._pie_card("Revenue by Department",
                                          "Revenue distribution by doctor department",
                                          dept_data or [("No data", 1, "#CCC")]))
            demo_data = [(d["age_group"], d["cnt"],
                          _DEMO_COLORS.get(d["age_group"], "#7F8C8D"))
                         for d in data.get("demographics", [])]
            row2.addWidget(self._pie_card("Patient Demographics",
                                          "Age group distribution",
                                          demo_data or [("No data", 1, "#CCC")]))
            lay.addLayout(row2)

            # ── Patient Retention ─────────────────────────────────
            lay.addWidget(self._retention_card(data.get("retention", [])))

            # ── Cancellation Rate Trend ───────────────────────────
            lay.addWidget(self._cancellation_card(data.get("cancel_trend", [])))

        # ── Doctor Performance (all roles) ────────────────────────
        lay.addWidget(self._doctor_perf_card(data.get("doctors", [])))

        if self._role == "Admin":
            # ── Top Services + Monthly Revenue ────────────────────
            row4 = QHBoxLayout(); row4.setSpacing(20)
            row4.addWidget(self._top_services_card(data.get("services", [])))
            row4.addWidget(self._monthly_revenue_card(data.get("monthly_rev", [])))
            lay.addLayout(row4)

            # ── Summary / KPI Table ───────────────────────────────
            lay.addWidget(self._summary_table_card(data))

        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

    # ── helpers ───────────────────────────────────────────────────
    @staticmethod
    def _lbl(text, obj_name):
        l = QLabel(text); l.setObjectName(obj_name); return l

    def _build_kpi_cards(self, kpi_row, stats, data, cmp):
        monthly_rev = data.get("monthly_rev", [])
        current_month_rev = float(monthly_rev[-1]["total_revenue"]) if monthly_rev else 0
        total_appts = stats.get("total_appts", 0)
        active_docs = data.get("active_doctors", 0)
        avg_per_day = stats.get("avg_per_day", 0)
        total_patients = stats.get("total_patients", 0)

        kpis = [
            ("Monthly Revenue", self._fmt_peso(current_month_rev), "#388087",
             cmp.get("revenue_delta", 0)),
            ("Total Patients", f"{total_patients:,}", "#5CB85C",
             cmp.get("patients_delta", 0)),
            ("Appointments", f"{total_appts:,}", "#6FB3B8",
             cmp.get("appts_delta", 0)),
            ("Active Doctors", f"{active_docs}", "#C2EDCE", None),
            ("Avg. Visit / Day", f"{avg_per_day}", "#388087", None),
        ]
        for label, value, color, delta in kpis:
            kpi_row.addWidget(self._kpi_card(label, value, color, delta))

    # ── Doctor-only analytics view ────────────────────────────────
    def _build_doctor_view(self, lay):
        """Build a personalised analytics page for a logged-in Doctor."""
        own = self._backend.get_doctor_own_stats(self._user_email) if self._backend else {}
        perf = own.get("performance", {})
        monthly = own.get("monthly", [])

        doc_name = perf.get("doctor_name", "Doctor")

        # ── KPI cards ─────────────────────────────────────────────
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(16)
        total_appts = int(perf.get("total_appointments", 0) or 0)
        completed   = int(perf.get("completed", 0) or 0)
        cancelled   = int(perf.get("cancelled", 0) or 0)
        revenue     = float(perf.get("revenue_generated", 0) or 0)
        comp_rate   = (completed / total_appts * 100) if total_appts else 0

        kpis = [
            ("Total Appointments", str(total_appts), "#388087"),
            ("Completed", str(completed), "#5CB85C"),
            ("Cancelled", str(cancelled), "#D9534F"),
            ("Revenue Generated", self._fmt_peso(revenue), "#6FB3B8"),
            ("Completion Rate", f"{comp_rate:.1f}%", "#C2EDCE"),
        ]
        for label, value, color in kpis:
            kpi_row.addWidget(self._kpi_card(label, value, color))
        lay.addLayout(kpi_row)

        # ── Info card (department, employment type) ───────────────
        info_card = QFrame(); info_card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 18))
        info_card.setGraphicsEffect(shadow)
        info_vbox = QVBoxLayout(info_card)
        info_vbox.setContentsMargins(20, 18, 20, 14); info_vbox.setSpacing(8)
        info_vbox.addWidget(self._lbl(f"Dr. {doc_name}", "cardTitle"))
        info_vbox.addWidget(self._lbl("Your profile summary", "mutedSubtext"))

        info_grid = QGridLayout(); info_grid.setSpacing(12)
        dept = perf.get("department_name", "—")
        emp_type = perf.get("employment_type", "—")
        for col, (lbl, val) in enumerate([
            ("Department", dept), ("Employment Type", emp_type),
            ("Total Revenue", self._fmt_peso(revenue)),
        ]):
            v = QLabel(val); v.setStyleSheet("font-size:16px; font-weight:bold; color:#388087;")
            l = QLabel(lbl); l.setStyleSheet("font-size:11px; color:#7F8C8D;")
            info_grid.addWidget(v, 0, col)
            info_grid.addWidget(l, 1, col)
        info_vbox.addLayout(info_grid)
        lay.addWidget(info_card)

        # ── Monthly Revenue Trend (own) ───────────────────────────
        if monthly:
            rev_card = QFrame(); rev_card.setObjectName("card")
            shadow2 = QGraphicsDropShadowEffect()
            shadow2.setBlurRadius(20); shadow2.setOffset(0, 4); shadow2.setColor(QColor(0, 0, 0, 18))
            rev_card.setGraphicsEffect(shadow2)
            vbox = QVBoxLayout(rev_card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
            vbox.addWidget(self._lbl("Your Monthly Revenue", "cardTitle"))
            vbox.addWidget(self._lbl("Revenue from completed appointments over the last 6 months", "mutedSubtext"))
            bar_data = [(m["month_label"][:3], int(float(m.get("revenue", 0))))
                        for m in monthly]
            colors = ["#388087"] * len(bar_data)
            chart_data = [(lbl, val, c) for (lbl, val), c in zip(bar_data, colors)]
            chart = _HBarChartWidget(chart_data)
            vbox.addWidget(chart)
            grand = sum(float(m.get("revenue", 0)) for m in monthly)
            total_row = QHBoxLayout(); total_row.addStretch()
            tl = QLabel(f"Total ({len(monthly)} months):  {self._fmt_peso(grand)}")
            tl.setObjectName("totalLabelSm")
            total_row.addWidget(tl); vbox.addLayout(total_row)
            lay.addWidget(rev_card)

        # ── Monthly breakdown table ───────────────────────────────
        if monthly:
            tbl_card = QFrame(); tbl_card.setObjectName("card")
            shadow3 = QGraphicsDropShadowEffect()
            shadow3.setBlurRadius(20); shadow3.setOffset(0, 4); shadow3.setColor(QColor(0, 0, 0, 18))
            tbl_card.setGraphicsEffect(shadow3)
            vbox2 = QVBoxLayout(tbl_card); vbox2.setContentsMargins(20, 18, 20, 14); vbox2.setSpacing(12)
            vbox2.addWidget(self._lbl("Monthly Breakdown", "cardTitle"))
            vbox2.addWidget(self._lbl("Appointments and revenue per month", "mutedSubtext"))
            cols = ["Month", "Appointments", "Completed", "Revenue"]
            tbl = QTableWidget(len(monthly), len(cols))
            tbl.setHorizontalHeaderLabels(cols)
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tbl.verticalHeader().setVisible(False)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
            tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            tbl.setAlternatingRowColors(True)
            tbl.setMaximumHeight(len(monthly) * 40 + 40)
            tbl.verticalHeader().setDefaultSectionSize(36)
            configure_table(tbl)
            for r, m in enumerate(monthly):
                tbl.setItem(r, 0, QTableWidgetItem(m.get("month_label", "")))
                tbl.setItem(r, 1, QTableWidgetItem(str(m.get("total_appointments", 0))))
                tbl.setItem(r, 2, QTableWidgetItem(str(m.get("completed", 0))))
                tbl.setItem(r, 3, QTableWidgetItem(self._fmt_peso(float(m.get("revenue", 0)))))
            vbox2.addWidget(tbl)
            lay.addWidget(tbl_card)

    @staticmethod
    def _kpi_card(label, value, color, delta=None) -> QFrame:
        card = QFrame(); card.setObjectName("card"); card.setMinimumHeight(110)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)
        vbox = QVBoxLayout(card); vbox.setContentsMargins(18, 14, 18, 14); vbox.setSpacing(4)
        strip = QFrame(); strip.setFixedHeight(3)
        strip.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
        vbox.addWidget(strip)
        v = QLabel(value); v.setObjectName("statValue"); vbox.addWidget(v)
        l = QLabel(label); l.setObjectName("statLabel"); vbox.addWidget(l)
        if delta is not None:
            arrow = "▲" if delta >= 0 else "▼"
            clr = "#5CB85C" if delta >= 0 else "#D9534F"
            d = QLabel(f"{arrow} {abs(delta):.1f}% vs last month")
            d.setStyleSheet(f"color: {clr}; font-size: 11px; font-weight: bold;")
            vbox.addWidget(d)
        return card

    # ── Refresh / Export ──────────────────────────────────────────
    def _on_refresh(self):
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            from PyQt6.QtWidgets import QWidget as _QW
            _QW().setLayout(old)
        self._build()

    # ── Pie card ──────────────────────────────────────────────────
    @staticmethod
    def _pie_card(title_text, subtitle_text, data) -> QFrame:
        card = QFrame(); card.setObjectName("card"); card.setMinimumHeight(340)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(8)
        t = QLabel(title_text); t.setObjectName("cardTitle")
        s = QLabel(subtitle_text); s.setObjectName("mutedSubtext")
        vbox.addWidget(t); vbox.addWidget(s)

        content = QHBoxLayout(); content.setSpacing(16)
        chart = _PieChartWidget(data); chart.setFixedSize(200, 200)
        content.addWidget(chart, alignment=Qt.AlignmentFlag.AlignCenter)
        legend = QVBoxLayout(); legend.setSpacing(6)
        total = sum(v for _, v, _ in data)
        for label, value, color in data:
            pct = (value / total * 100) if total else 0
            row = QHBoxLayout(); row.setSpacing(8)
            dot = QLabel("●"); dot.setStyleSheet(f"color:{color}; font-size:14px;"); dot.setFixedWidth(16)
            lbl = QLabel(label); lbl.setStyleSheet("color:#2C3E50; font-size:12px;")
            val = QLabel(f"{value:,} ({pct:.1f}%)"); val.setStyleSheet("color:#7F8C8D; font-size:11px;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(dot); row.addWidget(lbl, 1); row.addWidget(val)
            legend.addLayout(row)
        legend.addStretch()
        content.addLayout(legend, 1)
        vbox.addLayout(content, 1)
        total_lbl = QLabel(f"Total:  {total:,}"); total_lbl.setObjectName("chartTotal")
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(total_lbl)
        return card

    # ── Patient Retention card ────────────────────────────────────
    def _retention_card(self, retention: list) -> QFrame:
        card = QFrame(); card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
        vbox.addWidget(self._lbl("Patient Retention", "cardTitle"))
        vbox.addWidget(self._lbl("New vs returning patients per month", "mutedSubtext"))

        cols = ["Month", "New Patients", "Returning", "Total"]
        tbl = QTableWidget(len(retention), len(cols))
        tbl.setHorizontalHeaderLabels(cols)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(max(len(retention), 1) * 48 + 48)
        tbl.verticalHeader().setDefaultSectionSize(48)
        configure_table(tbl)
        for r, row in enumerate(retention):
            new_p = int(row.get("new_patients", 0) or 0)
            ret_p = int(row.get("returning_patients", 0) or 0)
            tbl.setItem(r, 0, QTableWidgetItem(row.get("month_label", "")))
            ni = QTableWidgetItem(str(new_p)); ni.setForeground(QColor("#6FB3B8"))
            tbl.setItem(r, 1, ni)
            ri = QTableWidgetItem(str(ret_p)); ri.setForeground(QColor("#388087"))
            tbl.setItem(r, 2, ri)
            tbl.setItem(r, 3, QTableWidgetItem(str(new_p + ret_p)))
        vbox.addWidget(tbl)
        return card

    # ── Cancellation Rate card ────────────────────────────────────
    def _cancellation_card(self, cancel_trend: list) -> QFrame:
        card = QFrame(); card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
        vbox.addWidget(self._lbl("Cancellation Rate Trend", "cardTitle"))
        vbox.addWidget(self._lbl("Monthly cancellation rate over time", "mutedSubtext"))

        cols = ["Month", "Total", "Cancelled", "Rate"]
        tbl = QTableWidget(len(cancel_trend), len(cols))
        tbl.setHorizontalHeaderLabels(cols)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(max(len(cancel_trend), 1) * 48 + 48)
        tbl.verticalHeader().setDefaultSectionSize(48)
        configure_table(tbl)
        for r, row in enumerate(cancel_trend):
            tbl.setItem(r, 0, QTableWidgetItem(row.get("month_label", "")))
            tbl.setItem(r, 1, QTableWidgetItem(str(row.get("total", 0))))
            ci = QTableWidgetItem(str(row.get("cancelled", 0)))
            ci.setForeground(QColor("#D9534F"))
            tbl.setItem(r, 2, ci)
            rate = float(row.get("rate", 0) or 0)
            ri = QTableWidgetItem(f"{rate:.1f}%")
            ri.setForeground(QColor("#D9534F" if rate > 15 else "#E8B931" if rate > 5 else "#5CB85C"))
            tbl.setItem(r, 3, ri)
        vbox.addWidget(tbl)
        return card

    # ── Doctor Performance ────────────────────────────────────────
    def _doctor_perf_card(self, doctors: list) -> QFrame:
        card = QFrame(); card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
        vbox.addWidget(self._lbl("Doctor Performance", "cardTitle"))
        vbox.addWidget(self._lbl("Appointments, completions, and revenue generated", "mutedSubtext"))

        cols = ["Doctor", "Total Appts", "Completed", "Revenue Generated"]
        tbl = QTableWidget(len(doctors), len(cols))
        tbl.setHorizontalHeaderLabels(cols)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(max(len(doctors), 1) * 48 + 48)
        tbl.verticalHeader().setDefaultSectionSize(48)
        configure_table(tbl)
        for r, doc in enumerate(doctors):
            name = doc.get("doctor_name", "")
            tbl.setItem(r, 0, QTableWidgetItem(f"Dr. {name.split()[-1]}" if name else ""))
            tbl.setItem(r, 1, QTableWidgetItem(str(doc.get("total_appointments", 0))))
            tbl.setItem(r, 2, QTableWidgetItem(str(doc.get("completed", 0))))
            tbl.setItem(r, 3, QTableWidgetItem(self._fmt_peso(float(doc.get("revenue_generated", 0)))))
        vbox.addWidget(tbl)
        return card

    # ── Top Services ──────────────────────────────────────────────
    def _top_services_card(self, services: list) -> QFrame:
        card = QFrame(); card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
        vbox.addWidget(self._lbl("Top Services", "cardTitle"))
        vbox.addWidget(self._lbl("Most requested services and revenue contribution", "mutedSubtext"))

        cols = ["Service", "Count", "Revenue"]
        tbl = QTableWidget(len(services), len(cols))
        tbl.setHorizontalHeaderLabels(cols)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(max(len(services), 1) * 48 + 48)
        tbl.verticalHeader().setDefaultSectionSize(48)
        configure_table(tbl)
        for r, svc in enumerate(services):
            tbl.setItem(r, 0, QTableWidgetItem(svc.get("service_name", "")))
            tbl.setItem(r, 1, QTableWidgetItem(str(svc.get("usage_count", 0))))
            tbl.setItem(r, 2, QTableWidgetItem(self._fmt_peso(float(svc.get("total_revenue", 0)))))
        vbox.addWidget(tbl)
        return card

    # ── Monthly Revenue ───────────────────────────────────────────
    def _monthly_revenue_card(self, monthly: list) -> QFrame:
        card = QFrame(); card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)
        vbox.addWidget(self._lbl("Monthly Revenue Trend", "cardTitle"))
        vbox.addWidget(self._lbl("Revenue over the last 6 months", "mutedSubtext"))

        cols = ["Month", "Revenue"]
        tbl = QTableWidget(len(monthly), len(cols))
        tbl.setHorizontalHeaderLabels(cols)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(max(len(monthly), 1) * 48 + 48)
        tbl.verticalHeader().setDefaultSectionSize(48)
        configure_table(tbl)
        grand = 0.0
        for r, row in enumerate(monthly):
            tbl.setItem(r, 0, QTableWidgetItem(row.get("month_label", "")))
            rev = float(row.get("total_revenue", 0)); grand += rev
            tbl.setItem(r, 1, QTableWidgetItem(self._fmt_peso(rev)))
        vbox.addWidget(tbl)
        total_row = QHBoxLayout(); total_row.addStretch()
        tl = QLabel(f"Total ({len(monthly)} months):  {self._fmt_peso(grand)}")
        tl.setObjectName("totalLabelSm")
        total_row.addWidget(tl); vbox.addLayout(total_row)
        return card

    # ── Summary / KPI Table ───────────────────────────────────────
    def _summary_table_card(self, data: dict) -> QFrame:
        card = QFrame(); card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)
        vbox = QVBoxLayout(card); vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)

        hdr = QHBoxLayout()
        tc = QVBoxLayout()
        tc.addWidget(self._lbl("Overall Summary", "cardTitle"))
        tc.addWidget(self._lbl("Key metrics at a glance for the selected period", "mutedSubtext"))
        hdr.addLayout(tc); hdr.addStretch()

        hdr.addWidget(QLabel("From:"))
        self.sum_from = QDateEdit(); self.sum_from.setCalendarPopup(True)
        self.sum_from.setDate(QDate.currentDate().addMonths(-6))
        self.sum_from.setObjectName("formCombo"); self.sum_from.setMinimumHeight(36); self.sum_from.setMaximumWidth(140)
        hdr.addWidget(self.sum_from)
        hdr.addWidget(QLabel("To:"))
        self.sum_to = QDateEdit(); self.sum_to.setCalendarPopup(True)
        self.sum_to.setDate(QDate.currentDate())
        self.sum_to.setObjectName("formCombo"); self.sum_to.setMinimumHeight(36); self.sum_to.setMaximumWidth(140)
        hdr.addWidget(self.sum_to)
        apply_btn = QPushButton("Apply"); apply_btn.setObjectName("secondaryBtn")
        apply_btn.setMinimumHeight(36); apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._on_refresh)
        hdr.addWidget(apply_btn)
        vbox.addLayout(hdr)

        stats = data.get("stats", {})
        monthly_rev = data.get("monthly_rev", [])
        grand_rev = sum(float(m.get("total_revenue", 0)) for m in monthly_rev)
        completed = stats.get("completed", 0)
        cancelled = stats.get("cancelled", 0)
        total_appts = stats.get("total_appts", 0)
        completion_rate = (completed / total_appts * 100) if total_appts else 0
        services = data.get("services", [])
        top_svc = services[0] if services else {}
        top_svc_text = (f"{top_svc.get('service_name','N/A')} "
                        f"({self._fmt_peso(float(top_svc.get('total_revenue',0)))})") if top_svc else "N/A"

        summary = [
            ("Total Revenue (period)", self._fmt_peso(grand_rev)),
            ("Appointments Completed", str(completed)),
            ("Appointments Cancelled", str(cancelled)),
            ("Completion Rate", f"{completion_rate:.1f}%"),
            ("Top Service", top_svc_text),
        ]
        cols = ["Metric", "Value"]
        tbl = QTableWidget(len(summary), len(cols))
        tbl.setHorizontalHeaderLabels(cols)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(len(summary) * 48 + 48)
        tbl.verticalHeader().setDefaultSectionSize(48)
        configure_table(tbl)
        for r, (metric, value) in enumerate(summary):
            tbl.setItem(r, 0, QTableWidgetItem(metric))
            vi = QTableWidgetItem(value); vi.setForeground(QColor("#2C3E50"))
            tbl.setItem(r, 1, vi)
        vbox.addWidget(tbl)
        return card
