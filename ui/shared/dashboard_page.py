# Dashboard - KPI cards, schedule, trends

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QDialog, QDateEdit, QTextEdit, QFormLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDate, QSize
from PyQt6.QtGui import QColor
from ui.styles import (
    configure_table, make_page_layout, finish_page, make_card,
    make_read_only_table, ACTION_COLORS, status_color,
)
from ui.icons import get_icon
from ui.shared.chart_widgets import BarChartWidget


class DashboardPage(QWidget):
    """Hospital dashboard – KPI cards, schedule preview, monthly trends."""

    navigate_to = pyqtSignal(int)

    def __init__(self, user_name="Admin", backend=None, role="Admin", user_email=""):
        super().__init__()
        self._user_name = user_name
        self._backend = backend
        self._role = role
        self._user_email = user_email
        self._kpi_labels = {}
        self._build()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1_000)
        self._data_timer = QTimer(self)
        self._data_timer.timeout.connect(self.refresh)
        self._data_timer.start(10_000)

    # ── Layout ────────────────────────────────────────────────────
    def _build(self):
        scroll, lay = make_page_layout()

        lay.addWidget(self._build_banner())

        kpi_row = QHBoxLayout(); kpi_row.setSpacing(16)
        self._kpi_cards_data = [
            ("today_appts",     "Today's Appointments", "#388087"),
            ("active_patients", "Active Patients",      "#5CB85C"),
            ("today_revenue",   "Today's Revenue",      "#6FB3B8"),
            ("active_staff",    "Active Staff",         "#C2EDCE"),
        ]
        for key, title, color in self._kpi_cards_data:
            if self._role == "HR" and key in ("today_appts", "active_patients"):
                continue
            kpi_row.addWidget(self._make_kpi_card(key, title, color))
        lay.addLayout(kpi_row)

        act_row = QHBoxLayout(); act_row.setSpacing(12)
        quick_actions = [
            ("New Patient", "new_patient", 1), ("New Appointment", "calendar_plus", 2),
            ("Clinical Queue", "nav_clinical", 3), ("Analytics", "nav_analytics", 4),
        ]
        for text, icon_key, pi in quick_actions:
            if self._role == "Doctor" and pi in (1, 2):
                continue
            if self._role == "HR" and pi in (1, 2, 3, 4):
                continue
            if self._role == "Cashier" and pi in (1, 4):
                continue
            if self._role == "Receptionist" and pi == 4:
                continue
            btn = QPushButton(text)
            btn.setIcon(get_icon(icon_key))
            btn.setIconSize(QSize(18, 18))
            btn.setObjectName("actionBtn")
            btn.setMinimumHeight(44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, p=pi: self.navigate_to.emit(p))
            act_row.addWidget(btn)
        act_row.addStretch()
        lay.addLayout(act_row)

        if self._role not in ("HR",):
            leave_card = make_card()
            lv_lay = QVBoxLayout(leave_card)
            lv_lay.setContentsMargins(20, 18, 20, 14); lv_lay.setSpacing(12)

            lv_hdr = QHBoxLayout()
            lv_title = QLabel("My Leave Requests")
            lv_title.setObjectName("cardTitle")
            lv_hdr.addWidget(lv_title); lv_hdr.addStretch()
            req_btn = QPushButton("Request Leave")
            req_btn.setIcon(get_icon("edit"))
            req_btn.setIconSize(QSize(18, 18))
            req_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            req_btn.setObjectName("actionBtn")
            req_btn.setMinimumHeight(44)
            req_btn.clicked.connect(self._on_request_leave)
            lv_hdr.addWidget(req_btn)
            lv_lay.addLayout(lv_hdr)

            self._my_leave_table = make_read_only_table(
                ["From", "Until", "Reason", "Status", "HR Note", "Submitted"],
                min_h=140, max_h=220, row_h=44)
            lv_lay.addWidget(self._my_leave_table)
            lay.addWidget(leave_card)

        cols = QHBoxLayout(); cols.setSpacing(16)
        cols.addWidget(self._schedule_card(), 3)
        cols.addWidget(self._chart_card(), 2)
        lay.addLayout(cols)

        if self._role in ("Admin",):
            lay.addWidget(self._recent_activity_card())

        lay.addStretch()
        finish_page(self, scroll)
        self.refresh()

    def _build_banner(self):
        # Outer wrapper holds the drop-shadow so it doesn't affect text rendering
        wrapper = QWidget()
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper_lay = QVBoxLayout(wrapper)
        wrapper_lay.setContentsMargins(0, 0, 0, 0)

        banner = QFrame()
        banner.setObjectName("pageBanner")
        banner.setFrameShape(QFrame.Shape.NoFrame)
        banner.setMinimumHeight(160)

        vl = QVBoxLayout(banner)
        vl.setContentsMargins(36, 34, 36, 34); vl.setSpacing(6)
        now = datetime.now()
        greeting = "Good Morning" if now.hour < 12 else (
            "Good Afternoon" if now.hour < 17 else "Good Evening")

        self._greeting_label = QLabel(f"{greeting}, {self._user_name}!")
        self._greeting_label.setObjectName("bannerTitle")
        vl.addWidget(self._greeting_label)

        self._date_label = QLabel(
            now.strftime("%I:%M %p  \u2022  %B %d, %Y"))
        self._date_label.setObjectName("bannerDate")
        vl.addWidget(self._date_label)

        # Thin accent separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(255,255,255,0.25); border: none;")
        vl.addWidget(sep)

        desc = QLabel("Here's what's happening at the hospital today.")
        desc.setObjectName("bannerSubtitle")
        vl.addWidget(desc)

        wrapper_lay.addWidget(banner)
        return wrapper

    def _make_kpi_card(self, key, title, color):
        card = make_card(min_height=110)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(18, 14, 18, 14); vbox.setSpacing(4)

        strip = QFrame(); strip.setFixedHeight(3)
        strip.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
        vbox.addWidget(strip)

        val = QLabel("\u2013")
        val.setObjectName("statValue")
        vbox.addWidget(val)
        self._kpi_labels[key] = val

        lbl = QLabel(title)
        lbl.setObjectName("statLabel")
        vbox.addWidget(lbl)

        delta_lbl = QLabel("")
        delta_lbl.setStyleSheet("font-size: 11px; font-weight: bold;")
        vbox.addWidget(delta_lbl)
        self._kpi_labels[f"{key}_sub"] = delta_lbl

        return card

    def _schedule_card(self):
        card = make_card()
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)

        hdr = QHBoxLayout()
        title = QLabel("Today's Schedule")
        title.setObjectName("cardTitle")
        hdr.addWidget(title); hdr.addStretch()
        self._sched_badge = QLabel("0 upcoming")
        self._sched_badge.setObjectName("pillBadge")
        hdr.addWidget(self._sched_badge)
        vbox.addLayout(hdr)

        self._sched_table = make_read_only_table(
            ["Time", "Patient", "Doctor", "Status"],
            min_h=240, max_h=300, row_h=44)
        vbox.addWidget(self._sched_table)

        view_all = QPushButton("View all appointments \u2192")
        view_all.setObjectName("linkBtn")
        view_all.setCursor(Qt.CursorShape.PointingHandCursor)
        view_all.clicked.connect(lambda: self.navigate_to.emit(2))
        vbox.addWidget(view_all)
        return card

    def _chart_card(self):
        card = make_card()
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)

        hdr = QHBoxLayout()
        title = QLabel("Monthly Visits"); title.setObjectName("cardTitle")
        hdr.addWidget(title); hdr.addStretch()
        period = QLabel("Last 6 Months"); period.setObjectName("mutedSubtext")
        hdr.addWidget(period)
        vbox.addLayout(hdr)

        self._chart_widget = BarChartWidget()
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

    def _recent_activity_card(self):
        card = make_card()
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(20, 18, 20, 14); vbox.setSpacing(12)

        hdr = QHBoxLayout()
        title = QLabel("Recent Activity"); title.setObjectName("cardTitle")
        hdr.addWidget(title); hdr.addStretch()
        self._activity_badge = QLabel("0 entries")
        self._activity_badge.setObjectName("pillBadge")
        hdr.addWidget(self._activity_badge)
        vbox.addLayout(hdr)

        self._activity_table = make_read_only_table(
            ["Time", "User", "Action", "Type", "Detail"],
            min_h=240, max_h=340, row_h=44)
        vbox.addWidget(self._activity_table)
        return card

    # ── Helpers ───────────────────────────────────────────────────
    def _update_time(self):
        now = datetime.now()
        self._date_label.setText(now.strftime("%I:%M %p  \u2022  %B %d, %Y"))
        greeting = "Good Morning" if now.hour < 12 else (
            "Good Afternoon" if now.hour < 17 else "Good Evening")
        self._greeting_label.setText(f"{greeting}, {self._user_name}!")

    @staticmethod
    def _fmt_time(t):
        if hasattr(t, "total_seconds"):
            s = int(t.total_seconds())
            h, rem = divmod(s, 3600); m = rem // 60
            return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"
        if hasattr(t, "strftime"):
            return t.strftime("%I:%M %p")
        return str(t)

    # ── Data refresh ──────────────────────────────────────────────
    def _refresh_kpis(self):
        doc_email = self._user_email if self._role == "Doctor" else None
        s = self._backend.get_dashboard_summary(doctor_email=doc_email) if self._backend else {}
        cmp = self._backend.get_period_comparison(doctor_email=doc_email) if self._backend else {}

        if "today_appts" in self._kpi_labels:
            today_appts = s.get("today_appts", 0)
            self._kpi_labels["today_appts"].setText(str(today_appts))
            appts_delta = cmp.get("appts_delta", 0)
            if appts_delta is not None and appts_delta != 0:
                arrow = "▲" if appts_delta >= 0 else "▼"
                clr = "#5CB85C" if appts_delta >= 0 else "#D9534F"
                self._kpi_labels["today_appts_sub"].setText(
                    f"{arrow} {abs(appts_delta):.1f}% vs last month")
                self._kpi_labels["today_appts_sub"].setStyleSheet(
                    f"color: {clr}; font-size: 11px; font-weight: bold;")
            else:
                self._kpi_labels["today_appts_sub"].setText("")

        if "active_patients" in self._kpi_labels:
            pts = s.get("active_patients", 0)
            self._kpi_labels["active_patients"].setText(f"{pts:,}")
            pts_delta = cmp.get("patients_delta", 0)
            if pts_delta is not None and pts_delta != 0:
                arrow = "▲" if pts_delta >= 0 else "▼"
                clr = "#5CB85C" if pts_delta >= 0 else "#D9534F"
                self._kpi_labels["active_patients_sub"].setText(
                    f"{arrow} {abs(pts_delta):.1f}% vs last month")
                self._kpi_labels["active_patients_sub"].setStyleSheet(
                    f"color: {clr}; font-size: 11px; font-weight: bold;")
            else:
                self._kpi_labels["active_patients_sub"].setText("")

        rev = s.get("today_revenue", 0)
        self._kpi_labels["today_revenue"].setText(f"\u20B1 {rev:,.0f}")
        rev_delta = cmp.get("revenue_delta", 0)
        if rev_delta is not None and rev_delta != 0:
            arrow = "▲" if rev_delta >= 0 else "▼"
            clr = "#5CB85C" if rev_delta >= 0 else "#D9534F"
            self._kpi_labels["today_revenue_sub"].setText(
                f"{arrow} {abs(rev_delta):.1f}% vs last month")
            self._kpi_labels["today_revenue_sub"].setStyleSheet(
                f"color: {clr}; font-size: 11px; font-weight: bold;")
        else:
            self._kpi_labels["today_revenue_sub"].setText("")

        self._kpi_labels["active_staff"].setText(str(s.get("active_staff", 0)))
        self._kpi_labels["active_staff_sub"].setText("")

    def _refresh_schedule(self):
        doc_email = self._user_email if self._role == "Doctor" else None
        upcoming = self._backend.get_upcoming_appointments(5, doctor_email=doc_email) if self._backend else []
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
                    item.setForeground(QColor(status_color(cell)))
                self._sched_table.setItem(r, c, item)

    def _refresh_chart(self):
        doc_email = self._user_email if self._role == "Doctor" else None
        monthly = self._backend.get_patient_stats_monthly(6, doctor_email=doc_email) if self._backend else []
        data = [(m["month_label"], m["visit_count"]) for m in monthly]
        self._chart_widget.set_data(data)
        total = sum(v for _, v in data)
        avg = total // len(data) if data else 0
        peak = max(v for _, v in data) if data else 0
        self._chart_summary["total"].setText(str(total))
        self._chart_summary["avg"].setText(str(avg))
        self._chart_summary["peak"].setText(str(peak))

    def _refresh_recent_activity(self):
        if not self._backend or not hasattr(self, "_activity_table"):
            return
        rows = self._backend.get_activity_log(limit=8) or []
        self._activity_badge.setText(f"{len(rows)} recent")
        self._activity_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            ts = row.get("created_at", "")
            if hasattr(ts, "strftime"):
                ts = ts.strftime("%I:%M %p")
            else:
                ts = str(ts)[-8:]
            cells = [
                ts,
                row.get("user_email", "").split("@")[0],
                row.get("action", ""),
                row.get("record_type", ""),
                row.get("record_detail", "") or "",
            ]
            for c, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if c == 2:
                    clr = ACTION_COLORS.get(val, "#2C3E50")
                    item.setForeground(QColor(clr))
                self._activity_table.setItem(r, c, item)

    def refresh(self):
        if not self.isVisible():
            return
        self._refresh_kpis()
        self._refresh_schedule()
        self._refresh_chart()
        if self._role in ("Admin",):
            self._refresh_recent_activity()
        if self._role not in ("HR",):
            self._refresh_my_leave()

    # ── Leave Request (for non-admin/non-HR roles) ────────────────
    def _get_my_employee_id(self):
        if not self._backend or not self._user_email:
            return None
        return self._backend.get_employee_id_by_email(self._user_email)

    def _refresh_my_leave(self):
        emp_id = self._get_my_employee_id()
        if not emp_id or not hasattr(self, "_my_leave_table"):
            return
        reqs = self._backend.get_my_leave_requests(emp_id) or []
        self._my_leave_table.setRowCount(0)
        for req in reqs:
            r = self._my_leave_table.rowCount()
            self._my_leave_table.insertRow(r)
            self._my_leave_table.setItem(r, 0, QTableWidgetItem(str(req.get("leave_from", ""))))
            self._my_leave_table.setItem(r, 1, QTableWidgetItem(str(req.get("leave_until", ""))))
            self._my_leave_table.setItem(r, 2, QTableWidgetItem(req.get("reason", "")))
            status_item = QTableWidgetItem(req.get("status", ""))
            status_item.setForeground(QColor(status_color(req.get("status", ""))))
            self._my_leave_table.setItem(r, 3, status_item)
            self._my_leave_table.setItem(r, 4, QTableWidgetItem(req.get("hr_note", "") or ""))
            created = str(req.get("created_at", ""))
            self._my_leave_table.setItem(r, 5, QTableWidgetItem(created))

    def _on_request_leave(self):
        emp_id = self._get_my_employee_id()
        if not emp_id:
            QMessageBox.warning(self, "Error", "Could not find your employee record.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Request Leave")
        dlg.setMinimumWidth(460)
        d_lay = QVBoxLayout(dlg)
        d_lay.setSpacing(14); d_lay.setContentsMargins(28, 24, 28, 24)

        title = QLabel("Submit Leave Request")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #388087;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d_lay.addWidget(title)
        d_lay.addSpacing(8)

        form = QFormLayout(); form.setSpacing(12)

        from_date = QDateEdit()
        from_date.setCalendarPopup(True)
        from_date.setDate(QDate.currentDate().addDays(1))
        from_date.setMinimumDate(QDate.currentDate().addDays(1))
        from_date.setObjectName("formCombo"); from_date.setMinimumHeight(38)

        until_date = QDateEdit()
        until_date.setCalendarPopup(True)
        until_date.setDate(QDate.currentDate().addDays(7))
        until_date.setMinimumDate(QDate.currentDate().addDays(1))
        until_date.setObjectName("formCombo"); until_date.setMinimumHeight(38)

        reason_edit = QTextEdit()
        reason_edit.setMaximumHeight(100)
        reason_edit.setPlaceholderText("Reason for leave request…")
        reason_edit.setStyleSheet(
            "QTextEdit { padding: 10px; border: 2px solid #BADFE7;"
            " border-radius: 10px; font-size: 13px; background: #FFF; }")

        form.addRow("Leave From:", from_date)
        form.addRow("Leave Until:", until_date)
        form.addRow("Reason:", reason_edit)
        d_lay.addLayout(form)

        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setMinimumHeight(36)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #6c757d; color: #FFF; border: none;"
            " border-radius: 4px; padding: 8px 24px; font-size: 13px; font-weight: bold; }")
        cancel_btn.clicked.connect(dlg.reject)
        submit_btn = QPushButton("Submit Request"); submit_btn.setMinimumHeight(36)
        submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        submit_btn.setStyleSheet(
            "QPushButton { background-color: #388087; color: #FFF; border: none;"
            " border-radius: 4px; padding: 8px 24px; font-size: 13px; font-weight: bold; }"
            " QPushButton:hover { background-color: #2C6A70; }")

        def _do_submit():
            reason_text = reason_edit.toPlainText().strip()
            if not reason_text:
                QMessageBox.warning(dlg, "Validation", "Please enter a reason for your leave request.")
                return
            f_date = from_date.date()
            u_date = until_date.date()
            if u_date < f_date:
                QMessageBox.warning(dlg, "Validation", "'Leave Until' must be on or after 'Leave From'.")
                return
            dlg.accept()

        submit_btn.clicked.connect(_do_submit)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(submit_btn)
        d_lay.addLayout(btn_row)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        leave_from = from_date.date().toString("yyyy-MM-dd")
        leave_until = until_date.date().toString("yyyy-MM-dd")
        reason = reason_edit.toPlainText().strip()

        ok = self._backend.submit_leave_request(emp_id, leave_from, leave_until, reason)
        if ok is True:
            QMessageBox.information(self, "Submitted",
                                    "Your leave request has been submitted.\n"
                                    "You will be notified when HR makes a decision.")
            self._refresh_my_leave()
        else:
            err = ok if isinstance(ok, str) else ""
            QMessageBox.warning(self, "Error", f"Failed to submit request.\n{err}")
