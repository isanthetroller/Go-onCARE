# Main window - sidebar nav + stacked pages

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QSpacerItem, QSizePolicy,
    QGraphicsDropShadowEffect, QMessageBox, QLineEdit, QDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QColor, QAction

from ui.styles import MAIN_STYLE
from ui.icons import get_icon, NAV_ICON_MAP
from ui.shared.dashboard_page     import DashboardPage
from ui.shared.patients_page      import PatientsPage
from ui.shared.appointments_page  import AppointmentsPage
from ui.shared.clinical_page      import ClinicalPage
from ui.shared.employees_page     import EmployeesPage
from ui.shared.hr_employees_page  import HREmployeesPage
from ui.shared.analytics_page     import AnalyticsPage
from ui.shared.settings_page      import SettingsPage
from ui.shared.activity_log_page  import ActivityLogPage
from backend                      import AuthBackend


_ALL_NAV = [
    ("Dashboard",      0),
    ("Patients",       1),
    ("Appointments",   2),
    ("Clinical & POS", 3),
    ("Data Analytics", 4),
    ("Employees",      5),
    ("Activity Log",   6),
    ("Settings",       7),
]

# Category groupings for the sidebar
_NAV_CATEGORIES = [
    ("OVERVIEW",      ["Dashboard"]),
    ("PATIENT CARE",  ["Patients", "Appointments", "Clinical & POS"]),
    ("INSIGHTS",      ["Data Analytics", "Activity Log"]),
    ("ADMINISTRATION",["Employees", "Settings"]),
]

_ROLE_ACCESS = {
    "Admin":        {"Dashboard", "Patients", "Appointments", "Clinical & POS",
                     "Data Analytics", "Employees", "Activity Log", "Settings"},
    "HR":           {"Dashboard", "Employees", "Activity Log", "Settings"},
    "Doctor":       {"Dashboard", "Patients", "Appointments", "Clinical & POS", "Data Analytics", "Settings"},
    "Cashier":      {"Dashboard", "Patients", "Appointments", "Clinical & POS", "Settings"},
    "Receptionist": {"Dashboard", "Patients", "Appointments", "Clinical & POS", "Settings"},
}


_NAV_TOOLTIPS = {
    "Dashboard":      "Overview, KPIs, and schedule",
    "Patients":       "Manage patient records",
    "Appointments":   "Schedule and track appointments",
    "Clinical & POS": "Queue, billing, and records",
    "Data Analytics": "Reports, charts, and insights",
    "Employees":      "Staff directory and management",
    "Activity Log":   "Audit trail of system actions",
    "Settings":       "Database, accounts, and profile",
}


class MainWindow(QMainWindow):
    """Primary application window shown after successful login."""

    logout_requested = pyqtSignal()

    def __init__(self, user_email: str = "admin@carecrud.com",
                 user_role: str = "Admin", user_name: str = "Admin"):
        super().__init__()
        self.setWindowTitle("Go-onCare \u2013 Healthcare Management System")
        self.setMinimumSize(1200, 750)
        self.setStyleSheet(MAIN_STYLE)

        self._user = user_email
        self._role = user_role
        self._user_name = user_name
        self._backend = AuthBackend()
        self._nav_buttons: list[QPushButton] = []
        self._nav_map: list[tuple[str, int]] = []

        central = QWidget()
        central.setAutoFillBackground(True)
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        right = QWidget()
        right.setAutoFillBackground(True)
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)
        right_lay.addWidget(self._build_top_bar())
        right_lay.addWidget(self._build_content(), 1)
        root.addWidget(right, 1)

        self._select_nav(0)

        # ── Notification check for leave request decisions ────────
        self._employee_id = self._backend.get_employee_id_by_email(self._user)
        if self._employee_id and self._role not in ("Admin", "HR"):
            # Check immediately, then every 15 seconds
            QTimer.singleShot(1500, self._check_notifications)
            self._notif_timer = QTimer(self)
            self._notif_timer.timeout.connect(self._check_notifications)
            self._notif_timer.start(15_000)

        # ── Auto-expire leaves past their end date ────────────────────
        try:
            self._backend.auto_expire_leaves()
        except Exception:
            pass
        self._leave_timer = QTimer(self)
        self._leave_timer.timeout.connect(lambda: self._backend.auto_expire_leaves())
        self._leave_timer.start(300_000)  # check every 5 minutes

    # ── Sidebar ────────────────────────────────────────────────────────
    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)

        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(16, 20, 16, 16)
        lay.setSpacing(0)

        # Logo area
        logo_frame = QWidget()
        logo_frame.setObjectName("logoFrame")
        logo_lay = QHBoxLayout(logo_frame)
        logo_lay.setContentsMargins(14, 12, 14, 12)
        logo_lay.setSpacing(10)

        logo_icon = QLabel("GC")
        logo_icon.setObjectName("logoIcon")
        logo_icon.setFixedSize(44, 44)
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lay.addWidget(logo_icon)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(0)
        brand = QLabel("Go-onCare")
        brand.setObjectName("brandLabel")
        brand_sub = QLabel("Healthcare Management")
        brand_sub.setObjectName("brandSubLabel")
        brand_col.addWidget(brand)
        brand_col.addWidget(brand_sub)
        logo_lay.addLayout(brand_col)
        logo_lay.addStretch()

        lay.addWidget(logo_frame)
        lay.addSpacing(16)

        # Build categorized navigation
        allowed = _ROLE_ACCESS.get(self._role, _ROLE_ACCESS["Admin"])
        nav_lookup = {label: idx for label, idx in _ALL_NAV}
        self._nav_map = []

        for cat_name, cat_items in _NAV_CATEGORIES:
            # Filter to only items this role can see
            visible = [item for item in cat_items if item in allowed]
            if not visible:
                continue

            sec = QLabel(cat_name)
            sec.setObjectName("sidebarSection")
            lay.addSpacing(12)
            lay.addWidget(sec)
            lay.addSpacing(4)

            for label in visible:
                stack_idx = nav_lookup[label]
                nav_idx = len(self._nav_map)
                self._nav_map.append((label, stack_idx))

                btn = QPushButton(label)
                btn.setObjectName("navBtn")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setMinimumHeight(40)
                btn.setToolTip(_NAV_TOOLTIPS.get(label, label))
                icon_key = NAV_ICON_MAP.get(label)
                if icon_key:
                    btn.setIcon(get_icon(icon_key))
                    btn.setIconSize(QSize(18, 18))
                btn.clicked.connect(lambda checked, i=nav_idx: self._select_nav(i))
                self._nav_buttons.append(btn)
                lay.addWidget(btn)

        lay.addStretch()

        sep = QFrame()
        sep.setObjectName("sidebarSep")
        sep.setFixedHeight(1)
        lay.addWidget(sep)
        lay.addSpacing(10)

        # User section
        user_card = QFrame()
        user_card.setObjectName("userCard")
        user_card_lay = QVBoxLayout(user_card)
        user_card_lay.setContentsMargins(12, 12, 12, 12)
        user_card_lay.setSpacing(8)

        user_row = QHBoxLayout()
        user_row.setSpacing(10)

        _display_name = self._user_name
        _initials = "".join(w[0].upper() for w in _display_name.split()[:2])
        self._avatar_label = QLabel(_initials)
        self._avatar_label.setObjectName("userAvatar")
        self._avatar_label.setFixedSize(36, 36)
        self._avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_row.addWidget(self._avatar_label)

        user_col = QVBoxLayout()
        user_col.setSpacing(1)
        self._sidebar_name_label = QLabel(_display_name)
        self._sidebar_name_label.setObjectName("userName")
        role_badge = QLabel(self._role)
        role_badge.setObjectName("roleBadge")
        user_col.addWidget(self._sidebar_name_label)
        user_col.addWidget(role_badge)
        user_row.addLayout(user_col)
        user_row.addStretch()
        user_card_lay.addLayout(user_row)

        logout_btn = QPushButton("Log Out")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setMinimumHeight(34)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.setToolTip("Sign out and return to login")
        logout_btn.setIcon(get_icon("nav_logout"))
        logout_btn.setIconSize(QSize(16, 16))
        logout_btn.clicked.connect(self.logout_requested.emit)
        user_card_lay.addWidget(logout_btn)

        lay.addWidget(user_card)
        return sidebar

    # ── Top bar ────────────────────────────────────────────────────────
    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("topBar")
        bar.setAutoFillBackground(True)
        bar.setFixedHeight(64)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 15))
        bar.setGraphicsEffect(shadow)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(16)

        # Page title + breadcrumb-style subtitle
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        self._top_title = QLabel("Dashboard")
        self._top_title.setObjectName("topTitle")
        self._top_subtitle = QLabel(f"Welcome, {self._user_name}")
        self._top_subtitle.setObjectName("topSubtitle")
        title_col.addWidget(self._top_title)
        title_col.addWidget(self._top_subtitle)
        lay.addLayout(title_col)
        lay.addStretch()

        self._search_bar = QLineEdit()
        self._search_bar.setObjectName("searchBar")
        self._search_bar.setPlaceholderText("Search patients, appointments, staff...")
        self._search_bar.setFixedWidth(320)
        self._search_bar.setMinimumHeight(36)
        self._search_bar.returnPressed.connect(self._on_global_search)
        lay.addWidget(self._search_bar)

        return bar

    def _nav_to_page(self, stack_idx: int):
        """Navigate to a page by stack index. Called by dashboard."""
        for nav_i, (label, si) in enumerate(self._nav_map):
            if si == stack_idx:
                self._select_nav(nav_i)
                return

    # ── Content area ───────────────────────────────────────────────────
    def _build_content(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("contentArea")
        wrapper.setAutoFillBackground(True)
        lay = QVBoxLayout(wrapper)
        lay.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # 0 – Dashboard
        self._dashboard_page = DashboardPage(
            user_name=self._user_name, backend=self._backend, role=self._role,
            user_email=self._user
        )
        self._dashboard_page.navigate_to.connect(self._nav_to_page)
        self.stack.addWidget(self._dashboard_page)

        # 1 – Patients
        self._patients_page = PatientsPage(backend=self._backend, role=self._role, user_email=self._user)
        self.stack.addWidget(self._patients_page)

        # 2 – Appointments
        self._appointments_page = AppointmentsPage(backend=self._backend, role=self._role, user_email=self._user)
        self.stack.addWidget(self._appointments_page)

        self._appointments_page.set_patient_names(
            self._patients_page.get_patient_names()
        )
        self._patients_page.patients_changed.connect(
            self._appointments_page.set_patient_names
        )
        # Also pass patient dicts with IDs for the searchable dropdown
        self._sync_appointment_patients()
        self._patients_page.patients_changed.connect(
            lambda _: self._sync_appointment_patients()
        )

        # 3 – Clinical & POS
        self._clinical_page = ClinicalPage(backend=self._backend, role=self._role, user_email=self._user)
        self.stack.addWidget(self._clinical_page)

        # 4 – Data Analytics
        self._analytics_page = AnalyticsPage(backend=self._backend, role=self._role, user_email=self._user)
        self.stack.addWidget(self._analytics_page)

        # 5 – Employees (Admin & HR get enhanced page with salary/leave data)
        if self._role in ("HR", "Admin"):
            self._employees_page = HREmployeesPage(backend=self._backend, role=self._role)
        else:
            self._employees_page = EmployeesPage(backend=self._backend, role=self._role)
        self.stack.addWidget(self._employees_page)

        # 6 – Activity Log
        self._activity_log_page = ActivityLogPage(backend=self._backend, role=self._role)
        self.stack.addWidget(self._activity_log_page)

        # 7 – Settings
        self._settings_page = SettingsPage(backend=self._backend, user_email=self._user, role=self._role)
        self.stack.addWidget(self._settings_page)

        # Page-refresh map: stack index → (page_ref, refresh_method_name)
        self._page_refresh_map = {
            0: (self._dashboard_page,   "refresh"),
            1: (self._patients_page,    "_load_from_db"),
            2: (self._appointments_page,"_load_from_db"),
            3: (self._clinical_page,    "refresh"),
            4: (self._analytics_page,   "_on_refresh"),
            5: (self._employees_page,   "_load_from_db"),
            6: (self._activity_log_page,"refresh"),
            7: (self._settings_page,    "_refresh_counts"),
        }

        lay.addWidget(self.stack)
        return wrapper

    # ── Sync patient list for appointment dropdown ──────────────
    def _sync_appointment_patients(self):
        if self._backend:
            patients = self._backend.get_active_patients() or []
            self._appointments_page.set_patients(patients)

    # ── Live user-name refresh ─────────────────────────────────────
    def _refresh_user_display_name(self):
        """Re-read the user's full_name from DB and update sidebar + dashboard."""
        row = self._backend.get_user_full_name(self._user)
        if not row:
            return
        new_name = row
        if new_name == self._user_name:
            return
        self._user_name = new_name
        # Sidebar
        if hasattr(self, "_sidebar_name_label"):
            self._sidebar_name_label.setText(new_name)
        if hasattr(self, "_avatar_label"):
            initials = "".join(w[0].upper() for w in new_name.split()[:2])
            self._avatar_label.setText(initials)
        # Dashboard greeting
        if hasattr(self, "_dashboard_page"):
            self._dashboard_page._user_name = new_name

    # ── Notification check ──────────────────────────────────────────
    def _check_notifications(self):
        """Check for unread notifications and display them."""
        if not self._employee_id:
            return
        try:
            notifs = self._backend.get_unread_notifications(self._employee_id) or []
            if notifs:
                messages = []
                for n in notifs:
                    messages.append(f"• {n.get('message', '')}")
                self._backend.mark_notifications_read(self._employee_id)
                QMessageBox.information(
                    self, "Leave Request Update",
                    "\n\n".join(messages))
        except Exception:
            pass

    # ── Nav helpers ────────────────────────────────────────────────────
    def _select_nav(self, index: int):
        for i, btn in enumerate(self._nav_buttons):
            btn.setObjectName("navBtnActive" if i == index else "navBtn")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        label, stack_idx = self._nav_map[index]
        self.stack.setCurrentIndex(stack_idx)
        if hasattr(self, "_top_title"):
            self._top_title.setText(label)
        if hasattr(self, "_top_subtitle"):
            self._top_subtitle.setText(_NAV_TOOLTIPS.get(label, ""))
        # Refresh user display name from DB
        self._refresh_user_display_name()
        # Refresh the target page on navigation
        if stack_idx in self._page_refresh_map:
            page, method = self._page_refresh_map[stack_idx]
            if hasattr(page, method):
                try:
                    getattr(page, method)()
                except Exception:
                    pass

    def _on_global_search(self):
        query = self._search_bar.text().strip()
        if len(query) < 2:
            return
        include_emp = self._role in ("Admin", "HR")
        results = self._backend.global_search(query, include_employees=include_emp)
        patients = results.get("patients", [])
        appts = results.get("appointments", [])
        employees = results.get("employees", [])
        total = len(patients) + len(appts) + len(employees)
        if total == 0:
            QMessageBox.information(self, "Search", f"No results for \"{query}\".")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Search Results — \"{query}\"")
        dlg.setMinimumSize(640, 420)
        lay = QVBoxLayout(dlg); lay.setSpacing(12); lay.setContentsMargins(16, 16, 16, 16)
        if patients:
            lay.addWidget(QLabel(f"Patients ({len(patients)})"))
            tbl = QTableWidget(len(patients), 4)
            tbl.setHorizontalHeaderLabels(["ID", "Name", "Phone", "Status"])
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tbl.verticalHeader().setVisible(False)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            for r, p in enumerate(patients):
                tbl.setItem(r, 0, QTableWidgetItem(f"PT-{p['patient_id']:04d}"))
                tbl.setItem(r, 1, QTableWidgetItem(p.get("name", "")))
                tbl.setItem(r, 2, QTableWidgetItem(p.get("phone", "") or ""))
                tbl.setItem(r, 3, QTableWidgetItem(p.get("status", "")))
            tbl.setMaximumHeight(min(len(patients) * 36 + 36, 200))
            lay.addWidget(tbl)
        if appts:
            lay.addWidget(QLabel(f"Appointments ({len(appts)})"))
            tbl = QTableWidget(len(appts), 4)
            tbl.setHorizontalHeaderLabels(["ID", "Patient", "Date", "Status"])
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tbl.verticalHeader().setVisible(False)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            for r, a in enumerate(appts):
                tbl.setItem(r, 0, QTableWidgetItem(str(a.get("appointment_id", ""))))
                tbl.setItem(r, 1, QTableWidgetItem(a.get("patient_name", "")))
                d = a.get("appointment_date", "")
                tbl.setItem(r, 2, QTableWidgetItem(str(d)))
                tbl.setItem(r, 3, QTableWidgetItem(a.get("status", "")))
            tbl.setMaximumHeight(min(len(appts) * 36 + 36, 200))
            lay.addWidget(tbl)
        if employees:
            lay.addWidget(QLabel(f"Employees ({len(employees)})"))
            tbl = QTableWidget(len(employees), 3)
            tbl.setHorizontalHeaderLabels(["ID", "Name", "Email"])
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            tbl.verticalHeader().setVisible(False)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            for r, e in enumerate(employees):
                tbl.setItem(r, 0, QTableWidgetItem(str(e.get("employee_id", ""))))
                tbl.setItem(r, 1, QTableWidgetItem(e.get("name", "")))
                tbl.setItem(r, 2, QTableWidgetItem(e.get("email", "")))
            tbl.setMaximumHeight(min(len(employees) * 36 + 36, 200))
            lay.addWidget(tbl)
        lay.addStretch()
        dlg.exec()
