"""Doctor role – Dashboard, Patients, Appointments, Clinical, Analytics.

Re-exports the pages a Doctor can access::

    from ui.doctor import DashboardPage, PatientsPage, ...
"""

from ui.shared.dashboard_page     import DashboardPage          # noqa: F401
from ui.shared.patients_page      import PatientsPage            # noqa: F401
from ui.shared.appointments_page  import AppointmentsPage        # noqa: F401
from ui.shared.clinical_page      import ClinicalPage            # noqa: F401
from ui.shared.analytics_page     import AnalyticsPage           # noqa: F401
