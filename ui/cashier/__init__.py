"""Cashier role – Dashboard, Patients, Appointments, Clinical & POS.

Re-exports the pages a Cashier can access::

    from ui.cashier import DashboardPage, PatientsPage, ...
"""

from ui.shared.dashboard_page     import DashboardPage          # noqa: F401
from ui.shared.patients_page      import PatientsPage            # noqa: F401
from ui.shared.appointments_page  import AppointmentsPage        # noqa: F401
from ui.shared.clinical_page      import ClinicalPage            # noqa: F401
