"""CareCRUD Backend Package – Modular database operations.

Each module handles one domain:
    base.py        – DB connection management & activity logging
    auth.py        – Login, user preferences, passwords
    employees.py   – Employee CRUD & performance
    patients.py    – Patient CRUD & profiles
    appointments.py– Appointment CRUD, conflicts, recurring
    clinical.py    – Queue, invoices, billing, services
    dashboard.py   – Dashboard stats & alerts
    analytics.py   – Revenue, trends, demographics, reports
    settings.py    – Data cleanup, table mgmt, standard conditions
    search.py      – Global cross-entity search

The AuthBackend class below composes all mixins so existing code using
``from backend import AuthBackend`` continues to work unchanged.
"""

from backend.base import DatabaseBase
from backend.auth import AuthMixin
from backend.employees import EmployeeMixin
from backend.patients import PatientMixin
from backend.appointments import AppointmentMixin
from backend.clinical import ClinicalMixin
from backend.dashboard import DashboardMixin
from backend.analytics import AnalyticsMixin
from backend.settings import SettingsMixin
from backend.search import SearchMixin


class AuthBackend(
    DatabaseBase,
    AuthMixin,
    EmployeeMixin,
    PatientMixin,
    AppointmentMixin,
    ClinicalMixin,
    DashboardMixin,
    AnalyticsMixin,
    SettingsMixin,
    SearchMixin,
):
    """Unified backend combining all domain mixins.

    Instantiate once and pass to all UI pages — every method from the
    original monolithic backend.py is available on this single object.
    """
    pass
