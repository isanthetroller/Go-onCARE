"""Main application window V2 – sidebar, top header, stacked pages."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QSpacerItem, QSizePolicy,
    QGraphicsDropShadowEffect, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QFont, QColor, QAction

from ui.styles import MAIN_STYLE
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

_ROLE_ACCESS = {
    "Admin":        {"Dashboard", "Patients", "Appointments", "Clinical & POS",
                     "Data Analytics", "Employees", "Activity Log", "Settings"},
    "HR":           {"Dashboard", "Employees", "Activity Log"},
    "Doctor":       {"Dashboard", "Patients", "Appointments", "Clinical & POS", "Data Analytics"},
    "Cashier":      {"Dashboard", "Patients", "Appointments", "Clinical & POS"},
    "Receptionist": {"Dashboard", "Patients", "Appointments", "Clinical & POS"},
}


class MainWindow(QMainWindow):
    """Primary application window shown after successful login."""

    logout_requested = pyqtSignal()

    def __init__(self, user_email: str = "admin@carecrud.com",
                 user_role: str = "Admin", user_name: str = "Admin"):
        super().__init__()
        self.setWindowTitle("CareCRUD \u2013 Healthcare Management System")
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
        lay.setContentsMargins(16, 20, 16, 20)
        lay.setSpacing(4)

        # Logo area
        logo_frame = QWidget()
        logo_frame.setObjectName("logoFrame")
        logo_lay = QHBoxLayout(logo_frame)
        logo_lay.setContentsMargins(14, 12, 14, 12)
        logo_lay.setSpacing(10)

        logo_icon = QLabel("CC")
        logo_icon.setObjectName("logoIcon")
        logo_icon.setFixedSize(44, 44)
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lay.addWidget(logo_icon)

        brand_col = QVBoxLayout()
        brand_col.setSpacing(0)
        brand = QLabel("CareCRUD")
        brand.setObjectName("brandLabel")
        brand_sub = QLabel("Healthcare Management")
        brand_sub.setObjectName("brandSubLabel")
        brand_col.addWidget(brand)
        brand_col.addWidget(brand_sub)
        logo_lay.addLayout(brand_col)
        logo_lay.addStretch()

        lay.addWidget(logo_frame)
        lay.addSpacing(20)

        sec = QLabel("MAIN MENU")
        sec.setObjectName("sidebarSection")
        lay.addWidget(sec)
        lay.addSpacing(4)

        allowed = _ROLE_ACCESS.get(self._role, _ROLE_ACCESS["Admin"])
        self._nav_map = [(label, idx) for label, idx in _ALL_NAV if label in allowed]

        for nav_idx, (label, stack_idx) in enumerate(self._nav_map):
            btn = QPushButton(label)
            btn.setObjectName("navBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(44)
            btn.clicked.connect(lambda checked, i=nav_idx: self._select_nav(i))
            self._nav_buttons.append(btn)
            lay.addWidget(btn)

        lay.addStretch()

        sep = QFrame()
        sep.setObjectName("sidebarSep")
        sep.setFixedHeight(1)
        lay.addWidget(sep)
        lay.addSpacing(12)

        # User section
        user_card = QFrame()
        user_card.setObjectName("userCard")
        user_card_lay = QVBoxLayout(user_card)
        user_card_lay.setContentsMargins(14, 14, 14, 14)
        user_card_lay.setSpacing(10)

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
        user_email = QLabel(self._user)
        user_email.setObjectName("userEmail")
        user_email.setWordWrap(True)
        user_col.addWidget(self._sidebar_name_label)
        user_col.addWidget(user_email)
        role_badge = QLabel(self._role)
        role_badge.setObjectName("roleBadge")
        user_col.addWidget(role_badge)
        user_row.addLayout(user_col)
        user_row.addStretch()
        user_card_lay.addLayout(user_row)

        logout_btn = QPushButton("Log Out")
        logout_btn.setObjectName("logoutBtn")
        logout_btn.setMinimumHeight(36)
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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

        self._top_title = QLabel("Dashboard")
        self._top_title.setObjectName("topTitle")
        lay.addWidget(self._top_title)
        lay.addStretch()

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

        # 3 – Clinical & POS
        self._clinical_page = ClinicalPage(backend=self._backend, role=self._role)
        self.stack.addWidget(self._clinical_page)

        # 4 – Data Analytics
        self._analytics_page = AnalyticsPage(backend=self._backend, role=self._role, user_email=self._user)
        self.stack.addWidget(self._analytics_page)

        # 5 – Employees (HR gets enhanced page)
        if self._role == "HR":
            self._employees_page = HREmployeesPage(backend=self._backend, role=self._role)
        else:
            self._employees_page = EmployeesPage(backend=self._backend, role=self._role)
        self.stack.addWidget(self._employees_page)

        # 6 – Activity Log
        self._activity_log_page = ActivityLogPage(backend=self._backend, role=self._role)
        self.stack.addWidget(self._activity_log_page)

        # 7 – Settings
        self._settings_page = SettingsPage(backend=self._backend, user_email=self._user)
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

    # ── Live user-name refresh ─────────────────────────────────────
    def _refresh_user_display_name(self):
        """Re-read the user's full_name from DB and update sidebar + dashboard."""
        row = self._backend.fetch(
            "SELECT full_name FROM users WHERE email=%s",
            (self._user,), one=True)
        if not row:
            return
        new_name = row["full_name"]
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
