# Appointments page - scheduling table with date tabs

from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDialog, QMessageBox, QInputDialog, QStackedWidget,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from ui.styles import (
    make_page_layout, finish_page, make_banner, make_read_only_table,
    make_action_table, make_table_btn, make_table_btn_danger,
    format_timedelta, status_color,
    TAB_ACTIVE, TAB_INACTIVE, make_action_cell,
)
from ui.shared.appointment_dialog import (
    AppointmentDialog, _pretty_date, _relative_label,
)


# ══════════════════════════════════════════════════════════════════════
#  Appointments Page
# ══════════════════════════════════════════════════════════════════════
class AppointmentsPage(QWidget):

    def __init__(self, backend=None, role: str = "Admin", user_email: str = ""):
        super().__init__()
        self._backend = backend
        self._role = role
        self._user_email = user_email
        self._patient_names: list[str] = []
        self._patients: list[dict] = []
        self._active_tab = "Today"
        self._tab_buttons: dict[str, QPushButton] = {}
        self._all_appointments: list[dict] = []
        self._appointment_ids: list[int] = []
        self._build()
        # Auto-refresh data every 10 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_from_db)
        self._refresh_timer.start(10_000)

    def set_patient_names(self, names: list[str]):
        self._patient_names = names

    def set_patients(self, patients: list[dict]):
        self._patients = patients

    def _load_from_db(self):
        if not self.isVisible():
            return
        if not self._backend:
            self._all_appointments = []; return
        # Doctor sees only their own appointments
        if self._role == "Doctor" and self._user_email:
            self._all_appointments = self._backend.get_appointments_for_doctor(self._user_email) or []
        else:
            self._all_appointments = self._backend.get_appointments() or []
        for appt in self._all_appointments:
            d = appt.get("appointment_date")
            if hasattr(d, "strftime"): appt["appointment_date"] = d.strftime("%Y-%m-%d")
            elif d is not None: appt["appointment_date"] = str(d)
            t = appt.get("appointment_time")
            appt["appointment_time"] = format_timedelta(t) + ":00" if hasattr(t, "total_seconds") else (
                t.strftime("%H:%M:%S") if hasattr(t, "strftime") else str(t) if t else "")
        self._update_doctor_filter()
        self._refresh_table()
        # Also refresh doctor availability if that view is active
        if hasattr(self, '_stack') and self._stack.currentIndex() == 1:
            self._load_avail_data()

    def _update_doctor_filter(self):
        current = self.doc_filter.currentText()
        self.doc_filter.blockSignals(True); self.doc_filter.clear()
        self.doc_filter.addItem("All Doctors")
        doc_names = sorted({a.get("doctor_name","") for a in self._all_appointments if a.get("doctor_name")})
        self.doc_filter.addItems(doc_names)
        idx = self.doc_filter.findText(current)
        if idx >= 0: self.doc_filter.setCurrentIndex(idx)
        self.doc_filter.blockSignals(False)

    def _build(self):
        scroll, lay = make_page_layout()
        lay.setSpacing(16)

        # ── Top-level view toggle (Appointments | Doctor Availability) ──
        if self._role in ("Admin", "Receptionist"):
            self._view_toggle_btns: dict[str, QPushButton] = {}
            toggle_row = QHBoxLayout(); toggle_row.setSpacing(8)
            for label in ("Appointments", "Doctor Availability"):
                btn = QPushButton(label); btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setMinimumHeight(38)
                btn.clicked.connect(lambda checked, l=label: self._switch_view(l))
                self._view_toggle_btns[label] = btn; toggle_row.addWidget(btn)
            toggle_row.addStretch(); lay.addLayout(toggle_row)

        # ── Stacked widget for the two views ──
        self._stack = QStackedWidget()
        lay.addWidget(self._stack)

        # ── Page 0: Appointments list ──
        self._appt_page = QWidget()
        appt_lay = QVBoxLayout(self._appt_page); appt_lay.setContentsMargins(0,0,0,0); appt_lay.setSpacing(16)

        # Banner
        btn_text = "+  New Walk-in" if self._role in ("Admin", "Receptionist") else ""
        appt_lay.addWidget(make_banner(
            "Walk-in Appointments",
            "View and manage today's walk-in consultations",
            btn_text=btn_text, btn_slot=self._on_new,
        ))

        # Quick-filter tabs
        tab_row = QHBoxLayout(); tab_row.setSpacing(8)
        for label in ("Today", "Tomorrow", "This Week", "This Month", "All"):
            btn = QPushButton(label); btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.setMinimumHeight(38)
            btn.clicked.connect(lambda checked, l=label: self._switch_tab(l))
            self._tab_buttons[label] = btn; tab_row.addWidget(btn)
        tab_row.addStretch(); appt_lay.addLayout(tab_row)

        self._summary_label = QLabel()
        self._summary_label.setObjectName("mutedSummary")
        appt_lay.addWidget(self._summary_label)

        # Filter bar
        bar = QHBoxLayout(); bar.setSpacing(10)
        self.search = QLineEdit(); self.search.setObjectName("searchBar")
        self.search.setPlaceholderText("Search by patient, doctor, or service...")
        self.search.setMinimumHeight(42); self.search.textChanged.connect(self._apply_filters)
        bar.addWidget(self.search)
        self.doc_filter = QComboBox(); self.doc_filter.setObjectName("formCombo")
        self.doc_filter.addItems(["All Doctors"]); self.doc_filter.setMinimumHeight(42); self.doc_filter.setMinimumWidth(150)
        self.doc_filter.currentTextChanged.connect(self._apply_filters); bar.addWidget(self.doc_filter)
        self.status_filter = QComboBox(); self.status_filter.setObjectName("formCombo")
        self.status_filter.addItems(["All Status","Pending","Confirmed","Cancelled","Completed"])
        self.status_filter.setMinimumHeight(42); self.status_filter.setMinimumWidth(140)
        self.status_filter.currentTextChanged.connect(self._apply_filters); bar.addWidget(self.status_filter)

        appt_lay.addLayout(bar)

        # Table – added Notes column
        cols = ["Day & Date", "Time", "Patient", "Doctor", "Service", "Notes", "Status"]
        if self._role != "Doctor": cols.append("Billing")
        if self._role not in ("Nurse",): cols.append("Actions")
        if self._role not in ("Nurse",):
            action_w = 210 if self._role == "Doctor" else 100
            self.table = make_action_table(cols, action_col_width=action_w)
        else:
            self.table = make_read_only_table(cols)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive); self.table.setColumnWidth(0, 260)
        appt_lay.addWidget(self.table)

        appt_lay.addStretch()
        self._stack.addWidget(self._appt_page)  # index 0

        # ── Page 1: Doctor Availability (Receptionist / Admin only) ──
        if self._role in ("Admin", "Receptionist"):
            self._avail_page = QWidget()
            avail_lay = QVBoxLayout(self._avail_page); avail_lay.setContentsMargins(0,0,0,0); avail_lay.setSpacing(16)

            avail_lay.addWidget(make_banner(
                "Doctor Availability",
                "View all doctors sorted by today's availability and appointment count",
            ))

            # Search bar for doctor availability
            avail_bar = QHBoxLayout(); avail_bar.setSpacing(10)
            self._avail_search = QLineEdit(); self._avail_search.setObjectName("searchBar")
            self._avail_search.setPlaceholderText("Search by doctor name or department...")
            self._avail_search.setMinimumHeight(42)
            self._avail_search.textChanged.connect(self._apply_avail_filters)
            avail_bar.addWidget(self._avail_search)

            self._avail_status_filter = QComboBox(); self._avail_status_filter.setObjectName("formCombo")
            self._avail_status_filter.addItems(["All", "Available", "Not Available"])
            self._avail_status_filter.setMinimumHeight(42); self._avail_status_filter.setMinimumWidth(160)
            self._avail_status_filter.currentTextChanged.connect(self._apply_avail_filters)
            avail_bar.addWidget(self._avail_status_filter)
            avail_lay.addLayout(avail_bar)

            self._avail_summary = QLabel(); self._avail_summary.setObjectName("mutedSummary")
            avail_lay.addWidget(self._avail_summary)

            avail_cols = ["Doctor", "Department", "Today's Schedule", "Status", "Appointments Today"]
            self._avail_table = make_read_only_table(avail_cols)
            avail_lay.addWidget(self._avail_table)

            avail_lay.addStretch()
            self._stack.addWidget(self._avail_page)  # index 1

        finish_page(self, scroll)
        self._load_from_db()
        self._switch_tab("Today")
        if self._role in ("Admin", "Receptionist"):
            self._switch_view("Appointments")

    def _switch_tab(self, label: str):
        self._active_tab = label
        for name, btn in self._tab_buttons.items():
            btn.setStyleSheet(TAB_ACTIVE if name == label else TAB_INACTIVE)
        self._refresh_table()

    def _rows_for_tab(self) -> list[dict]:
        today = date.today()
        tab = self._active_tab
        def _parse(d):
            try: return datetime.strptime(str(d), "%Y-%m-%d").date()
            except: return None
        if tab == "Today": return [a for a in self._all_appointments if _parse(a.get("appointment_date")) == today]
        if tab == "Tomorrow":
            tmr = today + timedelta(days=1); return [a for a in self._all_appointments if _parse(a.get("appointment_date")) == tmr]
        if tab == "This Week":
            start = today - timedelta(days=today.weekday()); end = start + timedelta(days=6)
            return [a for a in self._all_appointments if (d := _parse(a.get("appointment_date"))) and start <= d <= end]
        if tab == "This Month":
            ym = today.strftime("%Y-%m"); return [a for a in self._all_appointments if str(a.get("appointment_date",""))[:7] == ym]
        return list(self._all_appointments)

    def _refresh_table(self):
        rows = self._rows_for_tab()
        rows.sort(key=lambda a: (str(a.get("appointment_date","")), str(a.get("appointment_time",""))),
                  reverse=(self._active_tab == "All"))
        self.table.setRowCount(0)
        self.table.setRowCount(len(rows))
        self._appointment_ids = []
        col_count = self.table.columnCount()
        for r, appt in enumerate(rows):
            self._appointment_ids.append(appt.get("appointment_id", 0))
            date_str = str(appt.get("appointment_date",""))
            time_str = str(appt.get("appointment_time",""))
            try:
                t = datetime.strptime(time_str, "%H:%M:%S"); time_display = t.strftime("%I:%M %p")
            except: time_display = time_str
            pretty = _pretty_date(date_str); rel = _relative_label(date_str)
            date_display = f"{pretty}   ({rel})" if rel else pretty
            notes_preview = (appt.get("notes","") or "")[:40]
            if len(appt.get("notes","") or "") > 40: notes_preview += "…"
            values = [date_display, time_display, appt.get("patient_name",""),
                      appt.get("doctor_name",""), appt.get("service_name",""),
                      notes_preview, appt.get("status","")]
            # Add billing status for non-Doctor roles
            if self._role != "Doctor":
                values.append(appt.get("billing_status", "No Invoice"))
            for c, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                if c == 0: item.setFont(QFont("Segoe UI", 10))
                if c == 6:
                    item.setForeground(QColor(status_color(val)))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                # Billing column color coding
                if self._role != "Doctor" and c == 7:
                    item.setForeground(QColor(status_color(val)))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.table.setItem(r, c, item)
            if self._role not in ("Nurse",):
                if self._role == "Doctor":
                    status = appt.get("status", "")
                    btns = []
                    view_btn = make_table_btn("View")
                    view_btn.clicked.connect(lambda checked, a=appt: self._on_view(a))
                    btns.append(view_btn)
                    if status == "Pending":
                        confirm_btn = make_table_btn("Confirm")
                        confirm_btn.clicked.connect(lambda checked, a=appt: self._on_confirm(a))
                        btns.append(confirm_btn)
                    if status in ("Pending", "Confirmed"):
                        cancel_btn = make_table_btn_danger("Cancel")
                        cancel_btn.clicked.connect(lambda checked, a=appt: self._on_cancel(a))
                        btns.append(cancel_btn)
                    self.table.setCellWidget(r, col_count - 1, make_action_cell(*btns))
                else:
                    edit_btn = make_table_btn("Edit")
                    edit_btn.clicked.connect(lambda checked, a=appt: self._on_edit(a))
                    self.table.setCellWidget(r, col_count - 1, make_action_cell(edit_btn))
        self._summary_label.setText(f"Showing {len(rows)} appointment{'s' if len(rows)!=1 else ''}")
        self._apply_filters()

    def _apply_filters(self, _=None):
        search = self.search.text().lower()
        doc = self.doc_filter.currentText()
        status = self.status_filter.currentText()
        visible = 0
        for r in range(self.table.rowCount()):
            row_text = " ".join(self.table.item(r,c).text().lower() if self.table.item(r,c) else "" for c in range(self.table.columnCount()-1))
            doc_cell = self.table.item(r,3); status_cell = self.table.item(r,6)
            ok = (not search or search in row_text) and \
                 (doc=="All Doctors" or (doc_cell and doc_cell.text()==doc)) and \
                 (status=="All Status" or (status_cell and status_cell.text()==status))
            self.table.setRowHidden(r, not ok)
            if ok: visible += 1
        total = self.table.rowCount()
        self._summary_label.setText(f"Showing {visible} of {total} appointment{'s' if total!=1 else ''}" if visible != total
                                    else f"Showing {total} appointment{'s' if total!=1 else ''}")

    # ── Doctor Availability view (Receptionist / Admin) ────────────
    def _switch_view(self, label: str):
        """Toggle between Appointments list and Doctor Availability."""
        is_avail = label == "Doctor Availability"
        self._stack.setCurrentIndex(1 if is_avail else 0)
        for name, btn in self._view_toggle_btns.items():
            btn.setStyleSheet(TAB_ACTIVE if name == label else TAB_INACTIVE)
        if is_avail:
            self._load_avail_data()

    def _load_avail_data(self):
        """Fetch doctor availability overview and populate the table."""
        if not self._backend or not hasattr(self, '_avail_table'):
            return
        rows = self._backend.get_doctor_availability_overview() or []
        self._avail_rows = rows
        self._avail_table.setRowCount(len(rows))
        for r, doc in enumerate(rows):
            sched = ""
            if doc.get("sched_start") and doc.get("sched_end"):
                sched = f"{doc['sched_start']} – {doc['sched_end']}"
            else:
                sched = "No schedule today"
            avail = doc.get("availability", "Not Available")
            values = [
                doc.get("doctor_name", ""),
                doc.get("department", "—"),
                sched,
                avail,
                str(doc.get("appt_count", 0)),
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                if c == 3:  # Status column
                    color = "#27AE60" if avail == "Available" else "#E74C3C"
                    item.setForeground(QColor(color))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                if c == 4:  # Appointment count
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self._avail_table.setItem(r, c, item)
        total = len(rows)
        avail_count = sum(1 for d in rows if d.get("availability") == "Available")
        self._avail_summary.setText(
            f"{avail_count} of {total} doctor{'s' if total != 1 else ''} available today")
        self._apply_avail_filters()

    def _apply_avail_filters(self, _=None):
        """Filter the availability table by search text and status."""
        if not hasattr(self, '_avail_table'):
            return
        search = self._avail_search.text().lower()
        status = self._avail_status_filter.currentText()
        visible = 0
        for r in range(self._avail_table.rowCount()):
            row_text = " ".join(
                self._avail_table.item(r, c).text().lower()
                if self._avail_table.item(r, c) else ""
                for c in range(self._avail_table.columnCount()))
            status_cell = self._avail_table.item(r, 3)
            ok = (not search or search in row_text) and \
                 (status == "All" or (status_cell and status_cell.text() == status))
            self._avail_table.setRowHidden(r, not ok)
            if ok: visible += 1

    # ── CRUD ───────────────────────────────────────────────────────
    def _on_new(self):
        # For walk-in: show only doctors available today
        if self._backend and hasattr(self._backend, 'get_doctors_available_today'):
            doctors = self._backend.get_doctors_available_today() or []
            if not doctors:
                doctors = self._backend.get_doctors() or []
        else:
            doctors = self._backend.get_doctors() if self._backend else []
        services = self._backend.get_services_list() if self._backend else []
        dlg = AppointmentDialog(self, title="New Walk-in",
                                patients=self._patients,
                                doctors=doctors, services=services, backend=self._backend,
                                user_email=self._user_email, user_role=self._role)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["patient_name"].strip() or d["patient_id"] is None:
                QMessageBox.warning(self, "Validation", "Please select a patient from the list."); return
            if self._backend:
                ok = self._backend.add_appointment(d)
                if not ok:
                    QMessageBox.warning(self, "Error", "Failed to save appointment."); return
                QMessageBox.information(self, "Success", f"Appointment for '{d['patient_name']}' created.")
            self._load_from_db(); self._refresh_table()

    def _on_edit(self, appt: dict):
        data = {
            "patient": appt.get("patient_name",""), "doctor": appt.get("doctor_name",""),
            "date": str(appt.get("appointment_date","")), "time": str(appt.get("appointment_time","")),
            "purpose": appt.get("service_name",""), "status": appt.get("status",""),
            "notes": appt.get("notes","") or "",
            "cancellation_reason": appt.get("cancellation_reason","") or "",
            "reschedule_reason": appt.get("reschedule_reason","") or "",
        }
        doctors = self._backend.get_doctors() if self._backend else []
        services = self._backend.get_services_list() if self._backend else []
        dlg = AppointmentDialog(self, title="Edit Appointment", data=data,
                                patients=self._patients,
                                doctors=doctors, services=services, backend=self._backend)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["patient_name"].strip() or d["patient_id"] is None:
                QMessageBox.warning(self, "Validation", "Please select a patient from the list."); return
            appt_id = appt.get("appointment_id")
            if self._backend and appt_id:
                ok = self._backend.update_appointment(appt_id, d)
                if not ok:
                    QMessageBox.warning(self, "Error", "Failed to update appointment."); return
            self._load_from_db(); self._refresh_table()
            QMessageBox.information(self, "Success", f"Appointment for '{d['patient_name']}' updated.")

    def _on_view(self, appt: dict):
        time_str = str(appt.get("appointment_time", ""))
        try:
            t = datetime.strptime(time_str, "%H:%M:%S"); time_display = t.strftime("%I:%M %p")
        except Exception: time_display = time_str
        info = (
            f"Patient:  {appt.get('patient_name', '')}"
            f"\nDoctor:   {appt.get('doctor_name', '')}"
            f"\nDate:     {_pretty_date(str(appt.get('appointment_date', '')))}"
            f"\nTime:     {time_display}"
            f"\nService:  {appt.get('service_name', '')}"
            f"\nStatus:   {appt.get('status', '')}"
        )
        notes = appt.get("notes", "") or ""
        if notes:
            info += f"\n\nNotes:\n{notes}"
        cancel_reason = appt.get("cancellation_reason", "") or ""
        if cancel_reason:
            info += f"\n\nCancellation Reason:\n{cancel_reason}"
        QMessageBox.information(self, "Appointment Details", info)

    def _on_confirm(self, appt: dict):
        appt_id = appt.get("appointment_id")
        patient = appt.get("patient_name", "")
        if not self._backend or not appt_id:
            return
        reply = QMessageBox.question(
            self, "Confirm Appointment",
            f"Confirm appointment for {patient}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            ok = self._backend.exec(
                "UPDATE appointments SET status='Confirmed' WHERE appointment_id=%s",
                (appt_id,))
            if ok:
                self._backend.log_activity("Edited", "Appointment",
                    f"Confirmed appt #{appt_id} for {patient}")
                self._load_from_db(); self._refresh_table()
                QMessageBox.information(self, "Confirmed",
                    f"Appointment for {patient} confirmed.\n"
                    "It will appear in the Clinical Queue on the appointment date.")

    def _on_cancel(self, appt: dict):
        appt_id = appt.get("appointment_id")
        patient = appt.get("patient_name", "")
        if not self._backend or not appt_id:
            return
        reason, ok = QInputDialog.getMultiLineText(
            self, "Cancel Appointment",
            f"Reason for cancelling {patient}'s appointment:", "")
        if not ok:
            return
        self._backend.exec(
            "UPDATE appointments SET status='Cancelled', cancellation_reason=%s WHERE appointment_id=%s",
            (reason.strip(), appt_id))
        self._backend.log_activity("Edited", "Appointment",
            f"Cancelled appt #{appt_id} for {patient}")
        self._load_from_db(); self._refresh_table()
        QMessageBox.information(self, "Cancelled",
            f"Appointment for {patient} has been cancelled.")
