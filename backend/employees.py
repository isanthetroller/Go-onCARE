"""Employee backend – CRUD, performance queries, and HR operations."""


class EmployeeMixin:

    def _split_name(self, full_name):
        parts = full_name.split(None, 1)
        return parts[0], parts[1] if len(parts) > 1 else ""

    def _lookup_role_id(self, role_name):
        row = self.fetch("SELECT role_id FROM roles WHERE role_name = %s", (role_name,), one=True)
        return row["role_id"] if row else None

    def _lookup_dept_id(self, dept_name):
        row = self.fetch("SELECT department_id FROM departments WHERE department_name = %s", (dept_name,), one=True)
        return row["department_id"] if row else None

    def get_employees(self):
        return self.fetch("""
            SELECT e.employee_id, CONCAT(e.first_name,' ',e.last_name) AS full_name,
                   r.role_name, d.department_name, e.employment_type,
                   e.phone, e.email, e.hire_date, e.status, e.notes,
                   e.leave_from, e.leave_until
            FROM employees e
            INNER JOIN roles r ON e.role_id = r.role_id
            INNER JOIN departments d ON e.department_id = d.department_id
            ORDER BY e.employee_id
        """)

    # ── HR-specific queries ───────────────────────────────────────
    def get_employees_detailed(self):
        """Return all employee data including HR-only fields (salary, emergency contact)."""
        return self.fetch("""
            SELECT e.employee_id, CONCAT(e.first_name,' ',e.last_name) AS full_name,
                   r.role_name, d.department_name, e.employment_type,
                   e.phone, e.email, e.hire_date, e.status, e.notes,
                   e.leave_from, e.leave_until, e.salary, e.emergency_contact
            FROM employees e
            INNER JOIN roles r ON e.role_id = r.role_id
            INNER JOIN departments d ON e.department_id = d.department_id
            ORDER BY e.employee_id
        """)

    def get_leave_employees(self):
        """Return employees currently on leave with dates."""
        return self.fetch("""
            SELECT e.employee_id, CONCAT(e.first_name,' ',e.last_name) AS full_name,
                   r.role_name, d.department_name, e.leave_from, e.leave_until, e.notes
            FROM employees e
            INNER JOIN roles r ON e.role_id = r.role_id
            INNER JOIN departments d ON e.department_id = d.department_id
            WHERE e.status = 'On Leave'
            ORDER BY e.leave_until
        """)

    def get_hr_stats(self):
        """Enhanced stats for HR dashboard."""
        row = self.fetch("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN e.status='Active' THEN 1 ELSE 0 END) AS active,
                   SUM(CASE WHEN e.status='On Leave' THEN 1 ELSE 0 END) AS on_leave,
                   SUM(CASE WHEN e.status='Inactive' THEN 1 ELSE 0 END) AS inactive,
                   COALESCE(AVG(e.salary), 0) AS avg_salary,
                   COALESCE(SUM(CASE WHEN e.status='Active' THEN e.salary ELSE 0 END), 0) AS total_payroll
            FROM employees e
        """, one=True)
        return row or {"total": 0, "active": 0, "on_leave": 0, "inactive": 0,
                       "avg_salary": 0, "total_payroll": 0}

    def get_payroll_summary(self):
        """Return payroll breakdown by department."""
        return self.fetch("""
            SELECT d.department_name,
                   COUNT(e.employee_id) AS headcount,
                   COALESCE(SUM(e.salary), 0) AS total_salary,
                   COALESCE(AVG(e.salary), 0) AS avg_salary
            FROM departments d
            LEFT JOIN employees e ON d.department_id = e.department_id AND e.status = 'Active'
            GROUP BY d.department_id, d.department_name
            HAVING headcount > 0
            ORDER BY total_salary DESC
        """)

    def get_employment_type_counts(self):
        """Return employee counts by employment type."""
        return self.fetch("""
            SELECT employment_type, COUNT(*) AS cnt
            FROM employees WHERE status = 'Active'
            GROUP BY employment_type ORDER BY cnt DESC
        """)

    def update_employee_salary(self, employee_id, salary):
        """Update the salary of an employee."""
        if self.exec("UPDATE employees SET salary=%s WHERE employee_id=%s", (salary, employee_id)):
            self.log_activity("Edited", "Employee", f"Salary updated for employee ID {employee_id}")
            return True
        return False

    def add_employee(self, data):
        first, last = self._split_name(data["name"])
        role_id = self._lookup_role_id(data["role"])
        dept_id = self._lookup_dept_id(data["dept"])
        if not role_id or not dept_id:
            missing = []
            if not role_id: missing.append(f"role '{data['role']}'")
            if not dept_id: missing.append(f"department '{data['dept']}'")
            return f"Unknown {' and '.join(missing)} in database."
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cols = ["first_name", "last_name", "role_id", "department_id",
                        "employment_type", "phone", "email", "hire_date",
                        "status", "notes"]
                vals = [first, last, role_id, dept_id, data["type"],
                        data.get("phone", ""), data.get("email", ""),
                        data.get("hire_date") or None, data["status"],
                        data.get("notes", "")]
                if "leave_from" in data:
                    cols.append("leave_from")
                    vals.append(data.get("leave_from") or None)
                if "leave_until" in data:
                    cols.append("leave_until")
                    vals.append(data.get("leave_until") or None)
                if "salary" in data:
                    cols.append("salary")
                    vals.append(data.get("salary") or None)
                if "emergency_contact" in data:
                    cols.append("emergency_contact")
                    vals.append(data.get("emergency_contact", ""))
                placeholders = ", ".join(["%s"] * len(vals))
                # Use COALESCE for hire_date so it defaults to today
                col_str = ", ".join(cols)
                sql = f"INSERT INTO employees ({col_str}) VALUES ({placeholders})"
                cur.execute(sql, vals)
                email = data.get("email", "")
                if email:
                    cur.execute("SELECT user_id FROM users WHERE email=%s", (email,))
                    if not cur.fetchone():
                        # Auto-generate password: role_lowercase + "123"
                        role_lower = data["role"].lower().replace(" ", "")
                        pw = f"{role_lower}123"
                        cur.execute(
                            "INSERT INTO users (email,password,full_name,role_id,must_change_password) "
                            "VALUES (%s,%s,%s,%s,1)",
                            (email, pw, data["name"], role_id))
                conn.commit()
            self.log_activity("Created", "Employee", data["name"])
            return True
        except Exception as e:
            import traceback; traceback.print_exc()
            return str(e)

    def update_employee(self, employee_id, data, old_email=""):
        first, last = self._split_name(data["name"])
        role_id = self._lookup_role_id(data["role"])
        dept_id = self._lookup_dept_id(data["dept"])
        if not role_id or not dept_id:
            missing = []
            if not role_id: missing.append(f"role '{data['role']}'")
            if not dept_id: missing.append(f"department '{data['dept']}'")
            return f"Unknown {' and '.join(missing)} in database."
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                sets = ["first_name=%s", "last_name=%s", "role_id=%s",
                        "department_id=%s", "employment_type=%s", "phone=%s",
                        "email=%s", "status=%s", "notes=%s"]
                vals = [first, last, role_id, dept_id, data["type"],
                        data.get("phone", ""), data.get("email", ""),
                        data["status"], data.get("notes", "")]
                if "leave_from" in data:
                    sets.append("leave_from=%s")
                    vals.append(data.get("leave_from") or None)
                if "leave_until" in data:
                    sets.append("leave_until=%s")
                    vals.append(data.get("leave_until") or None)
                if "salary" in data:
                    sets.append("salary=%s")
                    vals.append(data.get("salary") or None)
                if "emergency_contact" in data:
                    sets.append("emergency_contact=%s")
                    vals.append(data.get("emergency_contact", ""))
                vals.append(employee_id)
                sql = f"UPDATE employees SET {', '.join(sets)} WHERE employee_id=%s"
                cur.execute(sql, vals)
                new_email = data.get("email", "")
                lookup = old_email or new_email
                if lookup and new_email:
                    # Try to update the existing user row by old email
                    cur.execute("UPDATE users SET email=%s, full_name=%s, role_id=%s WHERE email=%s",
                                (new_email, data["name"], role_id, lookup))
                    # If no user row matched (e.g. old_email didn't exist), create one
                    if cur.rowcount == 0:
                        cur.execute("SELECT user_id FROM users WHERE email=%s", (new_email,))
                        if not cur.fetchone():
                            role_lower = data["role"].lower().replace(" ", "")
                            pw = f"{role_lower}123"
                            cur.execute(
                                "INSERT INTO users (email,password,full_name,role_id,must_change_password) "
                                "VALUES (%s,%s,%s,%s,1)",
                                (new_email, pw, data["name"], role_id))
                conn.commit()
            self.log_activity("Edited", "Employee", data["name"])
            return True
        except Exception as e:
            import traceback; traceback.print_exc()
            return str(e)

    def delete_employee(self, employee_id):
        row = self.fetch("SELECT email, CONCAT(first_name,' ',last_name) AS n FROM employees WHERE employee_id=%s",
                         (employee_id,), one=True)
        queries = [
            ("DELETE FROM queue_entries WHERE doctor_id=%s", (employee_id,)),
            ("DELETE FROM employees WHERE employee_id=%s", (employee_id,)),
        ]
        if row and row.get("email"):
            queries.append(("DELETE FROM users WHERE email=%s", (row["email"],)))
        if self.exec_many(queries) is not False:
            self.log_activity("Deleted", "Employee", row["n"] if row else str(employee_id))
            return True
        return False

    def get_employee_stats(self):
        row = self.fetch("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN r.role_name='Doctor' THEN 1 ELSE 0 END) AS doctors,
                   SUM(CASE WHEN e.status='Active' THEN 1 ELSE 0 END) AS active,
                   SUM(CASE WHEN e.status='On Leave' THEN 1 ELSE 0 END) AS on_leave
            FROM employees e INNER JOIN roles r ON e.role_id = r.role_id
        """, one=True)
        return row or {"total": 0, "doctors": 0, "active": 0, "on_leave": 0}

    def get_department_counts(self):
        return self.fetch("""
            SELECT d.department_name, COUNT(e.employee_id) AS cnt
            FROM departments d LEFT JOIN employees e ON d.department_id = e.department_id
            GROUP BY d.department_id, d.department_name HAVING cnt > 0 ORDER BY cnt DESC
        """)

    def get_employee_performance(self, employee_id):
        row = self.fetch("""
            SELECT COUNT(a.appointment_id) AS total_appts,
                   SUM(CASE WHEN a.status='Completed' THEN 1 ELSE 0 END) AS completed,
                   COALESCE(SUM(CASE WHEN a.status='Completed' THEN s.price ELSE 0 END),0) AS revenue
            FROM appointments a INNER JOIN services s ON a.service_id = s.service_id
            WHERE a.doctor_id = %s
        """, (employee_id,), one=True)
        return row or {"total_appts": 0, "completed": 0, "revenue": 0}

    def get_employee_appointments(self, employee_id):
        return self.fetch("""
            SELECT a.appointment_date, a.appointment_time,
                   CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                   s.service_name, a.status
            FROM appointments a
            INNER JOIN patients p ON a.patient_id = p.patient_id
            INNER JOIN services s ON a.service_id = s.service_id
            WHERE a.doctor_id = %s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC LIMIT 20
        """, (employee_id,))

    def get_user_password(self, email):
        row = self.fetch("SELECT password FROM users WHERE email=%s", (email,), one=True)
        return row["password"] if row else ""

    def update_user_password(self, email, new_password):
        """Update the password for a user. Creates the user record if it doesn't exist."""
        if not email:
            return False
        # Try updating existing user
        result = self.exec("UPDATE users SET password=%s WHERE email=%s", (new_password, email))
        if result:
            return True
        # No user record found — create one
        row = self.fetch(
            "SELECT CONCAT(e.first_name,' ',e.last_name) AS full_name, e.role_id "
            "FROM employees e WHERE e.email=%s", (email,), one=True)
        if row:
            self.exec(
                "INSERT INTO users (email, password, full_name, role_id) VALUES (%s,%s,%s,%s)",
                (email, new_password, row["full_name"], row["role_id"]))
            return True
        return False

    # ── Leave Request System ──────────────────────────────────────

    def get_employee_id_by_email(self, email):
        """Look up employee_id from email."""
        row = self.fetch("SELECT employee_id FROM employees WHERE email=%s",
                         (email,), one=True)
        return row["employee_id"] if row else None

    def submit_leave_request(self, employee_id, leave_from, leave_until, reason):
        """Employee submits a leave request."""
        try:
            self.exec(
                "INSERT INTO leave_requests (employee_id, leave_from, leave_until, reason) "
                "VALUES (%s, %s, %s, %s)",
                (employee_id, leave_from, leave_until, reason))
            # Get employee name for log
            row = self.fetch(
                "SELECT CONCAT(first_name,' ',last_name) AS n FROM employees WHERE employee_id=%s",
                (employee_id,), one=True)
            name = row["n"] if row else str(employee_id)
            self.log_activity("Requested", "Leave",
                              f"{name} requested leave {leave_from} to {leave_until}")
            return True
        except Exception as e:
            import traceback; traceback.print_exc()
            return str(e)

    def get_pending_leave_requests(self):
        """HR: get all pending leave requests."""
        return self.fetch("""
            SELECT lr.request_id, lr.employee_id,
                   CONCAT(e.first_name,' ',e.last_name) AS employee_name,
                   r.role_name, d.department_name,
                   lr.leave_from, lr.leave_until, lr.reason, lr.status, lr.created_at
            FROM leave_requests lr
            INNER JOIN employees e ON lr.employee_id = e.employee_id
            INNER JOIN roles r ON e.role_id = r.role_id
            INNER JOIN departments d ON e.department_id = d.department_id
            WHERE lr.status = 'Pending'
            ORDER BY lr.created_at ASC
        """)

    def get_all_leave_requests(self):
        """HR: get all leave requests (all statuses)."""
        return self.fetch("""
            SELECT lr.request_id, lr.employee_id,
                   CONCAT(e.first_name,' ',e.last_name) AS employee_name,
                   r.role_name, d.department_name,
                   lr.leave_from, lr.leave_until, lr.reason,
                   lr.status, lr.hr_note, lr.decided_at, lr.created_at,
                   CASE WHEN lr.hr_decided_by IS NOT NULL
                        THEN (SELECT CONCAT(h.first_name,' ',h.last_name)
                              FROM employees h WHERE h.employee_id = lr.hr_decided_by)
                        ELSE NULL END AS decided_by_name
            FROM leave_requests lr
            INNER JOIN employees e ON lr.employee_id = e.employee_id
            INNER JOIN roles r ON e.role_id = r.role_id
            INNER JOIN departments d ON e.department_id = d.department_id
            ORDER BY lr.created_at DESC
        """)

    def get_my_leave_requests(self, employee_id):
        """Employee: get their own leave requests."""
        return self.fetch("""
            SELECT lr.request_id, lr.leave_from, lr.leave_until, lr.reason,
                   lr.status, lr.hr_note, lr.decided_at, lr.created_at
            FROM leave_requests lr
            WHERE lr.employee_id = %s
            ORDER BY lr.created_at DESC
        """, (employee_id,))

    def approve_leave_request(self, request_id, hr_employee_id):
        """HR approves a leave request. Updates employee status to On Leave."""
        try:
            conn = self._get_connection()
            with conn.cursor(dictionary=True) as cur:
                # Get request details
                cur.execute("SELECT * FROM leave_requests WHERE request_id=%s AND status='Pending'",
                            (request_id,))
                req = cur.fetchone()
                if not req:
                    return "Request not found or already decided."
                emp_id = req["employee_id"]
                # Update request
                cur.execute(
                    "UPDATE leave_requests SET status='Approved', hr_decided_by=%s, "
                    "decided_at=NOW() WHERE request_id=%s",
                    (hr_employee_id, request_id))
                # Update employee status to On Leave with dates
                cur.execute(
                    "UPDATE employees SET status='On Leave', leave_from=%s, leave_until=%s "
                    "WHERE employee_id=%s",
                    (req["leave_from"], req["leave_until"], emp_id))
                # Get names for notification and log
                cur.execute("SELECT CONCAT(first_name,' ',last_name) AS n FROM employees WHERE employee_id=%s",
                            (emp_id,))
                emp_row = cur.fetchone()
                emp_name = emp_row["n"] if emp_row else str(emp_id)
                # Create notification for employee
                msg = (f"Your leave request ({req['leave_from']} to {req['leave_until']}) "
                       f"has been approved.")
                cur.execute(
                    "INSERT INTO notifications (employee_id, message) VALUES (%s, %s)",
                    (emp_id, msg))
                conn.commit()
            self.log_activity("Approved", "Leave",
                              f"Approved leave for {emp_name} ({req['leave_from']} to {req['leave_until']})")
            return True
        except Exception as e:
            import traceback; traceback.print_exc()
            return str(e)

    def decline_leave_request(self, request_id, hr_employee_id, hr_note):
        """HR declines a leave request with a reason/note."""
        try:
            conn = self._get_connection()
            with conn.cursor(dictionary=True) as cur:
                cur.execute("SELECT * FROM leave_requests WHERE request_id=%s AND status='Pending'",
                            (request_id,))
                req = cur.fetchone()
                if not req:
                    return "Request not found or already decided."
                emp_id = req["employee_id"]
                cur.execute(
                    "UPDATE leave_requests SET status='Declined', hr_decided_by=%s, "
                    "hr_note=%s, decided_at=NOW() WHERE request_id=%s",
                    (hr_employee_id, hr_note, request_id))
                # Get employee name
                cur.execute("SELECT CONCAT(first_name,' ',last_name) AS n FROM employees WHERE employee_id=%s",
                            (emp_id,))
                emp_row = cur.fetchone()
                emp_name = emp_row["n"] if emp_row else str(emp_id)
                # Notification
                msg = (f"Your leave request ({req['leave_from']} to {req['leave_until']}) "
                       f"has been declined. Reason: {hr_note}")
                cur.execute(
                    "INSERT INTO notifications (employee_id, message) VALUES (%s, %s)",
                    (emp_id, msg))
                conn.commit()
            self.log_activity("Declined", "Leave",
                              f"Declined leave for {emp_name}: {hr_note}")
            return True
        except Exception as e:
            import traceback; traceback.print_exc()
            return str(e)

    def get_unread_notifications(self, employee_id):
        """Get unread notifications for an employee."""
        return self.fetch(
            "SELECT notification_id, message, created_at FROM notifications "
            "WHERE employee_id=%s AND is_read=0 ORDER BY created_at DESC",
            (employee_id,))

    def mark_notifications_read(self, employee_id):
        """Mark all notifications as read for an employee."""
        self.exec("UPDATE notifications SET is_read=1 WHERE employee_id=%s AND is_read=0",
                  (employee_id,))
