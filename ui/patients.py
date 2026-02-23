"""Patient Record Management page."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QFormLayout, QComboBox, QTextEdit, QDialog, QDialogButtonBox,
    QGraphicsDropShadowEffect, QMessageBox, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QColor
from ui.styles import configure_table, make_table_btn


# ── Sample data ────────────────────────────────────────────────────────
_PATIENTS = [
    ("PT-1001", "Maria Santos",    "Female", "32", "09171234567", "maria@email.com",    "Hypertension",   "Active"),
    ("PT-1002", "Juan Dela Cruz",  "Male",   "45", "09179876543", "juan@email.com",     "Diabetes",       "Active"),
    ("PT-1003", "Ana Reyes",       "Female", "28", "09171112233", "ana@email.com",      "Asthma",         "Active"),
    ("PT-1004", "Carlos Garcia",   "Male",   "60", "09174445566", "carlos@email.com",   "Heart Disease",  "Inactive"),
    ("PT-1005", "Lea Mendoza",     "Female", "37", "09177778899", "lea@email.com",      "None",           "Active"),
    ("PT-1006", "Roberto Cruz",    "Male",   "52", "09173334455", "roberto@email.com",  "Hypertension",   "Active"),
    ("PT-1007", "Isabel Tan",      "Female", "41", "09176667788", "isabel@email.com",   "Allergies",      "Active"),
    ("PT-1008", "Miguel Lim",      "Male",   "55", "09172223344", "miguel@email.com",   "Arthritis",      "Inactive"),
]


class PatientDialog(QDialog):
    """Add / Edit patient dialog."""

    def __init__(self, parent=None, *, title="Add New Patient", data=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        self.setStyleSheet("""
            QDialog { background: #FFFFFF; }
            QLabel { color: #2C3E50; font-size: 13px; }
        """)

        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.name_edit   = self._input("Full name")
        self.sex_combo   = QComboBox(); self.sex_combo.setObjectName("formCombo")
        self.sex_combo.addItems(["Male", "Female"])
        self.dob_edit    = QDateEdit(); self.dob_edit.setCalendarPopup(True)
        self.dob_edit.setDate(QDate.currentDate())
        self.dob_edit.setObjectName("formCombo")
        self.phone_edit  = self._input("Phone number")
        self.email_edit  = self._input("Email")
        self.cond_edit   = self._input("Medical conditions")
        self.status_combo = QComboBox(); self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Active", "Inactive"])
        self.notes_edit  = QTextEdit(); self.notes_edit.setObjectName("formInput")
        self.notes_edit.setMaximumHeight(90)

        form.addRow("Full Name",     self.name_edit)
        form.addRow("Sex",           self.sex_combo)
        form.addRow("Date of Birth", self.dob_edit)
        form.addRow("Phone",         self.phone_edit)
        form.addRow("Email",         self.email_edit)
        form.addRow("Conditions",    self.cond_edit)
        form.addRow("Status",        self.status_combo)
        form.addRow("Notes",         self.notes_edit)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

        if data:
            self.name_edit.setText(data.get("name", ""))
            idx = self.sex_combo.findText(data.get("sex", "Male"))
            if idx >= 0:
                self.sex_combo.setCurrentIndex(idx)
            self.phone_edit.setText(data.get("phone", ""))
            self.email_edit.setText(data.get("email", ""))
            self.cond_edit.setText(data.get("conditions", ""))
            sidx = self.status_combo.findText(data.get("status", "Active"))
            if sidx >= 0:
                self.status_combo.setCurrentIndex(sidx)

    def get_data(self) -> dict:
        """Return the current form values as a dict."""
        return {
            "name":       self.name_edit.text(),
            "sex":        self.sex_combo.currentText(),
            "phone":      self.phone_edit.text(),
            "email":      self.email_edit.text(),
            "conditions": self.cond_edit.text(),
            "status":     self.status_combo.currentText(),
        }

    @staticmethod
    def _input(placeholder: str) -> QLineEdit:
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        le.setObjectName("formInput")
        le.setMinimumHeight(38)
        return le


class PatientsPage(QWidget):
    patients_changed = pyqtSignal(list)   # emits list of patient names

    def __init__(self, role: str = "Admin"):
        super().__init__()
        self._role = role
        self._build()

    def get_patient_names(self) -> list[str]:
        """Return current patient names from the table."""
        names = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 1)
            if item and item.text().strip():
                names.append(item.text().strip())
        return names

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #F6F6F2; }")
        inner = QWidget()
        inner.setObjectName("pageInner")
        inner.setStyleSheet("QWidget#pageInner { background-color: #F6F6F2; }")
        lay = QVBoxLayout(inner)
        lay.setSpacing(20)
        lay.setContentsMargins(28, 28, 28, 28)

        # ── Header Banner ──────────────────────────────────────────
        banner = QFrame()
        banner.setObjectName("pageBanner")
        banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)
        banner.setStyleSheet(
            "QFrame#pageBanner { background: qlineargradient("
            "x1:0, y1:0, x2:1, y2:0,"
            "stop:0 #388087, stop:1 #6FB3B8);"
            "border-radius: 12px; }"
        )
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(32, 20, 32, 20)
        banner_lay.setSpacing(0)
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("Patient Records")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background: transparent;")
        sub = QLabel("Manage and view all patient information")
        sub.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.8); background: transparent;")
        title_col.addWidget(title)
        title_col.addWidget(sub)
        banner_lay.addLayout(title_col)
        banner_lay.addStretch()

        if self._role != "Nurse":
            add_btn = QPushButton("\uff0b  Add Patient")
            add_btn.setObjectName("secondaryBtn")
            add_btn.setMinimumHeight(42)
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.clicked.connect(self._on_add)
            add_btn.setStyleSheet(
                "QPushButton { background: rgba(255,255,255,0.2); color: #FFFFFF;"
                "border: 1px solid rgba(255,255,255,0.4); border-radius: 8px;"
                "padding: 8px 18px; font-size: 13px; font-weight: bold; }"
                "QPushButton:hover { background: rgba(255,255,255,0.35); }"
            )
            banner_lay.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(banner)

        # ── Search / filter bar ────────────────────────────────────────
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setObjectName("searchBar")
        self.search.setPlaceholderText("🔍  Search patients by name, ID, or condition…")
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(self._on_search)
        bar.addWidget(self.search)

        self.filter_combo = QComboBox()
        self.filter_combo.setObjectName("formCombo")
        self.filter_combo.addItems(["All Status", "Active", "Inactive"])
        self.filter_combo.setMinimumHeight(42)
        self.filter_combo.setMinimumWidth(140)
        self.filter_combo.currentTextChanged.connect(self._on_filter)
        bar.addWidget(self.filter_combo)
        lay.addLayout(bar)

        # ── Table ──────────────────────────────────────────────────────
        cols = ["ID", "Name", "Sex", "Age", "Phone", "Email", "Conditions", "Status"]
        if self._role != "Nurse":
            cols.append("Actions")
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        if self._role != "Nurse":
            self.table.horizontalHeader().setSectionResizeMode(len(cols) - 1, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(len(cols) - 1, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(420)
        self.table.verticalHeader().setDefaultSectionSize(48)
        configure_table(self.table)
        self._populate(_PATIENTS)
        lay.addWidget(self.table)

        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

    # ── Populate / filter ──────────────────────────────────────────────
    def _populate(self, rows):
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                self.table.setItem(r, c, item)
            if self._role != "Nurse":
                view_btn = make_table_btn("Edit")
                view_btn.clicked.connect(lambda checked, ri=r: self._on_edit(ri))
                self.table.setCellWidget(r, len(row), view_btn)

    def _on_search(self, text: str):
        text = text.lower()
        for r in range(self.table.rowCount()):
            match = any(
                text in (self.table.item(r, c).text().lower() if self.table.item(r, c) else "")
                for c in range(self.table.columnCount() - 1)
            )
            self.table.setRowHidden(r, not match)

    def _on_filter(self, status: str):
        status_col = 7
        for r in range(self.table.rowCount()):
            item = self.table.item(r, status_col)
            if status == "All Status" or (item and item.text() == status):
                self.table.setRowHidden(r, False)
            else:
                self.table.setRowHidden(r, True)

    # ── CRUD stubs ─────────────────────────────────────────────────────
    def _on_add(self):
        dlg = PatientDialog(self, title="Add New Patient")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Patient name is required.")
                return
            row = self.table.rowCount()
            self.table.insertRow(row)
            new_id = f"PT-{1001 + row}"
            values = [new_id, d["name"], d["sex"], "", d["phone"], d["email"], d["conditions"], d["status"]]
            for c, val in enumerate(values):
                self.table.setItem(row, c, QTableWidgetItem(val))
            if self._role != "Nurse":
                edit_btn = make_table_btn("Edit")
                edit_btn.clicked.connect(lambda checked, ri=row: self._on_edit(ri))
                self.table.setCellWidget(row, len(values), edit_btn)
            QMessageBox.information(self, "Success", f"Patient '{d['name']}' added successfully.")
            self.patients_changed.emit(self.get_patient_names())

    def _on_edit(self, row: int):
        data = {
            "name":       self.table.item(row, 1).text() if self.table.item(row, 1) else "",
            "sex":        self.table.item(row, 2).text() if self.table.item(row, 2) else "",
            "phone":      self.table.item(row, 4).text() if self.table.item(row, 4) else "",
            "email":      self.table.item(row, 5).text() if self.table.item(row, 5) else "",
            "conditions": self.table.item(row, 6).text() if self.table.item(row, 6) else "",
            "status":     self.table.item(row, 7).text() if self.table.item(row, 7) else "",
        }
        dlg = PatientDialog(self, title="Edit Patient", data=data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Patient name is required.")
                return
            orig_id = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
            orig_age = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
            values = [orig_id, d["name"], d["sex"], orig_age, d["phone"], d["email"], d["conditions"], d["status"]]
            for c, val in enumerate(values):
                self.table.setItem(row, c, QTableWidgetItem(val))
            QMessageBox.information(self, "Success", f"Patient '{d['name']}' updated successfully.")
            self.patients_changed.emit(self.get_patient_names())

    def _on_delete(self, row: int):
        name = self.table.item(row, 1).text() if self.table.item(row, 1) else "this patient"
        QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
