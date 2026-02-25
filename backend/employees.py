"""Employee backend – CRUD and performance queries."""


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

    def add_employee(self, data):
        first, last = self._split_name(data["name"])
        role_id = self._lookup_role_id(data["role"])
        dept_id = self._lookup_dept_id(data["dept"])
        if not role_id or not dept_id:
            return False
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO employees (first_name, last_name, role_id, department_id,
                        employment_type, phone, email, hire_date, status, notes, leave_from, leave_until)
                    VALUES (%s,%s,%s,%s,%s,%s,%s, COALESCE(%s,CURDATE()), %s,%s,%s,%s)
                """, (first, last, role_id, dept_id, data["type"],
                      data.get("phone",""), data.get("email",""),
                      data.get("hire_date") or None, data["status"],
                      data.get("notes",""), data.get("leave_from") or None,
                      data.get("leave_until") or None))
                email = data.get("email","")
                if email:
                    cur.execute("SELECT user_id FROM users WHERE email=%s", (email,))
                    if not cur.fetchone():
                        pw = data.get("password","").strip() or "password123"
                        cur.execute("INSERT INTO users (email,password,full_name,role_id) VALUES (%s,%s,%s,%s)",
                                    (email, pw, data["name"], role_id))
                conn.commit()
            self.log_activity("Created", "Employee", data["name"])
            return True
        except Exception:
            return False

    def update_employee(self, employee_id, data, old_email=""):
        first, last = self._split_name(data["name"])
        role_id = self._lookup_role_id(data["role"])
        dept_id = self._lookup_dept_id(data["dept"])
        if not role_id or not dept_id:
            return False
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE employees SET first_name=%s, last_name=%s, role_id=%s, department_id=%s,
                        employment_type=%s, phone=%s, email=%s, status=%s, notes=%s,
                        leave_from=%s, leave_until=%s
                    WHERE employee_id=%s
                """, (first, last, role_id, dept_id, data["type"],
                      data.get("phone",""), data.get("email",""), data["status"],
                      data.get("notes",""), data.get("leave_from") or None,
                      data.get("leave_until") or None, employee_id))
                lookup = old_email or data.get("email","")
                if lookup:
                    cur.execute("UPDATE users SET email=%s, full_name=%s, role_id=%s WHERE email=%s",
                                (data.get("email",""), data["name"], role_id, lookup))
                conn.commit()
            self.log_activity("Edited", "Employee", data["name"])
            return True
        except Exception:
            return False

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
        return bool(self.exec("UPDATE users SET password=%s WHERE email=%s", (new_password, email)))
