# HR employee dialogs - add/edit + profile with salary & HR tab

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QDateEdit, QTabWidget, QMessageBox, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, QDate, QEvent
from PyQt6.QtGui import QColor
from ui.styles import configure_table, style_dialog_btns, status_color
from ui.shared.employee_dialogs import EmployeeDialog


# ══════════════════════════════════════════════════════════════════════
#  HR Employee Add/Edit Dialog (extends EmployeeDialog with salary &
#  emergency contact fields)
# ══════════════════════════════════════════════════════════════════════
class HREmployeeDialog(EmployeeDialog):

    def __init__(self, parent=None, *, title="Add Employee", data=None):
        super().__init__(parent, title=title, data=data)

    # ── Override hooks ────────────────────────────────────────────
    def _build_fields(self, _unused):
        super()._build_fields(_unused)
        # Replace the plain salary_edit with a QDoubleSpinBox on the right column
        right = self._right_form
        self.salary_edit.setVisible(False)
        self.salary_spin = QDoubleSpinBox()
        self.salary_spin.setObjectName("formCombo")
        self.salary_spin.setRange(0, 999999.99)
        self.salary_spin.setDecimals(2)
        self.salary_spin.setPrefix("₱ ")
        self.salary_spin.setSingleStep(1000)
        self.salary_spin.setMinimumHeight(38)
        # Find and replace salary row in right form
        for r in range(right.rowCount()):
            lbl = right.itemAt(r, QFormLayout.ItemRole.LabelRole)
            if lbl and hasattr(lbl, 'widget') and lbl.widget() and lbl.widget().text() == "Salary":
                lbl.widget().setVisible(False)  # Hide the original "Salary" label
                right.insertRow(r + 1, "Monthly Salary", self.salary_spin)
                return
        # Fallback: append
        right.addRow("Monthly Salary", self.salary_spin)

    def _prefill(self, data):
        super()._prefill(data)
        try:
            self.salary_spin.setValue(float(data.get("salary", 0) or 0))
        except (ValueError, TypeError):
            self.salary_spin.setValue(0)
        if data.get("notes"):
            self.notes_edit.setPlainText(data["notes"])

    def get_data(self) -> dict:
        d = super().get_data()
        sal = self.salary_spin.value()
        d["salary"] = sal if sal > 0 else None
        d["emergency_contact"] = self.emergency_edit.text()
        return d


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
            ("Address",    self._emp.get("address", "") or "—"),
            ("Hire Date",  str(self._emp.get("hire_date", "")) or "—"),
            ("Status",     self._emp.get("status", "")),
            ("Notes",      self._emp.get("notes", "") or "—"),
        ]
        for label, value in fields:
            v = QLabel(str(value)); v.setWordWrap(True)
            v.setStyleSheet("color: #2C3E50; font-size: 13px;")
            lbl = QLabel(f"<b>{label}</b>")
            if label == "Status":
                clr = status_color(str(value))
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
            si.setForeground(QColor(status_color(a.get("status", ""))))
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
        close_btn.setObjectName("dialogSaveBtn")
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)


# ══════════════════════════════════════════════════════════════════
#  User Account Create Dialog (with validation)
# ══════════════════════════════════════════════════════════════════
class UserAccountDialog(QDialog):
    """Dialog to create a new user account with proper validation."""

    def __init__(self, parent=None, backend=None):
        super().__init__(parent)
        self.setWindowTitle("Create User Account")
        self.setMinimumWidth(500)

        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("formInput")
        self.name_edit.setMinimumHeight(38)
        self.name_edit.setPlaceholderText("Full name")

        self.email_edit = QLineEdit()
        self.email_edit.setObjectName("formInput")
        self.email_edit.setMinimumHeight(38)
        self.email_edit.setPlaceholderText("email@carecrud.com")

        self.pw_edit = QLineEdit()
        self.pw_edit.setObjectName("formInput")
        self.pw_edit.setMinimumHeight(38)
        self.pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_edit.setPlaceholderText("Temporary password (min 4 chars)")

        self.pw_confirm = QLineEdit()
        self.pw_confirm.setObjectName("formInput")
        self.pw_confirm.setMinimumHeight(38)
        self.pw_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_confirm.setPlaceholderText("Confirm password")

        self.role_combo = QComboBox()
        self.role_combo.setObjectName("formCombo")
        self.role_combo.setMinimumHeight(38)
        if backend:
            role_names = backend.get_all_roles()
            for rn in role_names:
                self.role_combo.addItem(rn)
        else:
            self.role_combo.addItems(
                ["Admin", "HR", "Finance", "Doctor", "Nurse", "Receptionist"])

        note = QLabel(
            "⚠️  The user will be required to change their password on first login.")
        note.setStyleSheet("font-size: 11px; color: #7F8C8D; padding-top: 4px;")
        note.setWordWrap(True)

        form.addRow("Full Name", self.name_edit)
        form.addRow("Email", self.email_edit)
        form.addRow("Password", self.pw_edit)
        form.addRow("Confirm Password", self.pw_confirm)
        form.addRow("Role", self.role_combo)
        form.addRow("", note)

        from PyQt6.QtWidgets import QDialogButtonBox
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        style_dialog_btns(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def accept(self):
        import re
        name = self.name_edit.text().strip()
        email = self.email_edit.text().strip()
        pw = self.pw_edit.text().strip()
        pw2 = self.pw_confirm.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation", "Full Name is required.")
            return
        if not email:
            QMessageBox.warning(self, "Validation", "Email is required.")
            return
        if not re.match(r'^[\w.+-]+@[\w-]+\.[\w.]+$', email):
            QMessageBox.warning(self, "Validation",
                                "Enter a valid email address.\nExample: doctor@carecrud.com")
            return
        if not pw:
            QMessageBox.warning(self, "Validation", "Password is required.")
            return
        if len(pw) < 4:
            QMessageBox.warning(self, "Validation",
                                "Password must be at least 4 characters.")
            return
        if pw != pw2:
            QMessageBox.warning(self, "Validation", "Passwords do not match.")
            return
        super().accept()

    def get_data(self) -> dict:
        return {
            "full_name": self.name_edit.text().strip(),
            "email": self.email_edit.text().strip(),
            "password": self.pw_edit.text().strip(),
            "role_name": self.role_combo.currentText(),
        }
