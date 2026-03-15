# Patient dialogs - add/edit, profile view, merge

from datetime import date

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QTabWidget,
    QDateEdit, QCheckBox, QMessageBox, QFrame, QPushButton,
    QGridLayout, QDialogButtonBox, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, QDate, QEvent
from ui.styles import configure_table, style_dialog_btns
from ui.validators import (
    NameValidator, PhoneDigitsValidator,
    validate_name, validate_email, validate_phone_digits,
)


# ══════════════════════════════════════════════════════════════════════
#  Patient Add/Edit Dialog — V3 (reorganised, with confirm step)
# ══════════════════════════════════════════════════════════════════════
class PatientDialog(QDialog):
    """Add / Edit patient dialog with emergency contact, blood type,
    condition picker, and a review-before-save confirmation."""

    _INPUT_STYLE = (
        "QLineEdit, QTextEdit { padding: 8px 14px 10px 14px;"
        " border: 2px solid #BADFE7; border-radius: 10px;"
        " font-size: 13px; background-color: #FFFFFF; color: #2C3E50; }"
        "QLineEdit:focus, QTextEdit:focus { border: 2px solid #388087; }"
    )

    _CB_STYLE = (
        "QCheckBox { font-size: 12px; color: #2C3E50; spacing: 6px;"
        " padding: 5px 4px; border: none; background: transparent; }"
        "QCheckBox:checked { color: #388087; font-weight: bold; }"
        "QCheckBox:hover { color: #388087; }"
        "QCheckBox::indicator { width: 16px; height: 16px;"
        " border: 2px solid #BADFE7; border-radius: 4px;"
        " background: #FFFFFF; }"
        "QCheckBox::indicator:checked { background: #388087;"
        " border-color: #388087; image: none; }"
        "QCheckBox::indicator:hover { border-color: #388087; }"
    )

    def __init__(self, parent=None, *, title="Add New Patient",
                 data=None, backend=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self._backend = backend

        # Screen-adaptive sizing
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen else None
        max_h = int(avail.height() * 0.9) if avail else 900
        max_w = int(avail.width() * 0.65) if avail else 960
        self.resize(min(960, max_w), min(860, max_h))
        self.setMinimumSize(820, 540)

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
            os.path.dirname(__file__), "..", "styles", "icon-patient.svg")
        try:
            from PyQt6.QtSvgWidgets import QSvgWidget
            icon_w = QSvgWidget(os.path.normpath(_icon_path))
            icon_w.setFixedSize(32, 32)
            icon_w.setStyleSheet("background: transparent;")
        except ImportError:
            icon_w = QLabel("\U0001F3E5")
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
        h_sub = QLabel("Fill in the patient details below")
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
            self._section_label("\u2460 Personal Information"))
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
            self._section_label("\u2461 Medical & Admin"))
        self._right_form = QFormLayout()
        self._right_form.setSpacing(12)
        self._right_form.setContentsMargins(0, 0, 0, 0)
        self._right_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._right_form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self._right_vbox.addLayout(self._right_form)

        # Conditions section (below right form)
        self._cond_section = QVBoxLayout()
        self._cond_section.setSpacing(6)
        self._right_vbox.addLayout(self._cond_section, 1)
        columns.addLayout(self._right_vbox, 1)

        content_lay.addLayout(columns)

        # Full-width bottom area (Notes)
        self._bottom_vbox = QVBoxLayout()
        self._bottom_vbox.setContentsMargins(0, 8, 0, 0)
        self._bottom_vbox.setSpacing(6)
        content_lay.addLayout(self._bottom_vbox)

        content_lay.addStretch()
        scroll.setWidget(scroll_inner)
        main_lay.addWidget(scroll, 1)

        self._build_fields(data)
        self._build_buttons(main_lay)
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

    @staticmethod
    def _input(placeholder: str) -> QLineEdit:
        le = QLineEdit(); le.setPlaceholderText(placeholder)
        le.setStyleSheet(
            "QLineEdit { padding: 8px 14px 10px 14px;"
            " border: 2px solid #BADFE7; border-radius: 10px;"
            " font-size: 13px; background-color: #FFFFFF;"
            " color: #2C3E50; }"
            "QLineEdit:focus { border: 2px solid #388087; }")
        le.setMinimumHeight(40)
        return le

    # ── Build all form fields ──────────────────────────────────────
    def _build_fields(self, data):
        left = self._left_form
        right = self._right_form

        # ── Left: Personal Information ────────────────────────────
        self.name_edit = self._input("Full name")
        self.name_edit.setValidator(NameValidator())
        self.name_edit.setMaxLength(100)

        self.sex_combo = QComboBox()
        self.sex_combo.setObjectName("formCombo")
        self.sex_combo.addItems(["Male", "Female"])
        self.sex_combo.setMinimumHeight(40)

        self.dob_edit = QDateEdit()
        self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDate(QDate.currentDate())
        self.dob_edit.setObjectName("formCombo")
        self.dob_edit.setMaximumDate(QDate.currentDate())
        self.dob_edit.setDisplayFormat("M/d/yyyy")
        self.dob_edit.setMinimumHeight(40)
        self.dob_edit.setToolTip("Patient's date of birth")

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
            " border-top-left-radius: 8px;"
            " border-bottom-left-radius: 8px; color: #2C3E50; }")
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

        self.email_edit = self._input("Email")
        self.email_edit.setMaxLength(150)
        self.email_edit.setToolTip("Patient email address")

        self.address_edit = self._input("Full address")
        self.address_edit.setMaxLength(300)
        self.address_edit.setToolTip("Home or mailing address")

        self.civil_combo = QComboBox()
        self.civil_combo.setObjectName("formCombo")
        self.civil_combo.addItems(
            ["Single", "Married", "Widowed", "Separated"])
        self.civil_combo.setMinimumHeight(40)

        self.emergency_edit = self._input("Name / phone")
        self.emergency_edit.setMaxLength(150)
        self.emergency_edit.setToolTip(
            "Name and phone of emergency contact")

        left.addRow(self._required_label("Full Name"), self.name_edit)
        left.addRow("Sex",               self.sex_combo)
        left.addRow("Date of Birth",     self.dob_edit)
        left.addRow(self._required_label("Phone"), self._phone_frame)
        left.addRow("Email",             self.email_edit)
        left.addRow("Address",           self.address_edit)
        left.addRow("Civil Status",      self.civil_combo)
        left.addRow("Emergency Contact", self.emergency_edit)

        self._left_vbox.addStretch(1)

        # ── Right: Medical & Admin ────────────────────────────────
        self.blood_combo = QComboBox()
        self.blood_combo.setObjectName("formCombo")
        self.blood_combo.addItems(
            ["Unknown", "A+", "A-", "B+", "B-",
             "AB+", "AB-", "O+", "O-"])
        self.blood_combo.setMinimumHeight(40)

        self.discount_combo = QComboBox()
        self.discount_combo.setObjectName("formCombo")
        self.discount_combo.setMinimumHeight(40)
        self.discount_combo.addItem("\u2014 None \u2014", None)
        self._discount_types = (
            self._backend.get_discount_types(active_only=True)
            if self._backend else [])
        for dt in self._discount_types:
            self.discount_combo.addItem(
                f"{dt['type_name']}"
                f" ({float(dt['discount_percent']):.0f}%)",
                dt["discount_id"])

        self.status_combo = QComboBox()
        self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Active", "Inactive"])
        self.status_combo.setMinimumHeight(40)

        right.addRow("Blood Type", self.blood_combo)
        right.addRow("Discount",   self.discount_combo)
        right.addRow("Status",     self.status_combo)

        # ── Conditions picker ─────────────────────────────────────
        cond_lbl = QLabel("Conditions")
        cond_lbl.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #388087;"
            " padding-top: 6px;")
        self._cond_section.addWidget(cond_lbl)

        self._cond_search = QLineEdit()
        self._cond_search.setPlaceholderText("Search conditions\u2026")
        self._cond_search.setStyleSheet(
            "QLineEdit { padding: 8px 12px; border: 2px solid #BADFE7;"
            " border-radius: 8px; font-size: 12px;"
            " background: #FFFFFF; }"
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

        self.cond_custom = self._input(
            "Other conditions (comma-separated)")
        self.cond_custom.setMaxLength(300)
        self._cond_section.addWidget(self.cond_custom)

        # ── Bottom: Notes ─────────────────────────────────────────
        bsep = QFrame()
        bsep.setFixedHeight(1)
        bsep.setStyleSheet("background: #E8F0F1;")
        self._bottom_vbox.addWidget(bsep)
        self._bottom_vbox.addWidget(
            self._section_label("\u2462 Additional Information"))

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
            "Internal notes about this patient...")
        self.notes_edit.setToolTip(
            "Optional notes \u2014 not visible to the patient")
        notes_row.addWidget(notes_lbl)
        notes_row.addWidget(self.notes_edit, 1)
        self._bottom_vbox.addLayout(notes_row)

    # ── Button bar ─────────────────────────────────────────────────
    def _build_buttons(self, parent_lay):
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
        idx = self.sex_combo.findText(data.get("sex", "Male"))
        if idx >= 0: self.sex_combo.setCurrentIndex(idx)
        raw_phone = data.get("phone", "")
        if raw_phone.startswith("+63"):
            raw_phone = raw_phone[3:]
        self.phone_edit.setText(raw_phone)
        self.email_edit.setText(data.get("email", ""))
        self.address_edit.setText(data.get("address", ""))
        cidx = self.civil_combo.findText(
            data.get("civil_status", "Single"))
        if cidx >= 0: self.civil_combo.setCurrentIndex(cidx)
        self.emergency_edit.setText(
            data.get("emergency_contact", ""))
        bidx = self.blood_combo.findText(
            data.get("blood_type", "Unknown"))
        if bidx >= 0: self.blood_combo.setCurrentIndex(bidx)
        dt_id = data.get("discount_type_id")
        if dt_id:
            for i in range(self.discount_combo.count()):
                if self.discount_combo.itemData(i) == dt_id:
                    self.discount_combo.setCurrentIndex(i); break
        sidx = self.status_combo.findText(
            data.get("status", "Active"))
        if sidx >= 0: self.status_combo.setCurrentIndex(sidx)
        self.notes_edit.setPlainText(data.get("notes", ""))

    # ── Conditions helpers ─────────────────────────────────────────
    def _load_standard_conditions(self, data, grid):
        existing = set()
        if data and data.get("conditions"):
            existing = {c.strip()
                        for c in data["conditions"].split(",")
                        if c.strip()}
        std = (self._backend.get_standard_conditions()
               if self._backend else [])
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
        if leftover and hasattr(self, "cond_custom"):
            self.cond_custom.setText(", ".join(sorted(leftover)))

    def _filter_conditions(self, text: str):
        needle = text.lower().strip()
        for cb in self._cond_checkboxes:
            cb.setVisible(
                needle in cb.text().lower() if needle else True)

    # ── Event filter for phone focus ───────────────────────────────
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
        err = validate_phone_digits(self.phone_edit.text())
        if err:
            QMessageBox.warning(self, "Validation", err); return
        err = validate_email(self.email_edit.text())
        if err:
            QMessageBox.warning(self, "Validation", err); return

        if not self._show_review():
            return
        super().accept()

    def _show_review(self) -> bool:
        """Show a formatted summary dialog. Returns True if confirmed."""
        d = self.get_data()
        conds = d.get("conditions", "")
        cond_str = conds if conds else "\u2014"
        disc_str = self.discount_combo.currentText()

        ROW = ("<tr>"
               "<td style='padding:4px 12px 4px 0; color:#7F8C8D;"
               " white-space:nowrap;'>{}</td>"
               "<td style='padding:4px 0;'><b>{}</b></td></tr>")
        SEP = ("<tr><td colspan='2'><hr style='border:none;"
               " border-top:1px solid #E8F0F1;'></td></tr>")

        rows = [
            ROW.format("Name",       d["name"]),
            ROW.format("Sex",        d["sex"]),
            ROW.format("Phone",      d["phone"]),
            ROW.format("Email",      d.get("email") or "\u2014"),
            ROW.format("Address",    d.get("address") or "\u2014"),
            ROW.format("Civil",      d.get("civil_status") or "\u2014"),
            ROW.format("Emergency",
                        d.get("emergency_contact") or "\u2014"),
            SEP,
            ROW.format("Blood Type", d.get("blood_type", "Unknown")),
            ROW.format("Discount",   disc_str),
            ROW.format("Conditions", cond_str),
            ROW.format("Status",     d["status"]),
        ]
        if d.get("notes", "").strip():
            note_preview = (d["notes"][:80]
                            + ("\u2026" if len(d["notes"]) > 80 else ""))
            rows.append(ROW.format("Notes", note_preview))

        html = ("<div style='font-size:13px; color:#2C3E50;'>"
                "<table cellpadding='0' cellspacing='0'>"
                + "".join(rows)
                + "</table></div>")

        dlg = QMessageBox(self)
        dlg.setWindowTitle("Review Patient Details")
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
        checked = [cb.text() for cb in self._cond_checkboxes
                   if cb.isChecked()]
        custom = [c.strip()
                  for c in self.cond_custom.text().split(",")
                  if c.strip()]
        all_conds = ", ".join(checked + custom)
        return {
            "name":              self.name_edit.text(),
            "sex":               self.sex_combo.currentText(),
            "phone":             "+63" + self.phone_edit.text().strip(),
            "email":             self.email_edit.text(),
            "address":           self.address_edit.text(),
            "civil_status":      self.civil_combo.currentText(),
            "emergency_contact": self.emergency_edit.text(),
            "blood_type":        self.blood_combo.currentText(),
            "discount_type_id":  self.discount_combo.currentData(),
            "conditions":        all_conds,
            "status":            self.status_combo.currentText(),
            "notes":             self.notes_edit.toPlainText(),
        }


# ══════════════════════════════════════════════════════════════════════
#  Patient Full Profile Dialog
# ══════════════════════════════════════════════════════════════════════
class PatientProfileDialog(QDialog):
    """Read-only full profile with tabs: Info, Appointments,
    Invoices, Queue."""

    def __init__(self, parent=None, profile: dict = None,
                 role: str = "Admin"):
        super().__init__(parent)
        self.setWindowTitle("Patient Profile")
        self.setMinimumSize(720, 520)
        p = profile or {}
        info = p.get("info", {})
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)

        # Header
        name = (f"{info.get('first_name', '')}"
                f" {info.get('last_name', '')}")
        hdr = QLabel(
            f"<b style='font-size:18px'>{name}</b>  "
            f"<span style='color:#7F8C8D'>"
            f"{info.get('status', '')}</span>")
        hdr.setTextFormat(Qt.TextFormat.RichText)
        lay.addWidget(hdr)

        tabs = QTabWidget()
        tabs.addTab(self._info_tab(info), "Info")
        tabs.addTab(self._table_tab(
            p.get("appointments", []),
            ["Date", "Time", "Doctor", "Service", "Status", "Notes"],
            lambda a: [
                str(a.get("appointment_date", "")),
                str(a.get("appointment_time", "")),
                a.get("doctor_name", ""),
                a.get("service_name", ""),
                a.get("status", ""),
                a.get("notes", "") or "",
            ]), "Appointments")
        if role != "Doctor":
            tabs.addTab(self._table_tab(
                p.get("invoices", []),
                ["Invoice #", "Services", "Total", "Paid",
                 "Status", "Payment", "Date"],
                lambda i: [
                    str(i.get("invoice_id", "")),
                    i.get("services", "") or "",
                    f"\u20b1{float(i.get('total_amount', 0)):,.2f}",
                    f"\u20b1{float(i.get('amount_paid', 0)):,.2f}",
                    i.get("status", ""),
                    i.get("payment_method", ""),
                    str(i.get("created_at", "")),
                ]), "Invoices")
        tabs.addTab(self._table_tab(
            p.get("queue", []),
            ["Queue #", "Time", "Doctor", "Purpose", "Status", "Date"],
            lambda q: [
                str(q.get("queue_id", "")),
                str(q.get("queue_time", "")),
                q.get("doctor_name", ""),
                q.get("purpose", "") or "",
                q.get("status", ""),
                str(q.get("created_at", "")),
            ]), "Queue History")
        lay.addWidget(tabs)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("dialogSaveBtn")
        close_btn.setMinimumHeight(38)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn,
                      alignment=Qt.AlignmentFlag.AlignRight)

    def _info_tab(self, info: dict) -> QWidget:
        w = QWidget(); form = QFormLayout(w)
        form.setSpacing(8)
        form.setContentsMargins(16, 16, 16, 16)
        fields = [
            ("Patient ID",
             f"PT-{info.get('patient_id', 0):04d}"),
            ("Sex",              info.get("sex", "")),
            ("Date of Birth",
             str(info.get("date_of_birth", ""))),
            ("Phone",            info.get("phone", "") or "\u2014"),
            ("Email",            info.get("email", "") or "\u2014"),
            ("Address",          info.get("address", "") or "\u2014"),
            ("Civil Status",
             info.get("civil_status", "") or "\u2014"),
            ("Emergency Contact",
             info.get("emergency_contact", "") or "\u2014"),
            ("Blood Type",
             info.get("blood_type", "") or "Unknown"),
            ("Conditions",
             info.get("conditions", "") or "None"),
            ("Notes",            info.get("notes", "") or "\u2014"),
        ]
        for label, val in fields:
            form.addRow(f"<b>{label}:</b>", QLabel(str(val)))
        return w

    def _table_tab(self, rows: list, headers: list,
                   mapper) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w)
        t = QTableWidget(len(rows), len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        t.setSelectionMode(
            QTableWidget.SelectionMode.NoSelection)
        t.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setDefaultSectionSize(48)
        configure_table(t)
        for r, row_data in enumerate(rows):
            vals = mapper(row_data)
            for c, v in enumerate(vals):
                t.setItem(r, c,
                          QTableWidgetItem(str(v) if v else ""))
        lay.addWidget(t); return w


# ══════════════════════════════════════════════════════════════════════
#  Merge Patients Dialog
# ══════════════════════════════════════════════════════════════════════
class MergeDialog(QDialog):
    def __init__(self, parent=None, patients=None):
        super().__init__(parent)
        self.setWindowTitle("Merge Duplicate Patients")
        self.setMinimumWidth(400)
        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)
        self._patients = patients or []
        names = [
            f"PT-{p['patient_id']:04d}  "
            f"{p['first_name']} {p['last_name']}"
            for p in self._patients
        ]
        self.keep_combo = QComboBox()
        self.keep_combo.addItems(names)
        self.remove_combo = QComboBox()
        self.remove_combo.addItems(names)
        if len(names) > 1:
            self.remove_combo.setCurrentIndex(1)

        form.addRow("Keep (primary):", self.keep_combo)
        form.addRow("Remove (merge into primary):",
                    self.remove_combo)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        style_dialog_btns(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def get_ids(self) -> tuple:
        ki = self.keep_combo.currentIndex()
        ri = self.remove_combo.currentIndex()
        return (
            (self._patients[ki]["patient_id"],
             self._patients[ri]["patient_id"])
            if ki != ri else (None, None)
        )
