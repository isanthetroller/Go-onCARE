"""Appointment Scheduling page – view and manage all appointments."""

from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QComboBox, QDialog, QMessageBox, QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from ui.styles import configure_table, make_table_btn
from ui.shared.appointment_dialog import (
    AppointmentDialog, _pretty_date, _relative_label,
)


# ══════════════════════════════════════════════════════════════════════
#  Appointments Page
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

    def __init__(self, backend=None, role: str = "Admin", user_email: str = ""):
        super().__init__()
        self._backend = backend
        self._role = role
        self._user_email = user_email
        self._patient_names: list[str] = []
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

    def _load_from_db(self):
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
            if hasattr(t, "total_seconds"):
                total = int(t.total_seconds()); h, m = divmod(total // 60, 60)
                appt["appointment_time"] = f"{h:02d}:{m:02d}:00"
            elif hasattr(t, "strftime"): appt["appointment_time"] = t.strftime("%H:%M:%S")
            elif t is not None: appt["appointment_time"] = str(t)
        self._update_doctor_filter()

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
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget(); inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner); lay.setSpacing(16); lay.setContentsMargins(28,28,28,28)

        # Banner
        banner = QFrame(); banner.setObjectName("pageBanner"); banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(20); shadow.setOffset(0,4); shadow.setColor(QColor(0,0,0,15))
        banner.setGraphicsEffect(shadow)
        banner_lay = QHBoxLayout(banner); banner_lay.setContentsMargins(32,20,32,20)
        tc = QVBoxLayout(); tc.setSpacing(4)
        title = QLabel("Appointment Scheduling"); title.setObjectName("bannerTitle")
        sub = QLabel("View and manage all doctor-patient appointments"); sub.setObjectName("bannerSubtitle")
        tc.addWidget(title); tc.addWidget(sub)
        banner_lay.addLayout(tc); banner_lay.addStretch()
        if self._role not in ("Cashier", "Doctor"):
            add_btn = QPushButton("\uff0b  New Appointment"); add_btn.setObjectName("bannerBtn")
            add_btn.setMinimumHeight(42); add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.clicked.connect(self._on_new)
            banner_lay.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(banner)

        # Quick-filter tabs
        tab_row = QHBoxLayout(); tab_row.setSpacing(8)
        for label in ("Today", "Tomorrow", "This Week", "This Month", "All"):
            btn = QPushButton(label); btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.setMinimumHeight(38)
            btn.clicked.connect(lambda checked, l=label: self._switch_tab(l))
            self._tab_buttons[label] = btn; tab_row.addWidget(btn)
        tab_row.addStretch(); lay.addLayout(tab_row)

        self._summary_label = QLabel()
        self._summary_label.setStyleSheet("font-size:13px;color:#7F8C8D;padding:2px 0;")
        lay.addWidget(self._summary_label)

        # Filter bar
        bar = QHBoxLayout(); bar.setSpacing(10)
        self.search = QLineEdit(); self.search.setObjectName("searchBar")
        self.search.setPlaceholderText("🔍  Search by patient, doctor, or service…")
        self.search.setMinimumHeight(42); self.search.textChanged.connect(self._apply_filters)
        bar.addWidget(self.search)
        self.doc_filter = QComboBox(); self.doc_filter.setObjectName("formCombo")
        self.doc_filter.addItems(["All Doctors"]); self.doc_filter.setMinimumHeight(42); self.doc_filter.setMinimumWidth(150)
        self.doc_filter.currentTextChanged.connect(self._apply_filters); bar.addWidget(self.doc_filter)
        self.status_filter = QComboBox(); self.status_filter.setObjectName("formCombo")
        self.status_filter.addItems(["All Status","Pending","Confirmed","Cancelled","Completed"])
        self.status_filter.setMinimumHeight(42); self.status_filter.setMinimumWidth(140)
        self.status_filter.currentTextChanged.connect(self._apply_filters); bar.addWidget(self.status_filter)

        lay.addLayout(bar)

        # Table – added Notes column
        cols = ["Day & Date", "Time", "Patient", "Doctor", "Service", "Notes", "Status"]
        if self._role != "Doctor": cols.append("Billing")
        if self._role != "Cashier": cols.append("Actions")
        self.table = QTableWidget(0, len(cols)); self.table.setHorizontalHeaderLabels(cols)
        hdr = self.table.horizontalHeader(); hdr.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive); self.table.setColumnWidth(0, 260)
        if self._role != "Cashier":
            hdr.setSectionResizeMode(len(cols)-1, QHeaderView.ResizeMode.Fixed); self.table.setColumnWidth(len(cols)-1, 80)
            hdr.setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus); self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(48); self.table.setMinimumHeight(420)
        configure_table(self.table); lay.addWidget(self.table)

        lay.addStretch(); scroll.setWidget(inner)
        wrapper = QVBoxLayout(self); wrapper.setContentsMargins(0,0,0,0); wrapper.addWidget(scroll)
        self._load_from_db(); self._switch_tab("Today")

    def _switch_tab(self, label: str):
        self._active_tab = label
        for name, btn in self._tab_buttons.items():
            btn.setStyleSheet(self._TAB_ACTIVE if name == label else self._TAB_INACTIVE)
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
                    color_map = {"Confirmed":"#5CB85C","Pending":"#E8B931","Cancelled":"#D9534F","Completed":"#388087"}
                    item.setForeground(QColor(color_map.get(val,"#2C3E50")))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                # Billing column color coding
                if self._role != "Doctor" and c == 7:
                    bill_colors = {"Paid":"#5CB85C","Partial":"#E8B931","Unpaid":"#D9534F","No Invoice":"#7F8C8D","Voided":"#7F8C8D"}
                    item.setForeground(QColor(bill_colors.get(val,"#2C3E50")))
                    item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.table.setItem(r, c, item)
            if self._role != "Cashier":
                act_w = QWidget(); act_lay = QHBoxLayout(act_w)
                act_lay.setContentsMargins(0,0,0,0); act_lay.setSpacing(6)
                edit_btn = make_table_btn("Edit"); edit_btn.setFixedWidth(52)
                edit_btn.clicked.connect(lambda checked, a=appt: self._on_edit(a))
                act_lay.addWidget(edit_btn)
                self.table.setCellWidget(r, col_count - 1, act_w)
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

    # ── CRUD ───────────────────────────────────────────────────────
    def _on_new(self):
        doctors = self._backend.get_doctors() if self._backend else []
        services = self._backend.get_services_list() if self._backend else []
        dlg = AppointmentDialog(self, title="New Appointment",
                                patient_names=self._patient_names,
                                doctors=doctors, services=services, backend=self._backend,
                                user_email=self._user_email, user_role=self._role)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["patient_name"].strip():
                QMessageBox.warning(self, "Validation", "Patient name is required."); return
            if self._backend:
                if d.get("recurring"):
                    cnt = self._backend.add_recurring_appointments(d, d["recur_freq"], d["recur_count"])
                    if cnt == 0:
                        QMessageBox.warning(self, "Error", "Failed to create recurring appointments."); return
                    QMessageBox.information(self, "Success", f"Created {cnt} recurring appointments.")
                else:
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
            "reminder_sent": appt.get("reminder_sent", 0),
        }
        doctors = self._backend.get_doctors() if self._backend else []
        services = self._backend.get_services_list() if self._backend else []
        dlg = AppointmentDialog(self, title="Edit Appointment", data=data,
                                patient_names=self._patient_names,
                                doctors=doctors, services=services, backend=self._backend)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["patient_name"].strip():
                QMessageBox.warning(self, "Validation", "Patient name is required."); return
            appt_id = appt.get("appointment_id")
            if self._backend and appt_id:
                ok = self._backend.update_appointment(appt_id, d)
                if not ok:
                    QMessageBox.warning(self, "Error", "Failed to update appointment."); return
            self._load_from_db(); self._refresh_table()
            QMessageBox.information(self, "Success", f"Appointment for '{d['patient_name']}' updated.")
