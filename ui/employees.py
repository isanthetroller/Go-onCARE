"""Employee Management page – V2

New: profile view dialog, department filter, on-leave dates, department
count card, performance stats."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QComboBox, QDialog, QFormLayout, QDateEdit, QTabWidget,
    QGraphicsDropShadowEffect, QMessageBox, QTextEdit,
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor
from ui.styles import configure_table, make_table_btn
from backend import AuthBackend


# ══════════════════════════════════════════════════════════════════════
#  Employee Add/Edit Dialog (V2 – leave dates)
# ══════════════════════════════════════════════════════════════════════
class EmployeeDialog(QDialog):
    _INPUT_STYLE = (
        "QLineEdit, QTextEdit { padding: 10px 14px; border: 2px solid #BADFE7;"
        " border-radius: 10px; font-size: 13px; background-color: #FFFFFF;"
        " color: #2C3E50; }"
        "QLineEdit:focus, QTextEdit:focus { border: 2px solid #388087; }"
    )

    def __init__(self, parent=None, *, title="Add Employee", data=None,
                 is_admin: bool = False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
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
        self.role_combo.addItems(["Doctor", "Cashier", "Receptionist", "Lab Tech", "Admin", "Pharmacist", "HR"])
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

        self.phone_edit = QLineEdit()
        self.phone_edit.setStyleSheet(self._INPUT_STYLE)
        self.phone_edit.setPlaceholderText("+639XXXXXXXXX")
        self.phone_edit.setMinimumHeight(38)
        self.phone_edit.setMaxLength(13)
        self.phone_edit.setMinimumWidth(320)

        self.email_edit = QLineEdit()
        self.email_edit.setStyleSheet(self._INPUT_STYLE)
        self.email_edit.setPlaceholderText("Email")
        self.email_edit.setMinimumHeight(38)
        self.email_edit.setMinimumWidth(320)

        self.hire_date = QDateEdit(); self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate()); self.hire_date.setObjectName("formCombo")
        self.hire_date.setMinimumHeight(38)

        self.status_combo = QComboBox(); self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Active", "On Leave", "Inactive"])
        self.status_combo.setMinimumHeight(38)

        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(self._INPUT_STYLE)
        self.notes_edit.setMaximumHeight(70)

        form.addRow("Full Name",   self.name_edit)
        form.addRow("Role",        self.role_combo)
        form.addRow("Department",  self.dept_combo)
        form.addRow("Type",        self.type_combo)
        form.addRow("Phone",       self.phone_edit)
        form.addRow("Email",       self.email_edit)
        form.addRow("Hire Date",   self.hire_date)
        form.addRow("Status",      self.status_combo)
        form.addRow("Notes",       self.notes_edit)

        # Password is auto-generated based on role (e.g. doctor123)
        # No manual password field needed
        self._is_admin = is_admin

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
            self.phone_edit.setText(data.get("phone", ""))
            self.email_edit.setText(data.get("email", ""))

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
        phone = self.phone_edit.text().strip()
        if not re.match(r'^\+63\d{10}$', phone):
            QMessageBox.warning(self, "Validation",
                                "Phone must be in Philippine format: +63 followed by 10 digits\n"
                                "Example: +639171234567")
            return
        super().accept()

    def get_data(self) -> dict:
        d = {
            "name":        self.name_edit.text(),
            "role":        self.role_combo.currentText(),
            "dept":        self.dept_combo.currentText(),
            "type":        self.type_combo.currentText(),
            "phone":       self.phone_edit.text(),
            "email":       self.email_edit.text(),
            "hire_date":   self.hire_date.date().toString("yyyy-MM-dd"),
            "status":      self.status_combo.currentText(),
            "notes":       self.notes_edit.toPlainText(),
        }
        return d


# ══════════════════════════════════════════════════════════════════════
#  Employee Profile Dialog (V2)
# ══════════════════════════════════════════════════════════════════════
class EmployeeProfileDialog(QDialog):
    """Read-only profile with tabs: Info, Appointments, Performance."""

    def __init__(self, parent=None, *, emp_data=None, backend=None):
        super().__init__(parent)
        self.setWindowTitle(f"Employee Profile – {emp_data.get('full_name', '')}")
        self.setMinimumSize(620, 500)
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
            info_lay.addRow(QLabel(f"<b>{label}</b>"), v)
        tabs.addTab(info_w, "Info")

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
            clr = {"Completed": "#5CB85C", "Confirmed": "#388087", "Cancelled": "#D9534F"}.get(a.get("status", ""), "#E8B931")
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
            v = QLabel(val); v.setStyleSheet("color: #388087; font-size: 16px; font-weight: bold;")
            perf_lay.addRow(QLabel(f"<b>{label}</b>"), v)
        tabs.addTab(perf_w, "Performance")

        lay.addWidget(tabs)
        close_btn = QPushButton("Close"); close_btn.setMinimumHeight(38)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)


# ══════════════════════════════════════════════════════════════════════
#  Employees Page
# ══════════════════════════════════════════════════════════════════════
class EmployeesPage(QWidget):
    def __init__(self, backend: AuthBackend | None = None, role: str = "Admin"):
        super().__init__()
        self._backend = backend or AuthBackend()
        self._role = role
        self._employees: list[dict] = []
        self._build()
        self._load_from_db()
        # Auto-refresh data every 10 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_from_db)
        self._refresh_timer.start(10_000)

    def _load_from_db(self):
        rows = self._backend.get_employees() or []
        self._employees = rows
        self.table.setRowCount(0)
        for emp in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            values = [
                str(emp.get("employee_id", "")),
                emp.get("full_name", ""),
                emp.get("role_name", ""),
                emp.get("department_name", ""),
                emp.get("employment_type", ""),
                emp.get("phone", "") or "",
                emp.get("email", "") or "",
                emp.get("status", ""),
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                if c == 7:
                    clr = {"Active": "#5CB85C", "On Leave": "#E8B931"}.get(val, "#D9534F")
                    item.setForeground(QColor(clr))
                self.table.setItem(r, c, item)

            # Actions: View | Edit
            act_w = QWidget()
            act_lay = QHBoxLayout(act_w); act_lay.setContentsMargins(0,0,0,0); act_lay.setSpacing(6)
            view_btn = make_table_btn("View"); view_btn.setFixedWidth(52)
            view_btn.clicked.connect(lambda checked, ri=r: self._on_view(ri))
            act_lay.addWidget(view_btn)
            edit_btn = make_table_btn("Edit"); edit_btn.setFixedWidth(52)
            edit_btn.clicked.connect(lambda checked, ri=r: self._on_edit(ri))
            act_lay.addWidget(edit_btn)
            self.table.setCellWidget(r, 8, act_w)

        # Stat cards
        stats = self._backend.get_employee_stats()
        for key, lbl in self._stat_labels.items():
            lbl.setText(str(stats.get(key, 0) or 0))

        # Department counts
        dept_counts = self._backend.get_department_counts()
        self._dept_table.setRowCount(len(dept_counts))
        for r, d in enumerate(dept_counts):
            self._dept_table.setItem(r, 0, QTableWidgetItem(d.get("department_name", "")))
            self._dept_table.setItem(r, 1, QTableWidgetItem(str(d.get("cnt", 0))))

    def _build(self):
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
        t = QLabel("Employee Management"); t.setObjectName("bannerTitle")
        s = QLabel("Manage staff, doctors, and personnel"); s.setObjectName("bannerSubtitle")
        tc.addWidget(t); tc.addWidget(s)
        banner_lay.addLayout(tc); banner_lay.addStretch()

        add_btn = QPushButton("＋  Add Employee")
        add_btn.setObjectName("bannerBtn"); add_btn.setMinimumHeight(42)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add)
        banner_lay.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(banner)

        # ── Stat cards ────────────────────────────────────────────
        stats_row = QHBoxLayout(); stats_row.setSpacing(16)
        self._stat_labels = {}
        for key, label, color in [
            ("total",    "Total Staff",   "#388087"),
            ("doctors",  "Doctors",       "#6FB3B8"),
            ("active",   "Active",        "#5CB85C"),
            ("on_leave", "On Leave",      "#E8B931"),
        ]:
            card = QFrame(); card.setObjectName("card"); card.setMinimumHeight(100)
            shadow2 = QGraphicsDropShadowEffect()
            shadow2.setBlurRadius(20); shadow2.setOffset(0, 4); shadow2.setColor(QColor(0, 0, 0, 18))
            card.setGraphicsEffect(shadow2)
            cl = QVBoxLayout(card); cl.setContentsMargins(18, 14, 18, 14); cl.setSpacing(4)
            strip = QFrame(); strip.setFixedHeight(3)
            strip.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
            v = QLabel("0"); v.setObjectName("statValue")
            self._stat_labels[key] = v
            l = QLabel(label); l.setObjectName("statLabel")
            cl.addWidget(strip); cl.addWidget(v); cl.addWidget(l)
            stats_row.addWidget(card)
        lay.addLayout(stats_row)

        # ── Department count mini-table ───────────────────────────
        dept_card = QFrame(); dept_card.setObjectName("card")
        dc_lay = QVBoxLayout(dept_card); dc_lay.setContentsMargins(16, 12, 16, 12); dc_lay.setSpacing(8)
        dc_title = QLabel("Staff per Department"); dc_title.setObjectName("cardTitle")
        dc_lay.addWidget(dc_title)
        self._dept_table = QTableWidget(0, 2)
        self._dept_table.setHorizontalHeaderLabels(["Department", "Count"])
        self._dept_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._dept_table.verticalHeader().setVisible(False)
        self._dept_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._dept_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._dept_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._dept_table.setAlternatingRowColors(True)
        self._dept_table.setMaximumHeight(200)
        self._dept_table.verticalHeader().setDefaultSectionSize(48)
        configure_table(self._dept_table)
        dc_lay.addWidget(self._dept_table)
        lay.addWidget(dept_card)

        # ── Filter bar ────────────────────────────────────────────
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setObjectName("searchBar")
        self.search.setPlaceholderText("🔍  Search employees by name, role, or department…")
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(lambda _: self._apply_filters())
        bar.addWidget(self.search)

        self.role_filter = QComboBox()
        self.role_filter.setObjectName("formCombo")
        self.role_filter.addItems(["All Roles", "Doctor", "Cashier", "Receptionist", "Lab Tech", "Admin", "Pharmacist", "HR"])
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
        lay.addLayout(bar)

        # ── Table ─────────────────────────────────────────────────
        cols = ["ID", "Name", "Role", "Department", "Type", "Phone", "Email", "Status", "Actions"]
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
        self.table.setMinimumHeight(420)
        self.table.verticalHeader().setDefaultSectionSize(48)
        configure_table(self.table)

        lay.addWidget(self.table)
        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

    # ── Filters ───────────────────────────────────────────────────
    def _apply_filters(self):
        text = self.search.text().strip().lower()
        role = self.role_filter.currentText()
        dept = self.dept_filter.currentText()
        status = self.status_filter.currentText()
        for r in range(self.table.rowCount()):
            text_match = True
            if text:
                text_match = any(
                    text in (self.table.item(r, c).text().lower() if self.table.item(r, c) else "")
                    for c in range(self.table.columnCount() - 1)
                )
            role_match = role == "All Roles" or (self.table.item(r, 2) and self.table.item(r, 2).text() == role)
            dept_match = dept == "All Departments" or (self.table.item(r, 3) and self.table.item(r, 3).text() == dept)
            status_match = status == "All Status" or (self.table.item(r, 7) and self.table.item(r, 7).text() == status)
            self.table.setRowHidden(r, not (text_match and role_match and dept_match and status_match))

    # ── View Profile ──────────────────────────────────────────────
    def _on_view(self, row: int):
        if row >= len(self._employees):
            return
        emp = self._employees[row]
        dlg = EmployeeProfileDialog(self, emp_data=emp, backend=self._backend)
        dlg.exec()

    # ── Add ───────────────────────────────────────────────────────
    def _on_add(self):
        is_admin = self._role in ("Admin", "HR")
        dlg = EmployeeDialog(self, title="Add Employee", is_admin=is_admin)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Employee name is required.")
                return
            ok = self._backend.add_employee(d)
            if ok is True:
                self._load_from_db()
                QMessageBox.information(self, "Success", f"Employee '{d['name']}' added.")
            else:
                err = ok if isinstance(ok, str) else ''
                QMessageBox.warning(self, "Error", f"Failed to save employee.\n{err}")

    # ── Edit ──────────────────────────────────────────────────────
    def _on_edit(self, row: int):
        data = {}
        keys = ["id", "name", "role", "dept", "type", "phone", "email", "status"]
        for c, key in enumerate(keys):
            item = self.table.item(row, c)
            data[key] = item.text() if item else ""

        is_admin = self._role in ("Admin", "HR")

        dlg = EmployeeDialog(self, title="Edit Employee", data=data,
                             is_admin=is_admin)
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
        name = self.table.item(row, 1).text() if self.table.item(row, 1) else "this employee"
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
            try:
                emp_id = int(self.table.item(row, 0).text())
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "Error", "Invalid employee ID."); return
            ok = self._backend.delete_employee(emp_id)
            if ok:
                self._load_from_db()
                QMessageBox.information(self, "Success", f"Employee '{name}' removed.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete employee.")
