# Activity log page - shows who did what and when

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QComboBox, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtGui import QColor
from ui.styles import (
    make_page_layout, finish_page, make_banner, make_card,
    make_read_only_table, ACTION_COLORS,
)


class ActivityLogPage(QWidget):
    """Displays the activity_log table with optional filters."""

    def __init__(self, backend=None, role: str = "Admin"):
        super().__init__()
        self._backend = backend
        self._role = role
        self._last_log_id = 0          # Track latest log_id for smart refresh
        self._build()

    def _build(self):
        scroll, lay = make_page_layout()

        # ── Banner ────────────────────────────────────────────────
        sub = "Audit trail of all system actions"
        lay.addWidget(make_banner("Activity Log", sub))

        # ── Filters row ──────────────────────────────────────────
        filt_card = make_card()
        fr = QHBoxLayout(filt_card); fr.setContentsMargins(16, 12, 16, 12); fr.setSpacing(12)

        fr.addWidget(QLabel("User:"))
        self._user_filter = QLineEdit(); self._user_filter.setPlaceholderText("email")
        self._user_filter.setObjectName("formInput"); self._user_filter.setMinimumHeight(36)
        self._user_filter.setMaximumWidth(180)
        fr.addWidget(self._user_filter)

        # Action & Type filters – hidden for HR (forced to Login only)
        self._action_label = QLabel("Action:")
        fr.addWidget(self._action_label)
        self._action_combo = QComboBox(); self._action_combo.setObjectName("formCombo")
        self._action_combo.setMinimumHeight(36)
        self._action_combo.addItems(["All", "Login", "Created", "Edited", "Deleted",
                                       "Voided", "Merged", "Requested", "Approved", "Declined",
                                       "Rejected"])
        fr.addWidget(self._action_combo)

        self._type_label = QLabel("Type:")
        fr.addWidget(self._type_label)
        self._type_combo = QComboBox(); self._type_combo.setObjectName("formCombo")
        self._type_combo.setMinimumHeight(36)
        self._type_combo.addItems(["All", "User", "Patient", "Appointment", "Invoice",
                                    "Service", "Employee", "Queue", "Leave", "Paycheck",
                                    "Condition", "Discount Type", "Notification", "System"])
        fr.addWidget(self._type_combo)

        # HR now sees the full activity log like Admin

        fr.addWidget(QLabel("From:"))
        self._from_date = QDateEdit(); self._from_date.setCalendarPopup(True)
        self._from_date.setDate(QDate.currentDate().addMonths(-1))
        self._from_date.setObjectName("formCombo")
        self._from_date.setMinimumHeight(36)
        self._from_date.setDisplayFormat("M/d/yyyy")
        fr.addWidget(self._from_date)

        fr.addWidget(QLabel("To:"))
        self._to_date = QDateEdit(); self._to_date.setCalendarPopup(True)
        self._to_date.setDate(QDate.currentDate())
        self._to_date.setObjectName("formCombo")
        self._to_date.setMinimumHeight(36)
        self._to_date.setDisplayFormat("M/d/yyyy")
        fr.addWidget(self._to_date)

        apply_btn = QPushButton("Apply"); apply_btn.setObjectName("cleanupBtn")
        apply_btn.setMinimumHeight(36); apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self.refresh)
        fr.addWidget(apply_btn)
        fr.addStretch()
        lay.addWidget(filt_card)

        # ── Table ────────────────────────────────────────────────
        self._table = make_read_only_table(
            ["Timestamp", "User", "Role", "Action", "Type", "Detail"])        
        # Adjust column sizing without using ResizeToContents which causes massive lag on 500+ rows
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table.setColumnWidth(0, 160)  # Timestamp
        self._table.setColumnWidth(1, 200)  # User
        self._table.setColumnWidth(2, 100)  # Role
        self._table.setColumnWidth(3, 120)  # Action
        self._table.setColumnWidth(4, 120)  # Type
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Detail column stretches
        lay.addWidget(self._table)

        lay.addStretch()
        finish_page(self, scroll)
        self.refresh()



    def refresh(self):
        if not self._backend:
            return
            
        self._table.setUpdatesEnabled(False)  # Immediately stop UI repaints while generating 500 rows to prevent freezing

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
        action_colors = ACTION_COLORS
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
                if c == 5 and val:
                    # Provide an immediate tooltip so the user can hover over long text without issue
                    item.setToolTip(val)
                self._table.setItem(r, c, item)
                
        # Update the last-seen log_id so the timer only refreshes on new entries
        if rows:
            max_id = max(r.get("log_id", 0) for r in rows)
            if max_id > self._last_log_id:
                self._last_log_id = max_id
                
        self._table.setUpdatesEnabled(True)  # Resume UI repaints
