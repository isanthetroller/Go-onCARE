"""HR Employee Management page – detailed employee management for HR role.

Includes: salary management, leave tracking, payroll summary,
employment type breakdown, enhanced employee profiles, and full CRUD
with HR-specific fields (salary, emergency contact, password)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QComboBox, QDialog, QFormLayout, QDateEdit, QTabWidget,
    QGraphicsDropShadowEffect, QMessageBox, QTextEdit,
    QDoubleSpinBox, QCheckBox,
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor
from ui.styles import configure_table, make_table_btn
from backend import AuthBackend


# ══════════════════════════════════════════════════════════════════════
#  HR Employee Add/Edit Dialog (extended with salary & emergency contact)
# ══════════════════════════════════════════════════════════════════════
class HREmployeeDialog(QDialog):
    _INPUT_STYLE = (
        "QLineEdit, QTextEdit { padding: 10px 14px; border: 2px solid #BADFE7;"
        " border-radius: 10px; font-size: 13px; background-color: #FFFFFF;"
        " color: #2C3E50; }"
        "QLineEdit:focus, QTextEdit:focus { border: 2px solid #388087; }"
    )

    def __init__(self, parent=None, *, title="Add Employee", data=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(640)
        self._fired = False

        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(self._INPUT_STYLE)
        self.name_edit.setPlaceholderText("Full name")
        self.name_edit.setMinimumHeight(38)
        self.name_edit.setMinimumWidth(320)

        self.role_combo = QComboBox(); self.role_combo.setObjectName("formCombo")
        self.role_combo.addItems(["Doctor", "Cashier", "Receptionist",
                                  "Admin", "HR"])
        self.role_combo.setMinimumHeight(38)

        self.dept_combo = QComboBox(); self.dept_combo.setObjectName("formCombo")
        self.dept_combo.addItems([
            "General Medicine", "Cardiology", "Dentistry", "Pediatrics",
            "Laboratory", "Front Desk", "Management", "Pharmacy", "Human Resources",
        ])
        self.dept_combo.setMinimumHeight(38)

        self.type_combo = QComboBox(); self.type_combo.setObjectName("formCombo")
        self.type_combo.addItems(["Full-time", "Part-time", "Contract"])
        self.type_combo.setMinimumHeight(38)

        # Phone: permanent +63 prefix + 10-digit input
        self._phone_row = QWidget()
        phone_lay = QHBoxLayout(self._phone_row)
        phone_lay.setContentsMargins(0, 0, 0, 0)
        phone_lay.setSpacing(0)
        self._phone_prefix = QLabel("+63")
        self._phone_prefix.setStyleSheet(
            "QLabel { padding: 10px 10px; border: 2px solid #BADFE7;"
            " border-right: none; border-radius: 10px 0px 0px 10px;"
            " font-size: 13px; font-weight: bold; background: #F0F7F8;"
            " color: #2C3E50; }"
        )
        self._phone_prefix.setFixedHeight(38)
        self.phone_edit = QLineEdit()
        self.phone_edit.setStyleSheet(
            "QLineEdit { padding: 10px 14px; border: 2px solid #BADFE7;"
            " border-left: none; border-radius: 0px 10px 10px 0px;"
            " font-size: 13px; background-color: #FFFFFF; color: #2C3E50; }"
            "QLineEdit:focus { border: 2px solid #388087; border-left: none; }"
        )
        self.phone_edit.setPlaceholderText("9XXXXXXXXX")
        self.phone_edit.setMinimumHeight(38)
        self.phone_edit.setMaxLength(10)
        phone_lay.addWidget(self._phone_prefix)
        phone_lay.addWidget(self.phone_edit, 1)

        self.email_edit = QLineEdit()
        self.email_edit.setStyleSheet(self._INPUT_STYLE)
        self.email_edit.setPlaceholderText("Email")
        self.email_edit.setMinimumHeight(38)
        self.email_edit.setMinimumWidth(320)

        self.hire_date = QDateEdit(); self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate()); self.hire_date.setObjectName("formCombo")
        self.hire_date.setMaximumDate(QDate.currentDate())  # Cannot hire in the future
        self.hire_date.setMinimumHeight(38)

        self.status_combo = QComboBox(); self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Active", "On Leave", "Inactive"])
        self.status_combo.setMinimumHeight(38)

        # HR-specific fields
        self.salary_spin = QDoubleSpinBox()
        self.salary_spin.setObjectName("formCombo")
        self.salary_spin.setRange(0, 999999.99)
        self.salary_spin.setDecimals(2)
        self.salary_spin.setPrefix("₱ ")
        self.salary_spin.setSingleStep(1000)
        self.salary_spin.setMinimumHeight(38)

        self.emergency_edit = QLineEdit()
        self.emergency_edit.setStyleSheet(self._INPUT_STYLE)
        self.emergency_edit.setPlaceholderText("Emergency contact (name – phone)")
        self.emergency_edit.setMinimumHeight(38)

        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(self._INPUT_STYLE)
        self.notes_edit.setMaximumHeight(70)

        # Password is auto-generated based on role (e.g. doctor123)
        # No manual password field needed

        form.addRow("Full Name",          self.name_edit)
        form.addRow("Role",               self.role_combo)
        form.addRow("Department",         self.dept_combo)
        form.addRow("Type",               self.type_combo)
        form.addRow("Phone",              self._phone_row)
        form.addRow("Email",              self.email_edit)
        form.addRow("Hire Date",          self.hire_date)
        form.addRow("Status",             self.status_combo)
        form.addRow("Monthly Salary",     self.salary_spin)
        form.addRow("Emergency Contact",  self.emergency_edit)
        form.addRow("Notes",              self.notes_edit)

        # Buttons
        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
        if data:
            fire_btn = QPushButton("🔥  Fire")
            fire_btn.setMinimumHeight(32); fire_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            fire_btn.setObjectName("dialogDangerBtn")
            fire_btn.clicked.connect(self._on_fire)
            btn_row.addWidget(fire_btn)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel"); cancel_btn.setMinimumHeight(32)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setObjectName("dialogCancelBtn")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save"); save_btn.setMinimumHeight(32)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setObjectName("dialogSaveBtn")
        save_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn); btn_row.addWidget(save_btn)
        form.addRow(btn_row)

        # Pre-fill data
        if data:
            self.name_edit.setText(data.get("name", ""))
            for combo, key in [
                (self.role_combo, "role"), (self.dept_combo, "dept"),
                (self.type_combo, "type"), (self.status_combo, "status"),
            ]:
                idx = combo.findText(data.get(key, ""))
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            raw_phone = data.get("phone", "")
            if raw_phone.startswith("+63"):
                raw_phone = raw_phone[3:]
            self.phone_edit.setText(raw_phone)
            self.email_edit.setText(data.get("email", ""))
            self.emergency_edit.setText(data.get("emergency_contact", ""))
            try:
                self.salary_spin.setValue(float(data.get("salary", 0) or 0))
            except (ValueError, TypeError):
                self.salary_spin.setValue(0)
            if data.get("notes"):
                self.notes_edit.setPlainText(data["notes"])

    def _on_fire(self):
        self._fired = True; self.reject()

    @property
    def fired(self) -> bool:
        return self._fired

    def accept(self):
        import re
        from PyQt6.QtWidgets import QMessageBox
        # All fields required
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Full Name is required."); return
        if not self.phone_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Phone number is required."); return
        if not self.email_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Email is required."); return
        digits = self.phone_edit.text().strip()
        if not re.match(r'^\d{10}$', digits):
            QMessageBox.warning(self, "Validation",
                                "Enter exactly 10 digits after +63\n"
                                "Example: 9171234567")
            return
        super().accept()

    def get_data(self) -> dict:
        sal = self.salary_spin.value()
        return {
            "name":              self.name_edit.text(),
            "role":              self.role_combo.currentText(),
            "dept":              self.dept_combo.currentText(),
            "type":              self.type_combo.currentText(),
            "phone":             "+63" + self.phone_edit.text().strip(),
            "email":             self.email_edit.text(),
            "hire_date":         self.hire_date.date().toString("yyyy-MM-dd"),
            "status":            self.status_combo.currentText(),
            "salary":            sal if sal > 0 else None,
            "emergency_contact": self.emergency_edit.text(),
            "notes":             self.notes_edit.toPlainText(),
        }


# ══════════════════════════════════════════════════════════════════════
#  HR Employee Profile Dialog (enhanced with salary, emergency contact)
# ══════════════════════════════════════════════════════════════════════
class HREmployeeProfileDialog(QDialog):
    """Full HR profile with tabs: Info, Salary & HR, Appointments, Performance."""

    def __init__(self, parent=None, *, emp_data=None, backend=None):
        super().__init__(parent)
        self.setWindowTitle(f"Employee Profile – {emp_data.get('full_name', '')}")
        self.setMinimumSize(680, 560)
        self._backend = backend
        self._emp = emp_data or {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)

        tabs = QTabWidget()

        # ── Info Tab ──────────────────────────────────────────────
        info_w = QWidget()
        info_lay = QFormLayout(info_w)
        info_lay.setSpacing(10)
        fields = [
            ("Name",       self._emp.get("full_name", "")),
            ("Role",       self._emp.get("role_name", "")),
            ("Department", self._emp.get("department_name", "")),
            ("Type",       self._emp.get("employment_type", "")),
            ("Phone",      self._emp.get("phone", "") or "—"),
            ("Email",      self._emp.get("email", "") or "—"),
            ("Hire Date",  str(self._emp.get("hire_date", "")) or "—"),
            ("Status",     self._emp.get("status", "")),
            ("Notes",      self._emp.get("notes", "") or "—"),
        ]
        for label, value in fields:
            v = QLabel(str(value)); v.setWordWrap(True)
            v.setStyleSheet("color: #2C3E50; font-size: 13px;")
            lbl = QLabel(f"<b>{label}</b>")
            # Color-code status
            if label == "Status":
                clr = {"Active": "#5CB85C", "On Leave": "#E8B931"}.get(str(value), "#D9534F")
                v.setStyleSheet(f"color: {clr}; font-size: 13px; font-weight: bold;")
            info_lay.addRow(lbl, v)
        tabs.addTab(info_w, "Info")

        # ── Salary & HR Tab ──────────────────────────────────────
        hr_w = QWidget()
        hr_lay = QFormLayout(hr_w)
        hr_lay.setSpacing(10)
        salary = self._emp.get("salary", 0) or 0
        emergency = self._emp.get("emergency_contact", "") or "—"
        hr_fields = [
            ("Monthly Salary",    f"₱{float(salary):,.2f}" if salary else "Not set"),
            ("Annual Salary",     f"₱{float(salary) * 12:,.2f}" if salary else "Not set"),
            ("Emergency Contact", emergency),
            ("Employment Type",   self._emp.get("employment_type", "")),
            ("Hire Date",         str(self._emp.get("hire_date", "")) or "—"),
        ]
        # Calculate tenure
        hire = self._emp.get("hire_date")
        if hire:
            try:
                from datetime import date
                if hasattr(hire, 'year'):
                    hd = hire
                else:
                    hd = date.fromisoformat(str(hire))
                today = date.today()
                years = today.year - hd.year
                months = today.month - hd.month
                if months < 0:
                    years -= 1
                    months += 12
                hr_fields.append(("Tenure", f"{years} year(s), {months} month(s)"))
            except Exception:
                hr_fields.append(("Tenure", "—"))

        for label, value in hr_fields:
            v = QLabel(str(value)); v.setWordWrap(True)
            if "Salary" in label:
                v.setStyleSheet("color: #388087; font-size: 15px; font-weight: bold;")
            else:
                v.setStyleSheet("color: #2C3E50; font-size: 13px;")
            hr_lay.addRow(QLabel(f"<b>{label}</b>"), v)
        tabs.addTab(hr_w, "Salary & HR")

        # ── Appointments Tab ─────────────────────────────────────
        appt_w = QWidget()
        appt_lay = QVBoxLayout(appt_w); appt_lay.setContentsMargins(8, 8, 8, 8)
        emp_id = self._emp.get("employee_id", 0)
        appts = self._backend.get_employee_appointments(emp_id) if self._backend else []
        cols = ["Date", "Time", "Patient", "Service", "Status"]
        at = QTableWidget(len(appts), len(cols))
        at.setHorizontalHeaderLabels(cols)
        at.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        at.verticalHeader().setVisible(False)
        at.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        at.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        at.setAlternatingRowColors(True)
        at.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        at.verticalHeader().setDefaultSectionSize(48)
        configure_table(at)
        for r, a in enumerate(appts):
            at.setItem(r, 0, QTableWidgetItem(str(a.get("appointment_date", ""))))
            t = a.get("appointment_time", "")
            if hasattr(t, "total_seconds"):
                total = int(t.total_seconds()); h, m = divmod(total // 60, 60)
                t = f"{h:02d}:{m:02d}"
            at.setItem(r, 1, QTableWidgetItem(str(t)))
            at.setItem(r, 2, QTableWidgetItem(a.get("patient_name", "")))
            at.setItem(r, 3, QTableWidgetItem(a.get("service_name", "")))
            si = QTableWidgetItem(a.get("status", ""))
            clr = {"Completed": "#5CB85C", "Confirmed": "#388087",
                   "Cancelled": "#D9534F"}.get(a.get("status", ""), "#E8B931")
            si.setForeground(QColor(clr))
            at.setItem(r, 4, si)
        appt_lay.addWidget(at)
        tabs.addTab(appt_w, f"Appointments ({len(appts)})")

        # ── Performance Tab ──────────────────────────────────────
        perf_w = QWidget()
        perf_lay = QFormLayout(perf_w); perf_lay.setSpacing(10)
        perf = self._backend.get_employee_performance(emp_id) if self._backend else {}
        perf_fields = [
            ("Total Appointments", str(perf.get("total_appts", 0))),
            ("Completed",          str(perf.get("completed", 0))),
            ("Revenue Generated",  f"₱{float(perf.get('revenue', 0)):,.0f}"),
        ]
        for label, val in perf_fields:
            v = QLabel(val)
            v.setStyleSheet("color: #388087; font-size: 16px; font-weight: bold;")
            perf_lay.addRow(QLabel(f"<b>{label}</b>"), v)
        tabs.addTab(perf_w, "Performance")

        lay.addWidget(tabs)
        close_btn = QPushButton("Close"); close_btn.setMinimumHeight(38)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)


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

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget(); inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner)
        lay.setSpacing(14); lay.setContentsMargins(24, 20, 24, 20)

        # ── Banner ────────────────────────────────────────────────
        banner = QFrame(); banner.setObjectName("pageBanner"); banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(32, 20, 32, 20); banner_lay.setSpacing(0)
        tc = QVBoxLayout(); tc.setSpacing(4)
        t = QLabel("HR Employee Management"); t.setObjectName("bannerTitle")
        s = QLabel("Comprehensive staff management – salary, leave, performance")
        s.setObjectName("bannerSubtitle")
        tc.addWidget(t); tc.addWidget(s)
        banner_lay.addLayout(tc); banner_lay.addStretch()
        lay.addWidget(banner)

        # ── Stat cards (6 cards) ──────────────────────────────────
        stats_row = QHBoxLayout(); stats_row.setSpacing(14)
        self._stat_labels = {}
        for key, label, color in [
            ("total",         "Total Staff",    "#388087"),
            ("active",        "Active",         "#5CB85C"),
            ("on_leave",      "On Leave",       "#E8B931"),
            ("inactive",      "Inactive",       "#D9534F"),
            ("avg_salary",    "Avg Salary",     "#6FB3B8"),
            ("total_payroll", "Total Payroll",   "#388087"),
        ]:
            card = QFrame(); card.setObjectName("card"); card.setMinimumHeight(80)
            shadow2 = QGraphicsDropShadowEffect()
            shadow2.setBlurRadius(20); shadow2.setOffset(0, 4)
            shadow2.setColor(QColor(0, 0, 0, 18))
            card.setGraphicsEffect(shadow2)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(18, 14, 18, 14); cl.setSpacing(4)
            strip = QFrame(); strip.setFixedHeight(3)
            strip.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
            v = QLabel("0"); v.setObjectName("statValue")
            self._stat_labels[key] = v
            l = QLabel(label); l.setObjectName("statLabel")
            cl.addWidget(strip); cl.addWidget(v); cl.addWidget(l)
            stats_row.addWidget(card)
        lay.addLayout(stats_row)

        # ── Secondary panels row: Leave Tracker + Dept Payroll + Type Breakdown ──
        panels_row = QHBoxLayout(); panels_row.setSpacing(16)

        # Leave tracker
        leave_card = QFrame(); leave_card.setObjectName("card")
        lc_shadow = QGraphicsDropShadowEffect()
        lc_shadow.setBlurRadius(16); lc_shadow.setOffset(0, 3)
        lc_shadow.setColor(QColor(0, 0, 0, 15))
        leave_card.setGraphicsEffect(lc_shadow)
        lc_lay = QVBoxLayout(leave_card)
        lc_lay.setContentsMargins(16, 12, 16, 12); lc_lay.setSpacing(8)
        lc_title = QLabel("Leave Tracker"); lc_title.setObjectName("cardTitle")
        lc_lay.addWidget(lc_title)
        self._leave_table = QTableWidget(0, 4)
        self._leave_table.setHorizontalHeaderLabels(["Employee", "Department", "From", "Until"])
        self._leave_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._leave_table.verticalHeader().setVisible(False)
        self._leave_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._leave_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._leave_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._leave_table.setAlternatingRowColors(True)
        self._leave_table.setMaximumHeight(130)
        self._leave_table.verticalHeader().setDefaultSectionSize(36)
        configure_table(self._leave_table)
        lc_lay.addWidget(self._leave_table)
        panels_row.addWidget(leave_card, 2)

        # Department payroll
        dept_card = QFrame(); dept_card.setObjectName("card")
        dc_shadow = QGraphicsDropShadowEffect()
        dc_shadow.setBlurRadius(16); dc_shadow.setOffset(0, 3)
        dc_shadow.setColor(QColor(0, 0, 0, 15))
        dept_card.setGraphicsEffect(dc_shadow)
        dc_lay = QVBoxLayout(dept_card)
        dc_lay.setContentsMargins(16, 12, 16, 12); dc_lay.setSpacing(8)
        dc_title = QLabel("Department Payroll"); dc_title.setObjectName("cardTitle")
        dc_lay.addWidget(dc_title)
        self._dept_table = QTableWidget(0, 4)
        self._dept_table.setHorizontalHeaderLabels(["Department", "Headcount", "Total Salary", "Avg Salary"])
        self._dept_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._dept_table.verticalHeader().setVisible(False)
        self._dept_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._dept_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._dept_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._dept_table.setAlternatingRowColors(True)
        self._dept_table.setMaximumHeight(130)
        self._dept_table.verticalHeader().setDefaultSectionSize(36)
        configure_table(self._dept_table)
        dc_lay.addWidget(self._dept_table)
        panels_row.addWidget(dept_card, 2)

        # Employment type breakdown
        type_card = QFrame(); type_card.setObjectName("card")
        tc_shadow = QGraphicsDropShadowEffect()
        tc_shadow.setBlurRadius(16); tc_shadow.setOffset(0, 3)
        tc_shadow.setColor(QColor(0, 0, 0, 15))
        type_card.setGraphicsEffect(tc_shadow)
        tc_lay2 = QVBoxLayout(type_card)
        tc_lay2.setContentsMargins(16, 12, 16, 12); tc_lay2.setSpacing(8)
        tc_title = QLabel("Employment Types"); tc_title.setObjectName("cardTitle")
        tc_lay2.addWidget(tc_title)
        self._type_table = QTableWidget(0, 2)
        self._type_table.setHorizontalHeaderLabels(["Type", "Count"])
        self._type_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._type_table.verticalHeader().setVisible(False)
        self._type_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._type_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._type_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._type_table.setAlternatingRowColors(True)
        self._type_table.setMaximumHeight(130)
        self._type_table.verticalHeader().setDefaultSectionSize(36)
        configure_table(self._type_table)
        tc_lay2.addWidget(self._type_table)
        panels_row.addWidget(type_card, 1)

        lay.addLayout(panels_row)

        # ── Leave Requests Management ─────────────────────────────
        lr_card = QFrame(); lr_card.setObjectName("card")
        lr_shadow = QGraphicsDropShadowEffect()
        lr_shadow.setBlurRadius(20); lr_shadow.setOffset(0, 4)
        lr_shadow.setColor(QColor(0, 0, 0, 18))
        lr_card.setGraphicsEffect(lr_shadow)
        lr_lay = QVBoxLayout(lr_card)
        lr_lay.setContentsMargins(16, 12, 16, 12); lr_lay.setSpacing(8)
        lr_header = QHBoxLayout()
        lr_title = QLabel("Leave Requests"); lr_title.setObjectName("cardTitle")
        lr_header.addWidget(lr_title)
        self._lr_status_filter = QComboBox()
        self._lr_status_filter.setObjectName("formCombo")
        self._lr_status_filter.addItems(["Pending", "All", "Approved", "Declined"])
        self._lr_status_filter.setMinimumHeight(34); self._lr_status_filter.setMinimumWidth(110)
        self._lr_status_filter.currentTextChanged.connect(lambda _: self._load_leave_requests())
        lr_header.addStretch()
        lr_header.addWidget(self._lr_status_filter)
        lr_lay.addLayout(lr_header)

        self._lr_table = QTableWidget(0, 8)
        self._lr_table.setHorizontalHeaderLabels([
            "Employee", "Role", "Department", "From", "Until", "Reason", "Status", "Actions"])
        self._lr_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._lr_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self._lr_table.setColumnWidth(7, 170)
        self._lr_table.horizontalHeader().setStretchLastSection(False)
        self._lr_table.verticalHeader().setVisible(False)
        self._lr_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._lr_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._lr_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._lr_table.setAlternatingRowColors(True)
        self._lr_table.setMinimumHeight(120)
        self._lr_table.verticalHeader().setDefaultSectionSize(42)
        configure_table(self._lr_table)
        lr_lay.addWidget(self._lr_table)
        lay.addWidget(lr_card)

        # ── Filter bar ────────────────────────────────────────────
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setObjectName("searchBar")
        self.search.setPlaceholderText("🔍  Search employees by name, role, department, email…")
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(lambda _: self._apply_filters())
        bar.addWidget(self.search)

        self.role_filter = QComboBox()
        self.role_filter.setObjectName("formCombo")
        self.role_filter.addItems(["All Roles", "Doctor", "Cashier", "Receptionist",
                                   "Admin", "HR"])
        self.role_filter.setMinimumHeight(42); self.role_filter.setMinimumWidth(140)
        self.role_filter.currentTextChanged.connect(lambda _: self._apply_filters())
        bar.addWidget(self.role_filter)

        self.dept_filter = QComboBox()
        self.dept_filter.setObjectName("formCombo")
        self.dept_filter.addItems([
            "All Departments", "General Medicine", "Cardiology", "Dentistry",
            "Pediatrics", "Laboratory", "Front Desk", "Management", "Pharmacy",
            "Human Resources",
        ])
        self.dept_filter.setMinimumHeight(42); self.dept_filter.setMinimumWidth(160)
        self.dept_filter.currentTextChanged.connect(lambda _: self._apply_filters())
        bar.addWidget(self.dept_filter)

        self.status_filter = QComboBox()
        self.status_filter.setObjectName("formCombo")
        self.status_filter.addItems(["All Status", "Active", "On Leave", "Inactive"])
        self.status_filter.setMinimumHeight(42); self.status_filter.setMinimumWidth(140)
        self.status_filter.currentTextChanged.connect(lambda _: self._apply_filters())
        bar.addWidget(self.status_filter)

        self.type_filter = QComboBox()
        self.type_filter.setObjectName("formCombo")
        self.type_filter.addItems(["All Types", "Full-time", "Part-time", "Contract"])
        self.type_filter.setMinimumHeight(42); self.type_filter.setMinimumWidth(130)
        self.type_filter.currentTextChanged.connect(lambda _: self._apply_filters())
        bar.addWidget(self.type_filter)
        lay.addLayout(bar)

        # ── Main Table ────────────────────────────────────────────
        cols = ["ID", "Name", "Role", "Department", "Type", "Phone", "Email",
                "Hire Date", "Salary", "Status", "Actions"]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(len(cols)-1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(len(cols)-1, 130)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(300)
        self.table.verticalHeader().setDefaultSectionSize(44)
        configure_table(self.table)

        lay.addWidget(self.table)
        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

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
