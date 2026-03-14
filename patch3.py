import os
import re

found_files = []
for root, _, files in os.walk('ui'):
    for f in files:
        if f.endswith('.py'):
            found_files.append(os.path.join(root, f))

for path in found_files:
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # We want to find patterns like ar = QDateEdit() and check if they have formats applied.
    # Actually, it's easier to just do it manually since there are only maybe 6 files:
    # activity_log_page.py, analytics_page.py, dashboard_page.py, employee_dialogs.py, hr_employees_page.py, patient_dialogs.py, payroll_page.py, settings_page.py
