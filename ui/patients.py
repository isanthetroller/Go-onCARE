"""Patient Record Management page – V2 with full profile, merge, conditions picker."""

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QFormLayout, QComboBox, QTextEdit, QDialog, QDialogButtonBox,
    QGraphicsDropShadowEffect, QMessageBox, QDateEdit, QTabWidget,
    QCompleter, QListWidget, QListWidgetItem, QCheckBox,
)
from PyQt6.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from ui.styles import configure_table, make_table_btn, make_table_btn_danger, style_dialog_btns


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
        self.dob_edit.setMaximumDate(QDate.currentDate())  # Birthday cannot be in the future
        self.dob_edit.setDisplayFormat("MMMM d, yyyy")
        self.phone_edit = self._input("+639XXXXXXXXX")
        self.phone_edit.setMaxLength(13)
        self.email_edit = self._input("Email")
        self.emergency_edit = self._input("Emergency contact (name / phone)")
        self.blood_combo = QComboBox(); self.blood_combo.setObjectName("formCombo")
        self.blood_combo.addItems(["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"])

        # Condition picker – list of checkboxes from standard_conditions + free text
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
        # leftover custom conditions not in standard list
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


# ══════════════════════════════════════════════════════════════════════
#  Patients Page
# ══════════════════════════════════════════════════════════════════════
class PatientsPage(QWidget):
    patients_changed = pyqtSignal(list)

    def __init__(self, backend=None, role: str = "Admin", user_email: str = ""):
        super().__init__()
        self._backend = backend
        self._role = role
        self._user_email = user_email
        self._patient_ids: list[int] = []
        self._all_patients: list[dict] = []
        self._build()
        # Auto-refresh data every 10 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_from_db)
        self._refresh_timer.start(10_000)

    def get_patient_names(self) -> list[str]:
        names = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 1)
            if item and item.text().strip():
                names.append(item.text().strip())
        return names

    def _build(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget(); inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner); lay.setSpacing(20); lay.setContentsMargins(28,28,28,28)

        # ── Banner ─────────────────────────────────────────────────
        banner = QFrame(); banner.setObjectName("pageBanner"); banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0,4); shadow.setColor(QColor(0,0,0,15))
        banner.setGraphicsEffect(shadow)
        banner_lay = QHBoxLayout(banner); banner_lay.setContentsMargins(32,20,32,20); banner_lay.setSpacing(0)
        title_col = QVBoxLayout(); title_col.setSpacing(4)
        title = QLabel("Patient Records"); title.setObjectName("bannerTitle")
        sub = QLabel("Manage and view all patient information"); sub.setObjectName("bannerSubtitle")
        title_col.addWidget(title); title_col.addWidget(sub)
        banner_lay.addLayout(title_col); banner_lay.addStretch()

        if self._role != "Cashier":
            add_btn = QPushButton("\uff0b  Add Patient"); add_btn.setObjectName("bannerBtn")
            add_btn.setMinimumHeight(42); add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.clicked.connect(self._on_add)
            banner_lay.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(banner)

        # ── Toolbar ────────────────────────────────────────────────
        bar = QHBoxLayout(); bar.setSpacing(10)
        self.search = QLineEdit(); self.search.setObjectName("searchBar")
        self.search.setPlaceholderText("🔍  Search patients by name, ID, or condition…")
        self.search.setMinimumHeight(42); self.search.textChanged.connect(self._apply_filters)
        bar.addWidget(self.search)

        self.filter_combo = QComboBox(); self.filter_combo.setObjectName("formCombo")
        self.filter_combo.addItems(["All Status", "Active", "Inactive"])
        self.filter_combo.setMinimumHeight(42); self.filter_combo.setMinimumWidth(140)
        self.filter_combo.currentTextChanged.connect(self._apply_filters)
        bar.addWidget(self.filter_combo)

        self.sex_filter = QComboBox(); self.sex_filter.setObjectName("formCombo")
        self.sex_filter.addItems(["All Sex", "Male", "Female"])
        self.sex_filter.setMinimumHeight(42); self.sex_filter.setMinimumWidth(120)
        self.sex_filter.currentTextChanged.connect(self._apply_filters)
        bar.addWidget(self.sex_filter)

        self.blood_filter = QComboBox(); self.blood_filter.setObjectName("formCombo")
        self.blood_filter.addItems(["All Blood Type", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"])
        self.blood_filter.setMinimumHeight(42); self.blood_filter.setMinimumWidth(140)
        self.blood_filter.currentTextChanged.connect(self._apply_filters)
        bar.addWidget(self.blood_filter)

        self.cond_filter = QComboBox(); self.cond_filter.setObjectName("formCombo")
        self.cond_filter.addItems(["All Conditions"])
        self.cond_filter.setMinimumHeight(42); self.cond_filter.setMinimumWidth(160)
        self.cond_filter.currentTextChanged.connect(self._apply_filters)
        bar.addWidget(self.cond_filter)
        lay.addLayout(bar)

        # ── Table ──────────────────────────────────────────────────
        cols = ["ID", "Name", "Sex", "Age", "Phone", "Blood Type",
                "Conditions", "Last Visit", "Status", "Actions"]
        if self._role == "Cashier":
            cols = cols[:-1]  # no actions
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        if self._role != "Cashier":
            self.table.horizontalHeader().setSectionResizeMode(len(cols)-1, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(len(cols)-1, 185)
            self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(420)
        self.table.verticalHeader().setDefaultSectionSize(48)
        configure_table(self.table)
        self.table.setSortingEnabled(True)
        self._load_from_db()
        lay.addWidget(self.table)

        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self); wrapper.setContentsMargins(0,0,0,0)
        wrapper.addWidget(scroll)

    # ── DB Load ────────────────────────────────────────────────────
    def _load_from_db(self):
        self.table.setSortingEnabled(False)
        if self._backend and self._role == "Doctor" and self._user_email:
            rows = self._backend.get_patients_for_doctor(self._user_email)
        else:
            rows = self._backend.get_patients() if self._backend else []
        self._all_patients = rows
        self._patient_ids.clear()
        self.table.setRowCount(len(rows))

        # Collect unique conditions for filter
        all_conds = set()
        for p in rows:
            conds = p.get("conditions", "") or ""
            for c in conds.split(","):
                c = c.strip()
                if c:
                    all_conds.add(c)

        prev_cond = self.cond_filter.currentText()
        self.cond_filter.blockSignals(True)
        self.cond_filter.clear()
        self.cond_filter.addItem("All Conditions")
        for c in sorted(all_conds):
            self.cond_filter.addItem(c)
        idx = self.cond_filter.findText(prev_cond)
        if idx >= 0:
            self.cond_filter.setCurrentIndex(idx)
        self.cond_filter.blockSignals(False)
        for r, p in enumerate(rows):
            self._patient_ids.append(p["patient_id"])
            pid_str = f"PT-{p['patient_id']:04d}"
            name = f"{p['first_name']} {p['last_name']}"
            dob = p.get("date_of_birth")
            age = ""
            if dob:
                if isinstance(dob, date):
                    today = date.today()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                else:
                    age = ""
            last_visit = p.get("last_visit", "")
            if last_visit and hasattr(last_visit, "strftime"):
                last_visit = last_visit.strftime("%Y-%m-%d")
            values = [pid_str, name, p.get("sex",""), str(age),
                      p.get("phone","") or "", p.get("blood_type","") or "Unknown",
                      p.get("conditions","") or "",
                      str(last_visit) if last_visit else "—",
                      p.get("status","")]
            for c, val in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(val))

            if self._role != "Cashier":
                act_w = QWidget(); act_lay = QHBoxLayout(act_w)
                act_lay.setContentsMargins(0,0,0,0); act_lay.setSpacing(6)
                view_btn = make_table_btn("View"); view_btn.setFixedWidth(52)
                view_btn.clicked.connect(lambda checked, ri=r: self._on_view(ri))
                edit_btn = make_table_btn("Edit"); edit_btn.setFixedWidth(52)
                edit_btn.clicked.connect(lambda checked, ri=r: self._on_edit(ri))
                del_btn = make_table_btn_danger("Del"); del_btn.setFixedWidth(46)
                del_btn.clicked.connect(lambda checked, ri=r: self._on_delete(ri))
                act_lay.addWidget(view_btn); act_lay.addWidget(edit_btn); act_lay.addWidget(del_btn)
                self.table.setCellWidget(r, len(values), act_w)
        self.table.setSortingEnabled(True)

    # ── Filters ────────────────────────────────────────────────────
    def _apply_filters(self, _=None):
        text = self.search.text().lower()
        status = self.filter_combo.currentText()
        sex = self.sex_filter.currentText()
        blood = self.blood_filter.currentText()
        cond = self.cond_filter.currentText()
        sex_col = 2
        blood_col = 5
        cond_col = 6
        status_col = 8
        for r in range(self.table.rowCount()):
            row_text = " ".join(
                self.table.item(r,c).text().lower() if self.table.item(r,c) else ""
                for c in range(self.table.columnCount()-1))
            ok_text = not text or text in row_text
            item_status = self.table.item(r, status_col)
            ok_status = status == "All Status" or (item_status and item_status.text() == status)
            item_sex = self.table.item(r, sex_col)
            ok_sex = sex == "All Sex" or (item_sex and item_sex.text() == sex)
            item_blood = self.table.item(r, blood_col)
            ok_blood = blood == "All Blood Type" or (item_blood and item_blood.text() == blood)
            item_cond = self.table.item(r, cond_col)
            ok_cond = cond == "All Conditions" or (item_cond and cond.lower() in item_cond.text().lower())
            self.table.setRowHidden(r, not (ok_text and ok_status and ok_sex and ok_blood and ok_cond))

    # ── CRUD ───────────────────────────────────────────────────────
    def _on_add(self):
        dlg = PatientDialog(self, title="Add New Patient", backend=self._backend)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Patient name is required."); return
            parts = d["name"].strip().rsplit(" ", 1)
            db_data = {
                "first_name": parts[0], "last_name": parts[1] if len(parts)>1 else "",
                "sex": d["sex"], "dob": dlg.dob_edit.date().toString("yyyy-MM-dd"),
                "phone": d["phone"], "email": d["email"],
                "emergency_contact": d["emergency_contact"],
                "blood_type": d["blood_type"],
                "conditions": d["conditions"], "status": d["status"],
                "notes": d["notes"],
            }
            if self._backend and self._backend.add_patient(db_data):
                QMessageBox.information(self, "Success", f"Patient '{d['name']}' added.")
                self._load_from_db(); self.patients_changed.emit(self.get_patient_names())
            else:
                QMessageBox.critical(self, "Error", "Failed to add patient.")

    def _on_edit(self, row: int):
        p = self._all_patients[row] if row < len(self._all_patients) else {}
        data = {
            "name": f"{p.get('first_name','')} {p.get('last_name','')}",
            "sex": p.get("sex",""), "phone": p.get("phone","") or "",
            "email": p.get("email","") or "",
            "emergency_contact": p.get("emergency_contact","") or "",
            "blood_type": p.get("blood_type","") or "Unknown",
            "conditions": p.get("conditions","") or "",
            "status": p.get("status",""),
            "notes": p.get("notes","") or "",
        }
        dlg = PatientDialog(self, title="Edit Patient", data=data, backend=self._backend)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Patient name is required."); return
            parts = d["name"].strip().rsplit(" ", 1)
            patient_id = self._patient_ids[row] if row < len(self._patient_ids) else None
            db_data = {
                "first_name": parts[0], "last_name": parts[1] if len(parts)>1 else "",
                "sex": d["sex"], "dob": dlg.dob_edit.date().toString("yyyy-MM-dd"),
                "phone": d["phone"], "email": d["email"],
                "emergency_contact": d["emergency_contact"],
                "blood_type": d["blood_type"],
                "conditions": d["conditions"], "status": d["status"],
                "notes": d["notes"],
            }
            if patient_id and self._backend and self._backend.update_patient(patient_id, db_data):
                QMessageBox.information(self, "Success", f"Patient '{d['name']}' updated.")
                self._load_from_db(); self.patients_changed.emit(self.get_patient_names())
            else:
                QMessageBox.critical(self, "Error", "Failed to update patient.")

    def _on_delete(self, row: int):
        name = self.table.item(row,1).text() if self.table.item(row,1) else "patient"
        reply = QMessageBox.question(self, "Confirm Delete",
            f"Delete {name}? All linked appointments, invoices, and conditions will be removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            pid = self._patient_ids[row] if row < len(self._patient_ids) else None
            if pid and self._backend and self._backend.delete_patient(pid):
                QMessageBox.information(self, "Deleted", f"Patient '{name}' deleted.")
                self._load_from_db(); self.patients_changed.emit(self.get_patient_names())
            else:
                QMessageBox.critical(self, "Error", "Failed to delete patient.")

    def _on_view(self, row: int):
        pid = self._patient_ids[row] if row < len(self._patient_ids) else None
        if not pid or not self._backend: return
        profile = self._backend.get_patient_full_profile(pid)
        if not profile:
            QMessageBox.warning(self, "Error", "Could not load patient profile."); return
        dlg = PatientProfileDialog(self, profile=profile)
        dlg.exec()

    def _on_merge(self):
        patients = self._backend.get_patients() if self._backend else []
        if len(patients) < 2:
            QMessageBox.information(self, "Merge", "Need at least 2 patients to merge."); return
        dlg = MergeDialog(self, patients=patients)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            keep_id, remove_id = dlg.get_ids()
            if keep_id is None:
                QMessageBox.warning(self, "Merge", "Cannot merge a patient with itself."); return
            reply = QMessageBox.question(self, "Confirm Merge",
                f"Merge PT-{remove_id:04d} into PT-{keep_id:04d}?\nThis cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self._backend.merge_patients(keep_id, remove_id):
                    QMessageBox.information(self, "Merged", "Patients merged successfully.")
                    self._load_from_db(); self.patients_changed.emit(self.get_patient_names())
                else:
                    QMessageBox.critical(self, "Error", "Merge failed.")
