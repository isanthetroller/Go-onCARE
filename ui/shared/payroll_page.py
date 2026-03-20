# Payroll page - Finance approves paycheck requests, HR submits/disburses

from calendar import monthrange
from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame,
    QComboBox, QDialog, QMessageBox, QTextEdit, QLineEdit, QDateEdit,
    QFormLayout, QDialogButtonBox, QStackedWidget, QSpinBox,
)
from PyQt6.QtCore import Qt, QDate, QTimer, QSize
from PyQt6.QtGui import QColor, QFont
from ui.styles import (
    make_page_layout, finish_page, make_banner, make_card, make_stat_card,
    make_read_only_table, make_action_table, make_table_btn, make_table_btn_danger,
    status_color, make_action_cell, TAB_ACTIVE, TAB_INACTIVE, style_dialog_btns,
    format_timedelta,
)
from ui.icons import get_icon


class PayrollPage(QWidget):

    def __init__(self, backend=None, role: str = "Finance", user_email: str = ""):
        super().__init__()
        self._backend = backend
        self._role = role
        self._user_email = user_email
        self._requests: list[dict] = []
        self._history: list[dict] = []
        if self._role == "Doctor":
            self._build_doctor()
        else:
            self._build()
        self._load_data()
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_data)
        self._refresh_timer.start(10_000)

    # ── Doctor-only build: read-only history view ────────────────
    def _build_doctor(self):
        scroll, lay = make_page_layout()
        lay.setSpacing(16)

        lay.addWidget(make_banner(
            "My Paychecks",
            "View your paycheck history and upcoming pay schedule"))

        # Next paycheck info card
        self._next_pay_card = make_card()
        npc_lay = QVBoxLayout(self._next_pay_card)
        npc_lay.setContentsMargins(20, 16, 20, 16)
        npc_lay.setSpacing(8)
        npc_title = QLabel("Next Paycheck")
        npc_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        npc_lay.addWidget(npc_title)
        self._next_pay_info = QLabel("Loading...")
        self._next_pay_info.setStyleSheet("font-size: 13px; color: #555;")
        self._next_pay_info.setWordWrap(True)
        npc_lay.addWidget(self._next_pay_info)
        lay.addWidget(self._next_pay_card)

        # Summary
        self._history_summary = QLabel()
        self._history_summary.setObjectName("mutedSummary")
        lay.addWidget(self._history_summary)

        # History table
        cols = ["Period", "Gross", "SSS", "PhilHealth", "Hospital",
                "Net Amount", "Status", "Requested By", "Disbursed At"]
        self._history_table = make_read_only_table(cols, min_h=350)
        lay.addWidget(self._history_table)

        lay.addStretch()
        finish_page(self, scroll)

    def _load_data(self):
        if not self.isVisible():
            return
        if not self._backend:
            return
        if self._role == "Doctor":
            self._load_doctor_history()
            return
        filt = self._status_filter.currentText()
        if filt == "Pending":
            self._requests = self._backend.get_pending_paycheck_requests() or []
        else:
            all_reqs = self._backend.get_all_paycheck_requests() or []
            if filt == "All":
                self._requests = all_reqs
            else:
                self._requests = [r for r in all_reqs if r.get("status") == filt]
        self._populate_table()

    def _load_doctor_history(self):
        emp_id = self._backend.get_employee_id_by_email(self._user_email)
        if not emp_id:
            self._next_pay_info.setText("Could not find your employee record.")
            return
        self._history = self._backend.get_paycheck_history(emp_id) or []
        emp = self._backend.get_employee_by_id(emp_id)
        salary = float(emp.get("salary", 0) or 0) if emp else 0

        # Next paycheck calculation
        last = self._backend.get_last_disbursed_paycheck(emp_id)
        self._update_next_pay_label(last, salary)

        # Populate history table
        self._history_table.setRowCount(0)
        for req in self._history:
            r = self._history_table.rowCount()
            self._history_table.insertRow(r)
            gross = float(req.get("amount", 0) or 0)
            sss = float(req.get("sss_deduction", 0) or 0)
            phil = float(req.get("philhealth_deduction", 0) or 0)
            hosp = float(req.get("hospital_share", 0) or 0)
            net = float(req.get("net_amount", 0) or 0)
            period = f"{req.get('period_from', '')} to {req.get('period_until', '')}"
            disbursed_raw = req.get("disbursed_at")
            if disbursed_raw:
                disbursed = disbursed_raw.strftime("%Y-%m-%d %I:%M %p") if hasattr(disbursed_raw, "strftime") else str(disbursed_raw)
            else:
                disbursed = "—"
            status = req.get("status", "")
            values = [period, f"₱{gross:,.2f}", f"₱{sss:,.2f}", f"₱{phil:,.2f}",
                      f"₱{hosp:,.2f}", f"₱{net:,.2f}", status,
                      req.get("requested_by_name", ""), disbursed]
            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                if c == 6:
                    item.setForeground(QColor(status_color(val)))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                if c in (1, 5):
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self._history_table.setItem(r, c, item)

        total = len(self._history)
        disbursed_count = sum(1 for h in self._history if h.get("status") == "Disbursed")
        self._history_summary.setText(
            f"Showing {total} paycheck{'s' if total != 1 else ''} · "
            f"{disbursed_count} disbursed")

    def _update_next_pay_label(self, last_paycheck, salary):
        today = date.today()
        if last_paycheck and last_paycheck.get("period_until"):
            last_until = last_paycheck["period_until"]
            if isinstance(last_until, str):
                from datetime import datetime
                last_until = datetime.strptime(last_until, "%Y-%m-%d").date()
            next_from = last_until + timedelta(days=1)
            # Next period ends at end of next_from's month
            _, days_in_month = monthrange(next_from.year, next_from.month)
            next_until = date(next_from.year, next_from.month, days_in_month)
            last_net = float(last_paycheck.get("net_amount", 0) or 0)
            self._next_pay_info.setText(
                f"Last paycheck disbursed: <b>{last_paycheck.get('disbursed_at', '—')}</b><br>"
                f"Last period: {last_paycheck.get('period_from', '')} to {last_paycheck.get('period_until', '')}<br>"
                f"Last net payout: <b>₱{last_net:,.2f}</b><br><br>"
                f"Next expected period: <b>{next_from}</b> to <b>{next_until}</b><br>"
                f"Base salary: <b>₱{salary:,.2f}</b>")
        else:
            # No previous paycheck
            first_of_month = date(today.year, today.month, 1)
            _, days_in_month = monthrange(today.year, today.month)
            end_of_month = date(today.year, today.month, days_in_month)
            self._next_pay_info.setText(
                f"No previous paychecks found.<br>"
                f"Expected first period: <b>{first_of_month}</b> to <b>{end_of_month}</b><br>"
                f"Base salary: <b>₱{salary:,.2f}</b>")

    def _build(self):
        scroll, lay = make_page_layout()
        lay.setSpacing(16)

        if self._role == "Finance":
            title = "Payroll Approvals"
            subtitle = "Review and approve paycheck requests from HR"
        else:
            title = "Paycheck Requests"
            subtitle = "Submit paycheck requests and track disbursements"

        # Banner
        banner_kwargs = {}
        if self._role in ("HR", "Admin"):
            banner_kwargs = {"btn_text": "+  Request Paycheck", "btn_slot": self._on_new_request}
        lay.addWidget(make_banner(title, subtitle, **banner_kwargs))

        # Partial paycheck button for HR/Admin
        if self._role in ("HR", "Admin"):
            partial_card = make_card()
            partial_lay = QHBoxLayout(partial_card)
            partial_lay.setContentsMargins(16, 10, 16, 10)
            partial_info = QLabel("Submit a prorated paycheck based on days worked in a period:")
            partial_info.setStyleSheet("font-size: 12px; color: #555;")
            partial_lay.addWidget(partial_info)
            partial_lay.addStretch()
            partial_btn = QPushButton("Partial Paycheck")
            partial_btn.setMinimumHeight(34)
            partial_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            partial_btn.setStyleSheet(
                "QPushButton { background-color: #E8B931; color: #FFF; border: none;"
                " border-radius: 8px; padding: 8px 20px; font-size: 12px; font-weight: bold; }"
                " QPushButton:hover { background-color: #D4A72C; }")
            partial_btn.clicked.connect(self._on_partial_request)
            partial_lay.addWidget(partial_btn)
            lay.addWidget(partial_card)

        # Filter bar
        bar_card = make_card()
        bar = QHBoxLayout(bar_card)
        bar.setContentsMargins(16, 12, 16, 12)
        bar.setSpacing(12)

        bar.addWidget(QLabel("Status:"))
        self._status_filter = QComboBox()
        self._status_filter.setObjectName("formCombo")
        self._status_filter.setMinimumHeight(36)
        if self._role == "Finance":
            self._status_filter.addItems(["Pending", "All", "Approved", "Rejected", "Disbursed"])
        else:
            self._status_filter.addItems(["All", "Pending", "Approved", "Rejected", "Disbursed"])
        self._status_filter.currentTextChanged.connect(lambda _: self._load_data())
        bar.addWidget(self._status_filter)

        self._search = QLineEdit()
        self._search.setObjectName("formInput")
        self._search.setPlaceholderText("Search by employee name...")
        self._search.setMinimumHeight(36)
        self._search.setMaximumWidth(250)
        self._search.textChanged.connect(self._apply_filters)
        bar.addWidget(self._search)

        bar.addWidget(QLabel("Role:"))
        self._role_filter = QComboBox()
        self._role_filter.setObjectName("formCombo")
        self._role_filter.setMinimumHeight(36)
        self._role_filter.addItems(["All Roles", "Doctor", "Nurse", "Receptionist", "Admin", "HR", "Finance"])
        self._role_filter.currentTextChanged.connect(lambda _: self._apply_filters())
        bar.addWidget(self._role_filter)

        bar.addWidget(QLabel("Department:"))
        self._dept_filter = QComboBox()
        self._dept_filter.setObjectName("formCombo")
        self._dept_filter.setMinimumHeight(36)
        self._dept_filter.addItems([
            "All Departments", "General Medicine", "Cardiology", "Dentistry",
            "Pediatrics", "Laboratory", "Front Desk", "Management", "Pharmacy",
            "Human Resources",
        ])
        self._dept_filter.currentTextChanged.connect(lambda _: self._apply_filters())
        bar.addWidget(self._dept_filter)

        bar.addStretch()

        lay.addWidget(bar_card)

        # Summary label
        self._summary = QLabel()
        self._summary.setObjectName("mutedSummary")
        lay.addWidget(self._summary)

        # Table
        cols = ["Employee", "Role", "Department", "Gross", "SSS", "PhilHealth",
                "Hospital", "Net Amount", "Period", "Requested By", "Status", "Actions"]
        self._table = make_action_table(cols, min_h=400, row_h=48, action_col_width=280)
        lay.addWidget(self._table)

        # ── Employee Paycheck History Section ─────────────────────
        hist_card = make_card()
        hist_lay = QVBoxLayout(hist_card)
        hist_lay.setContentsMargins(20, 16, 20, 16)
        hist_lay.setSpacing(10)

        hist_header = QHBoxLayout()
        hist_title = QLabel("Employee Paycheck History")
        hist_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        hist_header.addWidget(hist_title)
        hist_header.addStretch()

        hist_header.addWidget(QLabel("Employee:"))
        self._hist_emp_combo = QComboBox()
        self._hist_emp_combo.setObjectName("formCombo")
        self._hist_emp_combo.setMinimumHeight(36)
        self._hist_emp_combo.setMinimumWidth(250)
        self._hist_emp_combo.currentIndexChanged.connect(self._load_employee_history)
        hist_header.addWidget(self._hist_emp_combo)
        hist_lay.addLayout(hist_header)

        # Next paycheck info for selected employee
        self._hist_next_pay = QLabel("")
        self._hist_next_pay.setStyleSheet("font-size: 12px; color: #555; padding: 4px 0;")
        self._hist_next_pay.setWordWrap(True)
        hist_lay.addWidget(self._hist_next_pay)

        self._hist_summary = QLabel()
        self._hist_summary.setObjectName("mutedSummary")
        hist_lay.addWidget(self._hist_summary)

        hist_cols = ["Period", "Gross", "SSS", "PhilHealth", "Hospital",
                     "Net Amount", "Status", "Requested By", "Disbursed At"]
        self._hist_table = make_read_only_table(hist_cols, min_h=250)
        hist_lay.addWidget(self._hist_table)

        lay.addWidget(hist_card)

        lay.addStretch()
        finish_page(self, scroll)

        # Load employee list for history combo
        self._populate_hist_employees()

    def _populate_table(self):
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)
        for req in self._requests:
            r = self._table.rowCount()
            self._table.insertRow(r)

            gross = float(req.get("amount", 0) or 0)
            sss = float(req.get("sss_deduction", 0) or 0)
            phil = float(req.get("philhealth_deduction", 0) or 0)
            hosp = float(req.get("hospital_share", 0) or 0)
            net = float(req.get("net_amount", 0) or 0)
            period = f"{req.get('period_from', '')} to {req.get('period_until', '')}"
            status = req.get("status", "")

            values = [
                req.get("employee_name", ""),
                req.get("role_name", ""),
                req.get("department_name", ""),
                f"₱{gross:,.2f}",
                f"₱{sss:,.2f}",
                f"₱{phil:,.2f}",
                f"₱{hosp:,.2f}",
                f"₱{net:,.2f}",
                period,
                req.get("requested_by_name", ""),
                status,
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                if c == 10:  # Status column
                    item.setForeground(QColor(status_color(val)))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                if c in (3, 7):  # Gross and Net bold
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self._table.setItem(r, c, item)

            # Action buttons based on role and status
            parts = []
            if self._role == "Finance" and status == "Pending":
                review_btn = make_table_btn("Review")
                review_btn.clicked.connect(lambda checked, ri=r: self._on_review(ri))
                parts.append(review_btn)
                approve_btn = make_table_btn("Approve")
                approve_btn.setObjectName("tblSuccessBtn")
                approve_btn.clicked.connect(lambda checked, ri=r: self._on_approve(ri))
                parts.append(approve_btn)
                reject_btn = make_table_btn_danger("Reject")
                reject_btn.clicked.connect(lambda checked, ri=r: self._on_reject(ri))
                parts.append(reject_btn)
            elif self._role == "HR" and status == "Approved":
                disburse_btn = make_table_btn("Disburse")
                disburse_btn.setObjectName("tblSuccessBtn")
                disburse_btn.clicked.connect(lambda checked, ri=r: self._on_disburse(ri))
                parts.append(disburse_btn)
            elif self._role == "Admin" and status == "Approved":
                lbl = QLabel("Awaiting HR")
                lbl.setStyleSheet("font-size: 11px; color: #7F8C8D;")
                parts.append(lbl)
            elif self._role in ("HR", "Admin") and status == "Pending":
                review_btn = make_table_btn("Review")
                review_btn.clicked.connect(lambda checked, ri=r: self._on_review(ri))
                parts.append(review_btn)

            if status in ("Approved", "Rejected", "Disbursed"):
                view_btn = make_table_btn("Details")
                view_btn.clicked.connect(lambda checked, ri=r: self._on_view_details(ri))
                parts.append(view_btn)

            if parts:
                self._table.setCellWidget(r, 11, make_action_cell(*parts))

        total = len(self._requests)
        self._summary.setText(f"Showing {total} request{'s' if total != 1 else ''}")
        self._apply_filters()

    def _apply_filters(self, _=None):
        text = self._search.text().strip().lower()
        role = self._role_filter.currentText()
        dept = self._dept_filter.currentText()
        for r in range(self._table.rowCount()):
            text_match = True
            if text:
                name = self._table.item(r, 0)
                text_match = name and text in name.text().lower()
            role_match = role == "All Roles" or (self._table.item(r, 1) and self._table.item(r, 1).text() == role)
            dept_match = dept == "All Departments" or (self._table.item(r, 2) and self._table.item(r, 2).text() == dept)
            self._table.setRowHidden(r, not (text_match and role_match and dept_match))

    # ── Actions ──────────────────────────────────────────────────

    def _on_new_request(self):
        """HR submits a paycheck request."""
        dlg = _PaycheckRequestDialog(self, backend=self._backend)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            hr_emp_id = self._backend.get_employee_id_by_email(self._user_email)
            if not hr_emp_id:
                QMessageBox.warning(self, "Error", "Could not determine your employee ID.")
                return
            ok = self._backend.submit_paycheck_request(
                data["employee_id"], data["amount"],
                data["period_from"], data["period_until"], hr_emp_id)
            if ok is True:
                QMessageBox.information(self, "Success",
                    f"Paycheck request submitted for {data['employee_name']}.")
                self._load_data()
            else:
                err = ok if isinstance(ok, str) else ""
                QMessageBox.warning(self, "Error", f"Failed to submit request.\n{err}")

    def _on_review(self, row: int):
        """Show employee's activity for the paycheck period."""
        if row >= len(self._requests):
            return
        req = self._requests[row]
        emp_id = req.get("employee_id")
        emp_name = req.get("employee_name", "")
        period_from = str(req.get("period_from", ""))
        period_until = str(req.get("period_until", ""))

        activities = self._backend.get_employee_activity_for_period(
            emp_id, period_from, period_until) or []

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Activity Review — {emp_name}")
        dlg.setMinimumSize(750, 500)
        d_lay = QVBoxLayout(dlg)
        d_lay.setSpacing(14)
        d_lay.setContentsMargins(24, 20, 24, 20)

        # Header
        header = QLabel(f"<b>{emp_name}</b> — {req.get('role_name', '')} | "
                        f"{req.get('department_name', '')}")
        header.setStyleSheet("font-size: 14px; color: #2C3E50;")
        d_lay.addWidget(header)

        amount = float(req.get("amount", 0) or 0)
        salary = float(req.get("salary", 0) or 0)
        sss = float(req.get("sss_deduction", 0) or 0)
        phil = float(req.get("philhealth_deduction", 0) or 0)
        hosp = float(req.get("hospital_share", 0) or 0)
        net = float(req.get("net_amount", 0) or 0)
        info = QLabel(f"Period: <b>{period_from}</b> to <b>{period_until}</b> | "
                      f"Gross: <b>₱{amount:,.2f}</b> | "
                      f"Base Salary: ₱{salary:,.2f}")
        info.setStyleSheet("font-size: 13px; color: #555;")
        d_lay.addWidget(info)

        # Deduction breakdown
        ded_text = (
            f"<b>Deductions:</b>  SSS: ₱{sss:,.2f}  |  PhilHealth: ₱{phil:,.2f}  |  "
            f"Hospital Share: ₱{hosp:,.2f}  →  <b style='color:#388087;'>Net: ₱{net:,.2f}</b>"
        )
        ded_lbl = QLabel(ded_text)
        ded_lbl.setStyleSheet("font-size: 13px; color: #2C3E50; padding: 4px 0;")
        d_lay.addWidget(ded_lbl)
        d_lay.addWidget(info)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #BADFE7;")
        d_lay.addWidget(sep)

        if activities:
            completed = sum(1 for a in activities if a.get("status") == "Completed")
            total_rev = sum(float(a.get("price", 0) or 0) for a in activities if a.get("status") == "Completed")
            summary = QLabel(f"<b>{len(activities)}</b> appointments | "
                             f"<b>{completed}</b> completed | "
                             f"Revenue: <b>₱{total_rev:,.2f}</b>")
            summary.setStyleSheet("font-size: 13px; color: #388087; font-weight: bold;")
            d_lay.addWidget(summary)

            tbl = QTableWidget(len(activities), 6)
            tbl.setHorizontalHeaderLabels(["Date", "Time", "Patient", "Service", "Price", "Status"])
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tbl.verticalHeader().setVisible(False)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            tbl.setAlternatingRowColors(True)
            tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

            for i, act in enumerate(activities):
                appt_date = str(act.get("appointment_date", ""))
                appt_time = act.get("appointment_time", "")
                if hasattr(appt_time, "total_seconds"):
                    appt_time = format_timedelta(appt_time)
                elif hasattr(appt_time, "strftime"):
                    appt_time = appt_time.strftime("%H:%M")
                else:
                    appt_time = str(appt_time) if appt_time else ""
                price = float(act.get("price", 0) or 0)
                tbl.setItem(i, 0, QTableWidgetItem(appt_date))
                tbl.setItem(i, 1, QTableWidgetItem(str(appt_time)))
                tbl.setItem(i, 2, QTableWidgetItem(act.get("patient_name", "")))
                tbl.setItem(i, 3, QTableWidgetItem(act.get("service_name", "")))
                tbl.setItem(i, 4, QTableWidgetItem(f"₱{price:,.2f}"))
                status_item = QTableWidgetItem(act.get("status", ""))
                status_item.setForeground(QColor(status_color(act.get("status", ""))))
                tbl.setItem(i, 5, status_item)
            d_lay.addWidget(tbl)
        else:
            no_data = QLabel("No appointments found for this period.")
            no_data.setStyleSheet("font-size: 13px; color: #7F8C8D; padding: 20px;")
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            d_lay.addWidget(no_data)

        d_lay.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("dialogCancelBtn")
        close_btn.setMinimumHeight(36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(close_btn)
        d_lay.addLayout(btn_row)

        dlg.exec()

    def _on_approve(self, row: int):
        if row >= len(self._requests):
            return
        req = self._requests[row]
        emp_name = req.get("employee_name", "")
        amount = float(req.get("amount", 0) or 0)
        sss = float(req.get("sss_deduction", 0) or 0)
        phil = float(req.get("philhealth_deduction", 0) or 0)
        hosp = float(req.get("hospital_share", 0) or 0)
        net = float(req.get("net_amount", 0) or 0)

        reply = QMessageBox.question(
            self, "Approve Paycheck",
            f"Approve paycheck for {emp_name}?\n\n"
            f"  Gross Amount:    ₱{amount:,.2f}\n"
            f"  SSS Deduction:   ₱{sss:,.2f}\n"
            f"  PhilHealth:      ₱{phil:,.2f}\n"
            f"  Hospital Share:  ₱{hosp:,.2f}\n"
            f"  ─────────────\n"
            f"  Net Payout:      ₱{net:,.2f}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        fin_emp_id = self._backend.get_employee_id_by_email(self._user_email)
        ok = self._backend.approve_paycheck_request(
            req.get("request_id"), fin_emp_id)
        if ok is True:
            QMessageBox.information(self, "Approved",
                f"Paycheck for {emp_name} has been approved.\nHR will be notified.")
            self._load_data()
        else:
            err = ok if isinstance(ok, str) else ""
            QMessageBox.warning(self, "Error", f"Failed to approve.\n{err}")

    def _on_reject(self, row: int):
        if row >= len(self._requests):
            return
        req = self._requests[row]
        emp_name = req.get("employee_name", "")

        dlg = QDialog(self)
        dlg.setWindowTitle("Reject Paycheck Request")
        dlg.setMinimumWidth(450)
        d_lay = QVBoxLayout(dlg)
        d_lay.setSpacing(14)
        d_lay.setContentsMargins(24, 20, 24, 20)

        info = QLabel(f"Rejecting paycheck for <b>{emp_name}</b>")
        info.setStyleSheet("font-size: 13px;")
        d_lay.addWidget(info)

        reason_lbl = QLabel("Reason (required):")
        reason_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        d_lay.addWidget(reason_lbl)

        reason_edit = QTextEdit()
        reason_edit.setMaximumHeight(100)
        reason_edit.setStyleSheet(
            "QTextEdit { padding: 10px; border: 2px solid #BADFE7;"
            " border-radius: 10px; font-size: 13px; background: #FFF; }")
        d_lay.addWidget(reason_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #FFFFFF; color: #2C3E50; border: 2px solid #BADFE7;"
            " border-radius: 8px; padding: 8px 24px; font-size: 13px; font-weight: bold; }"
            " QPushButton:hover { background-color: #F0F7F8; border-color: #388087; }")
        cancel_btn.clicked.connect(dlg.reject)

        reject_btn = QPushButton("Reject")
        reject_btn.setMinimumHeight(36)
        reject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reject_btn.setStyleSheet(
            "QPushButton { background-color: #D9534F; color: #FFF; border: none;"
            " border-radius: 8px; padding: 8px 24px; font-size: 13px; font-weight: bold; }"
            " QPushButton:hover { background-color: #C9302C; }")

        def _do_reject():
            if not reason_edit.toPlainText().strip():
                QMessageBox.warning(dlg, "Required", "Please enter a reason.")
                return
            dlg.accept()

        reject_btn.clicked.connect(_do_reject)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(reject_btn)
        d_lay.addLayout(btn_row)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        fin_emp_id = self._backend.get_employee_id_by_email(self._user_email)
        ok = self._backend.reject_paycheck_request(
            req.get("request_id"), fin_emp_id, reason_edit.toPlainText().strip())
        if ok is True:
            QMessageBox.information(self, "Rejected",
                f"Paycheck request for {emp_name} has been rejected.")
            self._load_data()
        else:
            err = ok if isinstance(ok, str) else ""
            QMessageBox.warning(self, "Error", f"Failed to reject.\n{err}")

    def _on_disburse(self, row: int):
        if row >= len(self._requests):
            return
        req = self._requests[row]
        emp_name = req.get("employee_name", "")
        amount = float(req.get("amount", 0) or 0)

        reply = QMessageBox.question(
            self, "Disburse Paycheck",
            f"Mark paycheck of ₱{amount:,.2f} for {emp_name} as disbursed?\n\n"
            "This confirms the employee has received the payment.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        ok = self._backend.disburse_paycheck(req.get("request_id"))
        if ok is True:
            QMessageBox.information(self, "Disbursed",
                f"Paycheck for {emp_name} has been marked as disbursed.")
            self._load_data()
        else:
            err = ok if isinstance(ok, str) else ""
            QMessageBox.warning(self, "Error", f"Failed to disburse.\n{err}")

    def _on_view_details(self, row: int):
        if row >= len(self._requests):
            return
        req = self._requests[row]
        gross = float(req.get("amount", 0) or 0)
        sss = float(req.get("sss_deduction", 0) or 0)
        phil = float(req.get("philhealth_deduction", 0) or 0)
        hosp = float(req.get("hospital_share", 0) or 0)
        net = float(req.get("net_amount", 0) or 0)
        lines = [
            f"Employee: {req.get('employee_name', '')}",
            f"Role: {req.get('role_name', '')}",
            f"Department: {req.get('department_name', '')}",
            f"",
            f"Gross Amount:    ₱{gross:,.2f}",
            f"SSS Deduction:   ₱{sss:,.2f}",
            f"PhilHealth:      ₱{phil:,.2f}",
            f"Hospital Share:  ₱{hosp:,.2f}",
            f"Net Payout:      ₱{net:,.2f}",
            f"",
            f"Period: {req.get('period_from', '')} to {req.get('period_until', '')}",
            f"Requested By: {req.get('requested_by_name', '')}",
            f"Status: {req.get('status', '')}",
        ]
        if req.get("decided_by_name"):
            lines.append(f"Decided By: {req['decided_by_name']}")
        if req.get("finance_note"):
            lines.append(f"Finance Note: {req['finance_note']}")
        if req.get("decided_at"):
            lines.append(f"Decided At: {req['decided_at']}")
        if req.get("disbursed_at"):
            lines.append(f"Disbursed At: {req['disbursed_at']}")
        QMessageBox.information(self, "Paycheck Details", "\n".join(lines))

    # ── Employee Paycheck History ────────────────────────────────

    def _populate_hist_employees(self):
        if not self._backend:
            return
        emps = self._backend.get_employees(detailed=True) or []
        self._hist_employees = emps
        self._hist_emp_combo.blockSignals(True)
        self._hist_emp_combo.clear()
        self._hist_emp_combo.addItem("Select an employee...", None)
        for emp in emps:
            label = f"{emp.get('full_name', '')} — {emp.get('role_name', '')} ({emp.get('department_name', '')})"
            self._hist_emp_combo.addItem(label, emp.get("employee_id"))
        self._hist_emp_combo.blockSignals(False)

    def _load_employee_history(self, _=None):
        emp_id = self._hist_emp_combo.currentData()
        if not emp_id or not self._backend:
            self._hist_table.setRowCount(0)
            self._hist_summary.setText("")
            self._hist_next_pay.setText("")
            return

        history = self._backend.get_paycheck_history(emp_id) or []
        emp = self._backend.get_employee_by_id(emp_id)
        salary = float(emp.get("salary", 0) or 0) if emp else 0

        # Next paycheck info
        last = self._backend.get_last_disbursed_paycheck(emp_id)
        today = date.today()
        if last and last.get("period_until"):
            last_until = last["period_until"]
            if isinstance(last_until, str):
                from datetime import datetime
                last_until = datetime.strptime(last_until, "%Y-%m-%d").date()
            next_from = last_until + timedelta(days=1)
            _, days_in_month = monthrange(next_from.year, next_from.month)
            next_until = date(next_from.year, next_from.month, days_in_month)
            last_net = float(last.get("net_amount", 0) or 0)
            self._hist_next_pay.setText(
                f"Last disbursed: {last.get('disbursed_at', '—')} | "
                f"Last period: {last.get('period_from', '')} to {last.get('period_until', '')} | "
                f"Last net: ₱{last_net:,.2f}  ·  "
                f"Next expected: <b>{next_from} to {next_until}</b> | Base salary: ₱{salary:,.2f}")
        else:
            first_of_month = date(today.year, today.month, 1)
            _, days_in_month = monthrange(today.year, today.month)
            end_of_month = date(today.year, today.month, days_in_month)
            self._hist_next_pay.setText(
                f"No previous disbursements. Expected first period: "
                f"<b>{first_of_month} to {end_of_month}</b> | Base salary: ₱{salary:,.2f}")

        # Populate table
        self._hist_table.setRowCount(0)
        for req in history:
            r = self._hist_table.rowCount()
            self._hist_table.insertRow(r)
            gross = float(req.get("amount", 0) or 0)
            sss = float(req.get("sss_deduction", 0) or 0)
            phil = float(req.get("philhealth_deduction", 0) or 0)
            hosp = float(req.get("hospital_share", 0) or 0)
            net = float(req.get("net_amount", 0) or 0)
            period = f"{req.get('period_from', '')} to {req.get('period_until', '')}"
            disbursed_raw = req.get("disbursed_at")
            if disbursed_raw:
                disbursed = disbursed_raw.strftime("%Y-%m-%d %I:%M %p") if hasattr(disbursed_raw, "strftime") else str(disbursed_raw)
            else:
                disbursed = "—"
            status = req.get("status", "")
            values = [period, f"₱{gross:,.2f}", f"₱{sss:,.2f}", f"₱{phil:,.2f}",
                      f"₱{hosp:,.2f}", f"₱{net:,.2f}", status,
                      req.get("requested_by_name", ""), disbursed]
            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                if c == 6:
                    item.setForeground(QColor(status_color(val)))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                if c in (1, 5):
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self._hist_table.setItem(r, c, item)

        total = len(history)
        disbursed_count = sum(1 for h in history if h.get("status") == "Disbursed")
        pending_count = sum(1 for h in history if h.get("status") == "Pending")
        self._hist_summary.setText(
            f"Showing {total} paycheck{'s' if total != 1 else ''} · "
            f"{disbursed_count} disbursed · {pending_count} pending")

    # ── Partial (Prorated) Paycheck ──────────────────────────────

    def _on_partial_request(self):
        """HR submits a partial/prorated paycheck based on days worked."""
        dlg = _PartialPaycheckDialog(self, backend=self._backend)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            hr_emp_id = self._backend.get_employee_id_by_email(self._user_email)
            if not hr_emp_id:
                QMessageBox.warning(self, "Error", "Could not determine your employee ID.")
                return
            ok = self._backend.submit_partial_paycheck(
                data["employee_id"], data["full_salary"],
                data["days_worked"], data["total_days"],
                data["period_from"], data["period_until"], hr_emp_id)
            if ok is True:
                prorated = round(data["full_salary"] * data["days_worked"] / data["total_days"], 2)
                QMessageBox.information(self, "Success",
                    f"Partial paycheck (₱{prorated:,.2f}) submitted for {data['employee_name']}.\n"
                    f"({data['days_worked']}/{data['total_days']} days)")
                self._load_data()
            else:
                err = ok if isinstance(ok, str) else ""
                QMessageBox.warning(self, "Error", f"Failed to submit partial request.\n{err}")


# ══════════════════════════════════════════════════════════════════════
#  Paycheck Request Dialog (used by HR)
# ══════════════════════════════════════════════════════════════════════
class _PaycheckRequestDialog(QDialog):

    def __init__(self, parent=None, backend=None):
        super().__init__(parent)
        self.setWindowTitle("Request Paycheck")
        self.setMinimumWidth(500)
        self._backend = backend

        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 20, 24, 20)

        form = QFormLayout()
        form.setSpacing(12)

        # Employee selection
        self._emp_combo = QComboBox()
        self._emp_combo.setObjectName("formCombo")
        self._emp_combo.setMinimumHeight(40)
        self._employees = self._backend.get_employees(detailed=True) if self._backend else []
        for emp in self._employees:
            label = f"{emp.get('full_name', '')} — {emp.get('role_name', '')} ({emp.get('department_name', '')})"
            self._emp_combo.addItem(label, emp.get("employee_id"))
        self._emp_combo.currentIndexChanged.connect(self._on_employee_changed)
        form.addRow("Employee", self._emp_combo)

        # Salary display
        self._salary_label = QLabel("—")
        self._salary_label.setStyleSheet("font-size: 13px; color: #388087; font-weight: bold;")
        form.addRow("Base Salary", self._salary_label)

        # Deduction rates display
        rates = self._backend.get_tax_rates() if self._backend else {}
        sss_r = rates.get('sss_rate', 4.5)
        phil_r = rates.get('philhealth_rate', 2.5)
        hosp_r = rates.get('hospital_share_rate', 10.0)
        self._deduction_label = QLabel(
            f"SSS: {sss_r}%  |  PhilHealth: {phil_r}%  |  Hospital: {hosp_r}%  "
            f"(Total: {sss_r + phil_r + hosp_r}%)")
        self._deduction_label.setStyleSheet("font-size: 12px; color: #7F8C8D;")
        form.addRow("Deductions", self._deduction_label)

        # Net preview
        self._net_preview = QLabel("—")
        self._net_preview.setStyleSheet("font-size: 13px; color: #388087; font-weight: bold;")
        form.addRow("Est. Net", self._net_preview)

        # Amount
        self._amount = QLineEdit()
        self._amount.setObjectName("formInput")
        self._amount.setMinimumHeight(40)
        self._amount.setPlaceholderText("Paycheck amount (₱)")
        self._amount.textChanged.connect(self._update_net_preview)
        form.addRow("Amount", self._amount)

        # Period
        from ui.shared.modern_calendar import apply_modern_calendar
        self._from_date = QDateEdit()
        apply_modern_calendar(self._from_date)
        self._from_date.setDate(QDate.currentDate().addMonths(-1))
        self._from_date.setObjectName("formCombo")
        self._from_date.setMinimumHeight(40)
        self._from_date.setDisplayFormat("M/d/yyyy")
        form.addRow("Period From", self._from_date)

        self._until_date = QDateEdit()
        apply_modern_calendar(self._until_date)
        self._until_date.setDate(QDate.currentDate())
        self._until_date.setObjectName("formCombo")
        self._until_date.setMinimumHeight(40)
        self._until_date.setDisplayFormat("M/d/yyyy")
        form.addRow("Period Until", self._until_date)

        lay.addLayout(form)

        # Buttons
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        style_dialog_btns(btns)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        # Trigger initial salary display
        if self._emp_combo.count() > 0:
            self._on_employee_changed(0)

    def _update_net_preview(self, _=None):
        try:
            gross = float(self._amount.text().replace(",", ""))
            if gross > 0 and self._backend:
                ded = self._backend.calculate_deductions(gross)
                self._net_preview.setText(
                    f"₱{ded['net_amount']:,.2f}  "
                    f"(−₱{ded['total_deductions']:,.2f} deductions)")
                return
        except (ValueError, TypeError):
            pass
        self._net_preview.setText("—")

    def _on_employee_changed(self, index):
        emp_id = self._emp_combo.currentData()
        if emp_id and self._backend:
            # Find salary from employee list (detailed=True includes salary)
            for emp in self._employees:
                if emp.get("employee_id") == emp_id:
                    salary = emp.get("salary", 0) or 0
                    self._salary_label.setText(f"₱{float(salary):,.2f}")
                    self._amount.setText(f"{float(salary):,.2f}")
                    break

    def _validate_and_accept(self):
        if self._emp_combo.currentData() is None:
            QMessageBox.warning(self, "Validation", "Please select an employee.")
            return
        try:
            amount = float(self._amount.text().replace(",", ""))
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Validation", "Please enter a valid amount.")
            return
        if self._from_date.date() > self._until_date.date():
            QMessageBox.warning(self, "Validation", "Period 'From' must be before 'Until'.")
            return
        self.accept()

    def get_data(self) -> dict:
        emp_id = self._emp_combo.currentData()
        emp_name = self._emp_combo.currentText().split(" — ")[0]
        return {
            "employee_id": emp_id,
            "employee_name": emp_name,
            "amount": float(self._amount.text().replace(",", "")),
            "period_from": self._from_date.date().toString("yyyy-MM-dd"),
            "period_until": self._until_date.date().toString("yyyy-MM-dd"),
        }


# ══════════════════════════════════════════════════════════════════════
#  Partial (Prorated) Paycheck Dialog
# ══════════════════════════════════════════════════════════════════════
class _PartialPaycheckDialog(QDialog):
    """Submit a prorated paycheck, auto-computing amount based on days worked."""

    def __init__(self, parent=None, backend=None):
        super().__init__(parent)
        self.setWindowTitle("Partial / Prorated Paycheck")
        self.setMinimumWidth(520)
        self._backend = backend

        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 20, 24, 20)

        info = QLabel(
            "Submit a prorated paycheck for an employee based on the number of "
            "days worked in a period. The system will automatically compute the "
            "partial amount from their base salary.")
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 12px; color: #555; padding-bottom: 6px;")
        lay.addWidget(info)

        form = QFormLayout()
        form.setSpacing(12)

        # Employee selection
        self._emp_combo = QComboBox()
        self._emp_combo.setObjectName("formCombo")
        self._emp_combo.setMinimumHeight(40)
        self._employees = self._backend.get_employees(detailed=True) if self._backend else []
        for emp in self._employees:
            label = f"{emp.get('full_name', '')} — {emp.get('role_name', '')} ({emp.get('department_name', '')})"
            self._emp_combo.addItem(label, emp.get("employee_id"))
        self._emp_combo.currentIndexChanged.connect(self._on_employee_changed)
        form.addRow("Employee", self._emp_combo)

        # Salary display
        self._salary_label = QLabel("—")
        self._salary_label.setStyleSheet("font-size: 13px; color: #388087; font-weight: bold;")
        form.addRow("Base Salary", self._salary_label)

        # Period
        from ui.shared.modern_calendar import apply_modern_calendar
        self._from_date = QDateEdit()
        apply_modern_calendar(self._from_date)
        self._from_date.setDate(QDate.currentDate().addMonths(-1))
        self._from_date.setObjectName("formCombo")
        self._from_date.setMinimumHeight(40)
        self._from_date.setDisplayFormat("M/d/yyyy")
        self._from_date.dateChanged.connect(self._recalc)
        form.addRow("Period From", self._from_date)

        self._until_date = QDateEdit()
        apply_modern_calendar(self._until_date)
        self._until_date.setDate(QDate.currentDate())
        self._until_date.setObjectName("formCombo")
        self._until_date.setMinimumHeight(40)
        self._until_date.setDisplayFormat("M/d/yyyy")
        self._until_date.dateChanged.connect(self._recalc)
        form.addRow("Period Until", self._until_date)

        # Days worked / Total days
        days_row = QHBoxLayout()
        self._days_worked = QSpinBox()
        self._days_worked.setMinimum(1)
        self._days_worked.setMaximum(31)
        self._days_worked.setValue(15)
        self._days_worked.setMinimumHeight(40)
        self._days_worked.setObjectName("formCombo")
        self._days_worked.valueChanged.connect(self._recalc)
        days_row.addWidget(QLabel("Days Worked:"))
        days_row.addWidget(self._days_worked)

        self._total_days = QSpinBox()
        self._total_days.setMinimum(1)
        self._total_days.setMaximum(31)
        self._total_days.setMinimumHeight(40)
        self._total_days.setObjectName("formCombo")
        self._total_days.valueChanged.connect(self._recalc)
        days_row.addWidget(QLabel("of Total:"))
        days_row.addWidget(self._total_days)
        form.addRow("Days", days_row)

        # Computed amount
        self._computed_label = QLabel("—")
        self._computed_label.setStyleSheet("font-size: 14px; color: #388087; font-weight: bold;")
        form.addRow("Prorated Amount", self._computed_label)

        # Net after deductions
        self._net_label = QLabel("—")
        self._net_label.setStyleSheet("font-size: 13px; color: #388087; font-weight: bold;")
        form.addRow("Est. Net", self._net_label)

        # Deduction rates info
        rates = self._backend.get_tax_rates() if self._backend else {}
        sss_r = rates.get('sss_rate', 4.5)
        phil_r = rates.get('philhealth_rate', 2.5)
        hosp_r = rates.get('hospital_share_rate', 10.0)
        ded_info = QLabel(
            f"SSS: {sss_r}%  |  PhilHealth: {phil_r}%  |  Hospital: {hosp_r}%  "
            f"(Total: {sss_r + phil_r + hosp_r}%)")
        ded_info.setStyleSheet("font-size: 11px; color: #7F8C8D;")
        form.addRow("Deductions", ded_info)

        lay.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        style_dialog_btns(btns)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

        # Auto-fill total days from period & trigger initial calc
        self._recalc()
        if self._emp_combo.count() > 0:
            self._on_employee_changed(0)

    def _on_employee_changed(self, _=None):
        emp_id = self._emp_combo.currentData()
        if emp_id and self._backend:
            for emp in self._employees:
                if emp.get("employee_id") == emp_id:
                    self._current_salary = float(emp.get("salary", 0) or 0)
                    self._salary_label.setText(f"₱{self._current_salary:,.2f}")
                    self._recalc()
                    break
        else:
            self._current_salary = 0

    def _recalc(self, _=None):
        from_d = self._from_date.date().toPyDate()
        until_d = self._until_date.date().toPyDate()
        total_days = (until_d - from_d).days + 1
        if total_days < 1:
            total_days = 1
        self._total_days.blockSignals(True)
        self._total_days.setValue(total_days)
        self._total_days.blockSignals(False)
        if self._days_worked.value() > total_days:
            self._days_worked.blockSignals(True)
            self._days_worked.setValue(total_days)
            self._days_worked.blockSignals(False)
        self._days_worked.setMaximum(total_days)

        salary = getattr(self, "_current_salary", 0)
        if salary > 0 and total_days > 0:
            prorated = round(salary * self._days_worked.value() / total_days, 2)
            self._computed_label.setText(f"₱{prorated:,.2f}  ({self._days_worked.value()}/{total_days} days)")
            if self._backend:
                ded = self._backend.calculate_deductions(prorated)
                self._net_label.setText(
                    f"₱{ded['net_amount']:,.2f}  (−₱{ded['total_deductions']:,.2f})")
        else:
            self._computed_label.setText("—")
            self._net_label.setText("—")

    def _validate_and_accept(self):
        if self._emp_combo.currentData() is None:
            QMessageBox.warning(self, "Validation", "Please select an employee.")
            return
        salary = getattr(self, "_current_salary", 0)
        if salary <= 0:
            QMessageBox.warning(self, "Validation",
                "Selected employee has no base salary set.\nPlease set their salary first.")
            return
        if self._from_date.date() > self._until_date.date():
            QMessageBox.warning(self, "Validation", "Period 'From' must be before 'Until'.")
            return
        if self._days_worked.value() < 1:
            QMessageBox.warning(self, "Validation", "Days worked must be at least 1.")
            return
        self.accept()

    def get_data(self) -> dict:
        emp_id = self._emp_combo.currentData()
        emp_name = self._emp_combo.currentText().split(" — ")[0]
        return {
            "employee_id": emp_id,
            "employee_name": emp_name,
            "full_salary": getattr(self, "_current_salary", 0),
            "days_worked": self._days_worked.value(),
            "total_days": self._total_days.value(),
            "period_from": self._from_date.date().toString("yyyy-MM-dd"),
            "period_until": self._until_date.date().toString("yyyy-MM-dd"),
        }
