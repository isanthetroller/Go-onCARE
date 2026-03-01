"""HR role – Dashboard, Employee management (enhanced), Activity Log.

Re-exports the pages an HR user can access::

    from ui.hr import DashboardPage, HREmployeesPage, ActivityLogPage
"""

from ui.shared.dashboard_page      import DashboardPage          # noqa: F401
from ui.shared.hr_employees_page   import HREmployeesPage        # noqa: F401
from ui.shared.activity_log_page   import ActivityLogPage         # noqa: F401
