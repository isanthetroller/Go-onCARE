"""Appointment Scheduling page – single-table view with quick-filter tabs."""

from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QComboBox, QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QTimeEdit, QDateEdit, QTextEdit, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QColor, QFont
from ui.styles import configure_table, make_table_btn


# ── In-memory appointment store ───────────────────────────────────────
_APPOINTMENTS: list[tuple] = [
    # (date_str, time_str, patient, doctor, purpose, status)
    ("2026-02-23", "09:00 AM", "Maria Santos",     "Dr. Reyes", "General Checkup",    "Confirmed"),
    ("2026-02-23", "09:30 AM", "Juan Dela Cruz",   "Dr. Tan",   "Follow-up Visit",    "Confirmed"),
    ("2026-02-23", "10:00 AM", "Ana Reyes",        "Dr. Reyes", "Lab Results Review",  "Pending"),
    ("2026-02-23", "10:30 AM", "Carlos Garcia",    "Dr. Lim",   "Dental Cleaning",    "Confirmed"),
    ("2026-02-23", "11:00 AM", "Lea Mendoza",      "Dr. Tan",   "Consultation",       "Pending"),
    ("2026-02-24", "08:30 AM", "Roberto Cruz",     "Dr. Reyes", "Blood Work",         "Confirmed"),
    ("2026-02-24", "09:00 AM", "Isabel Tan",       "Dr. Lim",   "X-Ray Review",       "Pending"),
    ("2026-02-24", "10:00 AM", "Sofia Reyes",      "Dr. Tan",   "Consultation",       "Confirmed"),
    ("2026-02-25", "10:00 AM", "Miguel Lim",       "Dr. Tan",   "Physical Exam",      "Confirmed"),
    ("2026-02-18", "09:00 AM", "Rosa Mendoza",     "Dr. Reyes", "General Checkup",    "Completed"),
    ("2026-02-15", "02:00 PM", "Pedro Villanueva", "Dr. Lim",   "Dental Cleaning",    "Completed"),
    ("2026-01-28", "10:00 AM", "Luis Garcia",      "Dr. Tan",   "Follow-up Visit",    "Completed"),
    ("2026-01-22", "09:30 AM", "Maria Santos",     "Dr. Reyes", "Lab Results Review",  "Completed"),
    ("2026-01-15", "11:00 AM", "Ana Reyes",        "Dr. Lim",   "X-Ray Review",       "Completed"),
    ("2026-01-10", "08:30 AM", "Carlos Garcia",    "Dr. Reyes", "Blood Work",         "Completed"),
    ("2025-12-18", "09:00 AM", "Juan Dela Cruz",   "Dr. Tan",   "Physical Exam",      "Completed"),
    ("2025-12-10", "10:30 AM", "Lea Mendoza",      "Dr. Reyes", "General Checkup",    "Completed"),
    ("2025-12-05", "02:00 PM", "Roberto Cruz",     "Dr. Lim",   "Dental Cleaning",    "Completed"),
    ("2025-11-20", "09:30 AM", "Isabel Tan",       "Dr. Tan",   "Consultation",       "Completed"),
    ("2025-11-12", "10:00 AM", "Miguel Lim",       "Dr. Reyes", "Follow-up Visit",    "Completed"),
]

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _pretty_date(iso: str) -> str:
    """Convert '2026-02-23' → 'Monday, February 23, 2026'."""
    try:
        d = datetime.strptime(iso, "%Y-%m-%d")
        return f"{_DAY_NAMES[d.weekday()]},  {_MONTH_NAMES[d.month]} {d.day}, {d.year}"
    except Exception:
        return iso


def _relative_label(iso: str) -> str:
    """Return 'Today', 'Tomorrow', or '' for a date string."""
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


# ══════════════════════════════════════════════════════════════════════
#  Appointment Dialog  (shared by create & edit)
# ══════════════════════════════════════════════════════════════════════
class AppointmentDialog(QDialog):
    """Create / Edit appointment dialog."""

    def __init__(self, parent=None, *, title="New Appointment", data=None,
                 patient_names: list[str] | None = None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setStyleSheet(
            "QDialog { background: #FFFFFF; }"
            "QLabel  { color: #2C3E50; font-size: 13px; }"
        )

        form = QFormLayout(self)
        form.setSpacing(16)
        form.setContentsMargins(32, 32, 32, 32)

        # Patient
        self.patient_combo = QComboBox()
        self.patient_combo.setObjectName("formCombo")
        self.patient_combo.setMinimumHeight(40)
        if patient_names:
            self.patient_combo.addItems(patient_names)
        else:
            self.patient_combo.setEditable(True)
            self.patient_combo.lineEdit().setPlaceholderText("Select or type patient name")

        # Doctor
        self.doctor_combo = QComboBox()
        self.doctor_combo.setObjectName("formCombo")
        self.doctor_combo.addItems(["Dr. Reyes", "Dr. Tan", "Dr. Lim", "Dr. Santos"])
        self.doctor_combo.setMinimumHeight(40)

        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setObjectName("formCombo")
        self.date_edit.setDisplayFormat("dddd, MMMM d, yyyy")
        self.date_edit.setMinimumHeight(40)

        # Time
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(9, 0))
        self.time_edit.setObjectName("formCombo")
        self.time_edit.setDisplayFormat("hh:mm AP")
        self.time_edit.setMinimumHeight(40)

        # Purpose
        self.purpose_combo = QComboBox()
        self.purpose_combo.setObjectName("formCombo")
        self.purpose_combo.addItems([
            "General Checkup", "Follow-up Visit", "Lab Results Review",
            "Consultation", "Dental Cleaning", "Physical Exam",
            "X-Ray Review", "Blood Work",
        ])
        self.purpose_combo.setMinimumHeight(40)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Pending", "Confirmed", "Cancelled", "Completed"])
        self.status_combo.setMinimumHeight(40)

        # Notes
        self.notes_edit = QTextEdit()
        self.notes_edit.setObjectName("formInput")
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Optional notes…")

        form.addRow("Patient",  self.patient_combo)
        form.addRow("Doctor",   self.doctor_combo)
        form.addRow("Date",     self.date_edit)
        form.addRow("Time",     self.time_edit)
        form.addRow("Purpose",  self.purpose_combo)
        form.addRow("Status",   self.status_combo)
        form.addRow("Notes",    self.notes_edit)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

        # Pre-fill when editing
        if data:
            p_idx = self.patient_combo.findText(data.get("patient", ""))
            if p_idx >= 0:
                self.patient_combo.setCurrentIndex(p_idx)
            elif self.patient_combo.isEditable():
                self.patient_combo.setEditText(data.get("patient", ""))
            idx = self.doctor_combo.findText(data.get("doctor", ""))
            if idx >= 0:
                self.doctor_combo.setCurrentIndex(idx)
            if data.get("date"):
                self.date_edit.setDate(QDate.fromString(data["date"], "yyyy-MM-dd"))
            if data.get("time"):
                self.time_edit.setTime(QTime.fromString(data["time"], "hh:mm AP"))
            idx = self.purpose_combo.findText(data.get("purpose", ""))
            if idx >= 0:
                self.purpose_combo.setCurrentIndex(idx)
            idx = self.status_combo.findText(data.get("status", ""))
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)

    def get_data(self) -> dict:
        return {
            "patient": self.patient_combo.currentText(),
            "doctor":  self.doctor_combo.currentText(),
            "date":    self.date_edit.date().toString("yyyy-MM-dd"),
            "time":    self.time_edit.time().toString("hh:mm AP"),
            "purpose": self.purpose_combo.currentText(),
            "status":  self.status_combo.currentText(),
        }


# ══════════════════════════════════════════════════════════════════════
#  Appointments Page  (single table + quick-filter tabs)
# ══════════════════════════════════════════════════════════════════════
class AppointmentsPage(QWidget):
    _TAB_STYLE = (
        "QPushButton {{ background: {bg}; color: {fg}; border: none;"
        " border-radius: 8px; padding: 8px 20px;"
        " font-size: 13px; font-weight: bold; }}"
        " QPushButton:hover {{ background: {hv}; }}"
    )
    _TAB_ACTIVE   = _TAB_STYLE.format(bg="#388087", fg="#FFFFFF", hv="#2C6A70")
    _TAB_INACTIVE = _TAB_STYLE.format(bg="#FFFFFF", fg="#2C3E50", hv="#BADFE7")

    def __init__(self, role: str = "Admin"):
        super().__init__()
        self._role = role
        self._patient_names: list[str] = []
        self._active_tab = "Today"
        self._tab_buttons: dict[str, QPushButton] = {}
        self._build()

    def set_patient_names(self, names: list[str]):
        self._patient_names = names

    # ── Build ──────────────────────────────────────────────────────────
    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #F6F6F2; }")
        inner = QWidget()
        inner.setObjectName("pageInner")
        inner.setStyleSheet("QWidget#pageInner { background-color: #F6F6F2; }")
        lay = QVBoxLayout(inner)
        lay.setSpacing(16)
        lay.setContentsMargins(28, 28, 28, 28)

        # ── Banner ─────────────────────────────────────────────────
        banner = QFrame()
        banner.setObjectName("pageBanner")
        banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)
        banner.setStyleSheet(
            "QFrame#pageBanner { background: qlineargradient("
            "x1:0,y1:0,x2:1,y2:0, stop:0 #388087, stop:1 #6FB3B8);"
            "border-radius: 12px; }"
        )
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(32, 20, 32, 20)
        tc = QVBoxLayout(); tc.setSpacing(4)
        title = QLabel("Appointment Scheduling")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background: transparent;")
        sub = QLabel("View and manage all doctor-patient appointments")
        sub.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.8); background: transparent;")
        tc.addWidget(title); tc.addWidget(sub)
        banner_lay.addLayout(tc)
        banner_lay.addStretch()

        if self._role != "Nurse":
            add_btn = QPushButton("\uff0b  New Appointment")
            add_btn.setMinimumHeight(42)
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.clicked.connect(self._on_new)
            add_btn.setStyleSheet(
                "QPushButton { background: rgba(255,255,255,0.2); color: #FFF;"
                "border: 1px solid rgba(255,255,255,0.4); border-radius: 8px;"
                "padding: 8px 18px; font-size: 13px; font-weight: bold; }"
                "QPushButton:hover { background: rgba(255,255,255,0.35); }"
            )
            banner_lay.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(banner)

        # ── Quick-filter tabs ──────────────────────────────────────
        tab_row = QHBoxLayout()
        tab_row.setSpacing(8)
        for label in ("Today", "Tomorrow", "This Week", "This Month", "All"):
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(38)
            btn.clicked.connect(lambda checked, l=label: self._switch_tab(l))
            self._tab_buttons[label] = btn
            tab_row.addWidget(btn)
        tab_row.addStretch()
        lay.addLayout(tab_row)

        # ── Summary badge ──────────────────────────────────────────
        self._summary_label = QLabel()
        self._summary_label.setStyleSheet(
            "font-size: 13px; color: #7F8C8D; padding: 2px 0;"
        )
        lay.addWidget(self._summary_label)

        # ── Filter bar ─────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.search = QLineEdit()
        self.search.setObjectName("searchBar")
        self.search.setPlaceholderText("\U0001F50D  Search by patient, doctor, or purpose…")
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(self._apply_filters)
        bar.addWidget(self.search)

        self.doc_filter = QComboBox()
        self.doc_filter.setObjectName("formCombo")
        self.doc_filter.addItems(["All Doctors", "Dr. Reyes", "Dr. Tan", "Dr. Lim", "Dr. Santos"])
        self.doc_filter.setMinimumHeight(42); self.doc_filter.setMinimumWidth(150)
        self.doc_filter.currentTextChanged.connect(self._apply_filters)
        bar.addWidget(self.doc_filter)

        self.status_filter = QComboBox()
        self.status_filter.setObjectName("formCombo")
        self.status_filter.addItems(["All Status", "Pending", "Confirmed", "Cancelled", "Completed"])
        self.status_filter.setMinimumHeight(42); self.status_filter.setMinimumWidth(140)
        self.status_filter.currentTextChanged.connect(self._apply_filters)
        bar.addWidget(self.status_filter)
        lay.addLayout(bar)

        # ── Main table ─────────────────────────────────────────────
        cols = ["Day & Date", "Time", "Patient", "Doctor", "Purpose", "Status"]
        if self._role != "Nurse":
            cols.append("Actions")
        self.table = QTableWidget(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # Give "Day & Date" a wider stretch
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 260)
        if self._role != "Nurse":
            hdr.setSectionResizeMode(len(cols) - 1, QHeaderView.ResizeMode.Fixed)
            self.table.setColumnWidth(len(cols) - 1, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(52)
        self.table.setMinimumHeight(460)
        configure_table(self.table)
        lay.addWidget(self.table)

        lay.addStretch()
        scroll.setWidget(inner)

        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

        # Initial render
        self._switch_tab("Today")

    # ── Tab switching ──────────────────────────────────────────────
    def _switch_tab(self, label: str):
        self._active_tab = label
        for name, btn in self._tab_buttons.items():
            btn.setStyleSheet(self._TAB_ACTIVE if name == label else self._TAB_INACTIVE)
        self._refresh_table()

    # ── Data helpers ───────────────────────────────────────────────
    def _rows_for_tab(self) -> list[tuple]:
        """Return the subset of _APPOINTMENTS matching the active tab."""
        today = date.today()
        tab = self._active_tab

        if tab == "Today":
            key = today.strftime("%Y-%m-%d")
            return [a for a in _APPOINTMENTS if a[0] == key]

        if tab == "Tomorrow":
            key = (today + timedelta(days=1)).strftime("%Y-%m-%d")
            return [a for a in _APPOINTMENTS if a[0] == key]

        if tab == "This Week":
            start = today - timedelta(days=today.weekday())  # Monday
            end = start + timedelta(days=6)                  # Sunday
            return [
                a for a in _APPOINTMENTS
                if start <= datetime.strptime(a[0], "%Y-%m-%d").date() <= end
            ]

        if tab == "This Month":
            ym = today.strftime("%Y-%m")
            return [a for a in _APPOINTMENTS if a[0][:7] == ym]

        # "All"
        return list(_APPOINTMENTS)

    def _refresh_table(self):
        rows = self._rows_for_tab()
        # Sort chronologically (newest first for "All", oldest first otherwise)
        rows.sort(key=lambda a: (a[0], a[1]),
                  reverse=(self._active_tab == "All"))

        self.table.setRowCount(len(rows))
        col_count = self.table.columnCount()

        for r, appt in enumerate(rows):
            # appt: (date_str, time_str, patient, doctor, purpose, status)
            pretty = _pretty_date(appt[0])
            rel = _relative_label(appt[0])
            date_display = f"{pretty}   ({rel})" if rel else pretty

            values = [date_display, appt[1], appt[2], appt[3], appt[4], appt[5]]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                if c == 0:
                    item.setFont(QFont("Segoe UI", 11))
                # Status colouring
                if c == 5:
                    if val == "Confirmed":
                        item.setForeground(QColor("#5CB85C"))
                    elif val == "Pending":
                        item.setForeground(QColor("#E8B931"))
                    elif val == "Cancelled":
                        item.setForeground(QColor("#D9534F"))
                    elif val == "Completed":
                        item.setForeground(QColor("#388087"))
                    item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                item.setData(Qt.ItemDataRole.UserRole, appt)   # stash raw tuple
                self.table.setItem(r, c, item)

            if self._role != "Nurse":
                edit_btn = make_table_btn("Edit")
                edit_btn.clicked.connect(
                    lambda checked, a=appt: self._on_edit(a)
                )
                self.table.setCellWidget(r, col_count - 1, edit_btn)

        visible = sum(1 for r in range(self.table.rowCount())
                      if not self.table.isRowHidden(r))
        self._summary_label.setText(
            f"Showing {len(rows)} appointment{'s' if len(rows) != 1 else ''}"
        )
        self._apply_filters()

    # ── Filters ────────────────────────────────────────────────────
    def _apply_filters(self, _=None):
        search = self.search.text().lower()
        doc    = self.doc_filter.currentText()
        status = self.status_filter.currentText()
        visible = 0

        for r in range(self.table.rowCount()):
            row_text = " ".join(
                self.table.item(r, c).text().lower() if self.table.item(r, c) else ""
                for c in range(self.table.columnCount() - 1)
            )
            doc_cell    = self.table.item(r, 3)
            status_cell = self.table.item(r, 5)

            ok_search = not search or search in row_text
            ok_doc    = doc == "All Doctors" or (doc_cell and doc_cell.text() == doc)
            ok_status = status == "All Status" or (status_cell and status_cell.text() == status)
            show = ok_search and ok_doc and ok_status
            self.table.setRowHidden(r, not show)
            if show:
                visible += 1

        total = self.table.rowCount()
        if visible == total:
            self._summary_label.setText(
                f"Showing {total} appointment{'s' if total != 1 else ''}"
            )
        else:
            self._summary_label.setText(
                f"Showing {visible} of {total} appointment{'s' if total != 1 else ''}"
            )

    # ── CRUD ───────────────────────────────────────────────────────
    def _on_new(self):
        dlg = AppointmentDialog(self, title="New Appointment",
                                patient_names=self._patient_names)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["patient"].strip():
                QMessageBox.warning(self, "Validation", "Patient name is required.")
                return
            _APPOINTMENTS.append(
                (d["date"], d["time"], d["patient"], d["doctor"], d["purpose"], d["status"])
            )
            self._refresh_table()
            QMessageBox.information(
                self, "Success",
                f"Appointment for '{d['patient']}' on "
                f"{_pretty_date(d['date'])} at {d['time']} created."
            )

    def _on_edit(self, appt: tuple):
        data = {
            "date": appt[0], "time": appt[1], "patient": appt[2],
            "doctor": appt[3], "purpose": appt[4], "status": appt[5],
        }
        dlg = AppointmentDialog(self, title="Edit Appointment", data=data,
                                patient_names=self._patient_names)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["patient"].strip():
                QMessageBox.warning(self, "Validation", "Patient name is required.")
                return
            try:
                idx = _APPOINTMENTS.index(appt)
                _APPOINTMENTS[idx] = (
                    d["date"], d["time"], d["patient"],
                    d["doctor"], d["purpose"], d["status"],
                )
            except ValueError:
                pass
            self._refresh_table()
            QMessageBox.information(
                self, "Success",
                f"Appointment for '{d['patient']}' updated."
            )
