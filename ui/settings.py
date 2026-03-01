"""Settings V2 – Database cleanup, dark mode toggle, self-service profile."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGraphicsDropShadowEffect, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QComboBox,
    QLineEdit, QCheckBox,
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor
from ui.styles import configure_table


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
