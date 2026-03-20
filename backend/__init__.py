# Backend package - each file handles a different part of the DB logic.
# AuthBackend below pulls them all together into one class.

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
    # All DB methods in one class - just pass this to every page
    pass
