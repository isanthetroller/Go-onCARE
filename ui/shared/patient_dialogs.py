# Patient dialogs - add/edit, profile view, merge

from datetime import date

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QTabWidget,
    QDateEdit, QCheckBox, QMessageBox, QFrame, QPushButton,
    QGridLayout, QDialogButtonBox,
)
from PyQt6.QtCore import Qt, QDate, QEvent
from ui.styles import configure_table, style_dialog_btns
from ui.validators import NameValidator, PhoneDigitsValidator, validate_name, validate_email, validate_phone_digits


# ── Patient Add/Edit Dialog ───────────────────────────────────────────
class PatientDialog(QDialog):
    """Add / Edit patient dialog with emergency contact, blood type, condition picker."""

    _INPUT_STYLE = (
        "QLineEdit, QTextEdit { padding: 8px 14px 10px 14px; border: 2px solid #BADFE7;"
        " border-radius: 10px; font-size: 13px; background-color: #FFFFFF;"
        " color: #2C3E50; }"
        "QLineEdit:focus, QTextEdit:focus { border: 2px solid #388087; }"
    )

    def __init__(self, parent=None, *, title="Add New Patient", data=None, backend=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._backend = backend

        # Responsive sizing — landscape proportions
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.62), int(screen.height() * 0.82))
        self.setMinimumWidth(820)

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(28, 20, 28, 18)
        main_lay.setSpacing(0)

        # ── Dialog title header ──────────────────────────────────
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

        # ── Two-column layout ────────────────────────────────────
        columns = QHBoxLayout()
        columns.setSpacing(24)

        # Left column — Personal Information
        self._left_form = QFormLayout()
        self._left_form.setSpacing(10)
        self._left_form.setContentsMargins(0, 0, 0, 0)
        self._left_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        columns.addLayout(self._left_form, 1)

        # Vertical divider
        vdiv = QFrame()
        vdiv.setFrameShape(QFrame.Shape.VLine)
        vdiv.setStyleSheet("color: #BADFE7;")
        columns.addWidget(vdiv)

        # Right column — Medical & Admin
        right_col = QVBoxLayout()
        right_col.setSpacing(0)
        self._right_form = QFormLayout()
        self._right_form.setSpacing(10)
        self._right_form.setContentsMargins(0, 0, 0, 0)
        self._right_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        right_col.addLayout(self._right_form)

        # Conditions section (below right form fields)
        right_col.addSpacing(6)
        self._cond_section = QVBoxLayout()
        self._cond_section.setSpacing(6)
        right_col.addLayout(self._cond_section, 1)
        columns.addLayout(right_col, 1)

        main_lay.addLayout(columns, 1)
        main_lay.addSpacing(10)

        self._build_fields(data)
        self._build_buttons(main_lay)

        if data:
            self._prefill(data)

    _CB_STYLE = (
        "QCheckBox { font-size: 12px; color: #2C3E50; spacing: 6px;"
        " padding: 5px 4px; border: none; background: transparent; }"
        "QCheckBox:checked { color: #388087; font-weight: bold; }"
        "QCheckBox:hover { color: #388087; }"
        "QCheckBox::indicator { width: 16px; height: 16px;"
        " border: 2px solid #BADFE7; border-radius: 4px; background: #FFFFFF; }"
        "QCheckBox::indicator:checked { background: #388087;"
        " border-color: #388087;"
        " image: none; }"
        "QCheckBox::indicator:hover { border-color: #388087; }"
    )

    # ── Section label helper ──────────────────────────────────────
    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #388087;"
            " padding: 6px 0 2px 0; border: none; background: transparent;")
        return lbl

    # ── Build all fields across two columns ───────────────────────
    def _build_fields(self, data):
        left = self._left_form
        right = self._right_form

        # ── LEFT: Personal Information ────────────────────────────
        left.addRow(self._section_label("Personal Information"))

        self.name_edit = self._input("Full name")
        self.name_edit.setValidator(NameValidator())
        self.name_edit.setMaxLength(100)

        self.sex_combo = QComboBox(); self.sex_combo.setObjectName("formCombo")
        self.sex_combo.addItems(["Male", "Female"])
        self.sex_combo.setMinimumHeight(38)

        self.dob_edit = QDateEdit(); self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDate(QDate.currentDate()); self.dob_edit.setObjectName("formCombo")
        self.dob_edit.setMaximumDate(QDate.currentDate())
        self.dob_edit.setDisplayFormat("MMMM d, yyyy")
        self.dob_edit.setMinimumHeight(38)

        # Phone: +63 prefix frame
        self._phone_frame = QFrame()
        self._phone_frame.setObjectName("phoneFrame")
        self._phone_normal_ss = (
            "QFrame#phoneFrame { border: 2px solid #BADFE7; border-radius: 10px;"
            " background: #FFFFFF; }")
        self._phone_focus_ss = (
            "QFrame#phoneFrame { border: 2px solid #388087; border-radius: 10px;"
            " background: #FFFFFF; }")
        self._phone_frame.setStyleSheet(self._phone_normal_ss)
        self._phone_frame.setFixedHeight(44)
        phone_lay = QHBoxLayout(self._phone_frame)
        phone_lay.setContentsMargins(0, 0, 0, 0); phone_lay.setSpacing(0)
        self._phone_prefix = QLabel("+63")
        self._phone_prefix.setStyleSheet(
            "QLabel { padding: 0px 10px; border: none;"
            " font-size: 13px; font-weight: bold; background: #F0F7F8;"
            " border-top-left-radius: 8px; border-bottom-left-radius: 8px;"
            " color: #2C3E50; }")
        self.phone_edit = QLineEdit()
        self.phone_edit.setStyleSheet(
            "QLineEdit { padding: 0px 14px; border: none;"
            " font-size: 13px; background-color: transparent; color: #2C3E50; }")
        self.phone_edit.setPlaceholderText("9XXXXXXXXX")
        self.phone_edit.setMaxLength(10)
        self.phone_edit.setValidator(PhoneDigitsValidator())
        self.phone_edit.installEventFilter(self)
        phone_lay.addWidget(self._phone_prefix)
        phone_lay.addWidget(self.phone_edit, 1)

        self.email_edit = self._input("Email")
        self.email_edit.setMaxLength(150)
        self.address_edit = self._input("Full address")
        self.address_edit.setMaxLength(300)
        self.civil_combo = QComboBox(); self.civil_combo.setObjectName("formCombo")
        self.civil_combo.addItems(["Single", "Married", "Widowed", "Separated"])
        self.civil_combo.setMinimumHeight(38)
        self.emergency_edit = self._input("Emergency contact (name / phone)")
        self.emergency_edit.setMaxLength(150)

        left.addRow("Full Name", self.name_edit)
        left.addRow("Sex", self.sex_combo)
        left.addRow("Date of Birth", self.dob_edit)
        left.addRow("Phone", self._phone_frame)
        left.addRow("Email", self.email_edit)
        left.addRow("Address", self.address_edit)
        left.addRow("Civil Status", self.civil_combo)
        left.addRow("Emergency Contact", self.emergency_edit)

        # Notes at bottom of left column
        left.addRow(self._section_label("Additional"))
        self.notes_edit = QTextEdit(); self.notes_edit.setObjectName("formInput")
        self.notes_edit.setStyleSheet(self._INPUT_STYLE)
        self.notes_edit.setMaximumHeight(70)
        left.addRow("Notes", self.notes_edit)

        # ── RIGHT: Medical & Admin ────────────────────────────────
        right.addRow(self._section_label("Medical & Admin"))

        self.blood_combo = QComboBox(); self.blood_combo.setObjectName("formCombo")
        self.blood_combo.addItems(["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])
        self.blood_combo.setMinimumHeight(38)

        self.discount_combo = QComboBox(); self.discount_combo.setObjectName("formCombo")
        self.discount_combo.setMinimumHeight(38)
        self.discount_combo.addItem("— None —", None)
        self._discount_types = self._backend.get_discount_types(active_only=True) if self._backend else []
        for dt in self._discount_types:
            self.discount_combo.addItem(
                f"{dt['type_name']} ({float(dt['discount_percent']):.0f}%)",
                dt['discount_id'])

        self.status_combo = QComboBox(); self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Active", "Inactive"])
        self.status_combo.setMinimumHeight(38)

        right.addRow("Blood Type", self.blood_combo)
        right.addRow("Discount", self.discount_combo)
        right.addRow("Status", self.status_combo)

        # ── Conditions section (below right form) ─────────────────
        cond_lbl = self._section_label("Conditions")
        self._cond_section.addWidget(cond_lbl)

        self._cond_search = QLineEdit()
        self._cond_search.setPlaceholderText("Search conditions\u2026")
        self._cond_search.setStyleSheet(
            "QLineEdit { padding: 8px 12px; border: 2px solid #BADFE7;"
            " border-radius: 8px; font-size: 12px; background: #FFFFFF; }"
            "QLineEdit:focus { border-color: #388087; }")
        self._cond_search.setMinimumHeight(34)
        self._cond_search.textChanged.connect(self._filter_conditions)
        self._cond_section.addWidget(self._cond_search)

        self._cond_checkboxes = []
        self._cond_frame = QFrame()
        self._cond_frame.setStyleSheet(
            "QFrame { border: 1.5px solid #BADFE7; border-radius: 12px;"
            " background: #FAFCFD; }")
        self._cond_grid = QGridLayout(self._cond_frame)
        self._cond_grid.setContentsMargins(14, 12, 14, 12)
        self._cond_grid.setHorizontalSpacing(8)
        self._cond_grid.setVerticalSpacing(8)
        self._load_standard_conditions(data, self._cond_grid)
        self._cond_section.addWidget(self._cond_frame, 1)

        self.cond_custom = self._input("Other conditions (comma-separated)")
        self.cond_custom.setMaxLength(300)
        self._cond_section.addWidget(self.cond_custom)

    def _build_buttons(self, parent_lay):
        from PyQt6.QtWidgets import QPushButton
        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
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
        idx = self.sex_combo.findText(data.get("sex", "Male"))
        if idx >= 0: self.sex_combo.setCurrentIndex(idx)
        raw_phone = data.get("phone", "")
        if raw_phone.startswith("+63"):
            raw_phone = raw_phone[3:]
        self.phone_edit.setText(raw_phone)
        self.email_edit.setText(data.get("email", ""))
        self.address_edit.setText(data.get("address", ""))
        cidx = self.civil_combo.findText(data.get("civil_status", "Single"))
        if cidx >= 0: self.civil_combo.setCurrentIndex(cidx)
        self.emergency_edit.setText(data.get("emergency_contact", ""))
        bidx = self.blood_combo.findText(data.get("blood_type", "Unknown"))
        if bidx >= 0: self.blood_combo.setCurrentIndex(bidx)
        dt_id = data.get("discount_type_id")
        if dt_id:
            for i in range(self.discount_combo.count()):
                if self.discount_combo.itemData(i) == dt_id:
                    self.discount_combo.setCurrentIndex(i)
                    break
        sidx = self.status_combo.findText(data.get("status", "Active"))
        if sidx >= 0: self.status_combo.setCurrentIndex(sidx)
        self.notes_edit.setPlainText(data.get("notes", ""))

    def _load_standard_conditions(self, data, grid):
        existing = set()
        if data and data.get("conditions"):
            existing = {c.strip() for c in data["conditions"].split(",") if c.strip()}
        std = self._backend.get_standard_conditions() if self._backend else []
        std_names = {c["condition_name"] for c in std}
        cols = 3
        for i, c in enumerate(std):
            cb = QCheckBox(c["condition_name"])
            cb.setStyleSheet(self._CB_STYLE)
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            cb.setChecked(c["condition_name"] in existing)
            grid.addWidget(cb, i // cols, i % cols)
            self._cond_checkboxes.append(cb)
        leftover = existing - std_names
        if leftover and hasattr(self, 'cond_custom'):
            self.cond_custom.setText(", ".join(sorted(leftover)))

    def _filter_conditions(self, text: str):
        needle = text.lower().strip()
        for cb in self._cond_checkboxes:
            cb.setVisible(needle in cb.text().lower() if needle else True)

    def get_data(self) -> dict:
        checked = [cb.text() for cb in self._cond_checkboxes if cb.isChecked()]
        custom = [c.strip() for c in self.cond_custom.text().split(",") if c.strip()]
        all_conds = ", ".join(checked + custom)
        return {
            "name": self.name_edit.text(),
            "sex": self.sex_combo.currentText(),
            "phone": "+63" + self.phone_edit.text().strip(),
            "email": self.email_edit.text(),
            "address": self.address_edit.text(),
            "civil_status": self.civil_combo.currentText(),
            "emergency_contact": self.emergency_edit.text(),
            "blood_type": self.blood_combo.currentText(),
            "discount_type_id": self.discount_combo.currentData(),
            "conditions": all_conds,
            "status": self.status_combo.currentText(),
            "notes": self.notes_edit.toPlainText(),
        }

    @staticmethod
    def _input(placeholder: str) -> QLineEdit:
        le = QLineEdit(); le.setPlaceholderText(placeholder)
        le.setStyleSheet(
            "QLineEdit { padding: 8px 14px 10px 14px; border: 2px solid #BADFE7;"
            " border-radius: 10px; font-size: 13px; background-color: #FFFFFF;"
            " color: #2C3E50; }"
            "QLineEdit:focus { border: 2px solid #388087; }")
        le.setMinimumHeight(42)
        return le

    def eventFilter(self, obj, event):
        if obj is self.phone_edit:
            if event.type() == QEvent.Type.FocusIn:
                self._phone_frame.setStyleSheet(self._phone_focus_ss)
            elif event.type() == QEvent.Type.FocusOut:
                self._phone_frame.setStyleSheet(self._phone_normal_ss)
        return super().eventFilter(obj, event)

    def accept(self):
        err = validate_name(self.name_edit.text(), "Full Name")
        if err:
            QMessageBox.warning(self, "Validation", err); return
        err = validate_phone_digits(self.phone_edit.text())
        if err:
            QMessageBox.warning(self, "Validation", err); return
        err = validate_email(self.email_edit.text())
        if err:
            QMessageBox.warning(self, "Validation", err); return
        super().accept()


# ── Patient Full Profile Dialog ───────────────────────────────────────
class PatientProfileDialog(QDialog):
    """Read-only full profile with tabs: Info, Appointments, Invoices, Queue."""

    def __init__(self, parent=None, profile: dict = None, role: str = "Admin"):
        super().__init__(parent)
        self.setWindowTitle("Patient Profile")
        self.setMinimumSize(720, 520)
        p = profile or {}
        info = p.get("info", {})
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)

        # Header
        name = f"{info.get('first_name','')} {info.get('last_name','')}"
        hdr = QLabel(f"<b style='font-size:18px'>{name}</b>  "
                     f"<span style='color:#7F8C8D'>{info.get('status','')}</span>")
        hdr.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(hdr)

        tabs = QTabWidget()
        tabs.addTab(self._info_tab(info), "Info")
        tabs.addTab(self._table_tab(p.get("appointments", []),
                    ["Date", "Time", "Doctor", "Service", "Status", "Notes"],
                    lambda a: [str(a.get("appointment_date","")), str(a.get("appointment_time","")),
                               a.get("doctor_name",""), a.get("service_name",""),
                               a.get("status",""), a.get("notes","") or ""]), "Appointments")
        # Invoices tab — hidden for Doctor role
        if role != "Doctor":
            tabs.addTab(self._table_tab(p.get("invoices", []),
                        ["Invoice #", "Services", "Total", "Paid", "Status", "Payment", "Date"],
                        lambda i: [str(i.get("invoice_id","")), i.get("services","") or "",
                                   f"\u20b1{float(i.get('total_amount',0)):,.2f}",
                                   f"\u20b1{float(i.get('amount_paid',0)):,.2f}",
                                   i.get("status",""), i.get("payment_method",""),
                                   str(i.get("created_at",""))]), "Invoices")
        tabs.addTab(self._table_tab(p.get("queue", []),
                    ["Queue #", "Time", "Doctor", "Purpose", "Status", "Date"],
                    lambda q: [str(q.get("queue_id","")), str(q.get("queue_time","")),
                               q.get("doctor_name",""), q.get("purpose","") or "",
                               q.get("status",""), str(q.get("created_at",""))]), "Queue History")
        lay.addWidget(tabs)

        from PyQt6.QtWidgets import QPushButton
        close_btn = QPushButton("Close")
        close_btn.setObjectName("dialogSaveBtn")
        close_btn.setMinimumHeight(38)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _info_tab(self, info: dict) -> QWidget:
        w = QWidget(); form = QFormLayout(w)
        form.setSpacing(8); form.setContentsMargins(16, 16, 16, 16)
        fields = [
            ("Patient ID", f"PT-{info.get('patient_id', 0):04d}"),
            ("Sex", info.get("sex", "")),
            ("Date of Birth", str(info.get("date_of_birth", ""))),
            ("Phone", info.get("phone", "") or "—"),
            ("Email", info.get("email", "") or "—"),
            ("Address", info.get("address", "") or "—"),
            ("Civil Status", info.get("civil_status", "") or "—"),
            ("Emergency Contact", info.get("emergency_contact", "") or "—"),
            ("Blood Type", info.get("blood_type", "") or "Unknown"),
            ("Conditions", info.get("conditions", "") or "None"),
            ("Notes", info.get("notes", "") or "—"),
        ]
        for label, val in fields:
            form.addRow(f"<b>{label}:</b>", QLabel(str(val)))
        return w

    def _table_tab(self, rows: list, headers: list, mapper) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        t = QTableWidget(len(rows), len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setDefaultSectionSize(48)
        configure_table(t)
        for r, row_data in enumerate(rows):
            vals = mapper(row_data)
            for c, v in enumerate(vals):
                t.setItem(r, c, QTableWidgetItem(str(v) if v else ""))
        lay.addWidget(t); return w


# ── Merge Patients Dialog ─────────────────────────────────────────────
class MergeDialog(QDialog):
    def __init__(self, parent=None, patients=None):
        super().__init__(parent)
        self.setWindowTitle("Merge Duplicate Patients")
        self.setMinimumWidth(400)
        form = QFormLayout(self); form.setSpacing(14); form.setContentsMargins(28,28,28,28)
        self._patients = patients or []
        names = [f"PT-{p['patient_id']:04d}  {p['first_name']} {p['last_name']}" for p in self._patients]

        self.keep_combo = QComboBox(); self.keep_combo.addItems(names)
        self.remove_combo = QComboBox(); self.remove_combo.addItems(names)
        if len(names) > 1: self.remove_combo.setCurrentIndex(1)

        form.addRow("Keep (primary):", self.keep_combo)
        form.addRow("Remove (merge into primary):", self.remove_combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        style_dialog_btns(btns)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        form.addRow(btns)

    def get_ids(self) -> tuple:
        ki = self.keep_combo.currentIndex()
        ri = self.remove_combo.currentIndex()
        return (self._patients[ki]["patient_id"], self._patients[ri]["patient_id"]) if ki != ri else (None, None)
