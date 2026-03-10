# Appointment dialog + date formatting helpers

from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QDialogButtonBox, QLabel, QTimeEdit, QDateEdit,
    QMessageBox, QCompleter,
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

    def __init__(self, parent=None, *, title="New Walk-in", data=None,
                 patients=None, doctors=None, services=None, backend=None,
                 user_email: str = "", user_role: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self._patients = patients or []
        self._doctors = doctors or []
        self._services = services or []
        self._backend = backend
        self._user_email = user_email
        self._user_role = user_role
        self._is_edit = data is not None

        form = QFormLayout(self)
        form.setSpacing(14); form.setContentsMargins(32,32,32,32)

        # Today label (walk-in is always today)
        self._today_label = QLabel(_pretty_date(date.today().isoformat()))
        self._today_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #388087;")

        self.patient_combo = QComboBox(); self.patient_combo.setObjectName("formCombo")
        self.patient_combo.setMinimumHeight(40)
        self.patient_combo.setEditable(True)
        self.patient_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.patient_combo.lineEdit().setPlaceholderText("Search patient name…")
        for p in self._patients:
            self.patient_combo.addItem(p["name"], p["patient_id"])
        completer = QCompleter([p["name"] for p in self._patients], self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.activated.connect(self._on_patient_selected)
        self.patient_combo.setCompleter(completer)
        self._selected_patient_text = ""
        self._selected_patient_id = None
        if not data:
            self.patient_combo.setCurrentIndex(-1)

        # Show only available doctors for today (walk-in)
        self.doctor_combo = QComboBox(); self.doctor_combo.setObjectName("formCombo"); self.doctor_combo.setMinimumHeight(40)
        preselect_idx = 0
        _my_emp_id = None
        if self._user_role == "Doctor" and self._user_email and not data and self._backend:
            _my_emp_id = self._backend.get_employee_id_by_email(self._user_email)
        for i, doc in enumerate(self._doctors):
            self.doctor_combo.addItem(doc["doctor_name"], doc["employee_id"])
            if _my_emp_id is not None and doc["employee_id"] == _my_emp_id:
                preselect_idx = i
        if not data:
            self.doctor_combo.setCurrentIndex(preselect_idx)

        self.time_edit = QTimeEdit(); self.time_edit.setTime(QTime(9,0))
        self.time_edit.setObjectName("formCombo"); self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setMinimumHeight(40)

        self.purpose_combo = QComboBox(); self.purpose_combo.setObjectName("formCombo"); self.purpose_combo.setMinimumHeight(40)
        for svc in self._services:
            self.purpose_combo.addItem(svc["service_name"], svc["service_id"])

        self.notes_edit = QTextEdit(); self.notes_edit.setObjectName("formInput")
        self.notes_edit.setMaximumHeight(70); self.notes_edit.setPlaceholderText("Optional notes…")

        # Only show cancel/reschedule fields in edit mode
        self.cancel_reason = QLineEdit(); self.cancel_reason.setObjectName("formInput")
        self.cancel_reason.setPlaceholderText("Reason (if cancelling)"); self.cancel_reason.setMinimumHeight(38)
        self.cancel_reason.setMaxLength(300)

        self.status_combo = QComboBox(); self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Confirmed", "Cancelled", "Completed"]); self.status_combo.setMinimumHeight(40)

        form.addRow("Date", self._today_label)
        form.addRow("Patient", self.patient_combo)
        form.addRow("Doctor", self.doctor_combo)
        form.addRow("Time", self.time_edit)
        form.addRow("Service", self.purpose_combo)
        form.addRow("Notes", self.notes_edit)
        if self._is_edit:
            form.addRow("Status", self.status_combo)
            form.addRow("Cancel Reason", self.cancel_reason)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        style_dialog_btns(btns)
        btns.accepted.connect(self._validate_and_accept); btns.rejected.connect(self.reject)
        form.addRow(btns)

        if data:
            p_idx = self.patient_combo.findText(data.get("patient",""))
            if p_idx >= 0:
                self.patient_combo.setCurrentIndex(p_idx)
                self._selected_patient_text = data.get("patient", "")
                self._selected_patient_id = self.patient_combo.itemData(p_idx)
            else:
                self.patient_combo.setEditText(data.get("patient",""))
            idx = self.doctor_combo.findText(data.get("doctor",""))
            if idx >= 0: self.doctor_combo.setCurrentIndex(idx)
            if data.get("time"): self.time_edit.setTime(QTime.fromString(data["time"],"HH:mm:ss"))
            idx = self.purpose_combo.findText(data.get("purpose",""))
            if idx >= 0: self.purpose_combo.setCurrentIndex(idx)
            idx = self.status_combo.findText(data.get("status",""))
            if idx >= 0: self.status_combo.setCurrentIndex(idx)
            if data.get("notes"): self.notes_edit.setPlainText(data["notes"])
            self.cancel_reason.setText(data.get("cancellation_reason","") or "")

    def _on_patient_selected(self, text):
        """When user picks from the completer popup, lock in the selection."""
        idx = self.patient_combo.findText(text, Qt.MatchFlag.MatchExactly)
        if idx >= 0:
            self.patient_combo.blockSignals(True)
            self.patient_combo.setCurrentIndex(idx)
            self.patient_combo.blockSignals(False)
            self._selected_patient_text = text
            self._selected_patient_id = self.patient_combo.itemData(idx)

    def _get_patient_id(self):
        """Return the patient_id for the current selection, resolving typed text."""
        # If combo index is valid, use it directly
        pid = self.patient_combo.currentData()
        if pid is not None:
            return pid
        # Try to match typed text to a patient
        text = self.patient_combo.currentText().strip()
        idx = self.patient_combo.findText(text, Qt.MatchFlag.MatchExactly)
        if idx >= 0:
            return self.patient_combo.itemData(idx)
        # Fall back to last confirmed selection if text still matches
        if text and text == self._selected_patient_text:
            return self._selected_patient_id
        return None

    def _validate_and_accept(self):
        # Ensure patient exists in the system
        patient_text = self.patient_combo.currentText().strip()
        patient_id = self._get_patient_id()
        if not patient_text:
            QMessageBox.warning(self, "Missing Patient",
                "Please select a patient.")
            return
        if patient_id is None:
            QMessageBox.warning(self, "Patient Not Found",
                f"'{patient_text}' is not registered in the system.\n"
                "Please select an existing patient from the list.")
            self.patient_combo.setFocus()
            return
        if self._backend:
            doc_id = self.doctor_combo.currentData()
            dt = date.today().isoformat()
            tm = self.time_edit.time().toString("HH:mm:ss")
            if doc_id and self._backend.check_appointment_conflict(doc_id, dt, tm):
                reply = QMessageBox.warning(self, "Conflict Detected",
                    "This doctor already has an appointment at the same time.\nSave anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return
        self.accept()

    def get_data(self) -> dict:
        return {
            "patient_name": self.patient_combo.currentText(),
            "patient_id": self._get_patient_id(),
            "doctor": self.doctor_combo.currentText(),
            "doctor_id": self.doctor_combo.currentData(),
            "date": date.today().isoformat(),
            "time": self.time_edit.time().toString("HH:mm:ss"),
            "purpose": self.purpose_combo.currentText(),
            "service_id": self.purpose_combo.currentData(),
            "status": self.status_combo.currentText() if self._is_edit else "Confirmed",
            "notes": self.notes_edit.toPlainText(),
            "cancellation_reason": self.cancel_reason.text() if self._is_edit else "",
            "reschedule_reason": "",
        }
