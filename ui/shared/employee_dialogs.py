# Employee dialogs - add/edit form + profile view (Admin version)

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QDateEdit, QTabWidget, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate, QEvent
from PyQt6.QtGui import QColor
from ui.styles import configure_table, make_table_btn


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
        self.role_combo.addItems(["Doctor", "Cashier", "Receptionist", "Admin", "HR"])
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

        # Phone: container frame with unified border
        self._phone_frame = QFrame()
        self._phone_frame.setObjectName("phoneFrame")
        self._phone_normal_ss = (
            "QFrame#phoneFrame { border: 2px solid #BADFE7; border-radius: 10px;"
            " background: #FFFFFF; }"
        )
        self._phone_focus_ss = (
            "QFrame#phoneFrame { border: 2px solid #388087; border-radius: 10px;"
            " background: #FFFFFF; }"
        )
        self._phone_frame.setStyleSheet(self._phone_normal_ss)
        self._phone_frame.setFixedHeight(42)
        phone_lay = QHBoxLayout(self._phone_frame)
        phone_lay.setContentsMargins(0, 0, 0, 0)
        phone_lay.setSpacing(0)
        self._phone_prefix = QLabel("+63")
        self._phone_prefix.setStyleSheet(
            "QLabel { padding: 0px 10px; border: none;"
            " font-size: 13px; font-weight: bold; background: #F0F7F8;"
            " border-top-left-radius: 8px; border-bottom-left-radius: 8px;"
            " color: #2C3E50; }"
        )
        self.phone_edit = QLineEdit()
        self.phone_edit.setStyleSheet(
            "QLineEdit { padding: 0px 14px; border: none;"
            " font-size: 13px; background-color: transparent; color: #2C3E50; }"
        )
        self.phone_edit.setPlaceholderText("9XXXXXXXXX")
        self.phone_edit.setMaxLength(10)
        self.phone_edit.installEventFilter(self)
        phone_lay.addWidget(self._phone_prefix)
        phone_lay.addWidget(self.phone_edit, 1)

        self.email_edit = QLineEdit()
        self.email_edit.setStyleSheet(self._INPUT_STYLE)
        self.email_edit.setPlaceholderText("Email")
        self.email_edit.setMinimumHeight(38)
        self.email_edit.setMinimumWidth(320)

        self.hire_date = QDateEdit(); self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate()); self.hire_date.setObjectName("formCombo")
        self.hire_date.setMaximumDate(QDate.currentDate())
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
        form.addRow("Phone",       self._phone_frame)
        form.addRow("Email",       self.email_edit)
        form.addRow("Hire Date",   self.hire_date)
        form.addRow("Status",      self.status_combo)
        form.addRow("Notes",       self.notes_edit)

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
            raw_phone = data.get("phone", "")
            if raw_phone.startswith("+63"):
                raw_phone = raw_phone[3:]
            self.phone_edit.setText(raw_phone)
            self.email_edit.setText(data.get("email", ""))

    def _on_fire(self):
        self._fired = True; self.reject()

    @property
    def fired(self) -> bool:
        return self._fired

    def eventFilter(self, obj, event):
        if obj is self.phone_edit:
            if event.type() == QEvent.Type.FocusIn:
                self._phone_frame.setStyleSheet(self._phone_focus_ss)
            elif event.type() == QEvent.Type.FocusOut:
                self._phone_frame.setStyleSheet(self._phone_normal_ss)
        return super().eventFilter(obj, event)

    def accept(self):
        import re
        from PyQt6.QtWidgets import QMessageBox
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
        d = {
            "name":        self.name_edit.text(),
            "role":        self.role_combo.currentText(),
            "dept":        self.dept_combo.currentText(),
            "type":        self.type_combo.currentText(),
            "phone":       "+63" + self.phone_edit.text().strip(),
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

    def __init__(self, parent=None, *, emp_data=None, backend=None, role: str = "Admin"):
        super().__init__(parent)
        self.setWindowTitle(f"Employee Profile – {emp_data.get('full_name', '')}")
        self.setMinimumSize(620, 500)
        self._backend = backend
        self._emp = emp_data or {}
        self._role = role

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
        if self._role != "Receptionist":
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
