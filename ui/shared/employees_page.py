# Admin employee management page

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDialog, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from ui.styles import (
    make_page_layout, finish_page, make_banner, make_read_only_table,
    make_action_table, make_card, make_stat_card, make_table_btn, status_color,
    make_action_cell,
)
from ui.shared.employee_dialogs import EmployeeDialog, EmployeeProfileDialog
from backend import AuthBackend


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
        if not self.isVisible():
            return
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
                    item.setForeground(QColor(status_color(val)))
                self.table.setItem(r, c, item)

            # Actions: View | Edit
            view_btn = make_table_btn("View")
            view_btn.clicked.connect(lambda checked, ri=r: self._on_view(ri))
            edit_btn = make_table_btn("Edit")
            edit_btn.clicked.connect(lambda checked, ri=r: self._on_edit(ri))
            self.table.setCellWidget(r, 8, make_action_cell(view_btn, edit_btn))

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
        scroll, lay = make_page_layout()

        # ── Banner ────────────────────────────────────────────────
        banner = make_banner(
            "Employee Management",
            "Manage staff, doctors, and personnel",
        )
        banner_lay = banner.layout()

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
            stats_row.addWidget(make_stat_card(key, label, color, self._stat_labels))
        lay.addLayout(stats_row)

        # ── Department count mini-table ───────────────────────────
        dept_card = make_card()
        dc_lay = QVBoxLayout(dept_card); dc_lay.setContentsMargins(16, 12, 16, 12); dc_lay.setSpacing(8)
        dc_title = QLabel("Staff per Department"); dc_title.setObjectName("cardTitle")
        dc_lay.addWidget(dc_title)
        self._dept_table = make_read_only_table(["Department", "Count"], max_h=200, row_h=48)
        dc_lay.addWidget(self._dept_table)
        lay.addWidget(dept_card)

        # ── Filter bar ────────────────────────────────────────────
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setObjectName("searchBar")
        self.search.setPlaceholderText("Search employees by name, role, or department...")
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(lambda _: self._apply_filters())
        bar.addWidget(self.search)

        self.role_filter = QComboBox()
        self.role_filter.setObjectName("formCombo")
        self.role_filter.addItems(["All Roles", "Doctor", "Nurse", "Receptionist", "Admin", "HR"])
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
        self.table = make_action_table(cols)

        lay.addWidget(self.table)
        lay.addStretch()
        finish_page(self, scroll)

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
        dlg = EmployeeProfileDialog(self, emp_data=emp, backend=self._backend, role=self._role)
        dlg.exec()

    # ── Add ───────────────────────────────────────────────────────
    def _on_add(self):
        dlg = EmployeeDialog(self, title="Add Employee")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Employee name is required.")
                return
            # Check for duplicate phone number
            phone = d.get("phone", "").strip()
            if phone and self._backend:
                existing = self._backend.check_duplicate_phone(phone)
                if existing:
                    QMessageBox.warning(self, "Duplicate Phone",
                        f"Phone number {phone} is already assigned to "
                        f"{existing['full_name']} (ID: {existing['employee_id']}).")
                    return
            # Confirmation dialog
            reply = QMessageBox.question(self, "Confirm Add Employee",
                f"Are you sure you want to add '{d['name']}' as a new employee?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
            ok = self._backend.add_employee(d)
            if ok is True:
                # Save doctor schedules if applicable
                if d.get("role") == "Doctor" and d.get("schedules"):
                    emp_id = self._backend.get_employee_id_by_email(d.get("email", ""))
                    if emp_id:
                        self._backend.save_doctor_schedules(emp_id, d["schedules"])
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
        # Load doctor schedules for prefill
        if data.get("role") == "Doctor" and self._backend:
            try:
                emp_id = int(data["id"])
                data["schedules"] = self._backend.get_doctor_schedules(emp_id) or []
            except (ValueError, KeyError):
                data["schedules"] = []

        dlg = EmployeeDialog(self, title="Edit Employee", data=data)
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
            # Save doctor schedules if applicable
            if d.get("role") == "Doctor" and "schedules" in d:
                self._backend.save_doctor_schedules(emp_id, d["schedules"])
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
