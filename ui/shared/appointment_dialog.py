# Appointment dialog + date formatting helpers

from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QDialogButtonBox, QLabel, QTimeEdit, QDateEdit,
    QMessageBox, QCompleter, QHBoxLayout, QVBoxLayout,
    QWidget, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QColor, QFont
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


def _parse_time(t) -> str:
    """Convert timedelta or time to HH:MM string."""
    if hasattr(t, "total_seconds"):
        s = int(t.total_seconds())
        h, rem = divmod(s, 3600)
        m = rem // 60
        return f"{h:02d}:{m:02d}"
    if hasattr(t, "strftime"):
        return t.strftime("%H:%M")
    return str(t)[:5] if t else ""


def _format_time_display(hhmm: str) -> str:
    """Convert 'HH:MM' to '8:00 AM' style."""
    try:
        t = datetime.strptime(hhmm, "%H:%M")
        return t.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return hhmm


# ══════════════════════════════════════════════════════════════════════
#  Appointment Dialog
# ══════════════════════════════════════════════════════════════════════
class AppointmentDialog(QDialog):

    def __init__(self, parent=None, *, title="New Walk-in", data=None,
                 patients=None, doctors=None, services=None, backend=None,
                 user_email: str = "", user_role: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(820)
        self._patients = patients or []
        self._doctors = doctors or []
        self._services = services or []
        self._backend = backend
        self._user_email = user_email
        self._user_role = user_role
        self._is_edit = data is not None
        self._original_date = data.get("date", "") if data else ""

        # Main horizontal layout: form left, schedule right
        root = QHBoxLayout(self)
        root.setSpacing(20)
        root.setContentsMargins(24, 24, 24, 24)

        # ── Left: form ──
        left = QWidget()
        form = QFormLayout(left)
        form.setSpacing(14)
        form.setContentsMargins(8, 8, 8, 8)

        # Date label – show original date for edits, "Today" for walk-ins
        if self._is_edit and self._original_date:
            date_display = _pretty_date(self._original_date)
            rel = _relative_label(self._original_date)
            if rel:
                date_display += f"  ({rel})"
        else:
            date_display = f"{_pretty_date(date.today().isoformat())}  (Today)"
        self._today_label = QLabel(date_display)
        self._today_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #388087;")

        self.patient_combo = QComboBox()
        self.patient_combo.setObjectName("formCombo")
        self.patient_combo.setMinimumHeight(40)
        self.patient_combo.setEditable(True)
        self.patient_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.patient_combo.lineEdit().setPlaceholderText("Search patient name\u2026")
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

        # Doctor combo
        self.doctor_combo = QComboBox()
        self.doctor_combo.setObjectName("formCombo")
        self.doctor_combo.setMinimumHeight(40)
        preselect_idx = 0
        _my_emp_id = None
        if self._user_role == "Doctor" and self._user_email and not data and self._backend:
            _my_emp_id = self._backend.get_employee_id_by_email(self._user_email)
        for i, doc in enumerate(self._doctors):
            label = doc["doctor_name"]
            if doc.get("sched_start") and doc.get("sched_end"):
                label += f"  ({doc['sched_start']} \u2013 {doc['sched_end']})"
            self.doctor_combo.addItem(label, doc["employee_id"])
            if _my_emp_id is not None and doc["employee_id"] == _my_emp_id:
                preselect_idx = i
        if not data:
            self.doctor_combo.setCurrentIndex(preselect_idx)
        self.doctor_combo.currentIndexChanged.connect(self._on_doctor_changed)

        # Time edit
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(9, 0))
        self.time_edit.setObjectName("formCombo")
        self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setMinimumHeight(40)

        self.purpose_combo = QComboBox()
        self.purpose_combo.setObjectName("formCombo")
        self.purpose_combo.setMinimumHeight(40)
        for svc in self._services:
            self.purpose_combo.addItem(svc["service_name"], svc["service_id"])

        self.notes_edit = QTextEdit()
        self.notes_edit.setObjectName("formInput")
        self.notes_edit.setMaximumHeight(70)
        self.notes_edit.setPlaceholderText("Optional notes\u2026")

        self.cancel_reason = QLineEdit()
        self.cancel_reason.setObjectName("formInput")
        self.cancel_reason.setPlaceholderText("Reason (if cancelling)")
        self.cancel_reason.setMinimumHeight(38)
        self.cancel_reason.setMaxLength(300)

        self.status_combo = QComboBox()
        self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Confirmed", "Cancelled", "Completed"])
        self.status_combo.setMinimumHeight(40)

        form.addRow("Date", self._today_label)
        form.addRow("Patient", self.patient_combo)
        form.addRow("Doctor", self.doctor_combo)
        form.addRow("Time", self.time_edit)
        form.addRow("Service", self.purpose_combo)
        form.addRow("Notes", self.notes_edit)
        if self._is_edit:
            form.addRow("Status", self.status_combo)
            form.addRow("Cancel Reason", self.cancel_reason)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        style_dialog_btns(btns)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

        root.addWidget(left, 3)

        # ── Right: doctor schedule panel ──
        self._sched_panel = QWidget()
        sp_lay = QVBoxLayout(self._sched_panel)
        sp_lay.setContentsMargins(0, 8, 0, 8)
        sp_lay.setSpacing(10)

        sched_title = QLabel("Doctor\u2019s Weekly Schedule")
        sched_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #388087;")
        sp_lay.addWidget(sched_title)

        self._sched_info = QLabel("Select a doctor to view their schedule")
        self._sched_info.setStyleSheet("font-size: 12px; color: #7F8C8D;")
        self._sched_info.setWordWrap(True)
        sp_lay.addWidget(self._sched_info)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #BADFE7; border: none;")
        sp_lay.addWidget(sep)

        self._sched_table = QTableWidget()
        self._sched_table.setColumnCount(3)
        self._sched_table.setHorizontalHeaderLabels(["Day", "Start", "End"])
        self._sched_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self._sched_table.verticalHeader().setVisible(False)
        self._sched_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self._sched_table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection)
        self._sched_table.setAlternatingRowColors(True)
        self._sched_table.setStyleSheet(
            "QTableWidget { border: 1px solid #BADFE7; border-radius: 8px;"
            " font-size: 12px; background: #FFFFFF; }"
            " QTableWidget::item { padding: 6px; }"
            " QHeaderView::section { background: #388087; color: white;"
            " font-weight: bold; padding: 6px; border: none; }")
        self._sched_table.setMaximumHeight(260)
        sp_lay.addWidget(self._sched_table)

        self._today_sched_label = QLabel("")
        self._today_sched_label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #2C3E50;"
            " padding: 8px; background: #F0F7F8; border-radius: 6px;")
        self._today_sched_label.setWordWrap(True)
        sp_lay.addWidget(self._today_sched_label)

        sp_lay.addStretch()

        root.addWidget(self._sched_panel, 2)
        self._sched_panel.setVisible(False)

        # Pre-fill if editing
        if data:
            p_idx = self.patient_combo.findText(data.get("patient", ""))
            if p_idx >= 0:
                self.patient_combo.setCurrentIndex(p_idx)
                self._selected_patient_text = data.get("patient", "")
                self._selected_patient_id = self.patient_combo.itemData(p_idx)
            else:
                self.patient_combo.setEditText(data.get("patient", ""))
            doc_name = data.get("doctor", "")
            for i in range(self.doctor_combo.count()):
                if self.doctor_combo.itemText(i).startswith(doc_name):
                    self.doctor_combo.setCurrentIndex(i)
                    break
            if data.get("time"):
                self.time_edit.setTime(QTime.fromString(data["time"], "HH:mm:ss"))
            idx = self.purpose_combo.findText(data.get("purpose", ""))
            if idx >= 0:
                self.purpose_combo.setCurrentIndex(idx)
            idx = self.status_combo.findText(data.get("status", ""))
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
            if data.get("notes"):
                self.notes_edit.setPlainText(data["notes"])
            self.cancel_reason.setText(data.get("cancellation_reason", "") or "")

        # Trigger initial schedule load
        if self.doctor_combo.count() > 0:
            self._on_doctor_changed(self.doctor_combo.currentIndex())

    def _on_doctor_changed(self, index):
        """When doctor selection changes, load and display their schedule."""
        doc_id = self.doctor_combo.currentData()
        if not doc_id or not self._backend:
            self._sched_panel.setVisible(False)
            return

        self._sched_panel.setVisible(True)
        schedules = self._backend.get_doctor_schedules(doc_id) or []

        self._sched_table.setRowCount(len(schedules))
        today_day = _DAY_NAMES[date.today().weekday()]
        today_start = None
        today_end = None

        for r, s in enumerate(schedules):
            day = s.get("day_of_week", "")
            start = _parse_time(s.get("start_time", ""))
            end = _parse_time(s.get("end_time", ""))
            day_item = QTableWidgetItem(day)
            start_item = QTableWidgetItem(_format_time_display(start))
            end_item = QTableWidgetItem(_format_time_display(end))
            if day == today_day:
                today_start = start
                today_end = end
                for item in (day_item, start_item, end_item):
                    item.setBackground(QColor("#E8F6F3"))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self._sched_table.setItem(r, 0, day_item)
            self._sched_table.setItem(r, 1, start_item)
            self._sched_table.setItem(r, 2, end_item)

        if today_start and today_end:
            self._today_sched_label.setText(
                f"Today ({today_day}):  {_format_time_display(today_start)}"
                f" \u2013 {_format_time_display(today_end)}")
            self._today_sched_label.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: #27AE60;"
                " padding: 8px; background: #E8F6F3; border-radius: 6px;")
            self._sched_info.setText("Available today \u2014 time restricted to schedule hours")
            t_start = QTime.fromString(today_start, "HH:mm")
            t_end = QTime.fromString(today_end, "HH:mm")
            if t_start.isValid() and t_end.isValid():
                self.time_edit.setTimeRange(t_start, t_end)
                if self.time_edit.time() < t_start:
                    self.time_edit.setTime(t_start)
                elif self.time_edit.time() > t_end:
                    self.time_edit.setTime(t_start)
        else:
            self._today_sched_label.setText(f"Not available today ({today_day})")
            self._today_sched_label.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: #D9534F;"
                " padding: 8px; background: #FDECEA; border-radius: 6px;")
            self._sched_info.setText(
                "This doctor has no schedule for today.\n"
                "You can still create the appointment.")
            self.time_edit.setTimeRange(QTime(0, 0), QTime(23, 59))

    def _on_patient_selected(self, text):
        idx = self.patient_combo.findText(text, Qt.MatchFlag.MatchExactly)
        if idx >= 0:
            self.patient_combo.blockSignals(True)
            self.patient_combo.setCurrentIndex(idx)
            self.patient_combo.blockSignals(False)
            self._selected_patient_text = text
            self._selected_patient_id = self.patient_combo.itemData(idx)

    def _get_patient_id(self):
        pid = self.patient_combo.currentData()
        if pid is not None:
            return pid
        text = self.patient_combo.currentText().strip()
        idx = self.patient_combo.findText(text, Qt.MatchFlag.MatchExactly)
        if idx >= 0:
            return self.patient_combo.itemData(idx)
        if text and text == self._selected_patient_text:
            return self._selected_patient_id
        return None

    def _validate_and_accept(self):
        patient_text = self.patient_combo.currentText().strip()
        patient_id = self._get_patient_id()
        if not patient_text:
            QMessageBox.warning(self, "Missing Patient", "Please select a patient.")
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
                reply = QMessageBox.warning(
                    self, "Conflict Detected",
                    "This doctor already has an appointment at the same time.\nSave anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return
        self.accept()

    def get_data(self) -> dict:
        doc_text = self.doctor_combo.currentText()
        if "  (" in doc_text:
            doc_text = doc_text.split("  (")[0]
        # Preserve original date for edits, use today for new walk-ins
        appt_date = self._original_date if self._is_edit and self._original_date else date.today().isoformat()
        return {
            "patient_name": self.patient_combo.currentText(),
            "patient_id": self._get_patient_id(),
            "doctor": doc_text,
            "doctor_id": self.doctor_combo.currentData(),
            "date": appt_date,
            "time": self.time_edit.time().toString("HH:mm:ss"),
            "purpose": self.purpose_combo.currentText(),
            "service_id": self.purpose_combo.currentData(),
            "status": self.status_combo.currentText() if self._is_edit else "Confirmed",
            "notes": self.notes_edit.toPlainText(),
            "cancellation_reason": self.cancel_reason.text() if self._is_edit else "",
            "reschedule_reason": "",
        }
