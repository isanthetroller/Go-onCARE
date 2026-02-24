"""Admin Settings – Database Cleanup page."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGraphicsDropShadowEffect, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QComboBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from ui.styles import configure_table

from backend import AuthBackend


class SettingsPage(QWidget):
    """Admin‑only page for database maintenance."""

    def __init__(self):
        super().__init__()
        self._backend = AuthBackend()
        self._build()

    # ── UI ─────────────────────────────────────────────────────────────
    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner)
        lay.setSpacing(20)
        lay.setContentsMargins(28, 28, 28, 28)

        # ── Banner ─────────────────────────────────────────────────
        banner = QFrame()
        banner.setObjectName("pageBanner")
        banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(32, 20, 32, 20)
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("Settings")
        title.setObjectName("bannerTitle")
        sub = QLabel("Database maintenance and cleanup tools")
        sub.setObjectName("bannerSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(sub)
        banner_lay.addLayout(title_col)
        banner_lay.addStretch()

        refresh_btn = QPushButton("\u21BB  Refresh")
        refresh_btn.setObjectName("bannerBtn")
        refresh_btn.setMinimumHeight(42)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_counts)
        banner_lay.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(banner)

        # ── Table row counts card ──────────────────────────────────
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
        card1 = self._card()
        c1 = QHBoxLayout(card1)
        c1.setContentsMargins(20, 16, 20, 16)
        c1.setSpacing(12)
        lbl1 = QLabel("Remove completed appointments before:")
        lbl1.setObjectName("cleanupLabel")
        c1.addWidget(lbl1)
        self.cutoff_date = QDateEdit()
        self.cutoff_date.setCalendarPopup(True)
        self.cutoff_date.setDate(QDate.currentDate().addMonths(-3))
        self.cutoff_date.setObjectName("formCombo")
        self.cutoff_date.setMinimumHeight(38)
        c1.addWidget(self.cutoff_date)
        btn1 = self._action_btn("Clean Up")
        btn1.clicked.connect(self._cleanup_completed)
        c1.addWidget(btn1)
        lay.addWidget(card1)

        # 2) Cancelled appointments
        card2 = self._card()
        c2 = QHBoxLayout(card2)
        c2.setContentsMargins(20, 16, 20, 16)
        c2.setSpacing(12)
        lbl2 = QLabel("Remove all cancelled appointments and linked records")
        lbl2.setObjectName("cleanupLabel")
        c2.addWidget(lbl2, 1)
        btn2 = self._action_btn("Clean Up")
        btn2.clicked.connect(self._cleanup_cancelled)
        c2.addWidget(btn2)
        lay.addWidget(card2)

        # 3) Inactive patients
        card3 = self._card()
        c3 = QHBoxLayout(card3)
        c3.setContentsMargins(20, 16, 20, 16)
        c3.setSpacing(12)
        lbl3 = QLabel("Remove inactive patients and all their linked data")
        lbl3.setObjectName("cleanupLabel")
        c3.addWidget(lbl3, 1)
        btn3 = self._action_btn("Clean Up")
        btn3.clicked.connect(self._cleanup_inactive)
        c3.addWidget(btn3)
        lay.addWidget(card3)

        # 4) Truncate a transactional table
        card4 = self._card()
        c4 = QHBoxLayout(card4)
        c4.setContentsMargins(20, 16, 20, 16)
        c4.setSpacing(12)
        lbl4 = QLabel("Truncate (empty) table:")
        lbl4.setObjectName("cleanupLabel")
        c4.addWidget(lbl4)
        self.trunc_combo = QComboBox()
        self.trunc_combo.setObjectName("formCombo")
        self.trunc_combo.setMinimumHeight(38)
        self.trunc_combo.setMinimumWidth(200)
        self.trunc_combo.addItems([
            "queue_entries", "invoice_items", "invoices",
            "appointments", "patient_conditions",
        ])
        c4.addWidget(self.trunc_combo)
        btn4 = self._action_btn("Truncate", danger=True)
        btn4.clicked.connect(self._truncate)
        c4.addWidget(btn4)
        lay.addWidget(card4)

        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

        # initial load
        self._refresh_counts()

    # ── Helpers ────────────────────────────────────────────────────────
    @staticmethod
    def _section(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("sectionHeader")
        return lbl

    @staticmethod
    def _card() -> QFrame:
        f = QFrame()
        f.setObjectName("cleanupCard")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12); shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 10))
        f.setGraphicsEffect(shadow)
        return f

    @staticmethod
    def _action_btn(label: str, *, danger: bool = False) -> QPushButton:
        btn = QPushButton(label)
        btn.setMinimumHeight(38)
        btn.setMinimumWidth(110)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setObjectName("truncateBtn" if danger else "cleanupBtn")
        return btn

    # ── Slots ──────────────────────────────────────────────────────────
    def _refresh_counts(self):
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
