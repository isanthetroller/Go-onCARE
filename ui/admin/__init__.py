"""Admin role – full access to all 8 pages.

Re-exports every shared page so imports read clearly::

    from ui.admin import DashboardPage, PatientsPage, ...
"""

from ui.shared.dashboard_page     import DashboardPage          # noqa: F401
from ui.shared.patients_page      import PatientsPage            # noqa: F401
from ui.shared.appointments_page  import AppointmentsPage        # noqa: F401
from ui.shared.clinical_page      import ClinicalPage            # noqa: F401
from ui.shared.analytics_page     import AnalyticsPage           # noqa: F401
from ui.shared.employees_page     import EmployeesPage           # noqa: F401
from ui.shared.settings_page      import SettingsPage            # noqa: F401
from ui.shared.activity_log_page  import ActivityLogPage         # noqa: F401
