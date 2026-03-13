# Appointment dialog + date formatting helpers

from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QDialogButtonBox, QLabel, QTimeEdit, QDateEdit,
    QMessageBox, QCompleter, QHBoxLayout, QVBoxLayout,
    QWidget, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt, QDate, QTime, QTimer
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

        # Track current schedule bounds for time validation
        self._sched_start_hhmm: str | None = None
        self._sched_end_hhmm: str | None = None

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

        # No-slots warning (hidden by default)
        self._no_slots_label = QLabel()
        self._no_slots_label.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #D9534F; padding: 4px 0;")
        self._no_slots_label.setWordWrap(True)
        self._no_slots_label.setVisible(False)

        # Service combo — with placeholder
        self.purpose_combo = QComboBox()
        self.purpose_combo.setObjectName("formCombo")
        self.purpose_combo.setMinimumHeight(40)
        self.purpose_combo.addItem("Select a service\u2026", None)
        self.purpose_combo.setCurrentIndex(0)

        self.notes_edit = QTextEdit()
        self.notes_edit.setObjectName("formInput")
        self.notes_edit.setMaximumHeight(70)
        self.notes_edit.setPlaceholderText("Optional notes\u2026")

        # Cancel reason — hidden by default
        self._cancel_reason_label = QLabel("Cancel Reason")
        self.cancel_reason = QLineEdit()
        self.cancel_reason.setObjectName("formInput")
        self.cancel_reason.setPlaceholderText("Reason for cancellation")
        self.cancel_reason.setMinimumHeight(38)
        self.cancel_reason.setMaxLength(300)
        self._cancel_reason_label.setVisible(False)
        self.cancel_reason.setVisible(False)

        self.status_combo = QComboBox()
        self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Confirmed", "Cancelled", "Completed"])
        self.status_combo.setMinimumHeight(40)
        self.status_combo.currentTextChanged.connect(self._on_status_changed)

        form.addRow("Date", self._today_label)
        form.addRow("Patient", self.patient_combo)
        form.addRow("Doctor", self.doctor_combo)
        form.addRow("Time", self.time_edit)
        form.addRow("", self._no_slots_label)
        form.addRow("Service", self.purpose_combo)
        form.addRow("Notes", self.notes_edit)
        if self._is_edit:
            form.addRow("Status", self.status_combo)
            form.addRow(self._cancel_reason_label, self.cancel_reason)

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
            idx = self.status_combo.findText(data.get("status", ""))
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
            if data.get("notes"):
                self.notes_edit.setPlainText(data["notes"])
            self.cancel_reason.setText(data.get("cancellation_reason", "") or "")
            # Show cancel reason if editing a cancelled appointment
            if data.get("status") == "Cancelled":
                self._cancel_reason_label.setVisible(True)
                self.cancel_reason.setVisible(True)

        # Trigger initial schedule load (also sets service filtering)
        if self.doctor_combo.count() > 0:
            self._on_doctor_changed(self.doctor_combo.currentIndex())

        # After initial load, try to re-select the original service for edits
        if data and data.get("purpose"):
            idx = self.purpose_combo.findText(data["purpose"])
            if idx >= 0:
                self.purpose_combo.setCurrentIndex(idx)

        # Real-time clock timer: refresh time constraints every 60 seconds
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._refresh_time_range)
        self._clock_timer.start(60_000)

    # ── Service handling ──────────────────────────────────────────
    def _populate_services(self, services):
        """Fill the purpose combo with the given service list, keeping placeholder."""
        prev = self.purpose_combo.currentData()
        self.purpose_combo.clear()
        self.purpose_combo.addItem("Select a service\u2026", None)
        for svc in services:
            self.purpose_combo.addItem(svc["service_name"], svc["service_id"])
        # Try to re-select previous
        if prev is not None:
            for i in range(self.purpose_combo.count()):
                if self.purpose_combo.itemData(i) == prev:
                    self.purpose_combo.setCurrentIndex(i)
                    return
        self.purpose_combo.setCurrentIndex(0)

    # ── Doctor change ─────────────────────────────────────────────
    def _on_doctor_changed(self, index):
        """When doctor selection changes, load schedule and filter services."""
        doc_id = self.doctor_combo.currentData()
        if not doc_id or not self._backend:
            self._sched_panel.setVisible(False)
            return

        # Refresh services for this doctor's department
        if hasattr(self._backend, 'get_services_for_doctor'):
            filtered = self._backend.get_services_for_doctor(doc_id) or []
            self._populate_services(filtered if filtered else self._services)
        else:
            self._populate_services(self._services)

        self._sched_panel.setVisible(True)
        schedules = self._backend.get_doctor_schedules(doc_id) or []

        self._sched_table.setRowCount(len(schedules))
        # Use appointment date for edit mode, today for new walk-ins
        if self._is_edit and self._original_date:
            try:
                appt_d = datetime.strptime(self._original_date, "%Y-%m-%d").date()
            except Exception:
                appt_d = date.today()
        else:
            appt_d = date.today()
        target_day = _DAY_NAMES[appt_d.weekday()]
        today_start = None
        today_end = None

        for r, s in enumerate(schedules):
            day = s.get("day_of_week", "")
            start = _parse_time(s.get("start_time", ""))
            end = _parse_time(s.get("end_time", ""))
            day_item = QTableWidgetItem(day)
            start_item = QTableWidgetItem(_format_time_display(start))
            end_item = QTableWidgetItem(_format_time_display(end))
            if day == target_day:
                today_start = start
                today_end = end
                for item in (day_item, start_item, end_item):
                    item.setBackground(QColor("#E8F6F3"))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self._sched_table.setItem(r, 0, day_item)
            self._sched_table.setItem(r, 1, start_item)
            self._sched_table.setItem(r, 2, end_item)

        # Store schedule bounds for time validation
        self._sched_start_hhmm = today_start
        self._sched_end_hhmm = today_end
        self._apply_time_range(appt_d, target_day, today_start, today_end)

    def _apply_time_range(self, appt_d, target_day, today_start, today_end):
        """Set time edit range respecting schedule + real-time constraints."""
        day_label = "today" if appt_d == date.today() else f"on {target_day}"

        if today_start and today_end:
            t_start = QTime.fromString(today_start, "HH:mm")
            t_end = QTime.fromString(today_end, "HH:mm")
            if not t_start.isValid() or not t_end.isValid():
                self._set_no_schedule(target_day, day_label)
                return

            effective_start = t_start
            # If appointment date is today, enforce real-time floor
            if appt_d == date.today():
                now = QTime.currentTime()
                # Round up to next 30-min slot
                now_mins = now.hour() * 60 + now.minute()
                next_slot = now_mins + (30 - now_mins % 30)
                if next_slot >= 1440:
                    # Past midnight boundary — no valid slots remain
                    effective_start = t_end
                else:
                    real_floor = QTime(next_slot // 60, next_slot % 60)
                    if real_floor > t_start:
                        effective_start = real_floor

            if effective_start >= t_end:
                # All time slots have passed
                self.time_edit.setEnabled(False)
                self._no_slots_label.setText(
                    "No available time slots remaining for today. "
                    "Please select a future date.")
                self._no_slots_label.setVisible(True)
                self._today_sched_label.setText(
                    f"No remaining slots {day_label} ({target_day})")
                self._today_sched_label.setStyleSheet(
                    "font-size: 13px; font-weight: bold; color: #D9534F;"
                    " padding: 8px; background: #FDECEA; border-radius: 6px;")
                self._sched_info.setText(
                    f"Doctor's hours are {_format_time_display(today_start)} \u2013 "
                    f"{_format_time_display(today_end)} but all slots have passed.")
                return

            self.time_edit.setEnabled(True)
            self._no_slots_label.setVisible(False)
            self.time_edit.setTimeRange(effective_start, t_end)
            if self.time_edit.time() < effective_start:
                self.time_edit.setTime(effective_start)
            elif self.time_edit.time() > t_end:
                self.time_edit.setTime(effective_start)

            self._today_sched_label.setText(
                f"Available {day_label} ({target_day}):  "
                f"{_format_time_display(effective_start.toString('HH:mm'))}"
                f" \u2013 {_format_time_display(today_end)}")
            self._today_sched_label.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: #27AE60;"
                " padding: 8px; background: #E8F6F3; border-radius: 6px;")
            self._sched_info.setText(
                f"Available {day_label} \u2014 time restricted to schedule hours")
        else:
            self._set_no_schedule(target_day, day_label)

    def _set_no_schedule(self, target_day, day_label):
        """Doctor has no schedule for the target day."""
        self._today_sched_label.setText(f"Not available {day_label} ({target_day})")
        self._today_sched_label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #D9534F;"
            " padding: 8px; background: #FDECEA; border-radius: 6px;")
        self._sched_info.setText(
            f"This doctor has no schedule for {target_day}.\n"
            "You can still create the appointment.")
        self.time_edit.setEnabled(True)
        self._no_slots_label.setVisible(False)
        self.time_edit.setTimeRange(QTime(0, 0), QTime(23, 59))

    def _refresh_time_range(self):
        """Called by timer to refresh time constraints as real time advances."""
        if not self._sched_start_hhmm or not self._sched_end_hhmm:
            return
        if self._is_edit and self._original_date:
            try:
                appt_d = datetime.strptime(self._original_date, "%Y-%m-%d").date()
            except Exception:
                appt_d = date.today()
        else:
            appt_d = date.today()
        # Only re-apply if the appointment is for today
        if appt_d == date.today():
            target_day = _DAY_NAMES[appt_d.weekday()]
            self._apply_time_range(
                appt_d, target_day, self._sched_start_hhmm, self._sched_end_hhmm)

    # ── Status change → cancel reason visibility ──────────────────
    def _on_status_changed(self, status_text):
        is_cancelled = status_text == "Cancelled"
        self._cancel_reason_label.setVisible(is_cancelled)
        self.cancel_reason.setVisible(is_cancelled)
        if not is_cancelled:
            self.cancel_reason.clear()

    # ── Patient selection ─────────────────────────────────────────
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

    # ── Validation + Save ─────────────────────────────────────────
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

        # Validate service selection
        if self.purpose_combo.currentData() is None:
            QMessageBox.warning(self, "Missing Service",
                                "Please select a service.")
            self.purpose_combo.setFocus()
            return

        # Validate service matches doctor's department
        doc_id = self.doctor_combo.currentData()
        if doc_id and self._backend and hasattr(self._backend, 'get_services_for_doctor'):
            allowed = self._backend.get_services_for_doctor(doc_id) or []
            allowed_ids = {s["service_id"] for s in allowed}
            svc_id = self.purpose_combo.currentData()
            if svc_id and svc_id not in allowed_ids:
                QMessageBox.warning(
                    self, "Service Mismatch",
                    f"'{self.purpose_combo.currentText()}' is not available for this doctor's department.\n"
                    "Please select a valid service.")
                self.purpose_combo.setFocus()
                return

        # Validate cancel reason if status is Cancelled
        if self._is_edit and self.status_combo.currentText() == "Cancelled":
            if not self.cancel_reason.text().strip():
                QMessageBox.warning(self, "Missing Reason",
                                    "Please provide a cancellation reason.")
                self.cancel_reason.setFocus()
                return

        # Real-time re-validation of selected time
        appt_date = self._original_date if self._is_edit and self._original_date else date.today().isoformat()
        selected_time = self.time_edit.time()
        try:
            appt_d = datetime.strptime(appt_date, "%Y-%m-%d").date()
        except Exception:
            appt_d = date.today()

        if appt_d == date.today():
            now = QTime.currentTime()
            if selected_time <= now:
                QMessageBox.warning(
                    self, "Time Has Passed",
                    f"The selected time ({selected_time.toString('hh:mm AP')}) "
                    f"has already passed.\nCurrent time is {now.toString('hh:mm AP')}. "
                    "Please choose a later time.")
                self.time_edit.setFocus()
                # Refresh the time range to update stale limits
                self._refresh_time_range()
                return

        # Conflict check
        if self._backend and doc_id:
            dt = appt_date
            tm = selected_time.toString("HH:mm:ss")
            exclude_id = None
            if self._is_edit:
                # Pass the current appointment_id to exclude from conflict check
                # (the parent passes it via data, but we don't have it directly —
                #  so just check without exclusion for walk-ins)
                pass
            if self._backend.check_appointment_conflict(doc_id, dt, tm, exclude_id):
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
