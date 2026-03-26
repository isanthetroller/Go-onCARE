# Clinical page - Queue, Billing/POS, Services tabs

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QComboBox, QStackedWidget, QDialog, QFormLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QColor
from ui.styles import (
    configure_table, make_page_layout, finish_page, make_banner, make_read_only_table,
    make_table_btn, make_table_btn_danger, make_action_table,
    format_timedelta, status_color, TAB_ACTIVE, TAB_INACTIVE, make_action_cell,
)
from ui.icons import get_icon
from ui.shared.clinical_dialogs import (
    QueueEditDialog, ServiceEditDialog, NewInvoiceDialog,
    PaymentDialog, BulkPriceDialog,
)


# ══════════════════════════════════════════════════════════════════════
#  Clinical Page
# ══════════════════════════════════════════════════════════════════════
class ClinicalPage(QWidget):

    def __init__(self, backend=None, role: str = "Admin", user_email: str = ""):
        super().__init__()
        self._backend = backend
        self._role = role
        self._user_email = user_email
        self._tab_buttons: dict[str, QPushButton] = {}
        self._queue_ids: list[int] = []
        self._service_ids: list[int] = []
        self._invoice_ids: list[int] = []
        self._my_doctor_id = None
        if self._role == "Doctor" and self._user_email and self._backend:
            self._my_doctor_id = self._backend.get_employee_id_by_email(self._user_email)
            if not self._my_doctor_id:
                self._my_doctor_id = -1  # Sentinel: show nothing if lookup fails
        self._build()
        # Auto-refresh data every 10 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(300_000)

    def refresh(self):
        """Reload data for all clinical tabs, auto-sync appointments."""
        if not self.isVisible():
            return
        try:
            if self._backend:
                self._backend.sync_today_appointments_to_queue()
            self._load_queue()
        except Exception:
            pass
        try:
            self._load_billing()
        except Exception:
            pass
        try:
            self._load_services()
        except Exception:
            pass

    # ── Build ──────────────────────────────────────────────────────
    def _build(self):
        scroll, lay = make_page_layout()

        # ── Header Banner ─────────────────────────────────────────
        banner = make_banner(
            "Clinical Workflow & Billing",
            "Patient queue, consultations, and point-of-sale",
        )
        lay.addWidget(banner)

        # ── Tab row ───────────────────────────────────────────────
        tab_row = QHBoxLayout(); tab_row.setSpacing(8)
        self._stack = QStackedWidget()
        tab_labels: list[str] = []
        if self._role in ("Admin", "Doctor", "Nurse"):
            tab_labels.append("Patient Queue")
            self._stack.addWidget(self._build_queue_tab())
        if self._role in ("Admin", "Receptionist"):
            tab_labels.append("Billing / POS")
            self._stack.addWidget(self._build_billing_tab())
        if self._role == "Admin":
            tab_labels.append("Services && Pricing")
            self._stack.addWidget(self._build_services_tab())

        for i, label in enumerate(tab_labels):
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(38)
            btn.clicked.connect(lambda checked, idx=i, lbl=label: self._switch_tab(idx, lbl))
            self._tab_buttons[label] = btn
            tab_row.addWidget(btn)
        tab_row.addStretch()
        lay.addLayout(tab_row)
        lay.addWidget(self._stack)
        if tab_labels:
            self._switch_tab(0, tab_labels[0])

        lay.addStretch()
        finish_page(self, scroll)

    def _switch_tab(self, index: int, label: str):
        self._stack.setCurrentIndex(index)
        for name, btn in self._tab_buttons.items():
            btn.setStyleSheet(TAB_ACTIVE if name == label else TAB_INACTIVE)

    # ══════════════════════════════════════════════════════════════
    #  QUEUE TAB
    # ══════════════════════════════════════════════════════════════
    def _build_queue_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(16); lay.setContentsMargins(16, 16, 16, 16)

        # Status cards
        status_row = QHBoxLayout()
        stats = {"waiting": 0, "in_progress": 0, "completed": 0}
        if self._backend:
            stats = self._backend.get_queue_stats(doctor_id=self._my_doctor_id)
        self._queue_stat_labels = {}
        for key, label, color in [
            ("waiting",     "Waiting",          "#E8B931"),
            ("triaged",     "Triaged",          "#3498DB"),
            ("in_progress", "In Progress",      "#388087"),
            ("completed",   "Completed Today",  "#5CB85C"),
        ]:
            card = QFrame(); card.setObjectName("card")
            cl = QVBoxLayout(card); cl.setContentsMargins(16, 14, 16, 14); cl.setSpacing(4)
            strip = QFrame(); strip.setFixedHeight(3)
            strip.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
            v = QLabel(str(stats.get(key, 0) or 0)); v.setObjectName("statValue")
            self._queue_stat_labels[key] = v
            l = QLabel(label); l.setObjectName("statLabel")
            cl.addWidget(strip); cl.addWidget(v); cl.addWidget(l)
            status_row.addWidget(card)

        # Estimated wait time card
        avg_min = self._backend.get_avg_consultation_minutes() if self._backend else 15
        waiting_cnt = int(stats.get("waiting", 0) or 0)
        est_wait = waiting_cnt * avg_min
        wait_card = QFrame(); wait_card.setObjectName("card")
        wcl = QVBoxLayout(wait_card); wcl.setContentsMargins(16, 14, 16, 14); wcl.setSpacing(4)
        ws = QFrame(); ws.setFixedHeight(3)
        ws.setStyleSheet("background-color: #6FB3B8; border-radius: 1px;")
        self._wait_lbl = QLabel(f"~{est_wait} min"); self._wait_lbl.setObjectName("statValue")
        wl = QLabel("Est. Wait"); wl.setObjectName("statLabel")
        wcl.addWidget(ws); wcl.addWidget(self._wait_lbl); wcl.addWidget(wl)
        status_row.addWidget(wait_card)
        lay.addLayout(status_row)

        # Toolbar: call next (left), doctor filter (right)
        toolbar = QHBoxLayout(); toolbar.setSpacing(10)

        self._call_btn = QPushButton("Start Triage" if self._role == "Nurse" else "Call Next")
        self._call_btn.setIcon(get_icon("stethoscope" if self._role == "Nurse" else "megaphone", color=QColor("#FFFFFF")))
        self._call_btn.setIconSize(QSize(18, 18))
        self._call_btn.setObjectName("actionBtn"); self._call_btn.setMinimumHeight(40)
        self._call_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._call_btn.clicked.connect(self._on_call_next)
        toolbar.addWidget(self._call_btn)
        if self._role in ("Admin",):
            self._call_btn.setVisible(False)

        toolbar.addStretch()

        self._queue_doc_filter = QComboBox()
        self._queue_doc_filter.setObjectName("formCombo")
        self._queue_doc_filter.setMinimumHeight(40); self._queue_doc_filter.setMinimumWidth(180)
        self._queue_doc_filter.blockSignals(True)
        self._queue_doc_filter.addItem("All Doctors", None)
        if self._backend:
            for d in self._backend.get_doctors():
                self._queue_doc_filter.addItem(d["doctor_name"], d["employee_id"])
        # Doctor role: auto-select own name and hide the filter
        if self._role == "Doctor" and self._user_email and self._backend:
            my_id = self._backend.get_employee_id_by_email(self._user_email)
            if my_id:
                for i in range(self._queue_doc_filter.count()):
                    if self._queue_doc_filter.itemData(i) == my_id:
                        self._queue_doc_filter.setCurrentIndex(i)
                        break
            self._queue_doc_filter.setVisible(False)
        self._queue_doc_filter.blockSignals(False)
        toolbar.addWidget(self._queue_doc_filter)
        lay.addLayout(toolbar)

        # Queue table
        action_w = 180 if self._role == "Doctor" else (220 if self._role == "Nurse" else 100)
        cols = ["Queue #", "Patient", "Time", "Doctor", "Purpose", "Vitals", "Nurse Notes", "Status", "Actions"]
        self._queue_table = make_action_table(cols, min_h=420, row_h=48, action_col_width=action_w)
        self._queue_doc_filter.currentIndexChanged.connect(lambda _: self._filter_queue())
        # Auto-sync appointments into queue on first load
        if self._backend:
            try:
                self._backend.sync_today_appointments_to_queue()
            except Exception:
                pass
        self._load_queue()
        lay.addWidget(self._queue_table)
        return page

    def _load_queue(self):
        self._queue_table.setRowCount(0)
        self._queue_ids = []
        self._queue_doctor_ids = []
        if not self._backend:
            return
        doc_id = self._my_doctor_id if self._role == "Doctor" else None
        rows = self._backend.get_queue_entries(doctor_id=doc_id) or []
        for entry in rows:
            r = self._queue_table.rowCount()
            self._queue_table.insertRow(r)
            self._queue_ids.append(entry.get("queue_id", 0))
            self._queue_doctor_ids.append(entry.get("doctor_id", 0))
            t = entry.get("queue_time", "")
            if hasattr(t, "total_seconds"):
                total = int(t.total_seconds()); h, m = divmod(total // 60, 60)
                t = f"{h:02d}:{m:02d}"
            elif hasattr(t, "strftime"):
                t = t.strftime("%H:%M")
            status = entry.get("status", "")
            # Build vitals summary
            bp = entry.get("blood_pressure", "") or ""
            ht = entry.get("height_cm")
            wt = entry.get("weight_kg")
            temp = entry.get("temperature")
            vitals_parts = []
            if bp: vitals_parts.append(f"BP:{bp}")
            if ht: vitals_parts.append(f"H:{ht}cm")
            if wt: vitals_parts.append(f"W:{wt}kg")
            if temp: vitals_parts.append(f"T:{temp}°C")
            vitals_str = " | ".join(vitals_parts) if vitals_parts else "—"

            nurse_notes = entry.get("nurse_notes", "") or ""
            notes_preview = nurse_notes[:30] + ("…" if len(nurse_notes) > 30 else "") if nurse_notes else "—"

            values = [
                str(entry.get("queue_id", "")),
                entry.get("patient_name", ""),
                str(t),
                entry.get("doctor_name", ""),
                entry.get("purpose", "") or "",
                vitals_str,
                notes_preview,
                status,
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                if c == 7:
                    item.setForeground(QColor(status_color(val)))
                self._queue_table.setItem(r, c, item)

            # Nurse role: Triage button for Waiting, Update Vitals for Triaged/In Progress
            if self._role == "Nurse":
                btns = []
                if status == "Waiting":
                    triage_btn = make_table_btn("Triage")
                    triage_btn.clicked.connect(lambda checked, ri=r, e=entry: self._on_record_vitals(ri, e))
                    btns.append(triage_btn)
                elif status in ("Triaged", "In Progress"):
                    label = "Update Vitals"
                    vitals_btn = make_table_btn(label)
                    vitals_btn.clicked.connect(lambda checked, ri=r, e=entry: self._on_record_vitals(ri, e))
                    btns.append(vitals_btn)
                self._queue_table.setCellWidget(r, 8, make_action_cell(*btns))
            # Doctor role: Complete / Cancel only after Call Next (In Progress)
            elif self._role == "Doctor":
                btns = []
                if status == "In Progress":
                    done_btn = make_table_btn("Complete")
                    done_btn.clicked.connect(lambda checked, ri=r: self._on_complete_queue(ri))
                    btns.append(done_btn)
                    cancel_btn = make_table_btn_danger("Cancel")
                    cancel_btn.clicked.connect(lambda checked, ri=r: self._on_cancel_queue(ri))
                    btns.append(cancel_btn)
                self._queue_table.setCellWidget(r, 8, make_action_cell(*btns))
            else:
                edit_btn = make_table_btn("Edit")
                edit_btn.clicked.connect(lambda checked, ri=r: self._on_edit_queue(ri))
                if self._role == "Admin":
                    edit_btn.setVisible(False)
                self._queue_table.setCellWidget(r, 8, make_action_cell(edit_btn))

        # Update stat cards
        doc_id_for_stats = self._my_doctor_id if self._role == "Doctor" else self._queue_doc_filter.currentData()
        stats = self._backend.get_queue_stats(doctor_id=doc_id_for_stats)
        for key, lbl in self._queue_stat_labels.items():
            lbl.setText(str(stats.get(key, 0) or 0))
        # Update est wait
        avg_min = self._backend.get_avg_consultation_minutes()
        waiting_cnt = int(stats.get("waiting", 0) or 0)
        self._wait_lbl.setText(f"~{waiting_cnt * avg_min} min")

        # Doctor: disable Call Next if there's already an In Progress entry for this doctor
        if self._role == "Doctor":
            has_in_progress = any(
                self._queue_table.item(r, 7) and self._queue_table.item(r, 7).text() == "In Progress"
                for r in range(self._queue_table.rowCount())
            )
            self._call_btn.setEnabled(not has_in_progress)
            if has_in_progress:
                self._call_btn.setToolTip("Complete the current patient before calling next")
            else:
                self._call_btn.setToolTip("")
        # Nurse: disable Start Triage if no Waiting patients
        elif self._role == "Nurse":
            has_waiting = any(
                self._queue_table.item(r, 7) and self._queue_table.item(r, 7).text() == "Waiting"
                for r in range(self._queue_table.rowCount())
            )
            self._call_btn.setEnabled(has_waiting)
            if not has_waiting:
                self._call_btn.setToolTip("No patients waiting for triage")
            else:
                self._call_btn.setToolTip("")

        self._filter_queue()

    def _filter_queue(self):
        # Doctor role: data is already filtered at DB level, show all loaded rows
        if self._role == "Doctor":
            for r in range(self._queue_table.rowCount()):
                self._queue_table.setRowHidden(r, False)
            return
        doc_id = self._queue_doc_filter.currentData()
        for r in range(self._queue_table.rowCount()):
            if doc_id is None:
                self._queue_table.setRowHidden(r, False)
            else:
                hidden = (r < len(self._queue_doctor_ids) and self._queue_doctor_ids[r] != doc_id)
                self._queue_table.setRowHidden(r, hidden)

    def _on_sync_queue(self):
        if not self._backend:
            return
        n = self._backend.sync_today_appointments_to_queue()
        self._load_queue()
        QMessageBox.information(self, "Sync Complete", f"{n} appointment(s) added to today's queue.")

    def _on_call_next(self):
        if not self._backend:
            return
        doc_id = self._my_doctor_id if self._role == "Doctor" else self._queue_doc_filter.currentData()
        # Doctor: block if there's an In Progress entry
        if self._role == "Doctor" and doc_id:
            for r in range(self._queue_table.rowCount()):
                if (r < len(self._queue_doctor_ids) and self._queue_doctor_ids[r] == doc_id
                        and self._queue_table.item(r, 7) and self._queue_table.item(r, 7).text() == "In Progress"):
                    QMessageBox.warning(self, "Queue",
                        "You still have a patient In Progress.\nComplete or cancel them first.")
                    return
        entry = self._backend.call_next_queue(doctor_id=doc_id, role=self._role)
        if entry:
            self._load_queue()
            if self._role == "Nurse":
                # Auto-open triage dialog for the called patient
                qid = entry.get("queue_id")
                for r in range(self._queue_table.rowCount()):
                    if r < len(self._queue_ids) and self._queue_ids[r] == qid:
                        self._on_record_vitals(r)
                        break
                else:
                    QMessageBox.information(self, "Triage",
                        f"Triage: {entry.get('patient_name', 'Unknown')}")
            else:
                QMessageBox.information(self, "Called",
                    f"Now seeing: {entry.get('patient_name', 'Unknown')}")
        else:
            msg = "No waiting patients to triage." if self._role == "Nurse" else "No waiting patients in queue."
            QMessageBox.information(self, "Queue", msg)

    def _on_edit_queue(self, row):
        data = {}
        keys = ["queue", "patient", "time", "doctor", "purpose", "vitals", "nurse_notes", "status"]
        for c, key in enumerate(keys):
            data[key] = self._queue_table.item(row, c).text() if self._queue_table.item(row, c) else ""
        dlg = QueueEditDialog(self, data=data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if self._backend and row < len(self._queue_ids):
                self._backend.update_queue_entry(self._queue_ids[row], d)
            self._load_queue()
            QMessageBox.information(self, "Success", f"Queue entry '{d['queue']}' updated.")

    def _on_record_vitals(self, row, entry=None):
        """Nurse records or updates vitals (BP, height, weight, temperature) and triage notes."""
        if not self._backend or row >= len(self._queue_ids):
            return
        qid = self._queue_ids[row]
        patient = self._queue_table.item(row, 1).text() if self._queue_table.item(row, 1) else ""
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Record Vitals \u2013 {patient}")
        dlg.setMinimumWidth(520)
        main_lay = QVBoxLayout(dlg)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # Header bar
        hdr = QFrame()
        hdr.setStyleSheet("background: #388087; border: none;")
        hdr.setFixedHeight(56)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(20, 0, 20, 0)
        hdr_lbl = QLabel(f"Vitals \u2013 {patient}")
        hdr_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF; border: none;")
        hdr_lay.addWidget(hdr_lbl)
        main_lay.addWidget(hdr)

        content = QWidget()
        fl = QFormLayout(content)
        fl.setSpacing(14)
        fl.setContentsMargins(28, 22, 28, 22)
        fl.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        _LABEL_SS = "font-size: 13px; font-weight: bold; color: #2C3E50;"
        _INPUT_SS = (
            "QLineEdit { padding: 8px 14px; border: 2px solid #BADFE7;"
            " border-radius: 10px; font-size: 13px; background: #FFF; color: #2C3E50; }"
            "QLineEdit:focus { border: 2px solid #388087; }")
        _UNIT_SS = ("font-size: 11px; color: #7F8C8D; font-weight: bold;"
                    " padding: 0 6px; min-width: 30px;")

        from PyQt6.QtGui import QDoubleValidator, QRegularExpressionValidator
        from PyQt6.QtCore import QRegularExpression

        # Blood pressure (special: allow digits and /)
        bp_edit = QLineEdit()
        bp_edit.setPlaceholderText("e.g. 120/80")
        bp_edit.setMinimumHeight(40); bp_edit.setMaxLength(20)
        bp_edit.setStyleSheet(_INPUT_SS)
        bp_edit.setValidator(QRegularExpressionValidator(
            QRegularExpression(r"^[0-9]{0,3}/?[0-9]{0,3}$")))
        bp_row = QHBoxLayout(); bp_row.setSpacing(4)
        bp_row.addWidget(bp_edit, 1)
        bp_unit = QLabel("mmHg"); bp_unit.setStyleSheet(_UNIT_SS)
        bp_row.addWidget(bp_unit)
        bp_lbl = QLabel("Blood Pressure <span style='color:#E74C3C;'>*</span>"); bp_lbl.setTextFormat(Qt.TextFormat.RichText); bp_lbl.setStyleSheet(_LABEL_SS)
        fl.addRow(bp_lbl, bp_row)

        # Height with Feet/CM toggle
        height_edit = QLineEdit()
        height_edit.setMinimumHeight(40); height_edit.setMaxLength(10)
        height_edit.setStyleSheet(_INPUT_SS)
        height_edit.setValidator(QDoubleValidator(0.0, 999.9, 1))

        height_unit_btn = QPushButton("CM")
        height_unit_btn.setCheckable(True)
        height_unit_btn.setMinimumHeight(36); height_unit_btn.setMinimumWidth(64)
        height_unit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        height_unit_btn.setStyleSheet(
            "QPushButton { background: #388087; color: white; font-size: 11px;"
            " font-weight: bold; border-radius: 8px; padding: 4px 10px; }"
            "QPushButton:checked { background: #6FB3B8; }")

        _height_is_feet = [False]  # mutable flag

        def _toggle_height_unit(checked):
            current_text = height_edit.text().strip()
            current_val = None
            if current_text:
                try:
                    current_val = float(current_text)
                except ValueError:
                    pass

            if checked:
                height_unit_btn.setText("Feet")
                height_edit.setPlaceholderText("e.g. 5.6  (feet)")
                height_edit.setValidator(QDoubleValidator(0.0, 10.0, 2))
                _height_is_feet[0] = True
                # Convert CM → Feet
                if current_val is not None and current_val > 0:
                    converted = round(current_val / 30.48, 2)
                    height_edit.setText(str(converted))
            else:
                height_unit_btn.setText("CM")
                height_edit.setPlaceholderText("e.g. 165.5")
                height_edit.setValidator(QDoubleValidator(0.0, 999.9, 1))
                _height_is_feet[0] = False
                # Convert Feet → CM
                if current_val is not None and current_val > 0:
                    converted = round(current_val * 30.48, 1)
                    height_edit.setText(str(converted))

        height_unit_btn.toggled.connect(_toggle_height_unit)
        height_edit.setPlaceholderText("e.g. 165.5")

        ht_row = QHBoxLayout(); ht_row.setSpacing(4)
        ht_row.addWidget(height_edit, 1)
        ht_row.addWidget(height_unit_btn)
        ht_lbl = QLabel("Height"); ht_lbl.setStyleSheet(_LABEL_SS)
        fl.addRow(ht_lbl, ht_row)

        # Weight
        weight_edit = QLineEdit()
        weight_edit.setPlaceholderText("e.g. 70.5")
        weight_edit.setMinimumHeight(40); weight_edit.setMaxLength(10)
        weight_edit.setStyleSheet(_INPUT_SS)
        weight_edit.setValidator(QDoubleValidator(0.0, 999.9, 1))
        wt_row = QHBoxLayout(); wt_row.setSpacing(4)
        wt_row.addWidget(weight_edit, 1)
        wt_unit = QLabel("kg"); wt_unit.setStyleSheet(_UNIT_SS)
        wt_row.addWidget(wt_unit)
        wt_lbl = QLabel("Weight"); wt_lbl.setStyleSheet(_LABEL_SS)
        fl.addRow(wt_lbl, wt_row)

        # Temperature
        temp_edit = QLineEdit()
        temp_edit.setPlaceholderText("e.g. 36.5")
        temp_edit.setMinimumHeight(40); temp_edit.setMaxLength(10)
        temp_edit.setStyleSheet(_INPUT_SS)
        temp_edit.setValidator(QDoubleValidator(25.0, 45.0, 1))
        tp_row = QHBoxLayout(); tp_row.setSpacing(4)
        tp_row.addWidget(temp_edit, 1)
        tp_unit = QLabel("\u00b0C"); tp_unit.setStyleSheet(_UNIT_SS)
        tp_row.addWidget(tp_unit)
        tp_lbl = QLabel("Temperature"); tp_lbl.setStyleSheet(_LABEL_SS)
        fl.addRow(tp_lbl, tp_row)

        # Separator
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet("background: #BADFE7; border: none; margin: 4px 0;")
        fl.addRow(sep)

        # Nurse notes (free text)
        from PyQt6.QtWidgets import QTextEdit
        notes_edit = QTextEdit()
        notes_edit.setPlaceholderText("Triage observations, chief complaint, symptoms\u2026")
        notes_edit.setMaximumHeight(90)
        notes_edit.setStyleSheet(
            "QTextEdit { padding: 8px 12px; border: 2px solid #BADFE7;"
            " border-radius: 10px; font-size: 13px; background: #FFF; color: #2C3E50; }"
            "QTextEdit:focus { border: 2px solid #388087; }")
        notes_lbl = QLabel("Nurse Notes"); notes_lbl.setStyleSheet(_LABEL_SS)
        fl.addRow(notes_lbl, notes_edit)

        # Pre-fill existing vitals if updating
        if entry:
            bp_val = entry.get("blood_pressure", "") or ""
            if bp_val:
                bp_edit.setText(bp_val)
            ht_val = entry.get("height_cm")
            if ht_val:
                height_edit.setText(str(float(ht_val)))
            wt_val = entry.get("weight_kg")
            if wt_val:
                weight_edit.setText(str(float(wt_val)))
            temp_val = entry.get("temperature")
            if temp_val:
                temp_edit.setText(str(float(temp_val)))
            nn = entry.get("nurse_notes", "") or ""
            if nn:
                notes_edit.setPlainText(nn)

        hint = QLabel("Blood pressure is required. Other vitals are optional.")
        hint.setStyleSheet("font-size: 11px; color: #7F8C8D; font-style: italic;")
        fl.addRow(hint)

        main_lay.addWidget(content, 1)

        # Buttons
        btn_frame = QFrame()
        btn_frame.setStyleSheet("background: #F0F7F8; border-top: 1px solid #BADFE7;")
        btn_row = QHBoxLayout(btn_frame)
        btn_row.setContentsMargins(20, 12, 20, 12); btn_row.setSpacing(12); btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setMinimumHeight(42)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            "QPushButton { background: #F8D7DA; color: #C0392B; font-size: 13px;"
            " font-weight: bold; border-radius: 8px; padding: 8px 24px; border: none; }"
            "QPushButton:hover { background: #F1B0B7; }")
        cancel_btn.clicked.connect(dlg.reject)
        save_btn = QPushButton("Save Vitals"); save_btn.setMinimumHeight(42)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            "QPushButton { background: #388087; color: white; font-size: 13px;"
            " font-weight: bold; border-radius: 8px; padding: 8px 24px; border: none; }"
            "QPushButton:hover { background: #2C6A70; }")
        save_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(save_btn)
        main_lay.addWidget(btn_frame)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            bp = bp_edit.text().strip()
            ht_text = height_edit.text().strip()
            wt_text = weight_edit.text().strip()
            temp_text = temp_edit.text().strip()
            notes = notes_edit.toPlainText().strip()

            # Blood pressure is REQUIRED and must be formatted as systolic/diastolic
            if not bp:
                QMessageBox.warning(self, "Validation",
                    "Blood Pressure is required.\nPlease enter a value like 120/80.")
                return
            import re
            bp_match = re.match(r'^(\d{2,3})/(\d{2,3})$', bp)
            if not bp_match:
                QMessageBox.warning(self, "Validation",
                    "Blood Pressure must be in the format systolic/diastolic.\n"
                    "Example: 120/80")
                return
            systolic = int(bp_match.group(1))
            diastolic = int(bp_match.group(2))
            if systolic < 50 or systolic > 300:
                QMessageBox.warning(self, "Validation",
                    f"Systolic pressure ({systolic}) is out of range.\n"
                    "Expected: 50 – 300 mmHg.")
                return
            if diastolic < 20 or diastolic > 200:
                QMessageBox.warning(self, "Validation",
                    f"Diastolic pressure ({diastolic}) is out of range.\n"
                    "Expected: 20 – 200 mmHg.")
                return
            if diastolic >= systolic:
                QMessageBox.warning(self, "Validation",
                    "Diastolic pressure must be lower than systolic.\n"
                    f"You entered: {systolic}/{diastolic}")
                return

            # Convert height from feet to cm if needed
            ht = None
            if ht_text:
                try:
                    ht = float(ht_text)
                    if _height_is_feet[0]:
                        ht = round(ht * 30.48, 1)
                    if ht <= 0 or ht > 300:
                        QMessageBox.warning(self, "Validation",
                            "Height must be between 0 and 300 cm.")
                        return
                except ValueError:
                    QMessageBox.warning(self, "Validation",
                        "Height must be a number.")
                    return

            wt = None
            if wt_text:
                try:
                    wt = float(wt_text)
                    if wt <= 0 or wt > 500:
                        QMessageBox.warning(self, "Validation",
                            "Weight must be between 0 and 500 kg.")
                        return
                except ValueError:
                    QMessageBox.warning(self, "Validation",
                        "Weight must be a number.")
                    return

            temp = None
            if temp_text:
                try:
                    temp = float(temp_text)
                    if temp < 25 or temp > 45:
                        QMessageBox.warning(self, "Validation",
                            "Temperature must be between 25 and 45 \u00b0C.")
                        return
                except ValueError:
                    QMessageBox.warning(self, "Validation",
                        "Temperature must be a number.")
                    return

            # BP is already validated as required above

            ok = self._backend.record_vitals(qid, bp, ht, wt, temp, notes)
            if ok:
                self._load_queue()
                QMessageBox.information(self, "Vitals Recorded",
                    f"Vitals for {patient} saved successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to save vitals.")

    def _on_complete_queue(self, row):
        if not self._backend or row >= len(self._queue_ids):
            return
        qid = self._queue_ids[row]
        patient = self._queue_table.item(row, 1).text() if self._queue_table.item(row, 1) else ""
        purpose = self._queue_table.item(row, 4).text() if self._queue_table.item(row, 4) else ""
        self._backend.update_queue_entry(qid, {"status": "Completed", "purpose": purpose})
        invoiced = self._backend.create_invoice_from_queue(qid)
        # If invoice creation failed (no appointment linked), still mark appointment completed
        if not invoiced:
            self._backend.complete_appointment_from_queue(qid)
        self._load_queue()
        msg = f"{patient}'s consultation marked as completed."
        if invoiced:
            msg += "\nAn invoice has been automatically created."
        QMessageBox.information(self, "Completed", msg)

    def _on_cancel_queue(self, row):
        if not self._backend or row >= len(self._queue_ids):
            return
        qid = self._queue_ids[row]
        patient = self._queue_table.item(row, 1).text() if self._queue_table.item(row, 1) else ""
        reply = QMessageBox.question(self, "Cancel Queue Entry",
            f"Cancel {patient}'s queue entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._backend.update_queue_entry(qid, {"status": "Cancelled", "purpose": self._queue_table.item(row, 4).text() if self._queue_table.item(row, 4) else ""})
            self._backend.cancel_appointment_from_queue(qid)
            self._load_queue()

    # ══════════════════════════════════════════════════════════════
    #  BILLING TAB
    # ══════════════════════════════════════════════════════════════
    def _build_billing_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(16); lay.setContentsMargins(16, 16, 16, 16)

        bar = QHBoxLayout()
        self._billing_search = QLineEdit()
        self._billing_search.setObjectName("searchBar")
        self._billing_search.setPlaceholderText("Search invoices...")
        self._billing_search.setMinimumHeight(42)
        self._billing_search.textChanged.connect(self._apply_billing_filters)
        bar.addWidget(self._billing_search)

        new_btn = QPushButton("New Invoice")
        new_btn.setIcon(get_icon("receipt", color=QColor("#FFFFFF")))
        new_btn.setIconSize(QSize(18, 18))
        new_btn.setObjectName("actionBtn"); new_btn.setMinimumHeight(42)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self._on_new_invoice)
        bar.addWidget(new_btn)
        if self._role == "Admin":
            new_btn.setVisible(False)
        lay.addLayout(bar)

        # ── Sort & filter bar ─────────────────────────────────────
        sort_bar = QHBoxLayout(); sort_bar.setSpacing(10)

        self._billing_sort_combo = QComboBox()
        self._billing_sort_combo.setObjectName("formCombo")
        self._billing_sort_combo.addItems(["Sort By", "Patient", "Services", "Total", "Status"])
        self._billing_sort_combo.setMinimumHeight(42); self._billing_sort_combo.setMinimumWidth(140)
        self._billing_sort_combo.currentTextChanged.connect(self._apply_billing_filters)
        sort_bar.addWidget(self._billing_sort_combo)

        self._billing_order_combo = QComboBox()
        self._billing_order_combo.setObjectName("formCombo")
        self._billing_order_combo.addItems(["↑ Ascending", "↓ Descending"])
        self._billing_order_combo.setMinimumHeight(42); self._billing_order_combo.setMinimumWidth(140)
        self._billing_order_combo.currentTextChanged.connect(self._apply_billing_filters)
        sort_bar.addWidget(self._billing_order_combo)

        self._billing_status_filter = QComboBox()
        self._billing_status_filter.setObjectName("formCombo")
        self._billing_status_filter.addItems(["All Status", "Paid", "Unpaid", "Partial", "Voided"])
        self._billing_status_filter.setMinimumHeight(42); self._billing_status_filter.setMinimumWidth(140)
        self._billing_status_filter.currentTextChanged.connect(self._apply_billing_filters)
        sort_bar.addWidget(self._billing_status_filter)

        sort_bar.addStretch()
        lay.addLayout(sort_bar)

        cols = ["Inv #", "Patient", "Services", "Total", "Paid", "Status", "Actions"]
        self._billing_table = make_action_table(cols, min_h=420, row_h=48, action_col_width=200)
        self._all_invoices: list[dict] = []
        self._load_billing()
        lay.addWidget(self._billing_table)
        return page

    def _load_billing(self):
        self._all_invoices = []
        self._invoice_ids = []
        if not self._backend:
            self._render_billing_table([])
            return
        self._all_invoices = self._backend.get_invoices() or []
        self._apply_billing_filters()

    def _apply_billing_filters(self, _=None):
        """Filter by search text + status, then sort, then render."""
        text = self._billing_search.text().strip().lower()
        status_filter = self._billing_status_filter.currentText()
        sort_by = self._billing_sort_combo.currentText()
        descending = self._billing_order_combo.currentText().startswith("↓")

        # ── Filter ────────────────────────────────────────────────
        filtered = []
        for inv in self._all_invoices:
            # Status filter
            if status_filter != "All Status" and inv.get("status", "") != status_filter:
                continue
            # Text search
            if text:
                haystack = " ".join([
                    str(inv.get("invoice_id", "")),
                    inv.get("patient_name", ""),
                    inv.get("service_name", "") or "",
                    inv.get("status", ""),
                ]).lower()
                if text not in haystack:
                    continue
            filtered.append(inv)

        # ── Sort ──────────────────────────────────────────────────
        sort_key_map = {
            "Patient":  lambda inv: (inv.get("patient_name", "") or "").lower(),
            "Services": lambda inv: (inv.get("service_name", "") or "").lower(),
            "Total":    lambda inv: float(inv.get("total_amount", 0) or 0),
            "Status":   lambda inv: (inv.get("status", "") or "").lower(),
        }
        if sort_by in sort_key_map:
            filtered.sort(key=sort_key_map[sort_by], reverse=descending)

        self._render_billing_table(filtered)

    def _render_billing_table(self, invoices: list[dict]):
        """Populate the billing table with the given (sorted/filtered) invoices."""
        self._billing_table.setRowCount(0)
        self._invoice_ids = []
        for inv in invoices:
            r = self._billing_table.rowCount()
            self._billing_table.insertRow(r)
            inv_id = inv.get("invoice_id", 0)
            self._invoice_ids.append(inv_id)
            total = inv.get("total_amount", 0) or 0
            paid = inv.get("amount_paid", 0) or 0
            status = inv.get("status", "")
            values = [
                str(inv_id),
                inv.get("patient_name", ""),
                inv.get("service_name", "") or "",
                f"₱{float(total):,.2f}",
                f"₱{float(paid):,.2f}",
                status,
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                if c == 5:
                    item.setForeground(QColor(status_color(val)))
                self._billing_table.setItem(r, c, item)

            # Actions: Pay | Print | Void
            btns = []
            if status not in ("Paid", "Voided") and self._role in ("Receptionist",):
                pay_btn = make_table_btn("Pay")
                pay_btn.clicked.connect(lambda checked, iid=inv_id: self._on_add_payment(iid))
                btns.append(pay_btn)
            if status == "Paid":
                prt_btn = make_table_btn("Print")
                prt_btn.clicked.connect(lambda checked, iid=inv_id: self._on_print_receipt(iid))
                btns.append(prt_btn)
            if status != "Voided" and self._role in ("Admin", "Receptionist"):
                void_btn = make_table_btn_danger("Void")
                void_btn.clicked.connect(lambda checked, iid=inv_id: self._on_void_invoice(iid))
                btns.append(void_btn)
            
            w = make_action_cell(*btns)
            # Center the buttons solely in this page
            w.layout().setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._billing_table.setCellWidget(r, 6, w)

    def _on_new_invoice(self):
        services = self._backend.get_services_list() if self._backend else []
        methods = self._backend.get_payment_methods() if self._backend else []
        patients = self._backend.get_active_patients() if self._backend else []
        dlg = NewInvoiceDialog(self, services=services, payment_methods=methods,
                               patients=patients, backend=self._backend, role=self._role)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if self._backend:
                ok = self._backend.add_invoice(d)
                if not ok:
                    QMessageBox.warning(self, "Error", "Failed to create invoice. Check patient name.")
                    return
            self._load_billing()
            QMessageBox.information(self, "Success", f"Invoice for '{d['patient_name']}' created.")

    def _on_add_payment(self, invoice_id: int):
        if not self._backend:
            return
        detail = self._backend.get_invoice_detail(invoice_id)
        if not detail:
            return
        info = detail["info"]
        balance = float(info["total_amount"]) - float(info["amount_paid"])
        if balance <= 0:
            QMessageBox.information(self, "Paid", "This invoice is already fully paid.")
            return
        methods = self._backend.get_payment_methods()
        dlg = PaymentDialog(self, invoice_id=invoice_id, balance=balance, payment_methods=methods)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            self._backend.add_payment(invoice_id, d["amount"], d.get("method_id"))
            self._load_billing()
            msg = f"Payment recorded.\n\n"
            msg += f"  Amount Tendered:  ₱{d['tendered']:,.2f}\n"
            msg += f"  Applied to Invoice:  ₱{d['amount']:,.2f}\n"
            if d.get("change", 0) > 0:
                msg += f"  Change:  ₱{d['change']:,.2f}\n"
            QMessageBox.information(self, "Payment Recorded", msg)

    def _on_void_invoice(self, invoice_id: int):
        reply = QMessageBox.question(
            self, "Void Invoice",
            f"Void invoice #{invoice_id}? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._backend:
                self._backend.void_invoice(invoice_id)
            self._load_billing()
            QMessageBox.information(self, "Done", f"Invoice #{invoice_id} voided.")

    def _on_print_receipt(self, invoice_id: int):
        if not self._backend:
            return
        detail = self._backend.get_invoice_detail(invoice_id)
        if not detail:
            QMessageBox.warning(self, "Error", "Could not load invoice details.")
            return
        info = detail["info"]
        items = detail["items"]

        total_amount = float(info.get("total_amount", 0))
        amount_paid = float(info.get("amount_paid", 0))
        discount_pct = float(info.get("discount_percent", 0))

        # Calculate raw subtotal from line items
        raw_subtotal = sum(
            float(it.get("unit_price", 0)) * int(it.get("quantity", 1))
            for it in items
        )
        discount_amount = raw_subtotal - total_amount
        balance = total_amount - amount_paid

        w = 44

        lines = [
            "",
            "C A R E C R U D".center(w),
            "Healthcare Management System".center(w),
            "\u2500" * w,
            "",
            f"  Invoice #  :  {info.get('invoice_id', '')}",
            f"  Date       :  {str(info.get('created_at', ''))[:19]}",
            f"  Patient    :  {info.get('patient_name', '')}",
            f"  Phone      :  {info.get('phone', '') or '\u2014'}",
            f"  Payment    :  {info.get('payment_method', '\u2014')}",
            "",
            "\u2500" * w,
        ]

        # Item lines
        for it in items:
            sname = it.get("service_name", "")
            qty = int(it.get("quantity", 1))
            unit = float(it.get("unit_price", 0))
            sub = float(it.get("subtotal", 0))
            lines.append(f"  {sname}")
            lines.append(f"    {qty} x \u20b1{unit:,.2f}          \u20b1{sub:,.2f}")

        lines.append("\u2500" * w)

        if discount_amount > 0:
            lines.append(f"  Subtotal           \u20b1{raw_subtotal:>10,.2f}")
            lines.append(f"  Discount          -\u20b1{discount_amount:>10,.2f}")
            lines.append("")

        lines.append(f"  TOTAL              \u20b1{total_amount:>10,.2f}")
        lines.append(f"  AMOUNT PAID        \u20b1{amount_paid:>10,.2f}")

        if balance > 0:
            lines.append(f"  BALANCE DUE        \u20b1{balance:>10,.2f}")

        status = info.get("status", "")
        lines.append(f"  Status: {status}")
        lines.append("")
        lines.append("\u2500" * w)
        lines.append("Thank you for choosing us!".center(w))
        lines.append("\u2500" * w)

        text = "\n".join(lines)

        # Show in a proper dialog with monospace font
        from PyQt6.QtWidgets import QTextEdit as _QTE
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Receipt \u2013 Invoice #{invoice_id}")
        dlg.setMinimumWidth(420)
        dl = QVBoxLayout(dlg)
        dl.setContentsMargins(20, 16, 20, 16)
        dl.setSpacing(12)
        receipt_box = _QTE()
        receipt_box.setReadOnly(True)
        receipt_box.setPlainText(text)
        receipt_box.setStyleSheet(
            "QTextEdit { font-family: 'Consolas', 'Courier New', monospace;"
            " font-size: 13px; background: #FFFFFF; color: #2C3E50;"
            " border: 1px solid #BADFE7; border-radius: 8px; padding: 16px; }")
        receipt_box.setMinimumHeight(380)
        dl.addWidget(receipt_box)
        ok_btn = QPushButton("Close")
        ok_btn.setObjectName("actionBtn")
        ok_btn.setMinimumHeight(38)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(dlg.accept)
        dl.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        dlg.exec()

    # ══════════════════════════════════════════════════════════════
    #  SERVICES TAB
    # ══════════════════════════════════════════════════════════════
    def _build_services_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(16); lay.setContentsMargins(16, 16, 16, 16)

        bar = QHBoxLayout()
        self._svc_search = QLineEdit()
        self._svc_search.setObjectName("searchBar")
        self._svc_search.setPlaceholderText("Search services...")
        self._svc_search.setMinimumHeight(42)
        self._svc_search.textChanged.connect(self._on_svc_search)
        bar.addWidget(self._svc_search)

        self._svc_cat_filter = QComboBox()
        self._svc_cat_filter.setObjectName("formCombo")
        self._svc_cat_filter.setMinimumHeight(42); self._svc_cat_filter.setMinimumWidth(150)
        self._svc_cat_filter.addItem("All Categories")
        if self._backend:
            for c in self._backend.get_service_categories():
                self._svc_cat_filter.addItem(c)
        self._svc_cat_filter.currentTextChanged.connect(lambda _: self._apply_svc_filters())
        bar.addWidget(self._svc_cat_filter)

        add_btn = QPushButton("Add Service")
        add_btn.setIcon(get_icon("plus", color=QColor("#FFFFFF")))
        add_btn.setIconSize(QSize(18, 18))
        add_btn.setObjectName("actionBtn"); add_btn.setMinimumHeight(42)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add_service)
        bar.addWidget(add_btn)

        bulk_btn = QPushButton("Bulk Price Update")
        bulk_btn.setIcon(get_icon("dollar", color=QColor("#FFFFFF")))
        bulk_btn.setIconSize(QSize(18, 18))
        bulk_btn.setObjectName("actionBtn"); bulk_btn.setMinimumHeight(42)
        bulk_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bulk_btn.clicked.connect(self._on_bulk_price)
        bar.addWidget(bulk_btn)
        lay.addLayout(bar)

        cols = ["Service Name", "Category", "Price", "Usage", "Active", "Actions"]
        self._svc_table = make_action_table(cols, min_h=420, row_h=48, action_col_width=100)
        self._load_services()
        lay.addWidget(self._svc_table)
        return page

    def _load_services(self):
        self._svc_table.setRowCount(0)
        self._service_ids = []
        if not self._backend:
            return
        rows = self._backend.get_all_services() or []
        usage = self._backend.get_service_usage_counts() or {}
        for svc in rows:
            r = self._svc_table.rowCount()
            self._svc_table.insertRow(r)
            sid = svc.get("service_id", 0)
            self._service_ids.append(sid)
            price = svc.get("price", 0) or 0
            is_active = svc.get("is_active", 1)
            cat = svc.get("category", "General") or "General"
            use_cnt = usage.get(sid, 0)

            self._svc_table.setItem(r, 0, QTableWidgetItem(svc.get("service_name", "")))
            self._svc_table.setItem(r, 1, QTableWidgetItem(cat))
            self._svc_table.setItem(r, 2, QTableWidgetItem(f"₱{float(price):,.2f}"))
            self._svc_table.setItem(r, 3, QTableWidgetItem(str(use_cnt)))
            active_item = QTableWidgetItem("Yes" if is_active else "No")
            active_item.setForeground(QColor(status_color("Active" if is_active else "Inactive")))
            self._svc_table.setItem(r, 4, active_item)

            edit_btn = make_table_btn("Edit")
            edit_btn.clicked.connect(lambda checked, ri=r: self._on_edit_service(ri))
            self._svc_table.setCellWidget(r, 5, make_action_cell(edit_btn))

    def _on_svc_search(self, _text: str = ""):
        self._apply_svc_filters()

    def _apply_svc_filters(self):
        text = self._svc_search.text().strip().lower()
        cat = self._svc_cat_filter.currentText()
        for r in range(self._svc_table.rowCount()):
            text_match = True
            if text:
                text_match = any(
                    text in (self._svc_table.item(r, c).text().lower() if self._svc_table.item(r, c) else "")
                    for c in range(5)
                )
            cat_match = True
            if cat != "All Categories":
                cell = self._svc_table.item(r, 1)
                cat_match = (cell.text() == cat) if cell else False
            self._svc_table.setRowHidden(r, not (text_match and cat_match))

    def _on_add_service(self):
        self._refresh_timer.stop()
        try:
            cats = self._backend.get_service_categories() if self._backend else []
            if not cats:
                cats = ["General"]
            departments = self._backend.get_all_departments() if self._backend else []
            dlg = ServiceEditDialog(self, categories=cats, departments=departments)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                d = dlg.get_data()
                if not d["name"].strip():
                    QMessageBox.warning(self, "Validation", "Service name is required.")
                    return
                try:
                    price = float(d["price"].replace("₱", "").replace(",", ""))
                except (ValueError, AttributeError):
                    price = 0
                if self._backend:
                    ok = self._backend.add_service(d["name"], price, d["category"], departments=d.get("departments", []))
                    if not ok:
                        QMessageBox.warning(self, "Error", "Failed to add service.")
                        return
                self._load_services()
                QMessageBox.information(self, "Success", f"Service '{d['name']}' added.")
        finally:
            self._refresh_timer.start(300_000)

    def _on_edit_service(self, row):
        self._refresh_timer.stop()
        try:
            data = {
                "name":      self._svc_table.item(row, 0).text() if self._svc_table.item(row, 0) else "",
                "category":  self._svc_table.item(row, 1).text() if self._svc_table.item(row, 1) else "General",
                "price":     (self._svc_table.item(row, 2).text().replace("₱", "").replace(",", "")
                              if self._svc_table.item(row, 2) else ""),
                "is_active": (self._svc_table.item(row, 4).text() == "Yes") if self._svc_table.item(row, 4) else True,
            }
            cats = self._backend.get_service_categories() if self._backend else ["General"]
            departments = self._backend.get_all_departments() if self._backend else []
            service_id = self._service_ids[row] if row < len(self._service_ids) else None
            selected_deps = self._backend.get_service_departments(service_id) if (self._backend and service_id) else []
            
            dlg = ServiceEditDialog(self, data=data, categories=cats, departments=departments, selected_departments=selected_deps)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                d = dlg.get_data()
                if not d["name"].strip():
                    QMessageBox.warning(self, "Validation", "Service name is required.")
                    return
                try:
                    price = float(d["price"].replace("₱", "").replace(",", ""))
                except (ValueError, AttributeError):
                    price = 0
                if self._backend and row < len(self._service_ids):
                    ok = self._backend.update_service_full(
                        self._service_ids[row], d["name"], price,
                        d["category"], 1 if d["is_active"] else 0,
                        departments=d.get("departments", [])
                    )
                    if not ok:
                        QMessageBox.warning(self, "Error", "Failed to update service.")
                        return
                self._load_services()
                QMessageBox.information(self, "Success", f"Service '{d['name']}' updated.")
        finally:
            self._refresh_timer.start(300_000)

    def _on_bulk_price(self):
        if not self._backend:
            return
        self._refresh_timer.stop()
        try:
            services = self._backend.get_all_services() or []
            dlg = BulkPriceDialog(self, services=services)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                updates = dlg.get_updates()
                if updates:
                    self._backend.bulk_update_prices(updates)
                    self._load_services()
                    QMessageBox.information(self, "Done", f"{len(updates)} price(s) updated.")
                else:
                    QMessageBox.information(self, "No Changes", "No prices were modified.")
        finally:
            self._refresh_timer.start(300_000)

