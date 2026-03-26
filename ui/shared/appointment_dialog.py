# Appointment dialog + date formatting helpers

from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QLabel, QTimeEdit, QDateEdit, QScrollArea, QSizePolicy,
    QMessageBox, QCompleter, QHBoxLayout, QVBoxLayout,
    QWidget, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton,
)
from PyQt6.QtCore import Qt, QDate, QTime, QTimer
from PyQt6.QtGui import QColor, QFont


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
    if hasattr(t, "total_seconds"):
        s = int(t.total_seconds())
        h, rem = divmod(s, 3600)
        m = rem // 60
        return f"{h:02d}:{m:02d}"
    if hasattr(t, "strftime"):
        return t.strftime("%H:%M")
    return str(t)[:5] if t else ""


def _format_time_display(hhmm: str) -> str:
    try:
        t = datetime.strptime(hhmm, "%H:%M")
        return t.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return hhmm


def _svg_icon(filename: str):
    """Load an SVG icon widget with fallback."""
    import os
    path = os.path.join(
        os.path.dirname(__file__), "..", "styles", filename)
    try:
        from PyQt6.QtSvgWidgets import QSvgWidget
        w = QSvgWidget(os.path.normpath(path))
        w.setFixedSize(32, 32)
        w.setStyleSheet("QSvgWidget { background: transparent; }")
        return w
    except ImportError:
        lbl = QLabel("\U0001F4C5")
        lbl.setFixedSize(32, 32)
        lbl.setStyleSheet(
            "font-size: 22px; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl


# ══════════════════════════════════════════════════════════════════════
#  Appointment Dialog — V3 (gradient header, polished layout)
# ══════════════════════════════════════════════════════════════════════
class AppointmentDialog(QDialog):

    _INPUT_STYLE = (
        "QLineEdit, QTextEdit { padding: 8px 14px 10px 14px;"
        " border: 2px solid #BADFE7; border-radius: 10px;"
        " font-size: 13px; background-color: #FFFFFF; color: #2C3E50; }"
        "QLineEdit:focus, QTextEdit:focus { border: 2px solid #388087; }"
    )

    def __init__(self, parent=None, *, title="New Walk-in", data=None,
                 patients=None, doctors=None, services=None, backend=None,
                 user_email: str = "", user_role: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._patients = patients or []
        self._doctors = doctors or []
        self._services = services or []
        self._backend = backend
        self._user_email = user_email
        self._user_role = user_role
        self._is_edit = data is not None
        self._original_date = data.get("date", "") if data else ""

        self._sched_start_hhmm: str | None = None
        self._sched_end_hhmm: str | None = None

        # Screen-adaptive sizing
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None
        max_h = int(avail.height() * 0.82) if avail else 680
        max_w = int(avail.width() * 0.65) if avail else 950
        self.resize(min(950, max_w), min(650, max_h))
        self.setMinimumSize(820, 500)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Gradient header bar ────────────────────────────────────
        header_bar = QFrame()
        header_bar.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            " stop:0 #388087, stop:1 #6FB3B8); }")
        header_bar.setFixedHeight(58)
        hb_lay = QHBoxLayout(header_bar)
        hb_lay.setContentsMargins(28, 0, 28, 0)

        hb_lay.addWidget(_svg_icon("icon-appointment.svg"))
        hb_lay.addSpacing(12)

        h_lbl = QLabel(title)
        h_lbl.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #FFFFFF;"
            " background: transparent;")
        sub_text = "Edit appointment details" if self._is_edit else "Schedule a new walk-in appointment"
        h_sub = QLabel(sub_text)
        h_sub.setStyleSheet(
            "font-size: 12px; color: rgba(255,255,255,0.8);"
            " background: transparent;")
        h_col = QVBoxLayout(); h_col.setSpacing(0)
        h_col.addWidget(h_lbl); h_col.addWidget(h_sub)
        hb_lay.addLayout(h_col); hb_lay.addStretch()
        outer.addWidget(header_bar)

        # ── Content area ───────────────────────────────────────────
        content_w = QWidget()
        content_w.setObjectName("content_w_no_bleed"); content_w.setStyleSheet("#content_w_no_bleed { background: #FFFFFF; }")
        root = QHBoxLayout(content_w)
        root.setSpacing(24)
        root.setContentsMargins(28, 16, 28, 8)

        # ── Left: form (compact — no vertical stretch) ──
        left = QWidget()
        left.setObjectName("left_no_bleed"); left.setStyleSheet("#left_no_bleed { background: transparent; }")
        left_vbox = QVBoxLayout(left)
        left_vbox.setContentsMargins(0, 0, 0, 0)
        left_vbox.setSpacing(0)

        form = QFormLayout()
        form.setSpacing(18)
        form.setContentsMargins(0, 0, 0, 0)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        # Date label/picker
        from ui.shared.modern_calendar import apply_modern_calendar
        self.date_edit = QDateEdit()
        self.date_edit.setObjectName("formCombo")
        self.date_edit.setMinimumHeight(38)
        
        # Restrict appointments to the current month
        today = QDate.currentDate()
        self.date_edit.setMinimumDate(today)
        self.date_edit.setMaximumDate(QDate(today.year(), today.month(), today.daysInMonth()))
        
        if self._is_edit and self._original_date:
            try:
                appt_d = datetime.strptime(self._original_date, "%Y-%m-%d").date()
                self.date_edit.setDate(QDate(appt_d.year, appt_d.month, appt_d.day))
            except Exception:
                self.date_edit.setDate(today)
        else:
            self.date_edit.setDate(today)
            
        self.date_edit.setDisplayFormat("MMMM d, yyyy")
        
        apply_modern_calendar(self.date_edit)
        
        self.date_edit.dateChanged.connect(self._on_date_changed)

        self.patient_combo = QComboBox()
        self.patient_combo.setObjectName("formCombo")
        self.patient_combo.setMinimumHeight(38)
        self.patient_combo.setEditable(True)
        self.patient_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.patient_combo.lineEdit().setPlaceholderText(
            "Search patient name\u2026")
        for p in self._patients:
            self.patient_combo.addItem(p["name"], p["patient_id"])
        completer = QCompleter(
            [p["name"] for p in self._patients], self)
        completer.setCaseSensitivity(
            Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.activated.connect(self._on_patient_selected)
        self.patient_combo.setCompleter(completer)
        self.patient_combo.lineEdit().editingFinished.connect(self._check_patient_validity)
        self._selected_patient_text = ""
        self._selected_patient_id = None
        if not data:
            self.patient_combo.setCurrentIndex(-1)

        self.doctor_combo = QComboBox()
        self.doctor_combo.setObjectName("formCombo")
        self.doctor_combo.setMinimumHeight(38)
        preselect_idx = 0
        _my_emp_id = None
        if (self._user_role == "Doctor" and self._user_email
                and not data and self._backend):
            _my_emp_id = self._backend.get_employee_id_by_email(
                self._user_email)
        for i, doc in enumerate(self._doctors):
            label = doc["doctor_name"]
            self.doctor_combo.addItem(label, doc["employee_id"])
            if (_my_emp_id is not None
                    and doc["employee_id"] == _my_emp_id):
                preselect_idx = i
        if not data:
            self.doctor_combo.setCurrentIndex(preselect_idx)
        self.doctor_combo.currentIndexChanged.connect(
            self._on_doctor_changed)

        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(9, 0))
        self.time_edit.setObjectName("formCombo")
        self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setMinimumHeight(38)

        self._no_slots_label = QLabel()
        self._no_slots_label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #D9534F;"
            " padding: 10px; background: #FDECEA; border-radius: 6px;"
            " border: 1px solid #FADBD8; margin-top: 10px;"
        )
        self._no_slots_label.setWordWrap(True)
        self._no_slots_label.setVisible(False)

        self.purpose_combo = QComboBox()
        self.purpose_combo.setObjectName("formCombo")
        self.purpose_combo.setMinimumHeight(38)
        self.purpose_combo.addItem("Select a service\u2026", None)
        self.purpose_combo.setCurrentIndex(0)

        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(self._INPUT_STYLE)
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Optional notes\u2026")

        self._cancel_reason_label = QLabel("Cancel Reason")
        self.cancel_reason = QLineEdit()
        self.cancel_reason.setStyleSheet(self._INPUT_STYLE)
        self.cancel_reason.setPlaceholderText(
            "Reason for cancellation")
        self.cancel_reason.setMinimumHeight(38)
        self.cancel_reason.setMaxLength(300)
        self._cancel_reason_label.setVisible(False)
        self.cancel_reason.setVisible(False)

        self.status_combo = QComboBox()
        self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(
            ["Confirmed", "Cancelled", "Completed"])
        self.status_combo.setMinimumHeight(38)
        self.status_combo.currentTextChanged.connect(
            self._on_status_changed)

        form.addRow("Date",    self.date_edit)
        form.addRow("Patient", self.patient_combo)
        form.addRow("Doctor",  self.doctor_combo)
        form.addRow("Time",    self.time_edit)
        form.addRow("Service", self.purpose_combo)
        form.addRow("Notes",   self.notes_edit)
        if self._is_edit:
            form.addRow("Status", self.status_combo)
            form.addRow(self._cancel_reason_label,
                        self.cancel_reason)

        left_vbox.addLayout(form)
        left_vbox.addWidget(self._no_slots_label)
        left_vbox.addStretch()  # keeps form compact at top

        root.addWidget(left, 3)

        # ── Right: doctor schedule panel ──
        self._sched_panel = QWidget()
        self._sched_panel.setObjectName("_sched_panel_no_bleed"); self._sched_panel.setStyleSheet("#_sched_panel_no_bleed { background: transparent; }")
        sp_lay = QVBoxLayout(self._sched_panel)
        sp_lay.setContentsMargins(0, 0, 0, 0)
        sp_lay.setSpacing(10)

        sched_title = QLabel("Doctor\u2019s Weekly Schedule")
        sched_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #388087;")
        sp_lay.addWidget(sched_title)

        self._sched_info = QLabel(
            "Select a doctor to view their schedule")
        self._sched_info.setStyleSheet(
            "font-size: 12px; color: #7F8C8D;")
        self._sched_info.setWordWrap(True)
        sp_lay.addWidget(self._sched_info)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #BADFE7; border: none;")
        sp_lay.addWidget(sep)

        self._sched_table = QTableWidget()
        self._sched_table.setColumnCount(3)
        self._sched_table.setHorizontalHeaderLabels(
            ["Day", "Start", "End"])
        self._sched_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self._sched_table.verticalHeader().setVisible(False)
        self._sched_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self._sched_table.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection)
        self._sched_table.setAlternatingRowColors(True)
        self._sched_table.setStyleSheet(
            "QTableWidget { border: 1px solid #BADFE7;"
            " border-radius: 8px; font-size: 12px;"
            " background: #FFFFFF; }"
            " QTableWidget::item { padding: 6px; }"
            " QHeaderView::section { background: #388087;"
            " color: white; font-weight: bold; padding: 6px;"
            " border: none; }")
        self._sched_table.setMaximumHeight(280)
        sp_lay.addWidget(self._sched_table)

        self._today_sched_label = QLabel("")
        self._today_sched_label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #2C3E50;"
            " padding: 8px; background: #F0F7F8;"
            " border-radius: 6px;")
        self._today_sched_label.setWordWrap(True)
        sp_lay.addWidget(self._today_sched_label)

        sp_lay.addStretch()

        root.addWidget(self._sched_panel, 2)
        self._sched_panel.setVisible(False)

        outer.addWidget(content_w, 1)

        # ── Button bar ─────────────────────────────────────────────
        btn_sep = QFrame()
        btn_sep.setFixedHeight(1)
        btn_sep.setStyleSheet("background: #E8F0F1;")
        outer.addWidget(btn_sep)

        btn_bar = QWidget()
        btn_bar.setObjectName("btnBar")
        btn_bar.setStyleSheet(
            "QWidget#btnBar { background: #FAFBFB; }")
        btn_row = QHBoxLayout(btn_bar)
        btn_row.setContentsMargins(28, 12, 28, 12)
        btn_row.setSpacing(14)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(130)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setObjectName("dialogCancelBtn")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(130)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setObjectName("dialogSaveBtn")
        save_btn.clicked.connect(self._validate_and_accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        outer.addWidget(btn_bar)

        # Pre-fill if editing
        if data:
            p_idx = self.patient_combo.findText(
                data.get("patient", ""))
            if p_idx >= 0:
                self.patient_combo.setCurrentIndex(p_idx)
                self._selected_patient_text = data.get(
                    "patient", "")
                self._selected_patient_id = (
                    self.patient_combo.itemData(p_idx))
            else:
                self.patient_combo.setEditText(
                    data.get("patient", ""))
            doc_name = data.get("doctor", "")
            for i in range(self.doctor_combo.count()):
                if self.doctor_combo.itemText(i).startswith(
                        doc_name):
                    self.doctor_combo.setCurrentIndex(i); break
            if data.get("time"):
                self.time_edit.setTime(
                    QTime.fromString(data["time"], "HH:mm:ss"))
            idx = self.status_combo.findText(
                data.get("status", ""))
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
            if data.get("notes"):
                self.notes_edit.setPlainText(data["notes"])
            self.cancel_reason.setText(
                data.get("cancellation_reason", "") or "")
            if data.get("status") == "Cancelled":
                self._cancel_reason_label.setVisible(True)
                self.cancel_reason.setVisible(True)

        if self.doctor_combo.count() > 0:
            self._on_doctor_changed(
                self.doctor_combo.currentIndex())

        if data and data.get("purpose"):
            idx = self.purpose_combo.findText(data["purpose"])
            if idx >= 0:
                self.purpose_combo.setCurrentIndex(idx)

        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(
            self._refresh_time_range)
        self._clock_timer.start(60_000)

    # ── Service handling ──────────────────────────────────────────
    def _populate_services(self, services):
        prev = self.purpose_combo.currentData()
        self.purpose_combo.clear()
        self.purpose_combo.addItem("Select a service\u2026", None)
        for svc in services:
            self.purpose_combo.addItem(
                svc["service_name"], svc["service_id"])
        if prev is not None:
            for i in range(self.purpose_combo.count()):
                if self.purpose_combo.itemData(i) == prev:
                    self.purpose_combo.setCurrentIndex(i); return
        self.purpose_combo.setCurrentIndex(0)

    # ── Date/Doctor change ─────────────────────────────────────────────
    def _on_date_changed(self, new_date: QDate):
        if self.doctor_combo.count() > 0:
            self._on_doctor_changed(self.doctor_combo.currentIndex())

    def _on_doctor_changed(self, index):
        doc_id = self.doctor_combo.currentData()
        if not doc_id or not self._backend:
            self._sched_panel.setVisible(False); return

        if hasattr(self._backend, 'get_services_for_doctor'):
            filtered = (
                self._backend.get_services_for_doctor(doc_id) or [])
            self._populate_services(
                filtered if filtered else self._services)
        else:
            self._populate_services(self._services)

        self._sched_panel.setVisible(True)
        schedules = self._backend.get_doctor_schedules(doc_id) or []

        self._sched_table.setRowCount(len(schedules))
        
        selected_date = self.date_edit.date().toPyDate()
        appt_d = selected_date
        target_day = _DAY_NAMES[appt_d.weekday()]
        today_start = None
        today_end = None

        for r, s in enumerate(schedules):
            day = s.get("day_of_week", "")
            start = _parse_time(s.get("start_time", ""))
            end = _parse_time(s.get("end_time", ""))
            day_item = QTableWidgetItem(day)
            start_item = QTableWidgetItem(
                _format_time_display(start))
            end_item = QTableWidgetItem(
                _format_time_display(end))
            if day == target_day:
                today_start = start
                today_end = end
                for item in (day_item, start_item, end_item):
                    item.setBackground(QColor("#E8F6F3"))
                    item.setFont(
                        QFont("Segoe UI", 10, QFont.Weight.Bold))
            self._sched_table.setItem(r, 0, day_item)
            self._sched_table.setItem(r, 1, start_item)
            self._sched_table.setItem(r, 2, end_item)

        self._sched_start_hhmm = today_start
        self._sched_end_hhmm = today_end
        self._apply_time_range(
            appt_d, target_day, today_start, today_end)

    def _apply_time_range(self, appt_d, target_day,
                          today_start, today_end):
        day_label = ("today" if appt_d == date.today()
                     else f"on {target_day}")

        if today_start and today_end:
            t_start = QTime.fromString(today_start, "HH:mm")
            t_end = QTime.fromString(today_end, "HH:mm")
            if not t_start.isValid() or not t_end.isValid():
                self._set_no_schedule(target_day, day_label)
                return

            effective_start = t_start
            if appt_d == date.today():
                now = QTime.currentTime()
                now_mins = now.hour() * 60 + now.minute()
                next_slot = now_mins + (30 - now_mins % 30)
                if next_slot >= 1440:
                    effective_start = t_end
                else:
                    real_floor = QTime(
                        next_slot // 60, next_slot % 60)
                    if real_floor > t_start:
                        effective_start = real_floor

            if effective_start >= t_end:
                self.time_edit.setEnabled(False)
                self._no_slots_label.setText(
                    "No available time slots remaining for today."
                    " Please select a future date.")
                self._no_slots_label.setVisible(True)
                self._today_sched_label.setText(
                    f"No remaining slots {day_label}"
                    f" ({target_day})")
                self._today_sched_label.setStyleSheet(
                    "font-size: 13px; font-weight: bold;"
                    " color: #D9534F; padding: 8px;"
                    " background: #FDECEA; border-radius: 6px;")
                self._sched_info.setText(
                    f"Doctor's hours are"
                    f" {_format_time_display(today_start)}"
                    f" \u2013 {_format_time_display(today_end)}"
                    " but all slots have passed.")
                return

            self.time_edit.setEnabled(True)
            self._no_slots_label.setVisible(False)
            self.time_edit.setMinimumTime(effective_start)
            self.time_edit.setMaximumTime(t_end)
            # Always snap time to the effective schedule start
            self.time_edit.setTime(effective_start)

            self._today_sched_label.setText(
                f"Available {day_label} ({target_day}):  "
                f"{_format_time_display(effective_start.toString('HH:mm'))}"
                f" \u2013 {_format_time_display(today_end)}")
            self._today_sched_label.setStyleSheet(
                "font-size: 13px; font-weight: bold;"
                " color: #27AE60; padding: 8px;"
                " background: #E8F6F3; border-radius: 6px;")
            self._sched_info.setText(
                f"Available {day_label}"
                " \u2014 time restricted to schedule hours")
        else:
            self._set_no_schedule(target_day, day_label)

    def _set_no_schedule(self, target_day, day_label):
        self._today_sched_label.setText(
            f"Not available {day_label} ({target_day})")
        self._today_sched_label.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #D9534F;"
            " padding: 8px; background: #FDECEA;"
            " border-radius: 6px;")
        self._sched_info.setText(
            f"This doctor has no schedule for {target_day}.\n"
            "Please select a date when the doctor is available.")
        self.time_edit.setEnabled(False)
        self._no_slots_label.setText(
            f"\u26A0 The selected doctor does not work {day_label} ({target_day}).\n"
            "Please choose a different date that matches the doctor\u2019s schedule.")
        self._no_slots_label.setVisible(True)
        self.time_edit.clearMinimumTime()
        self.time_edit.clearMaximumTime()

    def _refresh_time_range(self):
        if (not self._sched_start_hhmm
                or not self._sched_end_hhmm):
            return
        
        appt_d = self.date_edit.date().toPyDate()
        if appt_d == date.today():
            target_day = _DAY_NAMES[appt_d.weekday()]
            self._apply_time_range(
                appt_d, target_day,
                self._sched_start_hhmm, self._sched_end_hhmm)

    def _on_status_changed(self, status_text):
        is_cancelled = status_text == "Cancelled"
        self._cancel_reason_label.setVisible(is_cancelled)
        self.cancel_reason.setVisible(is_cancelled)
        if not is_cancelled:
            self.cancel_reason.clear()

    def _on_patient_selected(self, text):
        match_idx = -1
        for i in range(self.patient_combo.count()):
            if self.patient_combo.itemText(i).strip().lower() == text.strip().lower():
                match_idx = i
                break
                
        if match_idx >= 0:
            self.patient_combo.blockSignals(True)
            self.patient_combo.setCurrentIndex(match_idx)
            self.patient_combo.blockSignals(False)
            self._selected_patient_text = self.patient_combo.itemText(match_idx)
            self._selected_patient_id = self.patient_combo.itemData(match_idx)

    def _check_patient_validity(self):
        text = self.patient_combo.currentText().strip()
        if not text:
            return
        
        # Case-insensitive substring search
        match_idx = -1
        for i in range(self.patient_combo.count()):
            if text.lower() in self.patient_combo.itemText(i).strip().lower():
                match_idx = i
                break
                
        if match_idx < 0:
            # We don't wipe the text anymore to allow the user to keep typing
            self.patient_combo.blockSignals(True)
            self.patient_combo.setCurrentIndex(-1)
            self.patient_combo.blockSignals(False)
            self._selected_patient_text = text
            self._selected_patient_id = None
        else:
            self.patient_combo.blockSignals(True)
            self.patient_combo.setCurrentIndex(match_idx)
            self.patient_combo.blockSignals(False)
            self._selected_patient_text = self.patient_combo.itemText(match_idx)
            self._selected_patient_id = self.patient_combo.itemData(match_idx)

    def _get_patient_id(self):
        pid = self.patient_combo.currentData()
        if pid is not None:
            return pid
        text = self.patient_combo.currentText().strip()
        
        # Case-insensitive substring search
        for i in range(self.patient_combo.count()):
            if text.lower() in self.patient_combo.itemText(i).strip().lower():
                return self.patient_combo.itemData(i)
                
        if text and (text == self._selected_patient_text or text in self._selected_patient_text):
            return self._selected_patient_id
        return None

    # ── Validation + Save ─────────────────────────────────────────
    def _validate_and_accept(self):
        patient_text = self.patient_combo.currentText().strip()
        patient_id = self._get_patient_id()
        if not patient_text:
            QMessageBox.warning(
                self, "Missing Patient",
                "Please select a patient."); return
        if patient_id is None:
            QMessageBox.warning(
                self, "Patient Not Found",
                f"'{patient_text}' is not registered.\n"
                "Please select an existing patient.")
            self.patient_combo.setFocus(); return

        if self.purpose_combo.currentData() is None:
            QMessageBox.warning(
                self, "Missing Service",
                "Please select a service.")
            self.purpose_combo.setFocus(); return

        doc_id = self.doctor_combo.currentData()
        if (doc_id and self._backend
                and hasattr(self._backend,
                            'get_services_for_doctor')):
            allowed = (
                self._backend.get_services_for_doctor(doc_id)
                or [])
            allowed_ids = {s["service_id"] for s in allowed}
            svc_id = self.purpose_combo.currentData()
            if svc_id and svc_id not in allowed_ids:
                QMessageBox.warning(
                    self, "Service Mismatch",
                    f"'{self.purpose_combo.currentText()}'"
                    " is not available for this doctor's"
                    " department.\nPlease select a valid"
                    " service.")
                self.purpose_combo.setFocus(); return

        if (self._is_edit
                and self.status_combo.currentText()
                == "Cancelled"):
            if not self.cancel_reason.text().strip():
                QMessageBox.warning(
                    self, "Missing Reason",
                    "Please provide a cancellation reason.")
                self.cancel_reason.setFocus(); return

        appt_date = self.date_edit.date().toString("yyyy-MM-dd")
        selected_time = self.time_edit.time()
        appt_d = self.date_edit.date().toPyDate()

        # Block saving if the doctor has no schedule for this day
        if not self._sched_start_hhmm or not self._sched_end_hhmm:
            target_day = _DAY_NAMES[appt_d.weekday()]
            QMessageBox.warning(
                self, "No Schedule",
                f"The selected doctor does not work on {target_day}.\n"
                "Please choose a date that matches the doctor\u2019s schedule.")
            return

        if appt_d == date.today() and not self._is_edit:
            now = QTime.currentTime()
            if selected_time <= now:
                QMessageBox.warning(
                    self, "Time Has Passed",
                    f"The selected time"
                    f" ({selected_time.toString('hh:mm AP')})"
                    f" has already passed.\nCurrent time is"
                    f" {now.toString('hh:mm AP')}."
                    " Please choose a later time.")
                self.time_edit.setFocus()
                self._refresh_time_range(); return

        if self._sched_start_hhmm and self._sched_end_hhmm:
            t_start = QTime.fromString(self._sched_start_hhmm, "HH:mm")
            t_end = QTime.fromString(self._sched_end_hhmm, "HH:mm")
            if t_start.isValid() and t_end.isValid():
                if selected_time < t_start or selected_time > t_end:
                    QMessageBox.warning(
                        self, "Outside Working Hours",
                        f"The selected time ({selected_time.toString('hh:mm AP')}) is outside "
                        f"the doctor's working hours for this day "
                        f"({_format_time_display(self._sched_start_hhmm or '')} \u2014 {_format_time_display(self._sched_end_hhmm or '')}).")
                    self.time_edit.setFocus()
                    return

        if self._backend and doc_id:
            dt = appt_date
            tm = selected_time.toString("HH:mm:ss")
            exclude_id = None
            if self._backend.check_appointment_conflict(
                    doc_id, dt, tm, exclude_id):
                reply = QMessageBox.warning(
                    self, "Conflict Detected",
                    "This doctor already has an appointment"
                    " at the same time.\nSave anyway?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No)
                if reply != QMessageBox.StandardButton.Yes:
                    return

            # Check daily quota
            if hasattr(self._backend, 'check_daily_quota'):
                under_quota, count, max_quota = self._backend.check_daily_quota(doc_id, dt, exclude_id)
                if not under_quota:
                    reply = QMessageBox.warning(
                        self, "Daily Quota Reached",
                        f"This doctor already has {count} appointments on this day, reaching the recommended daily quota of {max_quota}.\nSave anyway?",
                        QMessageBox.StandardButton.Yes
                        | QMessageBox.StandardButton.No)
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                        
        self.accept()



    def get_data(self) -> dict:
        doc_text = self.doctor_combo.currentText()
        if "  (" in doc_text:
            doc_text = doc_text.split("  (")[0]
        appt_date = self.date_edit.date().toString("yyyy-MM-dd")
        return {
            "patient_name": self.patient_combo.currentText(),
            "patient_id":   self._get_patient_id(),
            "doctor":       doc_text,
            "doctor_id":    self.doctor_combo.currentData(),
            "date":         appt_date,
            "time":         self.time_edit.time().toString("HH:mm:ss"),
            "purpose":      self.purpose_combo.currentText(),
            "service_id":   self.purpose_combo.currentData(),
            "status":       (self.status_combo.currentText() if self._is_edit else "Confirmed"),
            "notes":        self.notes_edit.toPlainText(),
            "cancellation_reason": (self.cancel_reason.text() if self._is_edit else ""),
            "reschedule_reason": "",
        }

# ══════════════════════════════════════════════════════════════════════
#  Appointment Details Dialog (Modern read-only view)
# ══════════════════════════════════════════════════════════════════════
class AppointmentDetailsDialog(QDialog):
    def __init__(self, parent=None, appt: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Appointment Details")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setMinimumWidth(460)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #F4F7F9;
            }
            QFrame#MainCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E1E8ED;
            }
            QLabel#TitleLabel {
                font-size: 18px;
                font-weight: 700;
                color: #2C3E50;
            }
            QLabel#FieldLabel {
                font-size: 13px;
                font-weight: 600;
                color: #7F8C8D;
                padding-right: 16px;
            }
            QLabel#FieldValue {
                font-size: 14px;
                font-weight: 500;
                color: #2C3E50;
            }
            QLabel#PatientName {
                font-size: 16px;
                font-weight: 700;
                color: #1A252F;
            }
            /* Status Pills */
            QLabel#StatusConfirmed {
                background-color: #D1E7DD; color: #0F5132;
                border-radius: 12px; padding: 4px 12px;
                font-size: 12px; font-weight: bold;
            }
            QLabel#StatusPending {
                background-color: #FFF3CD; color: #664D03;
                border-radius: 12px; padding: 4px 12px;
                font-size: 12px; font-weight: bold;
            }
            QLabel#StatusCancelled {
                background-color: #F8D7DA; color: #842029;
                border-radius: 12px; padding: 4px 12px;
                font-size: 12px; font-weight: bold;
            }
            QLabel#StatusCompleted {
                background-color: #CFF4FC; color: #055160;
                border-radius: 12px; padding: 4px 12px;
                font-size: 12px; font-weight: bold;
            }
            QLabel#StatusDefault {
                background-color: #E2E3E5; color: #41464A;
                border-radius: 12px; padding: 4px 12px;
                font-size: 12px; font-weight: bold;
            }
            /* OK Button */
            QPushButton#OkButton {
                background-color: #388087;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                border: none;
            }
            QPushButton#OkButton:hover {
                background-color: #2C6B71;
            }
            QPushButton#OkButton:pressed {
                background-color: #1F5257;
            }
            /* Multi-line fields like notes */
            QTextEdit#NotesField {
                background-color: #F9FAFC;
                border: 1px solid #E1E8ED;
                border-radius: 6px;
                padding: 8px;
                color: #34495E;
                font-size: 13px;
            }
        """)
        
        appt = appt or {}
        time_str = str(appt.get('appointment_time', ''))
        try:
            from datetime import datetime
            t = datetime.strptime(time_str, "%H:%M:%S")
            time_display = t.strftime("%I:%M %p").lstrip("0")
        except Exception: 
            time_display = time_str
            
        date_display = _pretty_date(str(appt.get('appointment_date', '')))
        
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(24, 24, 24, 24)
        main_lay.setSpacing(20)
        
        # -- Main Card Container --
        card = QFrame()
        card.setObjectName("MainCard")
        # Apply drop shadow effect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)
        
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)
        
        # Header Area (Icon + Title + Status)
        hdr_w = QWidget()
        hdr_lay = QHBoxLayout(hdr_w)
        hdr_lay.setContentsMargins(24, 24, 24, 20)
        hdr_lay.setSpacing(16)
        
        # Soft circle icon container
        import os
        from PyQt6.QtSvgWidgets import QSvgWidget
        icon_container = QFrame()
        icon_container.setFixedSize(48, 48)
        icon_container.setStyleSheet("background-color: #E6F0F2; border-radius: 24px;")
        
        icon_lay = QVBoxLayout(icon_container)
        icon_lay.setContentsMargins(12, 12, 12, 12)
        
        svg_path = os.path.join(os.path.dirname(__file__), "..", "styles", "icon-info.svg")
        icon_widget = QSvgWidget(os.path.normpath(svg_path))
        icon_widget.setFixedSize(24, 24)
        icon_widget.setStyleSheet("background: transparent;")
        
        icon_lay.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        hdr_lay.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignTop)
        
        # Title and Patient Name
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        
        title_lbl = QLabel("Appointment Details")
        title_lbl.setObjectName("TitleLabel")
        patient_lbl = QLabel(appt.get('patient_name', 'Unknown Patient'))
        patient_lbl.setObjectName("PatientName")
        
        title_col.addWidget(title_lbl)
        title_col.addWidget(patient_lbl)
        hdr_lay.addLayout(title_col)
        hdr_lay.addStretch()
        
        # Status Pill
        status_val = appt.get('status', 'Pending')
        status_lbl = QLabel(status_val.upper())
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if status_val == "Confirmed":
            status_lbl.setObjectName("StatusConfirmed")
        elif status_val == "Pending":
            status_lbl.setObjectName("StatusPending")
        elif status_val == "Cancelled":
            status_lbl.setObjectName("StatusCancelled")
        elif status_val == "Completed":
            status_lbl.setObjectName("StatusCompleted")
        else:
            status_lbl.setObjectName("StatusDefault")
        hdr_lay.addWidget(status_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        
        card_lay.addWidget(hdr_w)
        
        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #F0F4F7; border: none;")
        div.setFixedHeight(1)
        card_lay.addWidget(div)
        
        # Details Grid
        details_w = QWidget()
        details_lay = QFormLayout(details_w)
        details_lay.setContentsMargins(24, 24, 24, 24)
        details_lay.setHorizontalSpacing(16)
        details_lay.setVerticalSpacing(16)
        
        def _add_row(label, val):
            k = QLabel(label)
            k.setObjectName("FieldLabel")
            v = QLabel(str(val))
            v.setObjectName("FieldValue")
            v.setWordWrap(True)
            details_lay.addRow(k, v)
            
        _add_row("Doctor", appt.get('doctor_name', ''))
        _add_row("Date", date_display)
        _add_row("Time", time_display)
        _add_row("Service", appt.get('service_name', ''))
        
        notes = appt.get("notes", "") or ""
        cancel_reason = appt.get("cancellation_reason", "") or ""
        
        card_lay.addWidget(details_w)
        
        # Optional Notes Section
        if notes or cancel_reason:
            notes_w = QWidget()
            notes_lay = QVBoxLayout(notes_w)
            notes_lay.setContentsMargins(24, 0, 24, 24)
            notes_lay.setSpacing(12)
            
            if notes:
                n_lbl = QLabel("Notes")
                n_lbl.setObjectName("FieldLabel")
                n_val = QTextEdit(notes)
                n_val.setObjectName("NotesField")
                n_val.setReadOnly(True)
                n_val.setMaximumHeight(60)
                notes_lay.addWidget(n_lbl)
                notes_lay.addWidget(n_val)
                
            if cancel_reason:
                c_lbl = QLabel("Cancellation Reason")
                c_lbl.setObjectName("FieldLabel")
                c_val = QTextEdit(cancel_reason)
                c_val.setObjectName("NotesField")
                c_val.setReadOnly(True)
                c_val.setMaximumHeight(60)
                c_val.setStyleSheet("QTextEdit#NotesField { border: 1px solid #F8D7DA; background-color: #FFF5F6; }")
                notes_lay.addWidget(c_lbl)
                notes_lay.addWidget(c_val)
                
            card_lay.addWidget(notes_w)
            
        main_lay.addWidget(card)
        
        # Button Row
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("OkButton")
        ok_btn.setMinimumSize(100, 40)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_lay.addWidget(ok_btn)
        main_lay.addLayout(btn_lay)



# ══════════════════════════════════════════════════════════════════════
#  Cancel Appointment Dialog (Modern UI)
# ══════════════════════════════════════════════════════════════════════
class CancelAppointmentDialog(QDialog):
    def __init__(self, parent=None, patient_name: str = "Unknown"):
        from PyQt6.QtCore import Qt
        super().__init__(parent)
        self.setWindowTitle("Cancel Appointment")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setMinimumWidth(480)
        
        # Modern QSS Styling
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F7FA;
            }
            QFrame#MainCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #DCDCDC;
            }
            QLabel#Breadcrumb {
                font-size: 11px;
                font-weight: 500;
                color: #8A98A5;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QLabel#TitleLabel {
                font-size: 20px;
                font-weight: 800;
                color: #2C3E50;
            }
            QLabel#SubtitleLabel {
                font-size: 15px;
                font-weight: 600;
                color: #34495E;
            }
            QLabel#ReasonLabel {
                font-size: 13px;
                font-weight: 600;
                color: #2C3E50;
            }
            QTextEdit#ReasonText {
                background-color: #FFFFFF;
                border: 1px solid #DCDCDC;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: #2C3E50;
            }
            QTextEdit#ReasonText:focus {
                border: 2px solid #388087;
                background-color: #F8FBFC;
            }
            QPushButton#ConfirmBtn {
                background-color: #E74C3C;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
                border: none;
            }
            QPushButton#ConfirmBtn:hover {
                background-color: #C0392B;
            }
            QPushButton#ConfirmBtn:pressed {
                background-color: #A93226;
            }
            QPushButton#GoBackBtn {
                background-color: transparent;
                color: #7F8C8D;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
                border: 1px solid #DCDCDC;
            }
            QPushButton#GoBackBtn:hover {
                background-color: #F0F3F4;
                color: #34495E;
            }
            QPushButton#GoBackBtn:pressed {
                background-color: #E5E8E8;
            }
        """)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(24, 24, 24, 24)
        main_lay.setSpacing(0)
        
        # Card Container
        card = QFrame()
        card.setObjectName("MainCard")
        # Optional subtle drop shadow
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)
        
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(24, 24, 24, 24)
        card_lay.setSpacing(20)
        
        # --- Header Section ---
        header_lay = QVBoxLayout()
        header_lay.setSpacing(6)
        
        breadcrumb = QLabel("Appointments > Cancel Appointment")
        breadcrumb.setObjectName("Breadcrumb")
        
        title = QLabel("Cancel Appointment")
        title.setObjectName("TitleLabel")
        
        subtitle = QLabel(patient_name)
        subtitle.setObjectName("SubtitleLabel")
        
        header_lay.addWidget(breadcrumb)
        header_lay.addWidget(title)
        header_lay.addWidget(subtitle)
        
        card_lay.addLayout(header_lay)
        
        # --- Body Section ---
        body_lay = QVBoxLayout()
        body_lay.setSpacing(8)
        
        reason_lbl = QLabel("Cancellation Reason")
        reason_lbl.setObjectName("ReasonLabel")
        
        self.reason_text = QTextEdit()
        self.reason_text.setObjectName("ReasonText")
        self.reason_text.setPlaceholderText("Enter reason for cancellation...")
        self.reason_text.setMinimumHeight(100)
        self.reason_text.setMaximumHeight(140)
        
        body_lay.addWidget(reason_lbl)
        body_lay.addWidget(self.reason_text)
        
        card_lay.addLayout(body_lay)
        
        # --- Button Row ---
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(12)
        btn_lay.addStretch()
        
        go_back_btn = QPushButton("Go Back")
        go_back_btn.setObjectName("GoBackBtn")
        go_back_btn.setMinimumHeight(42)
        go_back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        go_back_btn.clicked.connect(self.reject)
        
        confirm_btn = QPushButton("Confirm Cancellation")
        confirm_btn.setObjectName("ConfirmBtn")
        confirm_btn.setMinimumHeight(42)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.clicked.connect(self.accept)
        
        btn_lay.addWidget(go_back_btn)
        btn_lay.addWidget(confirm_btn)
        
        card_lay.addLayout(btn_lay)
        main_lay.addWidget(card)
        
    def get_reason(self) -> str:
        return self.reason_text.toPlainText().strip()
