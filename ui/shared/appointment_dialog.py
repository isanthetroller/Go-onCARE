"""Appointment dialog and date-formatting helpers.

Extracted from ui/appointments.py for better organisation.
"""

from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QDialogButtonBox, QHBoxLayout, QLabel, QTimeEdit, QDateEdit,
    QSpinBox, QCheckBox, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate, QTime
from ui.styles import style_dialog_btns


_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _pretty_date(iso: str) -> str:
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
        return f"{_DAY_NAMES[d.weekday()]},  {_MONTH_NAMES[d.month]} {d.day}, {d.year}"
    except Exception:
        return iso


def _relative_label(iso: str) -> str:
    try:
        d = datetime.strptime(iso, "%Y-%m-%d").date()
        today = date.today()
        if d == today:
            return "Today"
        if d == today + timedelta(days=1):
            return "Tomorrow"
    except Exception:
        pass
    return ""


# ══════════════════════════════════════════════════════════════════════
#  Appointment Dialog
# ══════════════════════════════════════════════════════════════════════
class AppointmentDialog(QDialog):

    def __init__(self, parent=None, *, title="New Appointment", data=None,
                 patient_names=None, doctors=None, services=None, backend=None,
                 user_email: str = "", user_role: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self._doctors = doctors or []
        self._services = services or []
        self._backend = backend
        self._user_email = user_email
        self._user_role = user_role

        form = QFormLayout(self)
        form.setSpacing(14); form.setContentsMargins(32,32,32,32)

        self.patient_combo = QComboBox(); self.patient_combo.setObjectName("formCombo")
        self.patient_combo.setMinimumHeight(40)
        if patient_names:
            self.patient_combo.addItems(patient_names)
        else:
            self.patient_combo.setEditable(True)
            self.patient_combo.lineEdit().setPlaceholderText("Select or type patient name")

        self.doctor_combo = QComboBox(); self.doctor_combo.setObjectName("formCombo"); self.doctor_combo.setMinimumHeight(40)
        preselect_idx = 0
        _my_emp_id = None
        if self._user_role == "Doctor" and self._user_email and not data and self._backend:
            emp = self._backend.fetch(
                "SELECT employee_id FROM employees WHERE email=%s",
                (self._user_email,), one=True)
            if emp:
                _my_emp_id = emp["employee_id"]
        for i, doc in enumerate(self._doctors):
            self.doctor_combo.addItem(doc["doctor_name"], doc["employee_id"])
            if _my_emp_id is not None and doc["employee_id"] == _my_emp_id:
                preselect_idx = i
        if not data:
            self.doctor_combo.setCurrentIndex(preselect_idx)

        self.date_edit = QDateEdit(); self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate()); self.date_edit.setObjectName("formCombo")
        self.date_edit.setDisplayFormat("dddd, MMMM d, yyyy"); self.date_edit.setMinimumHeight(40)
        self.date_edit.setMinimumDate(QDate.currentDate())
        _today = QDate.currentDate()
        _next_month = _today.addMonths(1)
        _max_date = QDate(_next_month.year(), _next_month.month(), _next_month.daysInMonth())
        self.date_edit.setMaximumDate(_max_date)

        self.time_edit = QTimeEdit(); self.time_edit.setTime(QTime(9,0))
        self.time_edit.setObjectName("formCombo"); self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setMinimumHeight(40)

        self.purpose_combo = QComboBox(); self.purpose_combo.setObjectName("formCombo"); self.purpose_combo.setMinimumHeight(40)
        for svc in self._services:
            self.purpose_combo.addItem(svc["service_name"], svc["service_id"])

        self.status_combo = QComboBox(); self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Pending", "Confirmed", "Cancelled", "Completed"]); self.status_combo.setMinimumHeight(40)

        self.notes_edit = QTextEdit(); self.notes_edit.setObjectName("formInput")
        self.notes_edit.setMaximumHeight(70); self.notes_edit.setPlaceholderText("Optional notes…")

        self.cancel_reason = QLineEdit(); self.cancel_reason.setObjectName("formInput")
        self.cancel_reason.setPlaceholderText("Reason (if cancelling)"); self.cancel_reason.setMinimumHeight(38)

        self.resched_reason = QLineEdit(); self.resched_reason.setObjectName("formInput")
        self.resched_reason.setPlaceholderText("Reason (if rescheduling)"); self.resched_reason.setMinimumHeight(38)

        self.reminder_check = QCheckBox("Reminder Sent")

        self.recurring_check = QCheckBox("Make Recurring")
        self.recur_freq = QComboBox(); self.recur_freq.addItems(["Weekly", "Daily", "Monthly"])
        self.recur_freq.setObjectName("formCombo"); self.recur_freq.setMinimumHeight(38)
        self.recur_count = QSpinBox(); self.recur_count.setMinimum(2); self.recur_count.setMaximum(52)
        self.recur_count.setValue(4); self.recur_count.setMinimumHeight(38)
        self.recur_freq.setEnabled(False); self.recur_count.setEnabled(False)
        self.recurring_check.toggled.connect(lambda c: (self.recur_freq.setEnabled(c), self.recur_count.setEnabled(c)))

        form.addRow("Patient", self.patient_combo)
        form.addRow("Doctor", self.doctor_combo)
        form.addRow("Date", self.date_edit)
        form.addRow("Time", self.time_edit)
        form.addRow("Service", self.purpose_combo)
        form.addRow("Status", self.status_combo)
        form.addRow("Notes", self.notes_edit)
        form.addRow("Cancel Reason", self.cancel_reason)
        form.addRow("Reschedule Reason", self.resched_reason)
        form.addRow("", self.reminder_check)
        if title == "New Appointment":
            form.addRow("", self.recurring_check)
            recur_row = QHBoxLayout()
            recur_row.addWidget(QLabel("Every")); recur_row.addWidget(self.recur_freq)
            recur_row.addWidget(QLabel("×")); recur_row.addWidget(self.recur_count)
            form.addRow("Recurrence", recur_row)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        style_dialog_btns(btns)
        btns.accepted.connect(self._validate_and_accept); btns.rejected.connect(self.reject)
        form.addRow(btns)

        if data:
            p_idx = self.patient_combo.findText(data.get("patient",""))
            if p_idx >= 0: self.patient_combo.setCurrentIndex(p_idx)
            elif self.patient_combo.isEditable(): self.patient_combo.setEditText(data.get("patient",""))
            idx = self.doctor_combo.findText(data.get("doctor",""))
            if idx >= 0: self.doctor_combo.setCurrentIndex(idx)
            if data.get("date"):
                orig_date = QDate.fromString(data["date"], "yyyy-MM-dd")
                if orig_date < QDate.currentDate():
                    self.date_edit.setMinimumDate(orig_date)
                self.date_edit.setDate(orig_date)
            if data.get("time"): self.time_edit.setTime(QTime.fromString(data["time"],"HH:mm:ss"))
            idx = self.purpose_combo.findText(data.get("purpose",""))
            if idx >= 0: self.purpose_combo.setCurrentIndex(idx)
            idx = self.status_combo.findText(data.get("status",""))
            if idx >= 0: self.status_combo.setCurrentIndex(idx)
            if data.get("notes"): self.notes_edit.setPlainText(data["notes"])
            self.cancel_reason.setText(data.get("cancellation_reason","") or "")
            self.resched_reason.setText(data.get("reschedule_reason","") or "")
            self.reminder_check.setChecked(bool(data.get("reminder_sent", 0)))

    def _validate_and_accept(self):
        selected_date = self.date_edit.date()
        today = QDate.currentDate()
        if selected_date < today:
            QMessageBox.warning(self, "Invalid Date",
                "Cannot schedule an appointment in the past.\n"
                "Please select today or a future date.")
            return
        next_month = today.addMonths(1)
        max_date = QDate(next_month.year(), next_month.month(), next_month.daysInMonth())
        if selected_date > max_date:
            QMessageBox.warning(self, "Invalid Date",
                f"Appointments can only be scheduled within this month "
                f"or next month (up to {max_date.toString('MMMM d, yyyy')}).\n"
                f"Please select an earlier date.")
            return
        if self._backend:
            doc_id = self.doctor_combo.currentData()
            dt = self.date_edit.date().toString("yyyy-MM-dd")
            tm = self.time_edit.time().toString("HH:mm:ss")
            if doc_id and self._backend.check_appointment_conflict(doc_id, dt, tm):
                reply = QMessageBox.warning(self, "Conflict Detected",
                    "This doctor already has an appointment at the same date/time.\nSave anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return
        self.accept()

    def get_data(self) -> dict:
        return {
            "patient_name": self.patient_combo.currentText(),
            "doctor": self.doctor_combo.currentText(),
            "doctor_id": self.doctor_combo.currentData(),
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "time": self.time_edit.time().toString("HH:mm:ss"),
            "purpose": self.purpose_combo.currentText(),
            "service_id": self.purpose_combo.currentData(),
            "status": self.status_combo.currentText(),
            "notes": self.notes_edit.toPlainText(),
            "cancellation_reason": self.cancel_reason.text(),
            "reschedule_reason": self.resched_reason.text(),
            "reminder_sent": 1 if self.reminder_check.isChecked() else 0,
            "recurring": self.recurring_check.isChecked() if hasattr(self, 'recurring_check') else False,
            "recur_freq": self.recur_freq.currentText() if hasattr(self, 'recur_freq') else "Weekly",
            "recur_count": self.recur_count.value() if hasattr(self, 'recur_count') else 4,
        }
