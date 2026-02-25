"""Dashboard – glanceable hospital summary with KPI cards, schedule preview & trends."""

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QGraphicsDropShadowEffect,
    QScrollArea, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from ui.styles import configure_table


# ── Tiny bar-chart widget ─────────────────────────────────────────
class _BarChartWidget(QWidget):
    """Simple horizontal bar chart painted via QPainter."""

    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data or []
        self._max = max(v for _, v in self._data) if self._data else 1
        self.setMinimumHeight(max(len(self._data) * 38 + 10, 50))

    def set_data(self, data):
        self._data = data
        self._max = max(v for _, v in data) if data else 1
        self.setMinimumHeight(max(len(data) * 38 + 10, 50))
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        bar_h, spacing, label_w, padding_r = 22, 38, 36, 40
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
            painter.setBrush(QColor("#388087"))
            painter.drawRoundedRect(bar_x, y + 2, fill_w, bar_h - 4, 6, 6)
            painter.setPen(QColor("#2C3E50"))
            painter.drawText(bar_x + int(max_bar_w) + 6, y, 34, bar_h,
                             Qt.AlignmentFlag.AlignVCenter, str(value))
        painter.end()


# ── Dashboard page ────────────────────────────────────────────────
class DashboardPage(QWidget):
    """Hospital dashboard – KPI cards, schedule preview, monthly trends."""

    navigate_to = pyqtSignal(int)

    def __init__(self, user_name="Admin", backend=None, role="Admin"):
        super().__init__()
        self._user_name = user_name
        self._backend = backend
        self._role = role
        self._kpi_labels = {}
        self._build()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1_000)

    # ── Layout ────────────────────────────────────────────────────
    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget(); inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner)
        lay.setSpacing(20); lay.setContentsMargins(28, 28, 28, 28)

        # Banner
        lay.addWidget(self._build_banner())

        # KPI cards
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(16)
        for key, icon, title, page_idx in [
            ("today_appts",     "\U0001F4C5", "Today's Appointments", 2),
            ("active_patients", "\U0001F465", "Active Patients",      1),
            ("today_revenue",   "\U0001F4B0", "Today's Revenue",      4),
            ("active_staff",    "\U0001F3E5", "Active Staff",         5),
        ]:
            kpi_row.addWidget(self._make_kpi_card(key, icon, title, page_idx))
        lay.addLayout(kpi_row)

        # Quick actions
        act_row = QHBoxLayout(); act_row.setSpacing(12)
        for text, pi in [
            ("\u2795  New Patient", 1), ("\U0001F4C5  New Appointment", 2),
            ("\U0001F3E5  Clinical Queue", 3), ("\U0001F4CA  Analytics", 4),
        ]:
            btn = QPushButton(text)
            btn.setObjectName("actionBtn")
            btn.setMinimumHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, p=pi: self.navigate_to.emit(p))
            act_row.addWidget(btn)
        act_row.addStretch()
        lay.addLayout(act_row)

        # Two-column: schedule + chart
        cols = QHBoxLayout(); cols.setSpacing(16)
        cols.addWidget(self._schedule_card(), 3)
        cols.addWidget(self._chart_card(), 2)
        lay.addLayout(cols)

        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)
        self.refresh()

    # ── Banner ────────────────────────────────────────────────────
    def _build_banner(self):
        banner = QFrame()
        banner.setObjectName("pageBanner")
        banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)

        vl = QVBoxLayout(banner)
        vl.setContentsMargins(32, 24, 32, 24); vl.setSpacing(6)
        now = datetime.now()
        greeting = "Good Morning" if now.hour < 12 else (
            "Good Afternoon" if now.hour < 17 else "Good Evening")
        self._greeting_label = self._white_lbl(
            f"{greeting}, {self._user_name}!", 24, True)
        vl.addWidget(self._greeting_label)
        self._date_label = self._white_lbl(
            now.strftime("%I:%M %p  \u2022  %B %d, %Y"), 14, False, 0.85)
        vl.addWidget(self._date_label)
        vl.addWidget(self._white_lbl(
            "Here's what's happening at the hospital today.", 13, False, 0.7))
        return banner

    # ── KPI card builder ──────────────────────────────────────────
    def _make_kpi_card(self, key, icon, title, page_idx):
        card = QPushButton()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setMinimumHeight(110)
        card.setStyleSheet(
            "QPushButton { background: #FFFFFF; border: 1px solid #BADFE7;"
            " border-radius: 14px; padding: 16px; text-align: left; }"
            " QPushButton:hover { border-color: #388087; background: #F6F9FA; }"
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12); shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 8))
        card.setGraphicsEffect(shadow)

        vl = QVBoxLayout(card)
        vl.setSpacing(4); vl.setContentsMargins(4, 4, 4, 4)

        ic = QLabel(icon)
        ic.setStyleSheet("font-size: 22px; background: transparent;")
        vl.addWidget(ic)

        val = QLabel("\u2013")
        val.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #2C3E50; background: transparent;")
        vl.addWidget(val)
        self._kpi_labels[key] = val

        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 12px; color: #7F8C8D; background: transparent;")
        vl.addWidget(lbl)

        sub = QLabel("")
        sub.setStyleSheet("font-size: 11px; color: #388087; background: transparent;")
        vl.addWidget(sub)
        self._kpi_labels[f"{key}_sub"] = sub

        card.clicked.connect(lambda: self.navigate_to.emit(page_idx))
        return card

    # ── Schedule preview ──────────────────────────────────────────
    def _schedule_card(self):
        card = QFrame(); card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18); shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 12))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)

        hdr = QHBoxLayout()
        title = QLabel("Today's Schedule")
        title.setObjectName("cardTitle")
        hdr.addWidget(title); hdr.addStretch()
        self._sched_badge = QLabel("0 upcoming")
        self._sched_badge.setStyleSheet(
            "background-color:#BADFE7; color:#388087; border-radius:10px;"
            "padding:3px 10px; font-size:11px; font-weight:bold;")
        hdr.addWidget(self._sched_badge)
        vbox.addLayout(hdr)

        self._sched_table = QTableWidget(0, 4)
        self._sched_table.setHorizontalHeaderLabels(
            ["Time", "Patient", "Doctor", "Status"])
        self._sched_table.horizontalHeader().setStretchLastSection(True)
        self._sched_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self._sched_table.verticalHeader().setVisible(False)
        self._sched_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self._sched_table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection)
        self._sched_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._sched_table.setMinimumHeight(240)
        self._sched_table.setMaximumHeight(300)
        self._sched_table.verticalHeader().setDefaultSectionSize(44)
        self._sched_table.setAlternatingRowColors(True)
        configure_table(self._sched_table)
        vbox.addWidget(self._sched_table)

        view_all = QPushButton("View all appointments \u2192")
        view_all.setCursor(Qt.CursorShape.PointingHandCursor)
        view_all.setStyleSheet(
            "QPushButton { background: transparent; border: none; color: #388087;"
            " font-size: 12px; font-weight: bold; padding: 4px 0; text-align: left; }"
            " QPushButton:hover { color: #2C6A70; }")
        view_all.clicked.connect(lambda: self.navigate_to.emit(2))
        vbox.addWidget(view_all)
        return card

    # ── Chart card ────────────────────────────────────────────────
    def _chart_card(self):
        card = QFrame(); card.setObjectName("card")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18); shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 12))
        card.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)

        hdr = QHBoxLayout()
        title = QLabel("Monthly Visits"); title.setObjectName("cardTitle")
        hdr.addWidget(title); hdr.addStretch()
        period = QLabel("Last 6 Months"); period.setObjectName("mutedSubtext")
        hdr.addWidget(period)
        vbox.addLayout(hdr)

        self._chart_widget = _BarChartWidget()
        vbox.addWidget(self._chart_widget, 1)

        summary = QHBoxLayout(); summary.setSpacing(20)
        self._chart_summary = {}
        for key, lbl, clr in [
            ("total", "Total", "#2C3E50"),
            ("avg", "Average", "#388087"),
            ("peak", "Peak", "#5CB85C"),
        ]:
            col = QVBoxLayout(); col.setSpacing(2)
            v = QLabel("0")
            v.setStyleSheet(f"font-size:22px; font-weight:bold; color:{clr};")
            self._chart_summary[key] = v
            l = QLabel(lbl)
            l.setStyleSheet("font-size:11px; color:#7F8C8D;")
            col.addWidget(v); col.addWidget(l)
            summary.addLayout(col)
        summary.addStretch()
        vbox.addLayout(summary)
        return card

    # ── Helpers ───────────────────────────────────────────────────
    @staticmethod
    def _white_lbl(text, size, bold=False, alpha=1.0):
        l = QLabel(text)
        w = "bold" if bold else "normal"
        clr = f"rgba(255,255,255,{alpha})" if alpha < 1.0 else "#FFF"
        l.setStyleSheet(
            f"font-size:{size}px; font-weight:{w}; color:{clr}; background:transparent;")
        return l

    def _update_time(self):
        now = datetime.now()
        self._date_label.setText(now.strftime("%I:%M %p  \u2022  %B %d, %Y"))
        greeting = "Good Morning" if now.hour < 12 else (
            "Good Afternoon" if now.hour < 17 else "Good Evening")
        self._greeting_label.setText(f"{greeting}, {self._user_name}!")

    @staticmethod
    def _fmt_time(t):
        """Convert timedelta / time / str to readable AM/PM string."""
        if hasattr(t, "total_seconds"):
            s = int(t.total_seconds())
            h, rem = divmod(s, 3600); m = rem // 60
            return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"
        if hasattr(t, "strftime"):
            return t.strftime("%I:%M %p")
        return str(t)

    # ── Data refresh ──────────────────────────────────────────────
    def _refresh_kpis(self):
        s = self._backend.get_dashboard_summary() if self._backend else {}

        # Today's appointments
        self._kpi_labels["today_appts"].setText(str(s.get("today_appts", 0)))
        parts = []
        if s.get("today_confirmed"): parts.append(f"{s['today_confirmed']} confirmed")
        if s.get("today_pending"):   parts.append(f"{s['today_pending']} pending")
        if s.get("today_completed"): parts.append(f"{s['today_completed']} done")
        self._kpi_labels["today_appts_sub"].setText(
            ", ".join(parts) if parts else "No appointments")

        # Active patients
        pts = s.get("active_patients", 0)
        self._kpi_labels["active_patients"].setText(f"{pts:,}")
        nw = s.get("new_patients_week", 0)
        self._kpi_labels["active_patients_sub"].setText(
            f"+{nw} this week" if nw else "No new this week")

        # Today's revenue
        rev = s.get("today_revenue", 0)
        total_rev = s.get("total_revenue", 0)
        self._kpi_labels["today_revenue"].setText(
            f"\u20B1 {rev/1000:,.1f}K" if rev >= 1000 else f"\u20B1 {rev:,.0f}")
        self._kpi_labels["today_revenue_sub"].setText(
            f"\u20B1 {total_rev/1000:,.0f}K all time" if total_rev >= 1000 else
            f"\u20B1 {total_rev:,.0f} all time")

        # Active staff
        self._kpi_labels["active_staff"].setText(str(s.get("active_staff", 0)))
        self._kpi_labels["active_staff_sub"].setText("active employees")

    def _refresh_schedule(self):
        upcoming = self._backend.get_upcoming_appointments(5) if self._backend else []
        self._sched_badge.setText(f"{len(upcoming)} upcoming")
        self._sched_table.setRowCount(len(upcoming))
        for r, row in enumerate(upcoming):
            cells = [
                self._fmt_time(row.get("appointment_time", "")),
                row.get("patient_name", ""),
                (f"Dr. {row['doctor_name'].split()[-1]}"
                 if row.get("doctor_name") else ""),
                row.get("status", ""),
            ]
            for c, cell in enumerate(cells):
                item = QTableWidgetItem(cell)
                if c == 3:
                    clr = {"Confirmed": "#5CB85C", "Completed": "#388087",
                           "Cancelled": "#D9534F"}.get(cell, "#E8B931")
                    item.setForeground(QColor(clr))
                self._sched_table.setItem(r, c, item)

    def _refresh_chart(self):
        monthly = self._backend.get_patient_stats_monthly(6) if self._backend else []
        data = [(m["month_label"], m["visit_count"]) for m in monthly]
        self._chart_widget.set_data(data)
        total = sum(v for _, v in data)
        avg = total // len(data) if data else 0
        peak = max(v for _, v in data) if data else 0
        self._chart_summary["total"].setText(str(total))
        self._chart_summary["avg"].setText(str(avg))
        self._chart_summary["peak"].setText(str(peak))

    def refresh(self):
        self._refresh_kpis()
        self._refresh_schedule()
        self._refresh_chart()
