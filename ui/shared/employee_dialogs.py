# Employee dialogs - add/edit form + profile view (Admin version)

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QDateEdit, QTabWidget, QMessageBox, QCheckBox, QTimeEdit,
    QGroupBox, QScrollArea,
)
from PyQt6.QtCore import Qt, QDate, QEvent, QTime
from PyQt6.QtGui import QColor
from ui.styles import configure_table, make_table_btn, status_color
from ui.validators import NameValidator, PhoneDigitsValidator, validate_name, validate_email, validate_phone_digits


# ══════════════════════════════════════════════════════════════════════
#  Employee Add/Edit Dialog (V2 – leave dates)
# ══════════════════════════════════════════════════════════════════════
class EmployeeDialog(QDialog):
    _INPUT_STYLE = (
        "QLineEdit, QTextEdit { padding: 8px 14px 10px 14px; border: 2px solid #BADFE7;"
        " border-radius: 10px; font-size: 13px; background-color: #FFFFFF;"
        " color: #2C3E50; }"
        "QLineEdit:focus, QTextEdit:focus { border: 2px solid #388087; }"
    )

    def __init__(self, parent=None, *, title="Add Employee", data=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._fired = False

        # Size appropriately - removed screen ratio calculation as it stretches fields awkwardly on wide monitors
        self.resize(760, 560)
        self.setMinimumSize(700, 480)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(28, 20, 28, 18)
        main_lay.setSpacing(0)

        # Dialog title header
        header = QLabel(title)
        header.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #388087;"
            " padding-bottom: 4px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_lay.addWidget(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #BADFE7;")
        main_lay.addWidget(sep)
        main_lay.addSpacing(10)

        # Two-column form area (no scroll)
        columns = QHBoxLayout()
        columns.setSpacing(28)

        # Left column — Personal Information
        self._left_vbox = QVBoxLayout()
        self._left_vbox.setContentsMargins(0, 0, 0, 0)
        self._left_vbox.setSpacing(10)
        self._left_vbox.addWidget(self._section_label("Personal Information"))

        self._left_form = QFormLayout()
        self._left_form.setSpacing(10)
        self._left_form.setContentsMargins(0, 0, 0, 0)
        self._left_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._left_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self._left_vbox.addLayout(self._left_form)
        columns.addLayout(self._left_vbox, 1)

        # Vertical divider
        vdiv = QFrame()
        vdiv.setFrameShape(QFrame.Shape.VLine)
        vdiv.setStyleSheet("color: #BADFE7;")
        columns.addWidget(vdiv)

        # Right column — Employment Details
        self._right_vbox = QVBoxLayout()
        self._right_vbox.setContentsMargins(0, 0, 0, 0)
        self._right_vbox.setSpacing(10)
        self._right_vbox.addWidget(self._section_label("Employment Details"))

        self._right_form = QFormLayout()
        self._right_form.setSpacing(10)
        self._right_form.setContentsMargins(0, 0, 0, 0)
        self._right_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._right_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self._right_vbox.addLayout(self._right_form)
        columns.addLayout(self._right_vbox, 1)

        main_lay.addLayout(columns)
        
        self._build_fields(None)
        self._build_buttons(main_lay, data)
        if data:
            self._prefill(data)

    # ── Overridable hooks ─────────────────────────────────────────
    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #388087;"
            " padding: 8px 0 2px 0; border: none; background: transparent;")
        return lbl

    def _build_fields(self, _unused):
        """Create all form widgets and distribute across two columns."""
        left = self._left_form
        right = self._right_form

        # ── Left Column: Personal Information ─────────────────────
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(self._INPUT_STYLE)
        self.name_edit.setPlaceholderText("Full name")
        self.name_edit.setMinimumHeight(42)
        self.name_edit.setValidator(NameValidator())
        self.name_edit.setMaxLength(100)

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
        self._phone_frame.setFixedHeight(44)
        from PyQt6.QtWidgets import QSizePolicy
        self._phone_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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
        self.phone_edit.setValidator(PhoneDigitsValidator())
        self.phone_edit.installEventFilter(self)
        phone_lay.addWidget(self._phone_prefix)
        phone_lay.addWidget(self.phone_edit, 1)

        self.email_edit = QLineEdit()
        self.email_edit.setStyleSheet(self._INPUT_STYLE)
        self.email_edit.setPlaceholderText("Email")
        self.email_edit.setMinimumHeight(42)
        self.email_edit.setMaxLength(150)

        self.address_edit = QLineEdit()
        self.address_edit.setStyleSheet(self._INPUT_STYLE)
        self.address_edit.setPlaceholderText("Full address")
        self.address_edit.setMinimumHeight(42)
        self.address_edit.setMaxLength(300)

        self.emergency_edit = QLineEdit()
        self.emergency_edit.setStyleSheet(self._INPUT_STYLE)
        self.emergency_edit.setPlaceholderText("Emergency contact (name / phone)")
        self.emergency_edit.setMinimumHeight(42)
        self.emergency_edit.setMaxLength(200)

        left.addRow("Full Name",         self.name_edit)
        left.addRow("Phone",             self._phone_frame)
        left.addRow("Email",             self.email_edit)
        left.addRow("Address",           self.address_edit)
        left.addRow("Emergency Contact", self.emergency_edit)

        # Notes at bottom of left column
        # Moved out of the QFormLayout into the parent VBoxLayout to avoid layout stretching issues
        self._left_vbox.addWidget(self._section_label("Additional"))
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(self._INPUT_STYLE)
        self.notes_edit.setMaximumHeight(70)
        
        notes_form = QFormLayout()
        notes_form.setSpacing(10)
        notes_form.setContentsMargins(0, 0, 0, 0)
        notes_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        notes_form.addRow("Notes", self.notes_edit)
        
        # We need to insert this before the stretch element at the end of the vbox
        self._left_vbox.insertLayout(self._left_vbox.count() - 1, notes_form)

        # ── Right Column: Employment Details ──────────────────────

        self.role_combo = QComboBox(); self.role_combo.setObjectName("formCombo")
        self.role_combo.addItems(["Doctor", "Nurse", "Receptionist", "Admin", "HR", "Finance"])
        self.role_combo.setMinimumHeight(38)

        self.dept_combo = QComboBox(); self.dept_combo.setObjectName("formCombo")
        # Load departments from database if backend is available
        from backend import AuthBackend
        try:
            _be = AuthBackend()
            depts = _be.get_all_departments() if hasattr(_be, 'get_all_departments') else []
            for d in depts:
                self.dept_combo.addItem(d.get("department_name", ""))
            _be.close()
        except Exception:
            self.dept_combo.addItems([
                "General Medicine", "Cardiology", "Dentistry", "Pediatrics",
                "Laboratory", "Front Desk", "Management", "Pharmacy", "Human Resources",
            ])
        self.dept_combo.setMinimumHeight(38)

        self.type_combo = QComboBox(); self.type_combo.setObjectName("formCombo")
        self.type_combo.addItems(["Full-time", "Part-time", "Contract"])
        self.type_combo.setMinimumHeight(38)

        self.hire_date = QDateEdit(); self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate()); self.hire_date.setObjectName("formCombo")
        self.hire_date.setMaximumDate(QDate.currentDate())
        self.hire_date.setMinimumHeight(38)

        self.salary_edit = QLineEdit()
        self.salary_edit.setStyleSheet(self._INPUT_STYLE)
        self.salary_edit.setPlaceholderText("Monthly salary (e.g. 55000)")
        self.salary_edit.setMinimumHeight(42)
        self.salary_edit.setMaxLength(15)
        from PyQt6.QtGui import QDoubleValidator
        self.salary_edit.setValidator(QDoubleValidator(0.0, 9999999.99, 2))

        self.status_combo = QComboBox(); self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Active", "On Leave", "Inactive"])
        self.status_combo.setMinimumHeight(38)

        right.addRow("Role",        self.role_combo)
        right.addRow("Department",  self.dept_combo)
        right.addRow("Type",        self.type_combo)
        right.addRow("Hire Date",   self.hire_date)
        right.addRow("Salary",      self.salary_edit)
        right.addRow("Status",      self.status_combo)

        # Doctor schedule picker (shown only when role is Doctor)
        self._schedule_group = QGroupBox("Weekly Availability")
        self._schedule_group.setStyleSheet(
            "QGroupBox { font-weight: bold; border: 2px solid #BADFE7;"
            " border-radius: 10px; margin-top: 10px; padding-top: 18px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }"
        )
        # Add schedule to right VBox below the main form layout
        self._right_vbox.addWidget(self._schedule_group)

        sched_main = QVBoxLayout(self._schedule_group)
        sched_main.setSpacing(10)

        # Day selector row — compact checkboxes
        day_row = QHBoxLayout(); day_row.setSpacing(6)
        self._day_checks: list[QCheckBox] = []
        self._DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self._DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, abbr in enumerate(self._DAY_ABBR):
            cb = QCheckBox(abbr)
            cb.setStyleSheet("font-size: 12px;")
            cb.toggled.connect(self._refresh_schedule_times)
            self._day_checks.append(cb)
            day_row.addWidget(cb)
        day_row.addStretch()
        sched_main.addLayout(day_row)

        # Time pickers container — only visible rows for checked days
        self._time_container = QWidget()
        self._time_layout = QVBoxLayout(self._time_container)
        self._time_layout.setContentsMargins(0, 0, 0, 0)
        self._time_layout.setSpacing(6)
        self._day_time_rows: list[QWidget] = []
        self._day_start: list[QTimeEdit] = []
        self._day_end: list[QTimeEdit] = []
        for i, day in enumerate(self._DAYS):
            row_w = QWidget()
            rl = QHBoxLayout(row_w); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(8)
            lbl = QLabel(day); lbl.setMinimumWidth(80)
            lbl.setStyleSheet("font-size: 12px; color: #2C3E50;")
            st = QTimeEdit(); st.setTime(QTime(8, 0)); st.setDisplayFormat("hh:mm AP")
            st.setObjectName("formCombo"); st.setMinimumHeight(34); st.setMinimumWidth(100)
            en = QTimeEdit(); en.setTime(QTime(17, 0)); en.setDisplayFormat("hh:mm AP")
            en.setObjectName("formCombo"); en.setMinimumHeight(34); en.setMinimumWidth(100)
            rl.addWidget(lbl)
            rl.addWidget(QLabel("from")); rl.addWidget(st)
            rl.addWidget(QLabel("to")); rl.addWidget(en)
            rl.addStretch()
            self._day_start.append(st)
            self._day_end.append(en)
            self._day_time_rows.append(row_w)
            self._time_layout.addWidget(row_w)
            row_w.setVisible(False)
        sched_main.addWidget(self._time_container)

        self._schedule_group.setVisible(self.role_combo.currentText() == "Doctor")
        self.role_combo.currentTextChanged.connect(
            lambda txt: self._schedule_group.setVisible(txt == "Doctor"))
        
        self._left_vbox.addStretch(1)
        self._right_vbox.addStretch(1)
        if data:
            fire_btn = QPushButton("Fire")
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
        parent_lay.addLayout(btn_row)

    def _prefill(self, data):
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
        self.address_edit.setText(data.get("address", "") or "")
        self.emergency_edit.setText(data.get("emergency_contact", "") or "")
        sal = data.get("salary", "")
        if sal:
            self.salary_edit.setText(str(sal))
        # Prefill doctor schedule if present
        schedules = data.get("schedules", [])
        if schedules:
            days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
                        "Friday": 4, "Saturday": 5, "Sunday": 6}
            for s in schedules:
                idx = days_map.get(s.get("day_of_week", ""), -1)
                if idx >= 0:
                    self._day_checks[idx].setChecked(True)
                    st = s.get("start_time", "08:00")
                    en = s.get("end_time", "17:00")
                    if hasattr(st, "total_seconds"):
                        ts = int(st.total_seconds()); h, m = divmod(ts // 60, 60)
                        st = f"{h:02d}:{m:02d}"
                    if hasattr(en, "total_seconds"):
                        ts = int(en.total_seconds()); h, m = divmod(ts // 60, 60)
                        en = f"{h:02d}:{m:02d}"
                    self._day_start[idx].setTime(QTime.fromString(str(st)[:5], "HH:mm"))
                    self._day_end[idx].setTime(QTime.fromString(str(en)[:5], "HH:mm"))

    def _refresh_schedule_times(self):
        """Show/hide time-picker rows based on which day checkboxes are ticked."""
        for i, cb in enumerate(self._day_checks):
            self._day_time_rows[i].setVisible(cb.isChecked())

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
        from PyQt6.QtWidgets import QMessageBox
        err = validate_name(self.name_edit.text(), "Full Name")
        if err:
            QMessageBox.warning(self, "Validation", err); return
        if not self.phone_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Phone number is required."); return
        err = validate_phone_digits(self.phone_edit.text())
        if err:
            QMessageBox.warning(self, "Validation", err); return
        if not self.email_edit.text().strip():
            QMessageBox.warning(self, "Validation", "Email is required."); return
        err = validate_email(self.email_edit.text())
        if err:
            QMessageBox.warning(self, "Validation", err); return
        super().accept()

    def get_data(self) -> dict:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        schedules = []
        for i, day in enumerate(days):
            if self._day_checks[i].isChecked():
                schedules.append({
                    "day_of_week": day,
                    "start_time": self._day_start[i].time().toString("HH:mm:ss"),
                    "end_time": self._day_end[i].time().toString("HH:mm:ss"),
                })
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
            "schedules":   schedules,
            "address":     self.address_edit.text().strip(),
            "salary":      self.salary_edit.text().strip(),
            "emergency_contact": self.emergency_edit.text().strip(),
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
            si.setForeground(QColor(status_color(a.get("status", ""))))
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
        close_btn.setObjectName("dialogSaveBtn")
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
