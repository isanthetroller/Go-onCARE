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


_EMPLOYEES = [
    ("EMP-001", "Dr. Ana Reyes",      "Doctor",       "Cardiology",      "Full-time", "09171234567", "ana.reyes@carecrud.com",    "Active"),
    ("EMP-002", "Dr. Mark Tan",       "Doctor",       "General Medicine","Full-time", "09179876543", "mark.tan@carecrud.com",     "Active"),
    ("EMP-003", "Dr. Lisa Lim",       "Doctor",       "Dentistry",       "Part-time", "09171112233", "lisa.lim@carecrud.com",     "Active"),
    ("EMP-004", "Sofia Reyes",        "Nurse",        "Cardiology",      "Full-time", "09174445566", "sofia.reyes@carecrud.com",  "Active"),
    ("EMP-005", "James Cruz",         "Receptionist", "Front Desk",      "Full-time", "09177778899", "james.cruz@carecrud.com",   "Active"),
    ("EMP-006", "Maria Garcia",       "Lab Tech",     "Laboratory",      "Full-time", "09173334455", "maria.garcia@carecrud.com", "On Leave"),
    ("EMP-007", "Carlo Santos",       "Admin",        "Management",      "Full-time", "09176667788", "carlo.santos@carecrud.com", "Active"),
    ("EMP-008", "Dr. Pedro Santos",   "Doctor",       "Pediatrics",      "Full-time", "09172223344", "pedro.santos@carecrud.com", "Inactive"),
]


class EmployeeDialog(QDialog):
    def __init__(self, parent=None, *, title="Add Employee", data=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setStyleSheet("QDialog { background: #FFFFFF; } QLabel { color: #2C3E50; font-size: 13px; }")

        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.name_edit = QLineEdit(); self.name_edit.setObjectName("formInput")
        self.name_edit.setPlaceholderText("Full name"); self.name_edit.setMinimumHeight(38)

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

        self.phone_edit = QLineEdit(); self.phone_edit.setObjectName("formInput")
        self.phone_edit.setPlaceholderText("Phone number"); self.phone_edit.setMinimumHeight(38)

        self.email_edit = QLineEdit(); self.email_edit.setObjectName("formInput")
        self.email_edit.setPlaceholderText("Email"); self.email_edit.setMinimumHeight(38)

        self.hire_date = QDateEdit(); self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate()); self.hire_date.setObjectName("formCombo")

        self.status_combo = QComboBox(); self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Active", "On Leave", "Inactive"])
        self.status_combo.setMinimumHeight(38)

        self.notes_edit = QTextEdit(); self.notes_edit.setObjectName("formInput")
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
        return {
            "name":   self.name_edit.text(),
            "role":   self.role_combo.currentText(),
            "dept":   self.dept_combo.currentText(),
            "type":   self.type_combo.currentText(),
            "phone":  self.phone_edit.text(),
            "email":  self.email_edit.text(),
            "status": self.status_combo.currentText(),
        }


class EmployeesPage(QWidget):
    def __init__(self):
        super().__init__()
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #F6F6F2; }")
        inner = QWidget()
        inner.setObjectName("pageInner")
        inner.setStyleSheet("QWidget#pageInner { background-color: #F6F6F2; }")
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
        banner.setStyleSheet(
            "QFrame#pageBanner { background: qlineargradient("
            "x1:0, y1:0, x2:1, y2:0,"
            "stop:0 #388087, stop:1 #6FB3B8);"
            "border-radius: 12px; }"
        )
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(32, 20, 32, 20)
        banner_lay.setSpacing(0)
        tc = QVBoxLayout()
        tc.setSpacing(4)
        title = QLabel("Employee Management")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background: transparent;")
        sub = QLabel("Manage staff, doctors, and personnel")
        sub.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.8); background: transparent;")
        tc.addWidget(title); tc.addWidget(sub)
        banner_lay.addLayout(tc)
        banner_lay.addStretch()

        add_btn = QPushButton("＋  Add Employee")
        add_btn.setMinimumHeight(42)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add)
        add_btn.setStyleSheet(
            "QPushButton { background: rgba(255,255,255,0.2); color: #FFFFFF;"
            "border: 1px solid rgba(255,255,255,0.4); border-radius: 8px;"
            "padding: 8px 18px; font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background: rgba(255,255,255,0.35); }"
        )
        banner_lay.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(banner)

        # ── Stat cards ─────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        for label, val, color in [
            ("Total Staff",   "8",  "#388087"),
            ("Doctors",       "4",  "#6FB3B8"),
            ("Active",        "6",  "#5CB85C"),
            ("On Leave",      "1",  "#E8B931"),
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
        self.table = QTableWidget(len(_EMPLOYEES), len(cols))
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

        for r, row in enumerate(_EMPLOYEES):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                if c == 7:  # status color
                    if val == "Active":
                        item.setForeground(QColor("#5CB85C"))
                    elif val == "On Leave":
                        item.setForeground(QColor("#E8B931"))
                    else:
                        item.setForeground(QColor("#D9534F"))
                self.table.setItem(r, c, item)

            view_btn = make_table_btn("Edit")
            view_btn.clicked.connect(lambda checked, ri=r: self._on_edit(ri))
            self.table.setCellWidget(r, len(row), view_btn)

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
        dlg = EmployeeDialog(self, title="Add Employee")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Employee name is required.")
                return
            row = self.table.rowCount()
            self.table.insertRow(row)
            new_id = f"EMP-{row + 1:03d}"
            values = [new_id, d["name"], d["role"], d["dept"], d["type"], d["phone"], d["email"], d["status"]]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                if c == 7:
                    if val == "Active":
                        item.setForeground(QColor("#5CB85C"))
                    elif val == "On Leave":
                        item.setForeground(QColor("#E8B931"))
                    else:
                        item.setForeground(QColor("#D9534F"))
                self.table.setItem(row, c, item)
            edit_btn = make_table_btn("Edit")
            edit_btn.clicked.connect(lambda checked, ri=row: self._on_edit(ri))
            self.table.setCellWidget(row, 8, edit_btn)
            QMessageBox.information(self, "Success", f"Employee '{d['name']}' added successfully.")

    def _on_edit(self, row: int):
        data = {}
        keys = ["id", "name", "role", "dept", "type", "phone", "email", "status"]
        for c, key in enumerate(keys):
            item = self.table.item(row, c)
            data[key] = item.text() if item else ""
        dlg = EmployeeDialog(self, title="Edit Employee", data=data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Employee name is required.")
                return
            values = [data["id"], d["name"], d["role"], d["dept"], d["type"], d["phone"], d["email"], d["status"]]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                if c == 7:
                    if val == "Active":
                        item.setForeground(QColor("#5CB85C"))
                    elif val == "On Leave":
                        item.setForeground(QColor("#E8B931"))
                    else:
                        item.setForeground(QColor("#D9534F"))
                self.table.setItem(row, c, item)
            QMessageBox.information(self, "Success", f"Employee '{d['name']}' updated successfully.")

    def _on_delete(self, row: int):
        name = self.table.item(row, 1).text() if self.table.item(row, 1) else "this employee"
        QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to remove {name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
