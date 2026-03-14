import os, re

files = [
    'ui/shared/activity_log_page.py',
    'ui/shared/analytics_page.py',
    'ui/shared/dashboard_page.py',
    'ui/shared/employee_dialogs.py',
    'ui/shared/patient_dialogs.py',
    'ui/shared/payroll_page.py',
    'ui/shared/settings_page.py'
]

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We want to replace all occurrences of ar = QDateEdit()
    # with ar = QDateEdit(); var.setObjectName("formCombo"); var.setCalendarPopup(True); var.setDisplayFormat("M/d/yyyy")
    # BUT many already have parts of it.
    # It's safer to just inject .setDisplayFormat("M/d/yyyy") exactly where QDateEdit() is found.
    # Actually, some use self.xxx = QDateEdit(). 
    
    def repl(m):
        var_name = m.group(1)
        return f'{var_name} = QDateEdit(); {var_name}.setObjectName("formCombo"); {var_name}.setCalendarPopup(True); {var_name}.setDisplayFormat("M/d/yyyy")'
    
    new_content = re.sub(r'([a-zA-Z0-9_\.]+) = QDateEdit\(\)(?:;[^\n]*)?', repl, content)
    
    # But wait, this would wipe out code on the same line.
    
