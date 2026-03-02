# Patient dialogs - add/edit, profile view, merge

from datetime import date

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QTabWidget,
    QDateEdit, QListWidget, QListWidgetItem, QCheckBox, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from ui.styles import configure_table, style_dialog_btns


# ── Patient Add/Edit Dialog ───────────────────────────────────────────
class PatientDialog(QDialog):
    """Add / Edit patient dialog with emergency contact, blood type, condition picker."""

    def __init__(self, parent=None, *, title="Add New Patient", data=None, backend=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self._backend = backend

        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.name_edit = self._input("Full name")
        self.sex_combo = QComboBox(); self.sex_combo.setObjectName("formCombo")
        self.sex_combo.addItems(["Male", "Female"])
        self.dob_edit = QDateEdit(); self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDate(QDate.currentDate()); self.dob_edit.setObjectName("formCombo")
        self.dob_edit.setMaximumDate(QDate.currentDate())
        self.dob_edit.setDisplayFormat("MMMM d, yyyy")
        self.phone_edit = self._input("+639XXXXXXXXX")
        self.phone_edit.setMaxLength(13)
        self.email_edit = self._input("Email")
        self.emergency_edit = self._input("Emergency contact (name / phone)")
        self.blood_combo = QComboBox(); self.blood_combo.setObjectName("formCombo")
        self.blood_combo.addItems(["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])

        # Discount category
        self.discount_combo = QComboBox(); self.discount_combo.setObjectName("formCombo")
        self.discount_combo.setMinimumHeight(38)
        self.discount_combo.addItem("— None —", None)
        self._discount_types = self._backend.get_discount_types(active_only=True) if self._backend else []
        for dt in self._discount_types:
            self.discount_combo.addItem(
                f"{dt['type_name']} ({float(dt['discount_percent']):.0f}%)",
                dt['discount_id'])

        # Condition picker
        self.cond_list = QListWidget()
        self.cond_list.setMaximumHeight(120)
        self._load_standard_conditions(data)
        self.cond_custom = self._input("Other conditions (comma-separated)")

        self.status_combo = QComboBox(); self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Active", "Inactive"])
        self.notes_edit = QTextEdit(); self.notes_edit.setObjectName("formInput")
        self.notes_edit.setMaximumHeight(80)

        form.addRow("Full Name", self.name_edit)
        form.addRow("Sex", self.sex_combo)
        form.addRow("Date of Birth", self.dob_edit)
        form.addRow("Phone", self.phone_edit)
        form.addRow("Email", self.email_edit)
        form.addRow("Emergency Contact", self.emergency_edit)
        form.addRow("Blood Type", self.blood_combo)
        form.addRow("Discount Category", self.discount_combo)
        form.addRow("Conditions", self.cond_list)
        form.addRow("Other Conditions", self.cond_custom)
        form.addRow("Status", self.status_combo)
        form.addRow("Notes", self.notes_edit)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        style_dialog_btns(btns)
        btns.accepted.connect(self.accept); btns.rejected.connect(self.reject)
        form.addRow(btns)

        if data:
            self.name_edit.setText(data.get("name", ""))
            idx = self.sex_combo.findText(data.get("sex", "Male"))
            if idx >= 0: self.sex_combo.setCurrentIndex(idx)
            self.phone_edit.setText(data.get("phone", ""))
            self.email_edit.setText(data.get("email", ""))
            self.emergency_edit.setText(data.get("emergency_contact", ""))
            bidx = self.blood_combo.findText(data.get("blood_type", "Unknown"))
            if bidx >= 0: self.blood_combo.setCurrentIndex(bidx)
            # Restore discount type
            dt_id = data.get("discount_type_id")
            if dt_id:
                for i in range(self.discount_combo.count()):
                    if self.discount_combo.itemData(i) == dt_id:
                        self.discount_combo.setCurrentIndex(i)
                        break
            sidx = self.status_combo.findText(data.get("status", "Active"))
            if sidx >= 0: self.status_combo.setCurrentIndex(sidx)
            self.notes_edit.setPlainText(data.get("notes", ""))

    def _load_standard_conditions(self, data):
        existing = set()
        if data and data.get("conditions"):
            existing = {c.strip() for c in data["conditions"].split(",") if c.strip()}
        std = self._backend.get_standard_conditions() if self._backend else []
        std_names = {c["condition_name"] for c in std}
        for c in std:
            item = QListWidgetItem(c["condition_name"])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if c["condition_name"] in existing else Qt.CheckState.Unchecked)
            self.cond_list.addItem(item)
        leftover = existing - std_names
        if leftover and hasattr(self, 'cond_custom'):
            self.cond_custom.setText(", ".join(sorted(leftover)))

    def get_data(self) -> dict:
        checked = []
        for i in range(self.cond_list.count()):
            item = self.cond_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked.append(item.text())
        custom = [c.strip() for c in self.cond_custom.text().split(",") if c.strip()]
        all_conds = ", ".join(checked + custom)
        return {
            "name": self.name_edit.text(),
            "sex": self.sex_combo.currentText(),
            "phone": self.phone_edit.text(),
            "email": self.email_edit.text(),
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
        le.setObjectName("formInput"); le.setMinimumHeight(38); le.setMinimumWidth(320)
        return le

    def accept(self):
        import re
        phone = self.phone_edit.text().strip()
        if phone and not re.match(r'^\+63\d{10}$', phone):
            QMessageBox.warning(self, "Validation",
                                "Phone must be in Philippine format: +63 followed by 10 digits\n"
                                "Example: +639171234567")
            return
        super().accept()


# ── Patient Full Profile Dialog ───────────────────────────────────────
class PatientProfileDialog(QDialog):
    """Read-only full profile with tabs: Info, Appointments, Invoices, Queue."""

    def __init__(self, parent=None, profile: dict = None):
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
        tabs.addTab(self._table_tab(p.get("invoices", []),
                    ["Invoice #", "Services", "Total", "Paid", "Status", "Payment", "Date"],
                    lambda i: [str(i.get("invoice_id","")), i.get("services","") or "",
                               f"₱{float(i.get('total_amount',0)):,.2f}",
                               f"₱{float(i.get('amount_paid',0)):,.2f}",
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
        close_btn.setObjectName("bannerBtn")
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
