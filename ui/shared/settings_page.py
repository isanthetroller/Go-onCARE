# Settings page - db cleanup, dark mode, password change

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGraphicsDropShadowEffect, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QComboBox,
    QLineEdit, QCheckBox, QDoubleSpinBox, QDialog, QFormLayout,
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor
from ui.styles import configure_table, style_dialog_btns


class SettingsPage(QWidget):
    """Admin settings + self-service profile for all roles."""

    def __init__(self, backend=None, user_email: str = ""):
        super().__init__()
        self._backend = backend
        self._user_email = user_email
        self._build()
        # Auto-refresh data every 10 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_counts)
        self._refresh_timer.start(10_000)

    # ── UI ─────────────────────────────────────────────────────────────
    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget(); inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner); lay.setSpacing(20); lay.setContentsMargins(28, 28, 28, 28)

        # ── Banner ─────────────────────────────────────────────────
        banner = QFrame(); banner.setObjectName("pageBanner"); banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)
        bl = QHBoxLayout(banner); bl.setContentsMargins(32, 20, 32, 20)
        tc = QVBoxLayout(); tc.setSpacing(4)
        t = QLabel("Settings"); t.setObjectName("bannerTitle")
        s = QLabel("Database maintenance, appearance, and profile"); s.setObjectName("bannerSubtitle")
        tc.addWidget(t); tc.addWidget(s)
        bl.addLayout(tc); bl.addStretch()
        lay.addWidget(banner)

        # ── Profile & Appearance Card ──────────────────────────────
        lay.addWidget(self._section("Profile & Appearance"))
        prof_card = self._card()
        pl = QVBoxLayout(prof_card); pl.setContentsMargins(20, 16, 20, 16); pl.setSpacing(14)

        # Dark mode toggle
        dm_row = QHBoxLayout(); dm_row.setSpacing(12)
        dm_row.addWidget(QLabel("🌙  Dark Mode"))
        self._dark_toggle = QCheckBox("Enable dark theme")
        self._dark_toggle.setStyleSheet("font-size: 13px;")
        if self._backend and self._user_email:
            self._dark_toggle.setChecked(self._backend.get_dark_mode(self._user_email))
        self._dark_toggle.toggled.connect(self._on_dark_toggle)
        dm_row.addWidget(self._dark_toggle)
        dm_row.addStretch()
        pl.addLayout(dm_row)

        # Change password
        pw_lbl = QLabel("🔒  Change Password")
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

        self._disc_table = QTableWidget(0, 4)
        self._disc_table.setHorizontalHeaderLabels(["Type Name", "Discount %", "Legal Basis", "Active"])
        h = self._disc_table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._disc_table.verticalHeader().setVisible(False)
        self._disc_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._disc_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._disc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._disc_table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._disc_table.setAlternatingRowColors(True)
        self._disc_table.verticalHeader().setDefaultSectionSize(40)
        self._disc_table.setMinimumHeight(160)
        self._disc_table.setMaximumHeight(220)
        configure_table(self._disc_table)
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
        self._load_discount_types()

        # ── Database Overview ──────────────────────────────────────
        lay.addWidget(self._section("Database Overview"))
        self.counts_table = QTableWidget(0, 2)
        self.counts_table.setHorizontalHeaderLabels(["Table", "Row Count"])
        self.counts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.counts_table.verticalHeader().setVisible(False)
        self.counts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.counts_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.counts_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.counts_table.setAlternatingRowColors(True)
        self.counts_table.verticalHeader().setDefaultSectionSize(40)
        self.counts_table.setMinimumHeight(300)
        configure_table(self.counts_table)
        lay.addWidget(self.counts_table)

        # ── Cleanup actions ────────────────────────────────────────
        lay.addWidget(self._section("Cleanup Actions"))

        # 1) Completed appointments older than …
        card1 = self._card(); c1 = QHBoxLayout(card1)
        c1.setContentsMargins(20, 16, 20, 16); c1.setSpacing(12)
        c1.addWidget(self._cleanup_lbl("Remove completed appointments before:"))
        self.cutoff_date = QDateEdit(); self.cutoff_date.setCalendarPopup(True)
        self.cutoff_date.setDate(QDate.currentDate().addMonths(-3))
        self.cutoff_date.setObjectName("formCombo"); self.cutoff_date.setMinimumHeight(38)
        c1.addWidget(self.cutoff_date)
        btn1 = self._action_btn("Clean Up"); btn1.clicked.connect(self._cleanup_completed)
        c1.addWidget(btn1)
        lay.addWidget(card1)

        # 2) Cancelled appointments
        card2 = self._card(); c2 = QHBoxLayout(card2)
        c2.setContentsMargins(20, 16, 20, 16); c2.setSpacing(12)
        c2.addWidget(self._cleanup_lbl("Remove all cancelled appointments and linked records"), 1)
        btn2 = self._action_btn("Clean Up"); btn2.clicked.connect(self._cleanup_cancelled)
        c2.addWidget(btn2)
        lay.addWidget(card2)

        # 3) Inactive patients
        card3 = self._card(); c3 = QHBoxLayout(card3)
        c3.setContentsMargins(20, 16, 20, 16); c3.setSpacing(12)
        c3.addWidget(self._cleanup_lbl("Remove inactive patients and all their linked data"), 1)
        btn3 = self._action_btn("Clean Up"); btn3.clicked.connect(self._cleanup_inactive)
        c3.addWidget(btn3)
        lay.addWidget(card3)

        # 4) Truncate table
        card4 = self._card(); c4 = QHBoxLayout(card4)
        c4.setContentsMargins(20, 16, 20, 16); c4.setSpacing(12)
        c4.addWidget(self._cleanup_lbl("Truncate (empty) table:"))
        self.trunc_combo = QComboBox(); self.trunc_combo.setObjectName("formCombo")
        self.trunc_combo.setMinimumHeight(38); self.trunc_combo.setMinimumWidth(200)
        self.trunc_combo.addItems(["queue_entries", "invoice_items", "invoices",
                                   "appointments", "patient_conditions"])
        c4.addWidget(self.trunc_combo)
        btn4 = self._action_btn("Truncate", danger=True); btn4.clicked.connect(self._truncate)
        c4.addWidget(btn4)
        lay.addWidget(card4)

        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self); wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)
        self._refresh_counts()

    # ── Helpers ────────────────────────────────────────────────────────
    @staticmethod
    def _section(text: str) -> QLabel:
        l = QLabel(text); l.setObjectName("sectionHeader"); return l

    @staticmethod
    def _card() -> QFrame:
        f = QFrame(); f.setObjectName("cleanupCard")
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(12); sh.setOffset(0, 3); sh.setColor(QColor(0, 0, 0, 10))
        f.setGraphicsEffect(sh); return f

    @staticmethod
    def _cleanup_lbl(text: str) -> QLabel:
        l = QLabel(text); l.setObjectName("cleanupLabel"); return l

    @staticmethod
    def _action_btn(label: str, *, danger: bool = False) -> QPushButton:
        btn = QPushButton(label); btn.setMinimumHeight(38); btn.setMinimumWidth(110)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setObjectName("truncateBtn" if danger else "cleanupBtn"); return btn

    # ── Slots ──────────────────────────────────────────────────────────
    def _on_dark_toggle(self, checked: bool):
        if self._backend and self._user_email:
            self._backend.set_dark_mode(self._user_email, checked)
            QMessageBox.information(self, "Theme",
                                    "Dark mode preference saved.\n"
                                    "Restart the application to apply the full theme change.")

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
        if not self._backend:
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
        reply = QMessageBox.question(
            self, "Confirm Cleanup",
            f"Delete all completed appointments before {cutoff} and their linked invoices / queue entries?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            n = self._backend.cleanup_completed_appointments(cutoff)
            QMessageBox.information(self, "Done", f"{n} completed appointment(s) removed.")
            self._refresh_counts()

    def _cleanup_cancelled(self):
        reply = QMessageBox.question(
            self, "Confirm Cleanup",
            "Delete ALL cancelled appointments and their linked records?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            n = self._backend.cleanup_cancelled_appointments()
            QMessageBox.information(self, "Done", f"{n} cancelled appointment(s) removed.")
            self._refresh_counts()

    def _cleanup_inactive(self):
        reply = QMessageBox.question(
            self, "Confirm Cleanup",
            "Delete ALL inactive patients and every record linked to them\n"
            "(appointments, invoices, conditions, queue entries)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            n = self._backend.cleanup_inactive_patients()
            QMessageBox.information(self, "Done", f"{n} inactive patient(s) removed.")
            self._refresh_counts()

    def _truncate(self):
        table = self.trunc_combo.currentText()
        reply = QMessageBox.warning(
            self, "Confirm Truncate",
            f"This will permanently delete ALL rows from '{table}'.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            ok = self._backend.truncate_table(table)
            if ok:
                QMessageBox.information(self, "Done", f"Table '{table}' has been emptied.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to truncate '{table}'.")
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
            active_item = QTableWidgetItem("Yes" if dt.get("is_active") else "No")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not dt.get("is_active"):
                active_item.setForeground(QColor("#D9534F"))
            else:
                active_item.setForeground(QColor("#5CB85C"))
            self._disc_table.setItem(r, 3, active_item)

    def _on_add_discount(self):
        dlg = _DiscountTypeDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Type name is required.")
                return
            if self._backend:
                self._backend.add_discount_type(d["name"], d["percent"], d["legal_basis"])
            self._load_discount_types()
            QMessageBox.information(self, "Success", f"Discount type '{d['name']}' added.")

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
            "is_active": self._disc_table.item(row, 3).text() == "Yes",
        }
        dlg = _DiscountTypeDialog(self, data=current)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Type name is required.")
                return
            if self._backend:
                self._backend.update_discount_type(
                    did, d["name"], d["percent"], d["legal_basis"], 1 if d["is_active"] else 0)
            self._load_discount_types()
            QMessageBox.information(self, "Success", f"Discount type '{d['name']}' updated.")

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
                self._backend.delete_discount_type(did)
            self._load_discount_types()
            QMessageBox.information(self, "Done", f"Discount type '{name}' deleted.")


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

        self.active_check = QCheckBox("Active")
        self.active_check.setChecked(True)

        form.addRow("Type Name", self.name_edit)
        form.addRow("Discount %", self.percent_spin)
        form.addRow("Legal Basis", self.legal_edit)
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
            self.active_check.setChecked(data.get("is_active", True))

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "percent": self.percent_spin.value(),
            "legal_basis": self.legal_edit.text().strip(),
            "is_active": self.active_check.isChecked(),
        }