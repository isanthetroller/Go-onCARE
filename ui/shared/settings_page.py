# Settings page - db cleanup, user accounts, password change

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QComboBox,
    QLineEdit, QDoubleSpinBox, QDialog, QFormLayout, QInputDialog,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor
from ui.styles import (
    configure_table, make_page_layout, finish_page, make_banner, make_card,
    make_read_only_table, make_interactive_table, style_dialog_btns,
)


class SettingsPage(QWidget):
    """Admin settings + self-service profile for all roles."""

    def __init__(self, backend=None, user_email: str = "", role: str = "Admin"):
        super().__init__()
        self._backend = backend
        self._user_email = user_email
        self._role = role
        self._build()
        # Auto-refresh data every 10 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_counts)
        self._refresh_timer.start(300_000)

    # ── UI ─────────────────────────────────────────────────────────────
    def _build(self):
        scroll, lay = make_page_layout()

        # ── Banner ─────────────────────────────────────────────────
        lay.addWidget(make_banner(
            "Settings", "Database maintenance, user accounts, and profile",
        ))

        # ── Profile Card ──────────────────────────────────────────────────
        lay.addWidget(self._section("Profile"))
        prof_card = self._card()
        pl = QVBoxLayout(prof_card); pl.setContentsMargins(20, 16, 20, 16); pl.setSpacing(14)

        # Change password
        pw_lbl = QLabel("Change Password")
        pw_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        pl.addWidget(pw_lbl)
        pw_row = QHBoxLayout(); pw_row.setSpacing(10)
        self._cur_pw = QLineEdit(); self._cur_pw.setPlaceholderText("Current password")
        self._cur_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._cur_pw.setObjectName("formInput"); self._cur_pw.setMinimumHeight(38)
        pw_row.addWidget(self._cur_pw)
        self._new_pw = QLineEdit(); self._new_pw.setPlaceholderText("New password")
        self._new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._new_pw.setObjectName("formInput"); self._new_pw.setMinimumHeight(38)
        pw_row.addWidget(self._new_pw)
        self._confirm_pw = QLineEdit(); self._confirm_pw.setPlaceholderText("Confirm new password")
        self._confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_pw.setObjectName("formInput"); self._confirm_pw.setMinimumHeight(38)
        pw_row.addWidget(self._confirm_pw)
        pw_btn = QPushButton("Update Password"); pw_btn.setObjectName("cleanupBtn")
        pw_btn.setMinimumHeight(38); pw_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pw_btn.clicked.connect(self._change_password)
        pw_row.addWidget(pw_btn)
        pl.addLayout(pw_row)
        lay.addWidget(prof_card)

        # ── Admin-only sections below ─────────────────────────────
        if self._role != "Admin":
            lay.addStretch()
            finish_page(self, scroll)
            self.counts_table = None
            return

        # ── Discount Management ────────────────────────────────────
        lay.addWidget(self._section("Discount Management"))
        disc_card = self._card()
        dl = QVBoxLayout(disc_card); dl.setContentsMargins(20, 16, 20, 16); dl.setSpacing(12)

        disc_info = QLabel(
            "Manage discount categories applied to patients (e.g. PWD, Senior Citizen).\n"
            "Based on Philippine law: RA 9994 (Senior Citizen 20%) and RA 10754 (PWD 20%)."
        )
        disc_info.setStyleSheet("font-size: 12px; color: #7F8C8D;")
        disc_info.setWordWrap(True)
        dl.addWidget(disc_info)

        self._disc_table = make_interactive_table(
            ["Type Name", "Discount %", "Legal Basis", "Requires ID", "Active"],
            min_h=160, max_h=220, row_h=40)
        dl.addWidget(self._disc_table)

        disc_btn_row = QHBoxLayout(); disc_btn_row.setSpacing(8)
        add_disc_btn = self._action_btn("Add Discount Type")
        add_disc_btn.clicked.connect(self._on_add_discount)
        disc_btn_row.addWidget(add_disc_btn)
        edit_disc_btn = self._action_btn("Edit Selected")
        edit_disc_btn.clicked.connect(self._on_edit_discount)
        disc_btn_row.addWidget(edit_disc_btn)
        del_disc_btn = self._action_btn("Delete Selected", danger=True)
        del_disc_btn.clicked.connect(self._on_delete_discount)
        disc_btn_row.addWidget(del_disc_btn)
        disc_btn_row.addStretch()
        dl.addLayout(disc_btn_row)

        lay.addWidget(disc_card)

        self._discount_ids: list[int] = []
        self.get_discount_types()

        # ── Tax & Deduction Settings ───────────────────────────────
        lay.addWidget(self._section("Tax && Deduction Rates"))
        tax_card = self._card()
        tl = QVBoxLayout(tax_card); tl.setContentsMargins(20, 16, 20, 16); tl.setSpacing(12)

        tax_info = QLabel(
            "Configure automatic payroll deductions applied to every paycheck request.\n"
            "Philippine statutory rates (2025):\n"
            "• SSS Employee Share: 4.5% of salary (RA 11199, 2025 contribution schedule)\n"
            "• PhilHealth Employee Share: 2.5% of salary (5% premium split 50/50 – "
            "PhilHealth Circular 2024-0009)\n"
            "• Hospital Share: custom percentage retained by the hospital for operations"
        )
        tax_info.setStyleSheet("font-size: 12px; color: #7F8C8D;")
        tax_info.setWordWrap(True)
        tl.addWidget(tax_info)

        # SSS
        sss_row = QHBoxLayout(); sss_row.setSpacing(10)
        sss_lbl = QLabel("SSS Employee Rate (%):"); sss_lbl.setMinimumWidth(200)
        sss_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        sss_row.addWidget(sss_lbl)
        self._sss_spin = QDoubleSpinBox()
        self._sss_spin.setRange(0.0, 50.0); self._sss_spin.setDecimals(3)
        self._sss_spin.setSingleStep(0.5); self._sss_spin.setSuffix(" %")
        self._sss_spin.setObjectName("formCombo"); self._sss_spin.setMinimumHeight(38)
        sss_row.addWidget(self._sss_spin)
        sss_row.addStretch()
        tl.addLayout(sss_row)

        # PhilHealth
        phil_row = QHBoxLayout(); phil_row.setSpacing(10)
        phil_lbl = QLabel("PhilHealth Employee Rate (%):"); phil_lbl.setMinimumWidth(200)
        phil_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        phil_row.addWidget(phil_lbl)
        self._phil_spin = QDoubleSpinBox()
        self._phil_spin.setRange(0.0, 50.0); self._phil_spin.setDecimals(3)
        self._phil_spin.setSingleStep(0.5); self._phil_spin.setSuffix(" %")
        self._phil_spin.setObjectName("formCombo"); self._phil_spin.setMinimumHeight(38)
        phil_row.addWidget(self._phil_spin)
        phil_row.addStretch()
        tl.addLayout(phil_row)

        # Hospital Share
        hosp_row = QHBoxLayout(); hosp_row.setSpacing(10)
        hosp_lbl = QLabel("Hospital Share Rate (%):"); hosp_lbl.setMinimumWidth(200)
        hosp_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
        hosp_row.addWidget(hosp_lbl)
        self._hosp_spin = QDoubleSpinBox()
        self._hosp_spin.setRange(0.0, 50.0); self._hosp_spin.setDecimals(3)
        self._hosp_spin.setSingleStep(1.0); self._hosp_spin.setSuffix(" %")
        self._hosp_spin.setObjectName("formCombo"); self._hosp_spin.setMinimumHeight(38)
        hosp_row.addWidget(self._hosp_spin)
        hosp_row.addStretch()
        tl.addLayout(hosp_row)

        tax_btn_row = QHBoxLayout(); tax_btn_row.setSpacing(8)
        save_tax_btn = self._action_btn("Save Tax Rates")
        save_tax_btn.clicked.connect(self._save_tax_settings)
        tax_btn_row.addWidget(save_tax_btn)
        reset_tax_btn = self._action_btn("Reset to Defaults")
        reset_tax_btn.clicked.connect(self._reset_tax_defaults)
        tax_btn_row.addWidget(reset_tax_btn)
        tax_btn_row.addStretch()
        tl.addLayout(tax_btn_row)

        lay.addWidget(tax_card)
        self._load_tax_settings()

        # ── Department Management ──────────────────────────────────
        lay.addWidget(self._section("Department Management"))
        dept_card = self._card()
        dptl = QVBoxLayout(dept_card); dptl.setContentsMargins(20, 16, 20, 16); dptl.setSpacing(12)

        dept_info = QLabel(
            "Manage hospital departments. Departments with assigned employees cannot be deleted."
        )
        dept_info.setStyleSheet("font-size: 12px; color: #7F8C8D;")
        dept_info.setWordWrap(True)
        dptl.addWidget(dept_info)

        self._dept_table = make_interactive_table(
            ["Department Name", "Employees"], min_h=160, max_h=260, row_h=40)
        dptl.addWidget(self._dept_table)

        dept_btn_row = QHBoxLayout(); dept_btn_row.setSpacing(8)
        add_dept_btn = self._action_btn("Add Department")
        add_dept_btn.clicked.connect(self._on_add_department)
        dept_btn_row.addWidget(add_dept_btn)
        del_dept_btn = self._action_btn("Delete Selected", danger=True)
        del_dept_btn.clicked.connect(self._on_delete_department)
        dept_btn_row.addWidget(del_dept_btn)
        dept_btn_row.addStretch()
        dptl.addLayout(dept_btn_row)

        lay.addWidget(dept_card)
        self._dept_ids: list[int] = []
        self._load_departments()

        # ── Database Overview ──────────────────────────────────────
        lay.addWidget(self._section("Database Overview"))
        self.counts_table = make_read_only_table(
            ["Table", "Row Count"], min_h=300, row_h=40)
        lay.addWidget(self.counts_table)

        # ── Data maintenance ────────────────────────────────────────
        lay.addWidget(self._section("Data Maintenance"))

        # 1) Old completed appointments
        card1 = self._card(); c1 = QHBoxLayout(card1)
        c1.setContentsMargins(20, 16, 20, 16); c1.setSpacing(16)
        lbl_col1 = QVBoxLayout(); lbl_col1.setSpacing(2)
        lbl_col1.addWidget(self._cleanup_title("Archive Old Appointments"))
        lbl_col1.addWidget(self._cleanup_hint(
            "Permanently remove completed appointments older than the selected date.\n"
            "This helps keep your records tidy without affecting recent data."))
        c1.addLayout(lbl_col1, 1)
        from ui.shared.modern_calendar import apply_modern_calendar
        self.cutoff_date = QDateEdit(); apply_modern_calendar(self.cutoff_date)
        self.cutoff_date.setDate(QDate.currentDate().addMonths(-3))
        self.cutoff_date.setObjectName("formCombo"); self.cutoff_date.setMinimumHeight(38)
        self.cutoff_date.setDisplayFormat("M/d/yyyy")
        self.cutoff_date.setToolTip("Only appointments completed before this date will be removed")
        c1.addWidget(self.cutoff_date)
        btn1 = self._action_btn("Remove Old Data"); btn1.clicked.connect(self._cleanup_completed)
        c1.addWidget(btn1)
        lay.addWidget(card1)

        # 2) Cancelled appointments
        card2 = self._card(); c2 = QHBoxLayout(card2)
        c2.setContentsMargins(20, 16, 20, 16); c2.setSpacing(16)
        lbl_col2 = QVBoxLayout(); lbl_col2.setSpacing(2)
        lbl_col2.addWidget(self._cleanup_title("Clear Cancelled Appointments"))
        lbl_col2.addWidget(self._cleanup_hint(
            "Remove all appointments that were cancelled, along with any\n"
            "related billing or queue records. Active appointments are not affected."))
        c2.addLayout(lbl_col2, 1)
        btn2 = self._action_btn("Clear Cancelled"); btn2.clicked.connect(self._cleanup_cancelled)
        c2.addWidget(btn2)
        lay.addWidget(card2)

        # 3) Inactive patients
        card3 = self._card(); c3 = QHBoxLayout(card3)
        c3.setContentsMargins(20, 16, 20, 16); c3.setSpacing(16)
        lbl_col3 = QVBoxLayout(); lbl_col3.setSpacing(2)
        lbl_col3.addWidget(self._cleanup_title("Remove Inactive Patients"))
        lbl_col3.addWidget(self._cleanup_hint(
            "Delete patients marked as \"Inactive\" and all their associated records\n"
            "(appointments, invoices, conditions). Active patients are never touched."))
        c3.addLayout(lbl_col3, 1)
        btn3 = self._action_btn("Remove Inactive"); btn3.clicked.connect(self._cleanup_inactive)
        c3.addWidget(btn3)
        lay.addWidget(card3)

        # 4) Reset visit queue
        card4 = self._card(); c4 = QHBoxLayout(card4)
        c4.setContentsMargins(20, 16, 20, 16); c4.setSpacing(16)
        lbl_col4 = QVBoxLayout(); lbl_col4.setSpacing(2)
        lbl_col4.addWidget(self._cleanup_title("Reset Today's Visit Queue"))
        lbl_col4.addWidget(self._cleanup_hint(
            "Clear the patient waiting queue. Use this if the queue gets stuck\n"
            "or at the start of a new day to begin with a clean slate."))
        c4.addLayout(lbl_col4, 1)
        btn4 = self._action_btn("Reset Queue", danger=True); btn4.clicked.connect(self._reset_queue)
        c4.addWidget(btn4)
        lay.addWidget(card4)

        lay.addStretch()
        finish_page(self, scroll)
        self._refresh_counts()

    # ── Helpers ────────────────────────────────────────────────────────
    @staticmethod
    def _section(text: str) -> QLabel:
        l = QLabel(text); l.setObjectName("sectionHeader"); return l

    @staticmethod
    def _card() -> QFrame:
        return make_card()

    @staticmethod
    def _cleanup_lbl(text: str) -> QLabel:
        l = QLabel(text); l.setObjectName("cleanupLabel"); return l

    @staticmethod
    def _cleanup_title(text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet("font-size: 14px; font-weight: bold; color: #2C3E50;")
        return l

    @staticmethod
    def _cleanup_hint(text: str) -> QLabel:
        l = QLabel(text)
        l.setWordWrap(True)
        l.setStyleSheet("font-size: 12px; color: #7F8C8D; line-height: 1.4;")
        return l

    @staticmethod
    def _action_btn(label: str, *, danger: bool = False) -> QPushButton:
        btn = QPushButton(label); btn.setMinimumHeight(38); btn.setMinimumWidth(150)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setObjectName("truncateBtn" if danger else "cleanupBtn"); return btn

    # ── Slots ──────────────────────────────────────────────────────────
    def _change_password(self):
        cur = self._cur_pw.text().strip()
        new = self._new_pw.text().strip()
        confirm = self._confirm_pw.text().strip()
        if not cur:
            return QMessageBox.warning(self, "Validation", "Enter your current password.")
        if not new:
            return QMessageBox.warning(self, "Validation", "Enter a new password.")
        if len(new) < 4:
            return QMessageBox.warning(self, "Validation", "New password must be at least 4 characters.")
        if new != confirm:
            return QMessageBox.warning(self, "Validation", "New passwords do not match.")
        if not self._backend:
            return
        ok, msg = self._backend.update_own_password(self._user_email, cur, new)
        if ok:
            QMessageBox.information(self, "Success", msg)
            self._cur_pw.clear(); self._new_pw.clear(); self._confirm_pw.clear()
        else:
            QMessageBox.warning(self, "Error", msg)

    def _refresh_counts(self):
        if not self.isVisible() or not self._backend or not self.counts_table:
            return
        counts = self._backend.get_table_counts()
        self.counts_table.setRowCount(len(counts))
        for r, (tbl, cnt) in enumerate(counts):
            self.counts_table.setItem(r, 0, QTableWidgetItem(tbl))
            item = QTableWidgetItem(str(cnt))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.counts_table.setItem(r, 1, item)

    def _cleanup_completed(self):
        cutoff = self.cutoff_date.date().toString("yyyy-MM-dd")
        display_date = self.cutoff_date.date().toString("MMMM d, yyyy")
        reply = QMessageBox.question(
            self, "Archive Old Appointments",
            f"This will permanently remove all completed appointments "
            f"from before {display_date}, along with their billing and queue records.\n\n"
            f"Recent and upcoming appointments will not be affected.\n\n"
            f"Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            n = self._backend.cleanup_completed_appointments(cutoff)
            QMessageBox.information(self, "Done",
                f"Successfully removed {n} old appointment(s)." if n
                else "No old completed appointments found to remove.")
            self._refresh_counts()

    def _cleanup_cancelled(self):
        reply = QMessageBox.question(
            self, "Clear Cancelled Appointments",
            "This will permanently remove all cancelled appointments "
            "and their related records.\n\n"
            "Active, confirmed, and completed appointments will not be affected.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            n = self._backend.cleanup_cancelled_appointments()
            QMessageBox.information(self, "Done",
                f"Successfully removed {n} cancelled appointment(s)." if n
                else "No cancelled appointments found to remove.")
            self._refresh_counts()

    def _cleanup_inactive(self):
        reply = QMessageBox.question(
            self, "Remove Inactive Patients",
            "This will permanently remove all patients marked as \"Inactive\" "
            "and all of their associated records "
            "(appointments, invoices, medical conditions, and queue entries).\n\n"
            "Active patients will not be affected.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            n = self._backend.cleanup_inactive_patients()
            QMessageBox.information(self, "Done",
                f"Successfully removed {n} inactive patient(s) and their records." if n
                else "No inactive patients found to remove.")
            self._refresh_counts()

    def _reset_queue(self):
        reply = QMessageBox.warning(
            self, "Reset Visit Queue",
            "This will clear the entire patient visit queue.\n\n"
            "Use this if the queue is stuck or to start fresh for the day.\n"
            "Appointments themselves will not be deleted.\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok = self._backend.truncate_table("queue_entries")
            if ok:
                QMessageBox.information(self, "Done",
                    "The visit queue has been cleared. "
                    "New patients can now be queued as usual.")
            else:
                QMessageBox.critical(self, "Error",
                    "Could not reset the visit queue. Please try again.")
            self._refresh_counts()

    # ── Discount Management ────────────────────────────────────────────
    def _load_discount_types(self):
        self._disc_table.setRowCount(0)
        self._discount_ids.clear()
        if not self._backend:
            return
        types = self._backend.get_discount_types() or []
        for dt in types:
            r = self._disc_table.rowCount()
            self._disc_table.insertRow(r)
            self._discount_ids.append(dt["discount_id"])
            self._disc_table.setItem(r, 0, QTableWidgetItem(dt["type_name"]))
            pct_item = QTableWidgetItem(f"{float(dt['discount_percent']):.1f}%")
            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._disc_table.setItem(r, 1, pct_item)
            self._disc_table.setItem(r, 2, QTableWidgetItem(dt.get("legal_basis", "") or ""))
            req_id_item = QTableWidgetItem("Yes" if dt.get("requires_id_proof") else "No")
            req_id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if dt.get("requires_id_proof"):
                req_id_item.setForeground(QColor("#F39C12"))
            self._disc_table.setItem(r, 3, req_id_item)
            active_item = QTableWidgetItem("Yes" if dt.get("is_active") else "No")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not dt.get("is_active"):
                active_item.setForeground(QColor("#D9534F"))
            else:
                active_item.setForeground(QColor("#5CB85C"))
            self._disc_table.setItem(r, 4, active_item)

    def _on_add_discount(self):
        dlg = _DiscountTypeDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Type name is required.")
                return
            if self._backend:
                ok = self._backend.add_discount_type(d["name"], d["percent"], d["legal_basis"], 1 if d["requires_id_proof"] else 0)
                self._load_discount_types()
                if ok:
                    QMessageBox.information(self, "Success", f"Discount type '{d['name']}' added.")
                else:
                    QMessageBox.warning(self, "Error",
                        f"Failed to add '{d['name']}'.\n\n"
                        "A discount type with that name may already exist.")

    def _on_edit_discount(self):
        row = self._disc_table.currentRow()
        if row < 0 or row >= len(self._discount_ids):
            QMessageBox.warning(self, "Selection", "Select a discount type to edit.")
            return
        did = self._discount_ids[row]
        current = {
            "name": self._disc_table.item(row, 0).text(),
            "percent": float(self._disc_table.item(row, 1).text().replace("%", "")),
            "legal_basis": self._disc_table.item(row, 2).text(),
            "requires_id_proof": self._disc_table.item(row, 3).text() == "Yes",
            "is_active": self._disc_table.item(row, 4).text() == "Yes",
        }
        dlg = _DiscountTypeDialog(self, data=current)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Type name is required.")
                return
            if self._backend:
                ok = self._backend.update_discount_type(
                    did, d["name"], d["percent"], d["legal_basis"], 1 if d["requires_id_proof"] else 0, 1 if d["is_active"] else 0)
                self._load_discount_types()
                if ok:
                    QMessageBox.information(self, "Success", f"Discount type '{d['name']}' updated.")
                else:
                    QMessageBox.warning(self, "Error",
                        f"Failed to update '{d['name']}'.\nA discount type with that name may already exist.")

    def _on_delete_discount(self):
        row = self._disc_table.currentRow()
        if row < 0 or row >= len(self._discount_ids):
            QMessageBox.warning(self, "Selection", "Select a discount type to delete.")
            return
        name = self._disc_table.item(row, 0).text()
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete discount type '{name}'?\n\n"
            "Patients using this type will have their discount removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            did = self._discount_ids[row]
            if self._backend:
                ok = self._backend.delete_discount_type(did)
                self._load_discount_types()
                if ok:
                    QMessageBox.information(self, "Done", f"Discount type '{name}' deleted.")
                else:
                    QMessageBox.warning(self, "Error", f"Failed to delete '{name}'.")

    # ── Tax & Deduction Settings ───────────────────────────────────────
    def _load_tax_settings(self):
        if not self._backend or not hasattr(self, "_sss_spin"):
            return
        rates = self._backend.get_tax_rates() or {}
        self._sss_spin.setValue(rates.get("sss_rate", 4.5))
        self._phil_spin.setValue(rates.get("philhealth_rate", 2.5))
        self._hosp_spin.setValue(rates.get("hospital_share_rate", 10.0))

    def _save_tax_settings(self):
        if not self._backend:
            return
        sss = self._sss_spin.value()
        phil = self._phil_spin.value()
        hosp = self._hosp_spin.value()
        total = sss + phil + hosp
        if total > 80:
            QMessageBox.warning(self, "Validation",
                                f"Total deduction is {total:.1f}% — this is unreasonably high.\n"
                                "Please check your rates.")
            return
        reply = QMessageBox.question(
            self, "Confirm Tax Rate Update",
            f"Save these deduction rates?\n\n"
            f"  SSS Employee Share:  {sss:.3f}%\n"
            f"  PhilHealth Share:    {phil:.3f}%\n"
            f"  Hospital Share:      {hosp:.3f}%\n"
            f"  ─────────────────\n"
            f"  Total Deduction:     {total:.3f}%\n\n"
            "This will apply to all future paycheck requests.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._backend.update_tax_setting("sss_rate", sss)
        self._backend.update_tax_setting("philhealth_rate", phil)
        self._backend.update_tax_setting("hospital_share_rate", hosp)
        QMessageBox.information(self, "Saved", "Tax deduction rates updated successfully.")

    def _reset_tax_defaults(self):
        """Reset to Philippine statutory defaults (2025)."""
        reply = QMessageBox.question(
            self, "Reset to Defaults",
            "Reset to Philippine statutory defaults?\n\n"
            "  SSS:        4.500%   (RA 11199)\n"
            "  PhilHealth: 2.500%   (Circular 2024-0009)\n"
            "  Hospital:  10.000%",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._sss_spin.setValue(4.5)
            self._phil_spin.setValue(2.5)
            self._hosp_spin.setValue(10.0)
            self._save_tax_settings()

    # ── Department Management ──────────────────────────────────────
    def _load_departments(self):
        """Populate the department table from the database."""
        if not self._backend:
            return
        depts = self._backend.get_all_departments() if hasattr(self._backend, 'get_all_departments') else []
        self._dept_ids = []
        self._dept_table.setRowCount(len(depts))
        for r, d in enumerate(depts):
            dept_id = d.get("department_id", 0)
            self._dept_ids.append(dept_id)
            name_item = QTableWidgetItem(d.get("department_name", ""))
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._dept_table.setItem(r, 0, name_item)
            # Employee count
            count = 0
            if hasattr(self._backend, 'get_department_employee_count'):
                count = self._backend.get_department_employee_count(dept_id) or 0
            count_item = QTableWidgetItem(str(count))
            count_item.setFlags(count_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._dept_table.setItem(r, 1, count_item)

    def _on_add_department(self):
        name, ok = QInputDialog.getText(self, "Add Department", "Department name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if not self._backend or not hasattr(self._backend, 'add_department'):
            return
        result = self._backend.add_department(name)
        if result is True:
            QMessageBox.information(self, "Success", f"Department '{name}' created.")
            self._load_departments()
        else:
            QMessageBox.warning(self, "Error",
                                f"Could not create department.\n{result}" if isinstance(result, str)
                                else "Department may already exist.")

    def _on_delete_department(self):
        row = self._dept_table.currentRow()
        if row < 0 or row >= len(self._dept_ids):
            QMessageBox.information(self, "Delete", "Select a department first.")
            return
        dept_id = self._dept_ids[row]
        dept_name = self._dept_table.item(row, 0).text()
        emp_count = 0
        if hasattr(self._backend, 'get_department_employee_count'):
            emp_count = self._backend.get_department_employee_count(dept_id) or 0

        # ── First confirmation ──────────────────────────────────
        msg1 = (f"Are you sure you want to delete the department '{dept_name}'?\n\n"
                f"This department currently has {emp_count} employee(s).")
        reply1 = QMessageBox.question(
            self, "Confirm Deletion", msg1,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply1 != QMessageBox.StandardButton.Yes:
            return

        # ── Second confirmation (final) ─────────────────────────
        msg2 = (f"⚠  FINAL CONFIRMATION  ⚠\n\n"
                f"Deleting '{dept_name}' is permanent and cannot be undone.\n"
                f"Employees in this department MUST be reassigned first.\n\n"
                f"Proceed with deletion?")
        reply2 = QMessageBox.warning(
            self, "Final Confirmation – Delete Department", msg2,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply2 != QMessageBox.StandardButton.Yes:
            return

        if not self._backend or not hasattr(self._backend, 'delete_department'):
            return
        result = self._backend.delete_department(dept_id)
        if result is True:
            QMessageBox.information(self, "Deleted", f"Department '{dept_name}' has been removed.")
            self._load_departments()
        else:
            QMessageBox.warning(self, "Cannot Delete",
                                f"Cannot delete '{dept_name}'.\n\n"
                                "Reassign all employees from this department first."
                                if emp_count > 0 else
                                f"Deletion failed: {result}" if isinstance(result, str)
                                else "Deletion failed.")

# ══════════════════════════════════════════════════════════════════════
#  Discount Type Add/Edit Dialog
# ══════════════════════════════════════════════════════════════════════
class _DiscountTypeDialog(QDialog):
    """Dialog to add or edit a discount type."""

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Discount Type" if data else "Add Discount Type")
        self.setMinimumWidth(480)

        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.name_edit = QLineEdit()
        self.name_edit.setObjectName("formInput")
        self.name_edit.setMinimumHeight(38)
        self.name_edit.setPlaceholderText("e.g. Senior Citizen, PWD, Pregnant")
        self.name_edit.setMaxLength(100)

        self.percent_spin = QDoubleSpinBox()
        self.percent_spin.setMinimum(0)
        self.percent_spin.setMaximum(100)
        self.percent_spin.setDecimals(2)
        self.percent_spin.setSuffix(" %")
        self.percent_spin.setMinimumHeight(38)

        self.legal_edit = QLineEdit()
        self.legal_edit.setObjectName("formInput")
        self.legal_edit.setMinimumHeight(38)
        self.legal_edit.setPlaceholderText("e.g. RA 9994 – Expanded Senior Citizens Act")
        self.legal_edit.setMaxLength(200)

        self.req_id_check = QCheckBox("Requires ID Proof")
        self.req_id_check.setChecked(False)

        self.active_check = QCheckBox("Active")
        self.active_check.setChecked(True)

        form.addRow("Type Name", self.name_edit)
        form.addRow("Discount %", self.percent_spin)
        form.addRow("Legal Basis", self.legal_edit)
        form.addRow("", self.req_id_check)
        form.addRow("", self.active_check)

        from PyQt6.QtWidgets import QDialogButtonBox
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        style_dialog_btns(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

        if data:
            self.name_edit.setText(data.get("name", ""))
            self.percent_spin.setValue(data.get("percent", 0))
            self.legal_edit.setText(data.get("legal_basis", ""))
            self.req_id_check.setChecked(data.get("requires_id_proof", False))
            self.active_check.setChecked(data.get("is_active", True))

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "percent": self.percent_spin.value(),
            "legal_basis": self.legal_edit.text().strip(),
            "requires_id_proof": self.req_id_check.isChecked(),
            "is_active": self.active_check.isChecked(),
        }
