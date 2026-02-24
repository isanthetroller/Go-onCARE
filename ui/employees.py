"""Employee Management page."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QComboBox, QDialog, QFormLayout, QDialogButtonBox, QDateEdit,
    QGraphicsDropShadowEffect, QMessageBox, QTextEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from ui.styles import configure_table, make_table_btn
from backend import AuthBackend


# ── Dialog ─────────────────────────────────────────────────────────────

class EmployeeDialog(QDialog):
    """Add / Edit employee dialog.  When *is_admin* is True a password
    field is shown so the admin can view and change the account password."""

    _INPUT_STYLE = (
        "QLineEdit, QTextEdit { padding: 10px 14px; border: 2px solid #BADFE7;"
        " border-radius: 10px; font-size: 13px; background-color: #FFFFFF;"
        " color: #2C3E50; }"
        "QLineEdit:focus, QTextEdit:focus { border: 2px solid #388087; }"
    )

    def __init__(self, parent=None, *, title="Add Employee", data=None,
                 is_admin: bool = False, current_password: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)

        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(self._INPUT_STYLE)
        self.name_edit.setPlaceholderText("Full name")
        self.name_edit.setMinimumHeight(38)

        self.role_combo = QComboBox(); self.role_combo.setObjectName("formCombo")
        self.role_combo.addItems(["Doctor", "Nurse", "Receptionist", "Lab Tech", "Admin", "Pharmacist"])
        self.role_combo.setMinimumHeight(38)

        self.dept_combo = QComboBox(); self.dept_combo.setObjectName("formCombo")
        self.dept_combo.addItems([
            "General Medicine", "Cardiology", "Dentistry", "Pediatrics",
            "Laboratory", "Front Desk", "Management", "Pharmacy",
        ])
        self.dept_combo.setMinimumHeight(38)

        self.type_combo = QComboBox(); self.type_combo.setObjectName("formCombo")
        self.type_combo.addItems(["Full-time", "Part-time", "Contract"])
        self.type_combo.setMinimumHeight(38)

        self.phone_edit = QLineEdit()
        self.phone_edit.setStyleSheet(self._INPUT_STYLE)
        self.phone_edit.setPlaceholderText("Phone number")
        self.phone_edit.setMinimumHeight(38)

        self.email_edit = QLineEdit()
        self.email_edit.setStyleSheet(self._INPUT_STYLE)
        self.email_edit.setPlaceholderText("Email")
        self.email_edit.setMinimumHeight(38)

        self.hire_date = QDateEdit(); self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate()); self.hire_date.setObjectName("formCombo")

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

        # Password field — only visible to admin
        self.password_edit = QLineEdit()
        self.password_edit.setStyleSheet(self._INPUT_STYLE)
        self.password_edit.setPlaceholderText("Account password (leave blank to keep current)")
        self.password_edit.setMinimumHeight(38)
        if is_admin:
            self.password_edit.setText(current_password)
            form.addRow("Password", self.password_edit)
        else:
            self.password_edit.setVisible(False)

        self._is_admin = is_admin

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

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

    def get_data(self) -> dict:
        """Return the current form values as a dict."""
        d = {
            "name":   self.name_edit.text(),
            "role":   self.role_combo.currentText(),
            "dept":   self.dept_combo.currentText(),
            "type":   self.type_combo.currentText(),
            "phone":  self.phone_edit.text(),
            "email":  self.email_edit.text(),
            "status": self.status_combo.currentText(),
        }
        if self._is_admin:
            d["password"] = self.password_edit.text()
        return d


# ── Page ───────────────────────────────────────────────────────────────

class EmployeesPage(QWidget):
    def __init__(self, backend: AuthBackend | None = None, role: str = "Admin"):
        super().__init__()
        self._backend = backend or AuthBackend()
        self._role = role
        self._employees: list[dict] = []
        self._build()
        self._load_from_db()

    # ── Load from database ─────────────────────────────────────────────
    def _load_from_db(self):
        """Fetch employees from the database and populate the table."""
        rows = self._backend.get_employees()
        if not rows:
            return
        self._employees = rows
        self.table.setRowCount(0)
        for emp in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            emp_id = str(emp.get("employee_id", ""))
            values = [
                emp_id,
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
                    if val == "Active":
                        item.setForeground(QColor("#5CB85C"))
                    elif val == "On Leave":
                        item.setForeground(QColor("#E8B931"))
                    else:
                        item.setForeground(QColor("#D9534F"))
                self.table.setItem(r, c, item)
            edit_btn = make_table_btn("Edit")
            edit_btn.clicked.connect(lambda checked, ri=r: self._on_edit(ri))
            self.table.setCellWidget(r, 8, edit_btn)

    # ── UI ─────────────────────────────────────────────────────────────
    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner)
        lay.setSpacing(20)
        lay.setContentsMargins(28, 28, 28, 28)

        # ── Header Banner ──────────────────────────────────────────────
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
        title = QLabel("Employee Management")
        title.setObjectName("bannerTitle")
        sub = QLabel("Manage staff, doctors, and personnel")
        sub.setObjectName("bannerSubtitle")
        tc.addWidget(title); tc.addWidget(sub)
        banner_lay.addLayout(tc)
        banner_lay.addStretch()

        add_btn = QPushButton("＋  Add Employee")
        add_btn.setObjectName("bannerBtn")
        add_btn.setMinimumHeight(42)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add)
        banner_lay.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(banner)

        # ── Stat cards ─────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        for label, val, color in [
            ("Total Staff",   "0",  "#388087"),
            ("Doctors",       "0",  "#6FB3B8"),
            ("Active",        "0",  "#5CB85C"),
            ("On Leave",      "0",  "#E8B931"),
        ]:
            card = QFrame(); card.setObjectName("card"); card.setMinimumHeight(100)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 18))
            card.setGraphicsEffect(shadow)
            cl = QVBoxLayout(card); cl.setContentsMargins(18, 14, 18, 14); cl.setSpacing(4)
            strip = QFrame(); strip.setFixedHeight(3)
            strip.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
            v = QLabel(val); v.setObjectName("statValue"); v.setStyleSheet("font-size: 22px;")
            l = QLabel(label); l.setObjectName("statLabel")
            cl.addWidget(strip); cl.addWidget(v); cl.addWidget(l)
            stats_row.addWidget(card)
        lay.addLayout(stats_row)

        # ── Filter bar ─────────────────────────────────────────────────
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setObjectName("searchBar")
        self.search.setPlaceholderText("🔍  Search employees by name, role, or department…")
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(self._on_search)
        bar.addWidget(self.search)

        self.role_filter = QComboBox()
        self.role_filter.setObjectName("formCombo")
        self.role_filter.addItems(["All Roles", "Doctor", "Nurse", "Receptionist", "Lab Tech", "Admin"])
        self.role_filter.setMinimumHeight(42); self.role_filter.setMinimumWidth(140)
        bar.addWidget(self.role_filter)

        self.status_filter = QComboBox()
        self.status_filter.setObjectName("formCombo")
        self.status_filter.addItems(["All Status", "Active", "On Leave", "Inactive"])
        self.status_filter.setMinimumHeight(42); self.status_filter.setMinimumWidth(140)
        bar.addWidget(self.status_filter)
        lay.addLayout(bar)

        # ── Table ──────────────────────────────────────────────────────
        cols = ["ID", "Name", "Role", "Department", "Type", "Phone", "Email", "Status", "Actions"]
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(len(cols)-1, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(len(cols)-1, 120)
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

    # ── Slots ──────────────────────────────────────────────────────────
    def _on_search(self, text: str):
        text = text.lower()
        for r in range(self.table.rowCount()):
            match = any(
                text in (self.table.item(r, c).text().lower() if self.table.item(r, c) else "")
                for c in range(self.table.columnCount() - 1)
            )
            self.table.setRowHidden(r, not match)

    def _on_add(self):
        is_admin = self._role == "Admin"
        dlg = EmployeeDialog(self, title="Add Employee", is_admin=is_admin)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Employee name is required.")
                return
            ok = self._backend.add_employee(d)
            if ok:
                self._load_from_db()
                QMessageBox.information(self, "Success", f"Employee '{d['name']}' added successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to save employee to database.")

    def _on_edit(self, row: int):
        data = {}
        keys = ["id", "name", "role", "dept", "type", "phone", "email", "status"]
        for c, key in enumerate(keys):
            item = self.table.item(row, c)
            data[key] = item.text() if item else ""

        is_admin = self._role == "Admin"
        current_pw = ""
        if is_admin and data.get("email"):
            current_pw = self._backend.get_user_password(data["email"])

        dlg = EmployeeDialog(self, title="Edit Employee", data=data,
                             is_admin=is_admin, current_password=current_pw)
        if dlg.exec() == QDialog.DialogCode.Accepted:
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
            if not ok:
                QMessageBox.warning(self, "Error", "Failed to update employee in database.")
                return
            # Update password if admin changed it
            if is_admin and d.get("password") and d["password"] != current_pw:
                email_for_pw = d.get("email") or old_email
                if email_for_pw:
                    self._backend.update_user_password(email_for_pw, d["password"])
            self._load_from_db()
            QMessageBox.information(self, "Success", f"Employee '{d['name']}' updated successfully.")

    def _on_delete(self, row: int):
        name = self.table.item(row, 1).text() if self.table.item(row, 1) else "this employee"
        QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to remove {name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
