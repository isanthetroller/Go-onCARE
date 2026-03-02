# HR employee management page - full employee control + leave requests

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidgetItem, QHeaderView, QTabWidget, QScrollArea, QFrame,
    QComboBox, QDialog, QMessageBox, QTextEdit, QInputDialog,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from ui.styles import (
    make_table_btn, make_banner, make_card, make_stat_card,
    make_read_only_table, make_interactive_table, make_action_table,
)
from ui.shared.hr_employee_dialogs import HREmployeeDialog, HREmployeeProfileDialog, UserAccountDialog
from backend import AuthBackend


# ══════════════════════════════════════════════════════════════════════
#  HR Employees Page – comprehensive employee management
# ══════════════════════════════════════════════════════════════════════
class HREmployeesPage(QWidget):
    def __init__(self, backend: AuthBackend | None = None, role: str = "HR"):
        super().__init__()
        self._backend = backend or AuthBackend()
        self._role = role
        self._employees: list[dict] = []
        self._leave_requests: list[dict] = []
        self._build()
        self._load_from_db()
        # Auto-refresh data every 10 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_from_db)
        self._refresh_timer.start(10_000)

    def _load_from_db(self):
        if not self.isVisible():
            return
        rows = self._backend.get_employees_detailed() or []
        self._employees = rows
        self.table.setRowCount(0)
        for emp in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            salary = emp.get("salary", 0) or 0
            values = [
                str(emp.get("employee_id", "")),
                emp.get("full_name", ""),
                emp.get("role_name", ""),
                emp.get("department_name", ""),
                emp.get("employment_type", ""),
                emp.get("phone", "") or "",
                emp.get("email", "") or "",
                str(emp.get("hire_date", "")),
                f"₱{float(salary):,.0f}" if salary else "—",
                emp.get("status", ""),
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                if c == 9:  # Status column
                    clr = {"Active": "#5CB85C", "On Leave": "#E8B931"}.get(val, "#D9534F")
                    item.setForeground(QColor(clr))
                self.table.setItem(r, c, item)

            # Actions: View | Edit
            act_w = QWidget()
            act_lay = QHBoxLayout(act_w)
            act_lay.setContentsMargins(0,0,0,0); act_lay.setSpacing(6)
            view_btn = make_table_btn("View"); view_btn.setFixedWidth(52)
            view_btn.clicked.connect(lambda checked, ri=r: self._on_view(ri))
            act_lay.addWidget(view_btn)
            edit_btn = make_table_btn("Edit"); edit_btn.setFixedWidth(52)
            edit_btn.clicked.connect(lambda checked, ri=r: self._on_edit(ri))
            act_lay.addWidget(edit_btn)
            self.table.setCellWidget(r, 10, act_w)

        # HR Stats
        stats = self._backend.get_hr_stats()
        for key, lbl in self._stat_labels.items():
            val = stats.get(key, 0) or 0
            if key in ("avg_salary", "total_payroll"):
                lbl.setText(f"₱{float(val):,.0f}")
            else:
                lbl.setText(str(val))

        # Department payroll
        dept_payroll = self._backend.get_payroll_summary()
        self._dept_table.setRowCount(len(dept_payroll))
        for r, d in enumerate(dept_payroll):
            self._dept_table.setItem(r, 0, QTableWidgetItem(d.get("department_name", "")))
            self._dept_table.setItem(r, 1, QTableWidgetItem(str(d.get("headcount", 0))))
            total_sal = float(d.get("total_salary", 0) or 0)
            avg_sal = float(d.get("avg_salary", 0) or 0)
            self._dept_table.setItem(r, 2, QTableWidgetItem(f"₱{total_sal:,.0f}"))
            self._dept_table.setItem(r, 3, QTableWidgetItem(f"₱{avg_sal:,.0f}"))

        # Leave tracker
        leave_emps = self._backend.get_leave_employees()
        self._leave_table.setRowCount(len(leave_emps))
        for r, le in enumerate(leave_emps):
            self._leave_table.setItem(r, 0, QTableWidgetItem(le.get("full_name", "")))
            self._leave_table.setItem(r, 1, QTableWidgetItem(le.get("department_name", "")))
            self._leave_table.setItem(r, 2, QTableWidgetItem(str(le.get("leave_from", "") or "—")))
            self._leave_table.setItem(r, 3, QTableWidgetItem(str(le.get("leave_until", "") or "—")))

        # Employment type counts
        type_counts = self._backend.get_employment_type_counts()
        self._type_table.setRowCount(len(type_counts))
        for r, tc in enumerate(type_counts):
            self._type_table.setItem(r, 0, QTableWidgetItem(tc.get("employment_type", "")))
            self._type_table.setItem(r, 1, QTableWidgetItem(str(tc.get("cnt", 0))))

        # Leave requests
        self._load_leave_requests()

        # User accounts (Admin only)
        if hasattr(self, "_users_table"):
            self._load_user_accounts()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 16, 24, 16)
        outer.setSpacing(12)

        # ── Banner (always visible above tabs) ────────────────────
        outer.addWidget(make_banner(
            "HR Employee Management",
            "Comprehensive staff management \u2013 salary, leave, performance"))

        # ── Tab widget ────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            "QTabWidget::pane { background-color: #F6F6F2; }")
        self._tabs.addTab(self._build_employees_tab(), "\U0001F465  Employees")
        self._tabs.addTab(self._build_leave_tab(), "\U0001F4CB  Leave Management")
        self._tabs.addTab(self._build_payroll_tab(), "\U0001F4B0  Payroll & Staffing")
        if self._role == "Admin":
            self._tabs.addTab(self._build_accounts_tab(), "\U0001F510  User Accounts")
        outer.addWidget(self._tabs)

    # ── Tab helpers ───────────────────────────────────────────────

    @staticmethod
    def _make_tab_scroll():
        """Create a scrollable content area for one tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(inner)
        lay.setSpacing(14)
        lay.setContentsMargins(20, 16, 20, 20)
        scroll.setWidget(inner)
        return scroll, lay

    def _build_employees_tab(self):
        scroll, lay = self._make_tab_scroll()

        # ── Stat cards: row 1 (employee counts) ──────────────────
        self._stat_labels = {}
        row1 = QHBoxLayout(); row1.setSpacing(14)
        for key, label, color in [
            ("total",    "Total Staff", "#388087"),
            ("active",   "Active",      "#5CB85C"),
            ("on_leave", "On Leave",    "#E8B931"),
            ("inactive", "Inactive",    "#D9534F"),
        ]:
            row1.addWidget(make_stat_card(key, label, color, self._stat_labels))
        lay.addLayout(row1)

        # ── Stat cards: row 2 (payroll) ──────────────────────────
        row2 = QHBoxLayout(); row2.setSpacing(14)
        for key, label, color in [
            ("avg_salary",    "Avg Salary",    "#6FB3B8"),
            ("total_payroll", "Total Payroll", "#388087"),
        ]:
            row2.addWidget(make_stat_card(key, label, color, self._stat_labels))
        row2.addStretch(2)          # keep payroll cards from stretching too wide
        lay.addLayout(row2)

        # ── Filter bar (inside a card) ───────────────────────────
        filter_card = make_card()
        fc_lay = QVBoxLayout(filter_card)
        fc_lay.setContentsMargins(16, 12, 16, 12); fc_lay.setSpacing(0)

        bar = QHBoxLayout(); bar.setSpacing(10)
        self.search = QLineEdit()
        self.search.setObjectName("searchBar")
        self.search.setPlaceholderText("\U0001F50D  Search employees by name, role, department, email\u2026")
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(lambda _: self._apply_filters())
        bar.addWidget(self.search, 2)

        for attr, items, width in [
            ("role_filter",   ["All Roles", "Doctor", "Cashier", "Receptionist",
                               "Admin", "HR"], 130),
            ("dept_filter",   ["All Departments", "General Medicine", "Cardiology",
                               "Dentistry", "Pediatrics", "Laboratory",
                               "Front Desk", "Management", "Pharmacy",
                               "Human Resources"], 160),
            ("status_filter", ["All Status", "Active", "On Leave", "Inactive"], 130),
            ("type_filter",   ["All Types", "Full-time", "Part-time", "Contract"], 120),
        ]:
            combo = QComboBox()
            combo.setObjectName("formCombo")
            combo.addItems(items)
            combo.setMinimumHeight(42); combo.setMinimumWidth(width)
            combo.currentTextChanged.connect(lambda _: self._apply_filters())
            setattr(self, attr, combo)
            bar.addWidget(combo)

        fc_lay.addLayout(bar)
        lay.addWidget(filter_card)

        # ── Main employee table ──────────────────────────────────
        cols = ["ID", "Name", "Role", "Department", "Type", "Phone", "Email",
                "Hire Date", "Salary", "Status", "Actions"]
        self.table = make_action_table(cols, min_h=420, row_h=44,
                                       action_col_width=130)
        lay.addWidget(self.table)

        lay.addStretch()
        return scroll

    def _build_leave_tab(self):
        scroll, lay = self._make_tab_scroll()

        # ── Leave Tracker (employees currently on leave) ─────────
        leave_card = make_card(min_height=220)
        lc_lay = QVBoxLayout(leave_card)
        lc_lay.setContentsMargins(16, 14, 16, 14); lc_lay.setSpacing(10)
        lc_title = QLabel("Leave Tracker")
        lc_title.setObjectName("cardTitle")
        lc_lay.addWidget(lc_title)
        self._leave_table = make_read_only_table(
            ["Employee", "Department", "From", "Until"],
            min_h=160, row_h=38)
        lc_lay.addWidget(self._leave_table)
        lay.addWidget(leave_card)

        # ── Leave Requests Management ────────────────────────────
        lr_card = make_card(min_height=300)
        lr_lay = QVBoxLayout(lr_card)
        lr_lay.setContentsMargins(16, 14, 16, 14); lr_lay.setSpacing(10)

        lr_header = QHBoxLayout()
        lr_title = QLabel("Leave Requests")
        lr_title.setObjectName("cardTitle")
        lr_header.addWidget(lr_title)
        self._lr_status_filter = QComboBox()
        self._lr_status_filter.setObjectName("formCombo")
        self._lr_status_filter.addItems(["Pending", "All", "Approved", "Declined"])
        self._lr_status_filter.setMinimumHeight(36)
        self._lr_status_filter.setMinimumWidth(120)
        self._lr_status_filter.currentTextChanged.connect(
            lambda _: self._load_leave_requests())
        lr_header.addStretch()
        lr_header.addWidget(self._lr_status_filter)
        lr_lay.addLayout(lr_header)

        self._lr_table = make_read_only_table(
            ["Employee", "Role", "Department", "From", "Until",
             "Reason", "Status", "Actions"],
            min_h=200, row_h=44)
        self._lr_table.horizontalHeader().setSectionResizeMode(
            7, QHeaderView.ResizeMode.Fixed)
        self._lr_table.setColumnWidth(7, 180)
        self._lr_table.horizontalHeader().setStretchLastSection(False)
        lr_lay.addWidget(self._lr_table)
        lay.addWidget(lr_card)

        lay.addStretch()
        return scroll

    def _build_payroll_tab(self):
        scroll, lay = self._make_tab_scroll()

        # ── Department Payroll ────────────────────────────────────
        dept_card = make_card(min_height=300)
        dc_lay = QVBoxLayout(dept_card)
        dc_lay.setContentsMargins(16, 14, 16, 14); dc_lay.setSpacing(10)
        dc_title = QLabel("Department Payroll")
        dc_title.setObjectName("cardTitle")
        dc_lay.addWidget(dc_title)
        self._dept_table = make_read_only_table(
            ["Department", "Headcount", "Total Salary", "Avg Salary"],
            min_h=220, row_h=38)
        dc_lay.addWidget(self._dept_table)
        lay.addWidget(dept_card)

        # ── Employment Type Breakdown ────────────────────────────
        type_card = make_card(min_height=200)
        tc_lay = QVBoxLayout(type_card)
        tc_lay.setContentsMargins(16, 14, 16, 14); tc_lay.setSpacing(10)
        tc_title = QLabel("Employment Types")
        tc_title.setObjectName("cardTitle")
        tc_lay.addWidget(tc_title)
        self._type_table = make_read_only_table(
            ["Type", "Count"], min_h=160, row_h=38)
        tc_lay.addWidget(self._type_table)
        lay.addWidget(type_card)

        lay.addStretch()
        return scroll

    def _build_accounts_tab(self):
        scroll, lay = self._make_tab_scroll()

        ua_card = make_card(min_height=300)
        ua_lay = QVBoxLayout(ua_card)
        ua_lay.setContentsMargins(16, 14, 16, 14); ua_lay.setSpacing(10)

        ua_header = QHBoxLayout()
        ua_title = QLabel("User Accounts")
        ua_title.setObjectName("cardTitle")
        ua_header.addWidget(ua_title)
        ua_header.addStretch()

        create_btn = QPushButton("\uff0b  Create Account")
        create_btn.setObjectName("actionBtn"); create_btn.setMinimumHeight(38)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setToolTip("Create a new user account for an employee")
        create_btn.clicked.connect(self._on_create_account)
        ua_header.addWidget(create_btn)

        reset_btn = QPushButton("\U0001F511  Reset Password")
        reset_btn.setObjectName("actionBtn"); reset_btn.setMinimumHeight(38)
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setToolTip("Reset a user's password")
        reset_btn.clicked.connect(self._on_reset_password)
        ua_header.addWidget(reset_btn)

        del_btn = QPushButton("\U0001F5D1  Delete Account")
        del_btn.setObjectName("dangerBtn"); del_btn.setMinimumHeight(38)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setToolTip("Permanently delete a user account")
        del_btn.clicked.connect(self._on_delete_account)
        ua_header.addWidget(del_btn)

        ua_lay.addLayout(ua_header)

        self._users_table = make_interactive_table(
            ["ID", "Full Name", "Email", "Role", "Must Change PW"],
            min_h=220, row_h=40)
        ua_lay.addWidget(self._users_table)
        lay.addWidget(ua_card)
        self._user_account_ids: list[int] = []

        lay.addStretch()
        return scroll

    # ── Leave Request Management ────────────────────────────────
    def _load_leave_requests(self):
        """Load leave requests into the leave requests table."""
        filt = self._lr_status_filter.currentText()
        if filt == "All":
            reqs = self._backend.get_all_leave_requests() or []
        elif filt == "Pending":
            reqs = self._backend.get_pending_leave_requests() or []
        else:
            all_reqs = self._backend.get_all_leave_requests() or []
            reqs = [r for r in all_reqs if r.get("status") == filt]
        self._leave_requests = reqs
        self._lr_table.setRowCount(0)
        for req in reqs:
            r = self._lr_table.rowCount()
            self._lr_table.insertRow(r)
            self._lr_table.setItem(r, 0, QTableWidgetItem(req.get("employee_name", "")))
            self._lr_table.setItem(r, 1, QTableWidgetItem(req.get("role_name", "")))
            self._lr_table.setItem(r, 2, QTableWidgetItem(req.get("department_name", "")))
            self._lr_table.setItem(r, 3, QTableWidgetItem(str(req.get("leave_from", ""))))
            self._lr_table.setItem(r, 4, QTableWidgetItem(str(req.get("leave_until", ""))))
            self._lr_table.setItem(r, 5, QTableWidgetItem(req.get("reason", "")))
            status_item = QTableWidgetItem(req.get("status", ""))
            clr = {"Pending": "#E8B931", "Approved": "#5CB85C",
                   "Declined": "#D9534F"}.get(req.get("status", ""), "#7F8C8D")
            status_item.setForeground(QColor(clr))
            self._lr_table.setItem(r, 6, status_item)

            # Action buttons
            act_w = QWidget()
            act_lay = QHBoxLayout(act_w)
            act_lay.setContentsMargins(0,0,0,0); act_lay.setSpacing(6)
            if req.get("status") == "Pending":
                approve_btn = make_table_btn("Approve")
                approve_btn.setStyleSheet(
                    "QPushButton { background-color: #5CB85C; color: #FFF; border: none;"
                    " border-radius: 4px; padding: 4px 10px; font-size: 11px; font-weight: bold; }"
                    " QPushButton:hover { background-color: #4cae4c; }")
                approve_btn.clicked.connect(lambda checked, ri=r: self._on_approve_leave(ri))
                act_lay.addWidget(approve_btn)
                decline_btn = make_table_btn("Decline")
                decline_btn.setStyleSheet(
                    "QPushButton { background-color: #D9534F; color: #FFF; border: none;"
                    " border-radius: 4px; padding: 4px 10px; font-size: 11px; font-weight: bold; }"
                    " QPushButton:hover { background-color: #c9302c; }")
                decline_btn.clicked.connect(lambda checked, ri=r: self._on_decline_leave(ri))
                act_lay.addWidget(decline_btn)
            else:
                # Show note for declined or decided_at for approved
                note = req.get("hr_note", "") or ""
                decided = str(req.get("decided_at", "") or "")
                lbl = QLabel(note if note else decided)
                lbl.setStyleSheet("font-size: 11px; color: #7F8C8D;")
                lbl.setWordWrap(True)
                act_lay.addWidget(lbl)
            self._lr_table.setCellWidget(r, 7, act_w)

    def _on_approve_leave(self, row: int):
        if row >= len(self._leave_requests):
            return
        req = self._leave_requests[row]
        request_id = req.get("request_id")
        emp_name = req.get("employee_name", "")
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirm Approval")
        msg.setText(f"Approve leave request for {emp_name}?\n"
                    f"Period: {req.get('leave_from', '')} to {req.get('leave_until', '')}")
        msg.setIcon(QMessageBox.Icon.Question)
        yes_btn = msg.addButton("Approve", QMessageBox.ButtonRole.YesRole)
        no_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
        yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        yes_btn.setStyleSheet(
            "QPushButton { background-color: #5CB85C; color: #FFF; border: none;"
            " border-radius: 4px; padding: 8px 24px; font-size: 13px; font-weight: bold; }")
        no_btn.setStyleSheet(
            "QPushButton { background-color: #6c757d; color: #FFF; border: none;"
            " border-radius: 4px; padding: 8px 24px; font-size: 13px; font-weight: bold; }")
        msg.exec()
        if msg.clickedButton() == yes_btn:
            hr_emp_id = self._backend.get_employee_id_by_email(
                self._backend._current_user_email)
            ok = self._backend.approve_leave_request(request_id, hr_emp_id)
            if ok is True:
                QMessageBox.information(self, "Approved",
                                        f"Leave approved for {emp_name}.")
                self._load_from_db()
            else:
                err = ok if isinstance(ok, str) else ""
                QMessageBox.warning(self, "Error", f"Failed to approve.\n{err}")

    def _on_decline_leave(self, row: int):
        if row >= len(self._leave_requests):
            return
        req = self._leave_requests[row]
        request_id = req.get("request_id")
        emp_name = req.get("employee_name", "")

        # Dialog to enter decline reason
        dlg = QDialog(self)
        dlg.setWindowTitle("Decline Leave Request")
        dlg.setMinimumWidth(450)
        d_lay = QVBoxLayout(dlg)
        d_lay.setSpacing(14); d_lay.setContentsMargins(24, 20, 24, 20)

        info = QLabel(f"Declining leave for <b>{emp_name}</b><br>"
                      f"Period: {req.get('leave_from', '')} to {req.get('leave_until', '')}")
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 13px; color: #2C3E50;")
        d_lay.addWidget(info)

        reason_lbl = QLabel("Reason / Note (required):")
        reason_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        d_lay.addWidget(reason_lbl)

        reason_edit = QTextEdit()
        reason_edit.setMaximumHeight(100)
        reason_edit.setStyleSheet(
            "QTextEdit { padding: 10px; border: 2px solid #BADFE7;"
            " border-radius: 10px; font-size: 13px; background: #FFF; }")
        d_lay.addWidget(reason_edit)

        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setMinimumHeight(36)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #6c757d; color: #FFF; border: none;"
            " border-radius: 4px; padding: 8px 24px; font-size: 13px; font-weight: bold; }")
        cancel_btn.clicked.connect(dlg.reject)
        decline_btn = QPushButton("Decline"); decline_btn.setMinimumHeight(36)
        decline_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        decline_btn.setStyleSheet(
            "QPushButton { background-color: #D9534F; color: #FFF; border: none;"
            " border-radius: 4px; padding: 8px 24px; font-size: 13px; font-weight: bold; }")

        def _do_decline():
            reason_text = reason_edit.toPlainText().strip()
            if not reason_text:
                QMessageBox.warning(dlg, "Required", "Please enter a reason for declining.")
                return
            dlg.accept()

        decline_btn.clicked.connect(_do_decline)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(decline_btn)
        d_lay.addLayout(btn_row)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        reason_text = reason_edit.toPlainText().strip()
        hr_emp_id = self._backend.get_employee_id_by_email(
            self._backend._current_user_email)
        ok = self._backend.decline_leave_request(request_id, hr_emp_id, reason_text)
        if ok is True:
            QMessageBox.information(self, "Declined",
                                    f"Leave declined for {emp_name}.")
            self._load_from_db()
        else:
            err = ok if isinstance(ok, str) else ""
            QMessageBox.warning(self, "Error", f"Failed to decline.\n{err}")

    # ── Filters ───────────────────────────────────────────────────
    def _apply_filters(self):
        text = self.search.text().strip().lower()
        role = self.role_filter.currentText()
        dept = self.dept_filter.currentText()
        status = self.status_filter.currentText()
        emp_type = self.type_filter.currentText()
        for r in range(self.table.rowCount()):
            text_match = True
            if text:
                text_match = any(
                    text in (self.table.item(r, c).text().lower() if self.table.item(r, c) else "")
                    for c in range(self.table.columnCount() - 1)
                )
            role_match = role == "All Roles" or (
                self.table.item(r, 2) and self.table.item(r, 2).text() == role)
            dept_match = dept == "All Departments" or (
                self.table.item(r, 3) and self.table.item(r, 3).text() == dept)
            status_match = status == "All Status" or (
                self.table.item(r, 9) and self.table.item(r, 9).text() == status)
            type_match = emp_type == "All Types" or (
                self.table.item(r, 4) and self.table.item(r, 4).text() == emp_type)
            self.table.setRowHidden(r, not (text_match and role_match and dept_match
                                            and status_match and type_match))

    # ── View Profile ──────────────────────────────────────────────
    def _on_view(self, row: int):
        if row >= len(self._employees):
            return
        emp = self._employees[row]
        dlg = HREmployeeProfileDialog(self, emp_data=emp, backend=self._backend)
        dlg.exec()

    # ── Edit ──────────────────────────────────────────────────────
    def _on_edit(self, row: int):
        if row >= len(self._employees):
            return
        emp = self._employees[row]
        data = {
            "id":                str(emp.get("employee_id", "")),
            "name":              emp.get("full_name", ""),
            "role":              emp.get("role_name", ""),
            "dept":              emp.get("department_name", ""),
            "type":              emp.get("employment_type", ""),
            "phone":             emp.get("phone", ""),
            "email":             emp.get("email", ""),
            "status":            emp.get("status", ""),
            "salary":            emp.get("salary", 0),
            "emergency_contact": emp.get("emergency_contact", ""),
            "notes":             emp.get("notes", ""),
        }

        dlg = HREmployeeDialog(self, title="Edit Employee", data=data)
        result = dlg.exec()
        if dlg.fired:
            self._on_delete(row); return
        if result == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Employee name is required.")
                return
            try:
                emp_id = int(data["id"])
            except (ValueError, KeyError):
                QMessageBox.warning(self, "Error", "Invalid employee ID.")
                return
            old_email = data.get("email", "")
            ok = self._backend.update_employee(emp_id, d, old_email=old_email)
            if ok is not True:
                err = ok if isinstance(ok, str) else ''
                QMessageBox.warning(self, "Error", f"Failed to update employee.\n{err}")
                return
            self._load_from_db()
            QMessageBox.information(self, "Success", f"Employee '{d['name']}' updated.")

    # ── Delete ────────────────────────────────────────────────────
    def _on_delete(self, row: int):
        if row >= len(self._employees):
            return
        emp = self._employees[row]
        name = emp.get("full_name", "this employee")
        msg = QMessageBox(self); msg.setWindowTitle("Confirm Fire")
        msg.setText(f"Are you sure you want to fire {name}?")
        msg.setIcon(QMessageBox.Icon.Warning)
        yes_btn = msg.addButton("Yes, Fire", QMessageBox.ButtonRole.YesRole)
        no_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
        yes_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        no_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        yes_btn.setStyleSheet(
            "QPushButton { background-color: #D9534F; color: #FFF; border: none;"
            " border-radius: 4px; padding: 8px 24px; font-size: 13px; font-weight: bold; }"
            " QPushButton:hover { background-color: #c9302c; }"
        )
        no_btn.setStyleSheet(
            "QPushButton { background-color: #6c757d; color: #FFF; border: none;"
            " border-radius: 4px; padding: 8px 24px; font-size: 13px; font-weight: bold; }"
            " QPushButton:hover { background-color: #5a6268; }"
        )
        msg.exec()
        if msg.clickedButton() == yes_btn:
            emp_id = emp.get("employee_id")
            if not emp_id:
                QMessageBox.warning(self, "Error", "Invalid employee ID."); return
            ok = self._backend.delete_employee(emp_id)
            if ok:
                self._load_from_db()
                QMessageBox.information(self, "Success", f"Employee '{name}' removed.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete employee.")

    # ── User Account Management (Admin) ────────────────────
    def _load_user_accounts(self):
        if not hasattr(self, "_users_table"):
            return
        self._users_table.setRowCount(0)
        self._user_account_ids = []
        if not self._backend:
            return
        users = self._backend.get_all_user_accounts() or []
        for u in users:
            r = self._users_table.rowCount()
            self._users_table.insertRow(r)
            self._user_account_ids.append(u["user_id"])
            self._users_table.setItem(r, 0, QTableWidgetItem(str(u["user_id"])))
            self._users_table.setItem(r, 1, QTableWidgetItem(u.get("full_name", "")))
            self._users_table.setItem(r, 2, QTableWidgetItem(u.get("email", "")))
            self._users_table.setItem(r, 3, QTableWidgetItem(u.get("role_name", "")))
            mcp = "Yes" if u.get("must_change_password") else "No"
            mcp_item = QTableWidgetItem(mcp)
            mcp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if u.get("must_change_password"):
                mcp_item.setForeground(QColor("#E8B931"))
            else:
                mcp_item.setForeground(QColor("#5CB85C"))
            self._users_table.setItem(r, 4, mcp_item)

    def _on_create_account(self):
        dlg = UserAccountDialog(self, backend=self._backend)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if self._backend:
                ok, msg = self._backend.admin_create_user_account(
                    d["full_name"], d["email"], d["password"], d["role_name"])
                if ok:
                    QMessageBox.information(self, "Success", msg)
                    self._load_user_accounts()
                else:
                    QMessageBox.warning(self, "Error", msg)

    def _on_reset_password(self):
        if not hasattr(self, "_users_table"):
            return
        row = self._users_table.currentRow()
        if row < 0 or row >= len(self._user_account_ids):
            QMessageBox.warning(self, "Selection", "Select a user account first.")
            return
        uid = self._user_account_ids[row]
        name = self._users_table.item(row, 1).text()
        new_pw, ok_input = QInputDialog.getText(
            self, "Reset Password", f"New password for {name}:",
            QLineEdit.EchoMode.Password)
        if ok_input and new_pw.strip():
            if len(new_pw.strip()) < 4:
                QMessageBox.warning(self, "Validation",
                                    "Password must be at least 4 characters.")
                return
            ok, msg = self._backend.admin_reset_password(uid, new_pw.strip())
            if ok:
                QMessageBox.information(self, "Success", msg)
                self._load_user_accounts()
            else:
                QMessageBox.warning(self, "Error", msg)

    def _on_delete_account(self):
        if not hasattr(self, "_users_table"):
            return
        row = self._users_table.currentRow()
        if row < 0 or row >= len(self._user_account_ids):
            QMessageBox.warning(self, "Selection", "Select a user account to delete.")
            return
        uid = self._user_account_ids[row]
        name = self._users_table.item(row, 1).text()
        email = self._users_table.item(row, 2).text()
        if email == self._backend._current_user_email:
            QMessageBox.warning(self, "Error", "You cannot delete your own account.")
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete user account '{name}'?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            ok, msg = self._backend.admin_delete_user_account(uid)
            if ok:
                QMessageBox.information(self, "Done", msg)
                self._load_user_accounts()
            else:
                QMessageBox.warning(self, "Error", msg)
