"""Activity Log – audit trail viewer with filters."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QGraphicsDropShadowEffect, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from ui.styles import configure_table


class ActivityLogPage(QWidget):
    """Displays the activity_log table with optional filters."""

    def __init__(self, backend=None, role: str = "Admin"):
        super().__init__()
        self._backend = backend
        self._role = role
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget(); inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner); lay.setSpacing(20); lay.setContentsMargins(28, 28, 28, 28)

        # ── Banner ────────────────────────────────────────────────
        banner = QFrame(); banner.setObjectName("pageBanner"); banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4); shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)
        bl = QHBoxLayout(banner); bl.setContentsMargins(32, 20, 32, 20)
        tc = QVBoxLayout(); tc.setSpacing(4)
        t = QLabel("Activity Log"); t.setObjectName("bannerTitle")
        s = QLabel("Audit trail of all system actions"); s.setObjectName("bannerSubtitle")
        tc.addWidget(t); tc.addWidget(s)
        bl.addLayout(tc); bl.addStretch()
        ref = QPushButton("\u21BB  Refresh"); ref.setObjectName("bannerBtn"); ref.setMinimumHeight(42)
        ref.setCursor(Qt.CursorShape.PointingHandCursor); ref.clicked.connect(self.refresh)
        bl.addWidget(ref, alignment=Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(banner)

        # ── Filters row ──────────────────────────────────────────
        filt_card = QFrame(); filt_card.setObjectName("card")
        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(12); shadow2.setOffset(0, 2); shadow2.setColor(QColor(0, 0, 0, 10))
        filt_card.setGraphicsEffect(shadow2)
        fr = QHBoxLayout(filt_card); fr.setContentsMargins(16, 12, 16, 12); fr.setSpacing(12)

        fr.addWidget(QLabel("User:"))
        self._user_filter = QLineEdit(); self._user_filter.setPlaceholderText("email")
        self._user_filter.setObjectName("formInput"); self._user_filter.setMinimumHeight(36)
        self._user_filter.setMaximumWidth(180)
        fr.addWidget(self._user_filter)

        fr.addWidget(QLabel("Action:"))
        self._action_combo = QComboBox(); self._action_combo.setObjectName("formCombo")
        self._action_combo.setMinimumHeight(36)
        self._action_combo.addItems(["All", "Login", "Created", "Edited", "Deleted", "Voided", "Merged"])
        fr.addWidget(self._action_combo)

        fr.addWidget(QLabel("Type:"))
        self._type_combo = QComboBox(); self._type_combo.setObjectName("formCombo")
        self._type_combo.setMinimumHeight(36)
        self._type_combo.addItems(["All", "User", "Patient", "Appointment", "Invoice", "Service", "Employee", "Queue"])
        fr.addWidget(self._type_combo)

        fr.addWidget(QLabel("From:"))
        self._from_date = QDateEdit(); self._from_date.setCalendarPopup(True)
        self._from_date.setDate(QDate.currentDate().addMonths(-1))
        self._from_date.setObjectName("formCombo"); self._from_date.setMinimumHeight(36)
        fr.addWidget(self._from_date)

        fr.addWidget(QLabel("To:"))
        self._to_date = QDateEdit(); self._to_date.setCalendarPopup(True)
        self._to_date.setDate(QDate.currentDate())
        self._to_date.setObjectName("formCombo"); self._to_date.setMinimumHeight(36)
        fr.addWidget(self._to_date)

        apply_btn = QPushButton("Apply"); apply_btn.setObjectName("cleanupBtn")
        apply_btn.setMinimumHeight(36); apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self.refresh)
        fr.addWidget(apply_btn)
        fr.addStretch()
        lay.addWidget(filt_card)

        # ── Table ────────────────────────────────────────────────
        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["Timestamp", "User", "Role", "Action", "Type", "Detail"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(420)
        self._table.verticalHeader().setDefaultSectionSize(48)
        configure_table(self._table)
        lay.addWidget(self._table)

        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self); wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)
        self.refresh()

    def refresh(self):
        if not self._backend:
            return
        user = self._user_filter.text().strip()
        action = self._action_combo.currentText()
        rtype = self._type_combo.currentText()
        from_d = self._from_date.date().toString("yyyy-MM-dd")
        to_d = self._to_date.date().toString("yyyy-MM-dd")
        rows = self._backend.get_activity_log(
            limit=500,
            user_filter=user if user else "",
            action_filter=action if action != "All" else "",
            record_type_filter=rtype if rtype != "All" else "",
            from_date=from_d,
            to_date=to_d,
        )
        self._table.setRowCount(len(rows))
        action_colors = {
            "Login": "#388087", "Created": "#5CB85C", "Edited": "#E8B931",
            "Deleted": "#D9534F", "Voided": "#D9534F", "Merged": "#6FB3B8",
        }
        for r, row in enumerate(rows):
            ts = row.get("created_at", "")
            if hasattr(ts, "strftime"):
                ts = ts.strftime("%Y-%m-%d %H:%M:%S")
            cells = [
                str(ts),
                row.get("user_email", ""),
                row.get("user_role", ""),
                row.get("action", ""),
                row.get("record_type", ""),
                row.get("record_detail", ""),
            ]
            for c, val in enumerate(cells):
                item = QTableWidgetItem(val)
                if c == 3:
                    clr = action_colors.get(val, "#2C3E50")
                    item.setForeground(QColor(clr))
                self._table.setItem(r, c, item)
