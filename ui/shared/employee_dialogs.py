# Employee dialogs - add/edit form + profile view (Admin version)

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QDateEdit, QTabWidget, QMessageBox, QCheckBox, QTimeEdit,
    QGroupBox, QScrollArea, QDoubleSpinBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, QDate, QEvent, QTime
from PyQt6.QtGui import QColor
from ui.styles import configure_table, make_table_btn, status_color
from ui.validators import (
    NameValidator, PhoneDigitsValidator,
    validate_name, validate_email, validate_phone_digits,
)


# ══════════════════════════════════════════════════════════════════════
#  Employee Add/Edit Dialog — V3 (reorganised, with confirm step)
# ══════════════════════════════════════════════════════════════════════
class EmployeeDialog(QDialog):
    _INPUT_STYLE = (
        "QLineEdit, QTextEdit { padding: 8px 14px 10px 14px;"
        " border: 2px solid #BADFE7; border-radius: 10px;"
        " font-size: 13px; background-color: #FFFFFF; color: #2C3E50; }"
        "QLineEdit:focus, QTextEdit:focus { border: 2px solid #388087; }"
    )

    _ROLE_DEPT_MAP = {
        "Doctor":       "General Medicine",
        "Nurse":        "General Medicine",
        "Receptionist": "Front Desk",
        "Admin":        "Management",
        "HR":           "Human Resources",
        "Finance":      "Management",
    }

    def __init__(self, parent=None, *, title="Add Employee", data=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._fired = False
        self._title = title

        # Screen-adaptive sizing
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None
        max_h = int(avail.height() * 0.9) if avail else 900
        max_w = int(avail.width() * 0.65) if avail else 960
        self.resize(min(960, max_w), min(860, max_h))
        self.setMinimumSize(780, 540)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Gradient header bar ────────────────────────────────────
        header_bar = QFrame()
        header_bar.setStyleSheet(
            "QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            " stop:0 #388087, stop:1 #6FB3B8); }")
        header_bar.setFixedHeight(58)
        hb_lay = QHBoxLayout(header_bar)
        hb_lay.setContentsMargins(28, 0, 28, 0)

        # Header icon (graceful fallback if QtSvg not installed)
        import os
        _icon_path = os.path.join(
            os.path.dirname(__file__), "..", "styles", "icon-employee.svg")
        try:
            from PyQt6.QtSvgWidgets import QSvgWidget
            icon_w = QSvgWidget(os.path.normpath(_icon_path))
            icon_w.setFixedSize(32, 32)
            icon_w.setStyleSheet("background: transparent;")
        except ImportError:
            icon_w = QLabel("\U0001F464")
            icon_w.setFixedSize(32, 32)
            icon_w.setStyleSheet(
                "font-size: 22px; background: transparent;")
            icon_w.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hb_lay.addWidget(icon_w)
        hb_lay.addSpacing(12)

        h_lbl = QLabel(title)
        h_lbl.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #FFFFFF;"
            " background: transparent;")
        h_sub = QLabel("Fill in the details below")
        h_sub.setStyleSheet(
            "font-size: 12px; color: rgba(255,255,255,0.8);"
            " background: transparent;")
        h_col = QVBoxLayout(); h_col.setSpacing(0)
        h_col.addWidget(h_lbl); h_col.addWidget(h_sub)
        hb_lay.addLayout(h_col); hb_lay.addStretch()
        main_lay.addWidget(header_bar)

        # ── Scrollable content ─────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: #FFFFFF; border: none; }")
        scroll_inner = QWidget()
        scroll_inner.setStyleSheet("background: #FFFFFF;")
        content_lay = QVBoxLayout(scroll_inner)
        content_lay.setContentsMargins(32, 20, 32, 12)
        content_lay.setSpacing(0)

        # ── Two-column form ────────────────────────────────────────
        columns = QHBoxLayout()
        columns.setSpacing(36)

        # Left Column
        self._left_vbox = QVBoxLayout()
        self._left_vbox.setContentsMargins(0, 0, 0, 0)
        self._left_vbox.setSpacing(6)
        self._left_vbox.addWidget(
            self._section_label("\u2460 Identity & Contact"))
        self._left_form = QFormLayout()
        self._left_form.setSpacing(12)
        self._left_form.setContentsMargins(0, 0, 0, 0)
        self._left_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._left_form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self._left_vbox.addLayout(self._left_form)
        columns.addLayout(self._left_vbox, 1)

        # Vertical divider
        vdiv = QFrame()
        vdiv.setFrameShape(QFrame.Shape.VLine)
        vdiv.setStyleSheet("color: #E8F0F1;")
        columns.addWidget(vdiv)

        # Right Column
        self._right_vbox = QVBoxLayout()
        self._right_vbox.setContentsMargins(0, 0, 0, 0)
        self._right_vbox.setSpacing(6)
        self._right_vbox.addWidget(
            self._section_label("\u2461 Role & Compensation"))
        self._right_form = QFormLayout()
        self._right_form.setSpacing(12)
        self._right_form.setContentsMargins(0, 0, 0, 0)
        self._right_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._right_form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self._right_vbox.addLayout(self._right_form)
        columns.addLayout(self._right_vbox, 1)

        content_lay.addLayout(columns)

        # Full-width bottom area (Notes + Schedule)
        self._bottom_vbox = QVBoxLayout()
        self._bottom_vbox.setContentsMargins(0, 8, 0, 0)
        self._bottom_vbox.setSpacing(6)
        content_lay.addLayout(self._bottom_vbox)

        content_lay.addStretch()
        scroll.setWidget(scroll_inner)
        main_lay.addWidget(scroll, 1)

        self._build_fields(None)
        self._build_buttons(main_lay, data)
        if data:
            self._prefill(data)

    # ── UI helpers ─────────────────────────────────────────────────
    def _section_label(self, text: str) -> QWidget:
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 6, 0, 4)
        row.setSpacing(10)
        strip = QFrame()
        strip.setFixedSize(3, 20)
        strip.setStyleSheet(
            "background-color: #388087; border-radius: 1px;")
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #388087;"
            " border: none; background: transparent;")
        row.addWidget(strip); row.addWidget(lbl); row.addStretch()
        return container

    def _required_label(self, text: str) -> QLabel:
        lbl = QLabel(f'{text} <span style="color:#D9534F;">*</span>')
        lbl.setTextFormat(Qt.TextFormat.RichText)
        return lbl

    # ── Build all form fields ──────────────────────────────────────
    def _build_fields(self, _unused):
        left = self._left_form
        right = self._right_form

        # ── Left: Identity & Contact ──────────────────────────────
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet(self._INPUT_STYLE)
        self.name_edit.setPlaceholderText("Full name")
        self.name_edit.setMinimumHeight(40)
        self.name_edit.setValidator(NameValidator())
        self.name_edit.setMaxLength(100)

        self.email_edit = QLineEdit()
        self.email_edit.setStyleSheet(self._INPUT_STYLE)
        self.email_edit.setPlaceholderText("employee@carecrud.com")
        self.email_edit.setMinimumHeight(40)
        self.email_edit.setMaxLength(150)
        self.email_edit.setToolTip("Must be a valid email address")

        # Phone with +63 prefix
        self._phone_frame = QFrame()
        self._phone_frame.setObjectName("phoneFrame")
        self._phone_normal_ss = (
            "QFrame#phoneFrame { border: 2px solid #BADFE7;"
            " border-radius: 10px; background: #FFFFFF; }")
        self._phone_focus_ss = (
            "QFrame#phoneFrame { border: 2px solid #388087;"
            " border-radius: 10px; background: #FFFFFF; }")
        self._phone_frame.setStyleSheet(self._phone_normal_ss)
        self._phone_frame.setFixedHeight(42)
        self._phone_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        phone_lay = QHBoxLayout(self._phone_frame)
        phone_lay.setContentsMargins(0, 0, 0, 0)
        phone_lay.setSpacing(0)
        self._phone_prefix = QLabel("+63")
        self._phone_prefix.setStyleSheet(
            "QLabel { padding: 0px 10px; border: none;"
            " font-size: 13px; font-weight: bold; background: #F0F7F8;"
            " border-top-left-radius: 8px; border-bottom-left-radius: 8px;"
            " color: #2C3E50; }")
        self.phone_edit = QLineEdit()
        self.phone_edit.setStyleSheet(
            "QLineEdit { padding: 0px 14px; border: none;"
            " font-size: 13px; background-color: transparent;"
            " color: #2C3E50; }")
        self.phone_edit.setPlaceholderText("9XXXXXXXXX")
        self.phone_edit.setMaxLength(10)
        self.phone_edit.setValidator(PhoneDigitsValidator())
        self.phone_edit.installEventFilter(self)
        phone_lay.addWidget(self._phone_prefix)
        phone_lay.addWidget(self.phone_edit, 1)

        self.address_edit = QLineEdit()
        self.address_edit.setStyleSheet(self._INPUT_STYLE)
        self.address_edit.setPlaceholderText("Full address")
        self.address_edit.setMinimumHeight(40)
        self.address_edit.setMaxLength(300)
        self.address_edit.setToolTip("Home or mailing address")

        self.emergency_edit = QLineEdit()
        self.emergency_edit.setStyleSheet(self._INPUT_STYLE)
        self.emergency_edit.setPlaceholderText("Name / phone")
        self.emergency_edit.setMinimumHeight(40)
        self.emergency_edit.setMaxLength(200)
        self.emergency_edit.setToolTip(
            "Name and phone number of emergency contact")

        left.addRow(self._required_label("Full Name"), self.name_edit)
        left.addRow(self._required_label("Email"),     self.email_edit)
        left.addRow(self._required_label("Phone"),     self._phone_frame)
        left.addRow("Address",                         self.address_edit)
        left.addRow("Emergency Contact",               self.emergency_edit)

        # ── Right: Role & Compensation ────────────────────────────
        self.role_combo = QComboBox()
        self.role_combo.setObjectName("formCombo")
        self.role_combo.addItems(
            ["Doctor", "Nurse", "Receptionist", "Admin", "HR", "Finance"])
        self.role_combo.setMinimumHeight(40)

        self.dept_combo = QComboBox()
        self.dept_combo.setObjectName("formCombo")
        from backend import AuthBackend
        try:
            _be = AuthBackend()
            depts = (_be.get_all_departments()
                     if hasattr(_be, 'get_all_departments') else [])
            for d in depts:
                self.dept_combo.addItem(d.get("department_name", ""))
            _be.close()
        except Exception:
            self.dept_combo.addItems([
                "General Medicine", "Cardiology", "Dentistry",
                "Pediatrics", "Laboratory", "Front Desk",
                "Management", "Pharmacy", "Human Resources"])
        self.dept_combo.setMinimumHeight(40)
        self.role_combo.currentTextChanged.connect(
            self._on_role_changed_dept)
        self._on_role_changed_dept(self.role_combo.currentText())

        self.type_combo = QComboBox()
        self.type_combo.setObjectName("formCombo")
        self.type_combo.addItems(["Full-time", "Part-time", "Contract"])
        self.type_combo.setMinimumHeight(40)

        self.hire_date = QDateEdit()
        self.hire_date.setCalendarPopup(True)
        self.hire_date.setDate(QDate.currentDate())
        self.hire_date.setObjectName("formCombo")
        self.hire_date.setMaximumDate(QDate.currentDate())
        self.hire_date.setMinimumHeight(40)
        self.hire_date.setDisplayFormat("M/d/yyyy")
        self.hire_date.setToolTip("Cannot be a future date")

        self.salary_spin = QDoubleSpinBox()
        self.salary_spin.setObjectName("formCombo")
        self.salary_spin.setRange(0, 999999.99)
        self.salary_spin.setDecimals(2)
        self.salary_spin.setPrefix("\u20b1 ")
        self.salary_spin.setSingleStep(1000)
        self.salary_spin.setMinimumHeight(40)
        self.salary_spin.setToolTip("Monthly salary in Philippine Pesos")
        self.salary_edit = None  # back-compat alias

        self.status_combo = QComboBox()
        self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Active", "On Leave", "Inactive"])
        self.status_combo.setMinimumHeight(40)

        right.addRow("Role",           self.role_combo)
        right.addRow("Department",     self.dept_combo)
        right.addRow("Type",           self.type_combo)
        right.addRow("Hire Date",      self.hire_date)
        right.addRow("Monthly Salary", self.salary_spin)
        right.addRow("Status",         self.status_combo)

        self._left_vbox.addStretch(1)
        self._right_vbox.addStretch(1)

        # ── Bottom: Notes + Schedule (full width) ─────────────────
        bsep = QFrame()
        bsep.setFixedHeight(1)
        bsep.setStyleSheet("background: #E8F0F1;")
        self._bottom_vbox.addWidget(bsep)
        self._bottom_vbox.addWidget(
            self._section_label("\u2462 Additional Information"))

        # Notes row
        notes_row = QHBoxLayout(); notes_row.setSpacing(12)
        notes_lbl = QLabel("Notes")
        notes_lbl.setMinimumWidth(90)
        notes_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        notes_lbl.setStyleSheet("color: #2C3E50; font-size: 13px;")
        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(self._INPUT_STYLE)
        self.notes_edit.setMaximumHeight(70)
        self.notes_edit.setPlaceholderText(
            "Internal notes about this employee...")
        self.notes_edit.setToolTip(
            "Optional notes \u2014 not visible to the employee")
        notes_row.addWidget(notes_lbl)
        notes_row.addWidget(self.notes_edit, 1)
        self._bottom_vbox.addLayout(notes_row)

        # Doctor schedule
        self._schedule_group = QGroupBox("Weekly Availability")
        self._schedule_group.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #388087;"
            " border: 1.5px solid #BADFE7; border-radius: 10px;"
            " margin-top: 10px; padding: 20px 14px 14px 14px; }"
            "QGroupBox::title { subcontrol-origin: margin;"
            " left: 14px; padding: 0 8px; font-size: 13px; }")
        self._bottom_vbox.addWidget(self._schedule_group)

        sched_main = QVBoxLayout(self._schedule_group)
        sched_main.setSpacing(8)

        day_row = QHBoxLayout(); day_row.setSpacing(6)
        self._day_checks: list[QCheckBox] = []
        self._DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
                      "Friday", "Saturday", "Sunday"]
        self._DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat",
                          "Sun"]
        for abbr in self._DAY_ABBR:
            cb = QCheckBox(abbr)
            cb.setStyleSheet("font-size: 12px;")
            cb.toggled.connect(self._refresh_schedule_times)
            self._day_checks.append(cb)
            day_row.addWidget(cb)
        day_row.addStretch()
        sched_main.addLayout(day_row)

        self._time_container = QWidget()
        self._time_layout = QVBoxLayout(self._time_container)
        self._time_layout.setContentsMargins(0, 0, 0, 0)
        self._time_layout.setSpacing(6)
        self._day_time_rows: list[QWidget] = []
        self._day_start: list[QTimeEdit] = []
        self._day_end: list[QTimeEdit] = []
        for i, day in enumerate(self._DAYS):
            row_w = QWidget()
            rl = QHBoxLayout(row_w)
            rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(8)
            lbl = QLabel(day); lbl.setMinimumWidth(85)
            lbl.setStyleSheet("font-size: 12px; color: #2C3E50;")
            st = QTimeEdit()
            st.setTime(QTime(8, 0))
            st.setDisplayFormat("hh:mm AP")
            st.setObjectName("formCombo")
            st.setMinimumHeight(34); st.setMinimumWidth(130)
            en = QTimeEdit()
            en.setTime(QTime(17, 0))
            en.setDisplayFormat("hh:mm AP")
            en.setObjectName("formCombo")
            en.setMinimumHeight(34); en.setMinimumWidth(130)
            rl.addWidget(lbl)
            rl.addWidget(QLabel("from")); rl.addWidget(st, 1)
            rl.addWidget(QLabel("to"));   rl.addWidget(en, 1)
            self._day_start.append(st)
            self._day_end.append(en)
            self._day_time_rows.append(row_w)
            self._time_layout.addWidget(row_w)
            row_w.setVisible(False)
        sched_main.addWidget(self._time_container)

        self._schedule_group.setVisible(
            self.role_combo.currentText() == "Doctor")
        self.role_combo.currentTextChanged.connect(
            lambda txt: self._schedule_group.setVisible(txt == "Doctor"))

    # ── Smart department ───────────────────────────────────────────
    def _on_role_changed_dept(self, role_text: str):
        suggested = self._ROLE_DEPT_MAP.get(role_text)
        if suggested:
            idx = self.dept_combo.findText(suggested)
            if idx >= 0:
                self.dept_combo.setCurrentIndex(idx)

    # ── Button bar ─────────────────────────────────────────────────
    def _build_buttons(self, parent_lay, data):
        btn_sep = QFrame()
        btn_sep.setFixedHeight(1)
        btn_sep.setStyleSheet("background: #E8F0F1;")
        parent_lay.addWidget(btn_sep)

        btn_bar = QWidget()
        btn_bar.setObjectName("btnBar")
        btn_bar.setStyleSheet("QWidget#btnBar { background: #FAFBFB; }")
        btn_row = QHBoxLayout(btn_bar)
        btn_row.setContentsMargins(28, 12, 28, 12)
        btn_row.setSpacing(14)

        if data:
            fire_btn = QPushButton("Fire")
            fire_btn.setMinimumHeight(40)
            fire_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            fire_btn.setObjectName("dialogDangerBtn")
            fire_btn.clicked.connect(self._on_fire)
            btn_row.addWidget(fire_btn)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setMinimumWidth(130)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setObjectName("dialogCancelBtn")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Review && Confirm")
        save_btn.setMinimumHeight(40)
        save_btn.setMinimumWidth(170)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setObjectName("dialogSaveBtn")
        save_btn.clicked.connect(self.accept)
        save_btn.setToolTip("Review a summary before saving")

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        parent_lay.addWidget(btn_bar)

    # ── Prefill for edit mode ──────────────────────────────────────
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
        self.emergency_edit.setText(
            data.get("emergency_contact", "") or "")
        sal = data.get("salary", "")
        if sal:
            try:
                self.salary_spin.setValue(float(sal))
            except (ValueError, TypeError):
                self.salary_spin.setValue(0)
        schedules = data.get("schedules", [])
        if schedules:
            days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2,
                        "Thursday": 3, "Friday": 4, "Saturday": 5,
                        "Sunday": 6}
            for s in schedules:
                idx = days_map.get(s.get("day_of_week", ""), -1)
                if idx >= 0:
                    self._day_checks[idx].setChecked(True)
                    st = s.get("start_time", "08:00")
                    en = s.get("end_time", "17:00")
                    if hasattr(st, "total_seconds"):
                        ts = int(st.total_seconds())
                        h, m = divmod(ts // 60, 60)
                        st = f"{h:02d}:{m:02d}"
                    if hasattr(en, "total_seconds"):
                        ts = int(en.total_seconds())
                        h, m = divmod(ts // 60, 60)
                        en = f"{h:02d}:{m:02d}"
                    self._day_start[idx].setTime(
                        QTime.fromString(str(st)[:5], "HH:mm"))
                    self._day_end[idx].setTime(
                        QTime.fromString(str(en)[:5], "HH:mm"))

    def _refresh_schedule_times(self):
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

    # ── Validation + Review & Confirm ──────────────────────────────
    def accept(self):
        err = validate_name(self.name_edit.text(), "Full Name")
        if err:
            QMessageBox.warning(self, "Validation", err); return
        if not self.phone_edit.text().strip():
            QMessageBox.warning(
                self, "Validation", "Phone number is required."); return
        err = validate_phone_digits(self.phone_edit.text())
        if err:
            QMessageBox.warning(self, "Validation", err); return
        if not self.email_edit.text().strip():
            QMessageBox.warning(
                self, "Validation", "Email is required."); return
        err = validate_email(self.email_edit.text())
        if err:
            QMessageBox.warning(self, "Validation", err); return

        # Show the review confirmation dialog
        if not self._show_review():
            return
        super().accept()

    def _show_review(self) -> bool:
        """Show a formatted summary dialog. Returns True if confirmed."""
        d = self.get_data()
        sal = d.get("salary")
        sal_str = f"\u20b1 {float(sal):,.2f}" if sal else "Not set"

        sched_html = ""
        for s in d.get("schedules", []):
            day = s["day_of_week"]
            st = s["start_time"][:5]
            en = s["end_time"][:5]
            sched_html += (
                f"<br>&nbsp;&nbsp;&bull; {day}: {st} \u2013 {en}")

        ROW = ("<tr>"
               "<td style='padding:4px 12px 4px 0; color:#7F8C8D;"
               " white-space:nowrap;'>{}</td>"
               "<td style='padding:4px 0;'><b>{}</b></td></tr>")
        SEP = "<tr><td colspan='2'><hr style='border:none;" \
              " border-top:1px solid #E8F0F1;'></td></tr>"

        rows = [
            ROW.format("Name",       d["name"]),
            ROW.format("Email",      d["email"]),
            ROW.format("Phone",      d["phone"]),
            ROW.format("Address",    d.get("address") or "\u2014"),
            ROW.format("Emergency",  d.get("emergency_contact") or "\u2014"),
            SEP,
            ROW.format("Role",       d["role"]),
            ROW.format("Department", d["dept"]),
            ROW.format("Type",       d["type"]),
            ROW.format("Hire Date",  d["hire_date"]),
            ROW.format("Salary",     sal_str),
            ROW.format("Status",     d["status"]),
        ]
        if sched_html:
            rows.append(SEP)
            rows.append(ROW.format("Schedule", sched_html))
        if d.get("notes", "").strip():
            rows.append(ROW.format("Notes",
                        d["notes"][:80] + ("\u2026" if len(d["notes"]) > 80 else "")))

        html = ("<div style='font-size:13px; color:#2C3E50;'>"
                "<table cellpadding='0' cellspacing='0'>"
                + "".join(rows)
                + "</table></div>")

        dlg = QMessageBox(self)
        dlg.setWindowTitle("Review Employee Details")
        dlg.setIcon(QMessageBox.Icon.Question)
        dlg.setText(
            "<b style='font-size:15px; color:#388087;'>"
            "Please review before saving</b>")
        dlg.setInformativeText(html)
        confirm_btn = dlg.addButton(
            "Confirm && Save", QMessageBox.ButtonRole.AcceptRole)
        back_btn = dlg.addButton(
            "Go Back", QMessageBox.ButtonRole.RejectRole)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.setStyleSheet(
            "QPushButton { background-color: #388087; color: #FFF;"
            " border: none; border-radius: 8px; padding: 8px 24px;"
            " font-size: 13px; font-weight: bold; min-height: 38px; }"
            " QPushButton:hover { background-color: #2C6A70; }")
        back_btn.setStyleSheet(
            "QPushButton { background-color: #F6F6F2; color: #2C3E50;"
            " border: 2px solid #BADFE7; border-radius: 8px;"
            " padding: 8px 24px; font-size: 13px; font-weight: bold;"
            " min-height: 38px; }"
            " QPushButton:hover { background-color: #E8F4F5;"
            " border-color: #388087; }")
        dlg.exec()
        return dlg.clickedButton() == confirm_btn

    # ── Data out ───────────────────────────────────────────────────
    def get_data(self) -> dict:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday"]
        schedules = []
        for i, day in enumerate(days):
            if self._day_checks[i].isChecked():
                schedules.append({
                    "day_of_week": day,
                    "start_time": self._day_start[i].time().toString(
                        "HH:mm:ss"),
                    "end_time": self._day_end[i].time().toString(
                        "HH:mm:ss"),
                })
        sal = self.salary_spin.value()
        return {
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
            "salary":      sal if sal > 0 else None,
            "emergency_contact": self.emergency_edit.text().strip(),
        }


# ══════════════════════════════════════════════════════════════════════
#  Employee Profile Dialog (V2)
# ══════════════════════════════════════════════════════════════════════
class EmployeeProfileDialog(QDialog):
    """Read-only profile with tabs: Info, Appointments, Performance."""

    def __init__(self, parent=None, *, emp_data=None, backend=None, role: str = "Admin"):
        super().__init__(parent)
        self.setWindowTitle(f"Employee Profile \u2013 {emp_data.get('full_name', '')}")
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
            ("Phone",      self._emp.get("phone", "") or "\u2014"),
            ("Email",      self._emp.get("email", "") or "\u2014"),
            ("Hire Date",  str(self._emp.get("hire_date", "")) or "\u2014"),
            ("Status",     self._emp.get("status", "")),
            ("Notes",      self._emp.get("notes", "") or "\u2014"),
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
            ("Revenue Generated",  f"\u20b1{float(perf.get('revenue', 0)):,.0f}"),
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
