"""Data Analytics page – pie charts, hospital performance, reports & summary."""

import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy, QPushButton, QDateEdit,
)
from PyQt6.QtCore import Qt, QRectF, QDate
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath
from ui.styles import configure_table


# ── Sample analytics data ──────────────────────────────────────────────

_DISEASE_DISTRIBUTION = [
    ("Hypertension",     218, "#388087"),
    ("Diabetes",         164, "#6FB3B8"),
    ("Respiratory",      132, "#BADFE7"),
    ("Heart Disease",     98, "#C2EDCE"),
    ("Dental Issues",     87, "#E8B931"),
    ("Skin Conditions",   62, "#D9534F"),
    ("Others",           145, "#7F8C8D"),
]

_APPOINTMENT_STATUS = [
    ("Completed",  342, "#5CB85C"),
    ("Confirmed",  128, "#388087"),
    ("Pending",     67, "#E8B931"),
    ("Cancelled",   36, "#D9534F"),
]

_REVENUE_BY_DEPT = [
    ("General Medicine", 285000, "#388087"),
    ("Cardiology",       198000, "#6FB3B8"),
    ("Dentistry",        165000, "#BADFE7"),
    ("Pediatrics",       142000, "#C2EDCE"),
    ("Laboratory",       124000, "#E8B931"),
    ("Pharmacy",          98000, "#7F8C8D"),
]

_PATIENT_DEMOGRAPHICS = [
    ("0–17",   185, "#6FB3B8"),
    ("18–35",  312, "#388087"),
    ("36–50",  278, "#BADFE7"),
    ("51–65",  224, "#C2EDCE"),
    ("65+",    149, "#E8B931"),
]

_DOCTOR_PERFORMANCE = [
    ("Dr. Ana Reyes",    156, 148, "₱ 125,600", "4.8"),
    ("Dr. Mark Tan",     132, 128, "₱ 108,400", "4.7"),
    ("Dr. Lisa Lim",      98,  94, "₱ 92,300",  "4.9"),
    ("Dr. Pedro Santos",  87,  82, "₱ 78,500",  "4.6"),
]

_MONTHLY_REVENUE = [
    ("Sep 2025", "₱ 368,200"),
    ("Oct 2025", "₱ 402,500"),
    ("Nov 2025", "₱ 425,800"),
    ("Dec 2025", "₱ 398,100"),
    ("Jan 2026", "₱ 452,300"),
    ("Feb 2026", "₱ 482,300"),
]

_TOP_SERVICES = [
    ("General Checkup",     312, "₱ 249,600"),
    ("Lab Tests – CBC",     198, "₱ 237,600"),
    ("Dental Cleaning",     145, "₱ 362,500"),
    ("X-Ray",               132, "₱ 198,000"),
    ("Follow-up Visit",     287, "₱ 143,500"),
    ("ECG",                  98, "₱ 98,000"),
    ("Physical Therapy",     76, "₱ 136,800"),
]

# ── Pie Chart Widget ───────────────────────────────────────────────────

class _PieChartWidget(QWidget):
    """Custom-painted donut / pie chart."""

    def __init__(self, data: list[tuple[str, int, str]], *, donut: bool = True,
                 parent=None):
        super().__init__(parent)
        self._data = data
        self._donut = donut
        self._total = sum(v for _, v, _ in data)
        self.setMinimumSize(220, 220)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = min(self.width(), self.height()) - 20
        x = (self.width() - size) / 2
        y = (self.height() - size) / 2
        rect = QRectF(x, y, size, size)

        start = 90 * 16  # start from top
        for label, value, color in self._data:
            span = int(value / self._total * 360 * 16) if self._total else 0
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawPie(rect, start, -span)
            start -= span

        # Donut hole
        if self._donut:
            hole = size * 0.52
            hx = (self.width() - hole) / 2
            hy = (self.height() - hole) / 2
            painter.setBrush(QBrush(QColor("#FFFFFF")))
            painter.drawEllipse(QRectF(hx, hy, hole, hole))

        painter.end()


# ── Horizontal Bar Chart Widget ────────────────────────────────────────

class _HBarChartWidget(QWidget):
    """Simple horizontal bar chart."""

    def __init__(self, data: list[tuple[str, int, str]], parent=None):
        super().__init__(parent)
        self._data = data
        self._max = max(v for _, v, _ in data) if data else 1
        self.setMinimumHeight(len(data) * 38 + 10)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bar_h = 22
        spacing = 38
        label_w = 130
        value_w = 60
        bar_area = self.width() - label_w - value_w - 20

        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)

        for i, (label, value, color) in enumerate(self._data):
            y = i * spacing + 8

            # Label
            painter.setPen(QPen(QColor("#2C3E50")))
            painter.drawText(QRectF(0, y, label_w, bar_h),
                             Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                             label)

            # Bar
            bar_w = int((value / self._max) * bar_area) if self._max else 0
            bar_rect = QRectF(label_w, y, bar_w, bar_h)
            path = QPainterPath()
            path.addRoundedRect(bar_rect, 4, 4)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color)))
            painter.drawPath(path)

            # Value
            painter.setPen(QPen(QColor("#2C3E50")))
            painter.drawText(
                QRectF(label_w + bar_area + 4, y, value_w, bar_h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                f"{value:,}",
            )

        painter.end()


# ── Analytics Page ─────────────────────────────────────────────────────

class AnalyticsPage(QWidget):
    def __init__(self, role: str = "Admin"):
        super().__init__()
        self._role = role
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

        # ── Header Banner ──────────────────────────────────────────
        banner = QFrame()
        banner.setObjectName("pageBanner")
        banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(32, 20, 32, 20)
        banner_lay.setSpacing(0)
        tc = QVBoxLayout()
        tc.setSpacing(4)
        title = QLabel("Data Analytics & Reports")
        title.setObjectName("bannerTitle")
        sub = QLabel("Hospital performance overview, revenue, trends, and insights")
        sub.setObjectName("bannerSubtitle")
        tc.addWidget(title)
        tc.addWidget(sub)
        banner_lay.addLayout(tc)
        banner_lay.addStretch()

        if self._role == "Admin":
            export_btn = QPushButton("Export Report")
            export_btn.setObjectName("bannerBtn")
            export_btn.setMinimumHeight(42)
            export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            banner_lay.addWidget(export_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(banner)

        if self._role == "Admin":
            # ── KPI Summary Cards ──────────────────────────────────────
            kpi_row = QHBoxLayout()
            kpi_row.setSpacing(16)
            kpis = [
                ("Monthly Revenue",    "₱ 482,300",   "+12.4%",  "#388087"),
                ("Total Patients",     "1,248",        "+3.2%",   "#5CB85C"),
                ("Appointments",       "573",          "+8.1%",   "#6FB3B8"),
                ("Avg. Satisfaction",  "4.75 / 5",     "+0.3%",   "#E8B931"),
                ("Active Doctors",     "4",            "Stable",  "#C2EDCE"),
                ("Avg. Visit / Day",   "15.8",         "+1.5%",   "#388087"),
            ]
            for label, value, change, color in kpis:
                kpi_row.addWidget(self._kpi_card(label, value, change, color))
            lay.addLayout(kpi_row)

            # ── Row 1: Disease Distribution + Appointment Status ───────
            row1 = QHBoxLayout()
            row1.setSpacing(20)
            row1.addWidget(self._pie_card(
                "Patient Conditions", "Distribution of diagnosed conditions",
                _DISEASE_DISTRIBUTION))
            row1.addWidget(self._pie_card(
                "Appointment Status", "Current month appointment outcomes",
                _APPOINTMENT_STATUS))
            lay.addLayout(row1)

            # ── Row 2: Revenue by Department + Patient Demographics ────
            row2 = QHBoxLayout()
            row2.setSpacing(20)
            row2.addWidget(self._pie_card(
                "Revenue by Department", "Monthly revenue distribution",
                _REVENUE_BY_DEPT))
            row2.addWidget(self._pie_card(
                "Patient Demographics", "Age group distribution",
                _PATIENT_DEMOGRAPHICS))
            lay.addLayout(row2)

        # ── Doctor Performance Table ───────────────────────────────────
        lay.addWidget(self._doctor_perf_card())

        if self._role == "Admin":
            # ── Top Services + Monthly Revenue ─────────────────────────
            row4 = QHBoxLayout()
            row4.setSpacing(20)
            row4.addWidget(self._top_services_card())
            row4.addWidget(self._monthly_revenue_card())
            lay.addLayout(row4)

            # ── Summary Table ──────────────────────────────────────────
            lay.addWidget(self._summary_table_card())

        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

    # ── KPI card ───────────────────────────────────────────────────────
    @staticmethod
    def _kpi_card(label, value, change, color) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(110)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(18, 14, 18, 14)
        vbox.setSpacing(4)

        strip = QFrame()
        strip.setFixedHeight(3)
        strip.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
        vbox.addWidget(strip)

        val_row = QHBoxLayout()
        v = QLabel(value)
        v.setObjectName("statValue")
        v.setStyleSheet("font-size: 18px;")
        ch = QLabel(change)
        ch_color = "#5CB85C" if change.startswith("+") else "#7F8C8D"
        ch.setStyleSheet(f"color: {ch_color}; font-size: 11px; font-weight: bold;")
        val_row.addWidget(v)
        val_row.addStretch()
        val_row.addWidget(ch)
        vbox.addLayout(val_row)

        l = QLabel(label)
        l.setObjectName("statLabel")
        vbox.addWidget(l)
        return card

    # ── Pie chart card ─────────────────────────────────────────────────
    @staticmethod
    def _pie_card(title_text, subtitle_text, data) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(340)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14)
        vbox.setSpacing(8)

        t = QLabel(title_text)
        t.setObjectName("cardTitle")
        s = QLabel(subtitle_text)
        s.setObjectName("mutedSubtext")
        vbox.addWidget(t)
        vbox.addWidget(s)

        content = QHBoxLayout()
        content.setSpacing(16)

        chart = _PieChartWidget(data)
        chart.setFixedSize(200, 200)
        content.addWidget(chart, alignment=Qt.AlignmentFlag.AlignCenter)

        # Legend
        legend = QVBoxLayout()
        legend.setSpacing(6)
        total = sum(v for _, v, _ in data)
        for label, value, color in data:
            pct = (value / total * 100) if total else 0
            row = QHBoxLayout()
            row.setSpacing(8)
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 14px;")
            dot.setFixedWidth(16)
            lbl = QLabel(f"{label}")
            lbl.setStyleSheet("color: #2C3E50; font-size: 12px;")
            val = QLabel(f"{value:,} ({pct:.1f}%)")
            val.setStyleSheet("color: #7F8C8D; font-size: 11px;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(dot)
            row.addWidget(lbl, 1)
            row.addWidget(val)
            legend.addLayout(row)
        legend.addStretch()
        content.addLayout(legend, 1)

        vbox.addLayout(content, 1)

        # Total bar at bottom
        total_lbl = QLabel(f"Total:  {total:,}")
        total_lbl.setObjectName("chartTotal")
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(total_lbl)

        return card

    # ── Doctor performance card ────────────────────────────────────────
    def _doctor_perf_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14)
        vbox.setSpacing(12)

        t = QLabel("Doctor Performance")
        t.setObjectName("cardTitle")
        s = QLabel("Appointments, revenue, and patient satisfaction ratings")
        s.setObjectName("mutedSubtext")
        vbox.addWidget(t)
        vbox.addWidget(s)

        cols = ["Doctor", "Total Appts", "Completed", "Revenue Generated", "Patient Rating"]
        tbl = QTableWidget(len(_DOCTOR_PERFORMANCE), len(cols))
        tbl.setHorizontalHeaderLabels(cols)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(len(_DOCTOR_PERFORMANCE) * 48 + 48)
        tbl.verticalHeader().setDefaultSectionSize(48)
        configure_table(tbl)

        for r, (name, total, completed, revenue, rating) in enumerate(_DOCTOR_PERFORMANCE):
            tbl.setItem(r, 0, QTableWidgetItem(name))
            tbl.setItem(r, 1, QTableWidgetItem(str(total)))
            tbl.setItem(r, 2, QTableWidgetItem(str(completed)))
            tbl.setItem(r, 3, QTableWidgetItem(revenue))
            item = QTableWidgetItem(f"⭐ {rating}")
            rating_val = float(rating)
            if rating_val >= 4.8:
                item.setForeground(QColor("#5CB85C"))
            elif rating_val >= 4.6:
                item.setForeground(QColor("#388087"))
            else:
                item.setForeground(QColor("#E8B931"))
            tbl.setItem(r, 4, item)

        vbox.addWidget(tbl)
        return card

    # ── Top services card ──────────────────────────────────────────────
    def _top_services_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14)
        vbox.setSpacing(12)

        t = QLabel("Top Services")
        t.setObjectName("cardTitle")
        s = QLabel("Most requested services and revenue contribution")
        s.setObjectName("mutedSubtext")
        vbox.addWidget(t)
        vbox.addWidget(s)

        cols = ["Service", "Count", "Revenue"]
        tbl = QTableWidget(len(_TOP_SERVICES), len(cols))
        tbl.setHorizontalHeaderLabels(cols)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(len(_TOP_SERVICES) * 44 + 48)
        tbl.verticalHeader().setDefaultSectionSize(44)
        configure_table(tbl)

        for r, (name, count, revenue) in enumerate(_TOP_SERVICES):
            tbl.setItem(r, 0, QTableWidgetItem(name))
            tbl.setItem(r, 1, QTableWidgetItem(str(count)))
            tbl.setItem(r, 2, QTableWidgetItem(revenue))

        vbox.addWidget(tbl)
        return card

    # ── Monthly revenue card ───────────────────────────────────────────
    def _monthly_revenue_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14)
        vbox.setSpacing(12)

        t = QLabel("Monthly Revenue Trend")
        t.setObjectName("cardTitle")
        s = QLabel("Revenue over the last 6 months")
        s.setObjectName("mutedSubtext")
        vbox.addWidget(t)
        vbox.addWidget(s)

        cols = ["Month", "Revenue"]
        tbl = QTableWidget(len(_MONTHLY_REVENUE), len(cols))
        tbl.setHorizontalHeaderLabels(cols)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(len(_MONTHLY_REVENUE) * 44 + 48)
        tbl.verticalHeader().setDefaultSectionSize(44)
        configure_table(tbl)

        for r, (month, revenue) in enumerate(_MONTHLY_REVENUE):
            tbl.setItem(r, 0, QTableWidgetItem(month))
            tbl.setItem(r, 1, QTableWidgetItem(revenue))

        vbox.addWidget(tbl)

        # Total
        total_row = QHBoxLayout()
        total_row.addStretch()
        tl = QLabel("Total (6 months):  ₱ 2,529,200")
        tl.setObjectName("totalLabelSm")
        total_row.addWidget(tl)
        vbox.addLayout(total_row)

        return card

    # ── Summary table card ─────────────────────────────────────────────
    def _summary_table_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 18))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14)
        vbox.setSpacing(12)

        hdr = QHBoxLayout()
        title_col = QVBoxLayout()
        t = QLabel("Overall Summary")
        t.setObjectName("cardTitle")
        s = QLabel("Key metrics at a glance for the selected period")
        s.setObjectName("mutedSubtext")
        title_col.addWidget(t)
        title_col.addWidget(s)
        hdr.addLayout(title_col)
        hdr.addStretch()

        hdr.addWidget(QLabel("From:"))
        self.sum_from = QDateEdit()
        self.sum_from.setCalendarPopup(True)
        self.sum_from.setDate(QDate(2025, 9, 1))
        self.sum_from.setObjectName("formCombo")
        self.sum_from.setMinimumHeight(36)
        self.sum_from.setMaximumWidth(140)
        hdr.addWidget(self.sum_from)

        hdr.addWidget(QLabel("To:"))
        self.sum_to = QDateEdit()
        self.sum_to.setCalendarPopup(True)
        self.sum_to.setDate(QDate.currentDate())
        self.sum_to.setObjectName("formCombo")
        self.sum_to.setMinimumHeight(36)
        self.sum_to.setMaximumWidth(140)
        hdr.addWidget(self.sum_to)

        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("secondaryBtn")
        apply_btn.setMinimumHeight(36)
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        hdr.addWidget(apply_btn)

        vbox.addLayout(hdr)

        summary_data = [
            ("Total Revenue (6 months)", "₱ 2,529,200",  "+9.8%"),
            ("Appointments Completed",   "342",          "+8.1%"),
            ("Appointments Cancelled",   "36",           "-2.1%"),
            ("Completion Rate",          "89.7%",        "+1.3%"),
            ("Top Service",              "Dental Cleaning (₱ 362,500)", "—"),
        ]

        cols = ["Metric", "Value", "Change"]
        tbl = QTableWidget(len(summary_data), len(cols))
        tbl.setHorizontalHeaderLabels(cols)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(len(summary_data) * 44 + 48)
        tbl.verticalHeader().setDefaultSectionSize(44)
        configure_table(tbl)

        for r, (metric, value, change) in enumerate(summary_data):
            m_item = QTableWidgetItem(metric)
            tbl.setItem(r, 0, m_item)

            v_item = QTableWidgetItem(value)
            v_item.setForeground(QColor("#2C3E50"))
            tbl.setItem(r, 1, v_item)

            ch_item = QTableWidgetItem(change)
            if change.startswith("+"):
                ch_item.setForeground(QColor("#5CB85C"))
            elif change.startswith("-"):
                ch_item.setForeground(QColor("#D9534F"))
            else:
                ch_item.setForeground(QColor("#7F8C8D"))
            tbl.setItem(r, 2, ch_item)

        vbox.addWidget(tbl)
        return card

    # ── Table helper ───────────────────────────────────────────────────
    @staticmethod
    def _make_table(headers, rows) -> QTableWidget:
        tbl = QTableWidget(len(rows), len(headers))
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tbl.verticalHeader().setVisible(False)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tbl.setAlternatingRowColors(True)
        tbl.setMinimumHeight(min(len(rows) * 48 + 48, 360))
        tbl.verticalHeader().setDefaultSectionSize(48)
        configure_table(tbl)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                tbl.setItem(r, c, QTableWidgetItem(val))
        return tbl