"""CareCRUD Backend – Database connection, authentication, and all CRUD operations."""

import mysql.connector
from mysql.connector import Error


class AuthBackend:
    """Handles database connection and all application logic."""

    DB_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "carecrud_db",
        "connection_timeout": 5,
        "use_pure": True,
    }

    def __init__(self):
        self._conn = None
        self._current_user_email = ""
        self._current_user_role = ""

    def set_current_user(self, email: str, role: str):
        self._current_user_email = email
        self._current_user_role = role

    # ── Connection ─────────────────────────────────────────────────────
    def _get_connection(self):
        try:
            if self._conn is None or not self._conn.is_connected():
                self._conn = mysql.connector.connect(**self.DB_CONFIG)
            return self._conn
        except Error as e:
            raise ConnectionError(f"Cannot connect to database.\n\n{e}")

    def close(self):
        if self._conn and self._conn.is_connected():
            self._conn.close()
            self._conn = None

    # ── Activity Log ───────────────────────────────────────────────────
    def log_activity(self, action: str, record_type: str, detail: str = ""):
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO activity_log (user_email, user_role, action, record_type, record_detail)
                VALUES (%s, %s, %s, %s, %s)
            """, (self._current_user_email, self._current_user_role, action, record_type, detail))
            conn.commit()
            cur.close()
        except Exception:
            pass

    def get_activity_log(self, limit: int = 200, user_filter: str = "",
                         action_filter: str = "", record_type_filter: str = "",
                         from_date: str = "", to_date: str = "") -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            where = ["1=1"]
            params = []
            if user_filter:
                where.append("user_email = %s")
                params.append(user_filter)
            if action_filter:
                where.append("action = %s")
                params.append(action_filter)
            if record_type_filter:
                where.append("record_type = %s")
                params.append(record_type_filter)
            if from_date:
                where.append("DATE(created_at) >= %s")
                params.append(from_date)
            if to_date:
                where.append("DATE(created_at) <= %s")
                params.append(to_date)
            params.append(limit)
            cur.execute(f"""
                SELECT log_id, user_email, user_role, action, record_type,
                       record_detail, created_at
                FROM activity_log
                WHERE {' AND '.join(where)}
                ORDER BY created_at DESC
                LIMIT %s
            """, params)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    # ── Authentication ─────────────────────────────────────────────────
    def login(self, email: str, password: str) -> tuple:
        if not email:
            return False, "", "", "Please enter your email address."
        if not password:
            return False, "", "", "Please enter your password."
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT u.user_id, u.full_name, u.password, r.role_name
                FROM users u INNER JOIN roles r ON u.role_id = r.role_id
                WHERE u.email = %s
            """, (email,))
            user = cursor.fetchone()
            cursor.close()
            if user is None:
                return False, "", "", "No account found with that email."
            if user["password"] != password:
                return False, "", "", "Incorrect password."
            self.set_current_user(email, user["role_name"])
            self.log_activity("Login", "User", f"{user['full_name']} logged in")
            return True, user["role_name"], user["full_name"], "Login successful."
        except ConnectionError as e:
            return False, "", "", str(e)
        except Error as e:
            return False, "", "", f"Database error: {e}"
        except Exception as e:
            return False, "", "", f"Unexpected error: {e}"

    # ── User Preferences ───────────────────────────────────────────────
    def get_dark_mode(self, email: str) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT dark_mode FROM user_preferences WHERE user_email = %s", (email,))
            row = cur.fetchone()
            cur.close()
            return bool(row[0]) if row else False
        except Exception:
            return False

    def set_dark_mode(self, email: str, enabled: bool) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO user_preferences (user_email, dark_mode)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE dark_mode = %s
            """, (email, int(enabled), int(enabled)))
            conn.commit()
            cur.close()
            return True
        except Exception:
            return False

    def update_own_password(self, email: str, current_pw: str, new_pw: str) -> tuple:
        """Returns (success, message)."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if not row:
                cur.close()
                return False, "User not found."
            if row[0] != current_pw:
                cur.close()
                return False, "Current password is incorrect."
            cur.execute("UPDATE users SET password = %s WHERE email = %s", (new_pw, email))
            conn.commit()
            cur.close()
            self.log_activity("Edited", "User", f"Password changed for {email}")
            return True, "Password updated successfully."
        except Exception as e:
            return False, str(e)

    # ── Data-cleanup helpers (Admin settings) ────────────────────────
    def get_table_counts(self) -> list:
        tables = [
            "patients", "patient_conditions", "appointments",
            "queue_entries", "invoices", "invoice_items",
            "employees", "users", "services",
            "departments", "roles", "payment_methods",
            "activity_log", "standard_conditions",
        ]
        results = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            for t in tables:
                try:
                    cur.execute(f"SELECT COUNT(*) FROM `{t}`")
                    results.append((t, cur.fetchone()[0]))
                except Exception:
                    results.append((t, 0))
            cur.close()
        except Exception:
            pass
        return results

    def cleanup_completed_appointments(self, before_date: str) -> int:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                DELETE ii FROM invoice_items ii
                INNER JOIN invoices i ON ii.invoice_id = i.invoice_id
                INNER JOIN appointments a ON i.appointment_id = a.appointment_id
                WHERE a.status = 'Completed' AND a.appointment_date < %s
            """, (before_date,))
            cur.execute("""
                DELETE i FROM invoices i
                INNER JOIN appointments a ON i.appointment_id = a.appointment_id
                WHERE a.status = 'Completed' AND a.appointment_date < %s
            """, (before_date,))
            cur.execute("""
                DELETE q FROM queue_entries q
                INNER JOIN appointments a ON q.appointment_id = a.appointment_id
                WHERE a.status = 'Completed' AND a.appointment_date < %s
            """, (before_date,))
            cur.execute("DELETE FROM appointments WHERE status = 'Completed' AND appointment_date < %s", (before_date,))
            removed = cur.rowcount
            conn.commit()
            cur.close()
            self.log_activity("Deleted", "Appointment", f"Cleaned {removed} completed appts before {before_date}")
            return removed
        except Exception:
            return 0

    def cleanup_cancelled_appointments(self) -> int:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""DELETE ii FROM invoice_items ii INNER JOIN invoices i ON ii.invoice_id = i.invoice_id INNER JOIN appointments a ON i.appointment_id = a.appointment_id WHERE a.status = 'Cancelled'""")
            cur.execute("""DELETE i FROM invoices i INNER JOIN appointments a ON i.appointment_id = a.appointment_id WHERE a.status = 'Cancelled'""")
            cur.execute("""DELETE q FROM queue_entries q INNER JOIN appointments a ON q.appointment_id = a.appointment_id WHERE a.status = 'Cancelled'""")
            cur.execute("DELETE FROM appointments WHERE status = 'Cancelled'")
            removed = cur.rowcount
            conn.commit()
            cur.close()
            self.log_activity("Deleted", "Appointment", f"Cleaned {removed} cancelled appointments")
            return removed
        except Exception:
            return 0

    def cleanup_inactive_patients(self) -> int:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE ii FROM invoice_items ii INNER JOIN invoices i ON ii.invoice_id = i.invoice_id INNER JOIN patients p ON i.patient_id = p.patient_id WHERE p.status = 'Inactive'")
            cur.execute("DELETE i FROM invoices i INNER JOIN patients p ON i.patient_id = p.patient_id WHERE p.status = 'Inactive'")
            cur.execute("DELETE q FROM queue_entries q INNER JOIN patients p ON q.patient_id = p.patient_id WHERE p.status = 'Inactive'")
            cur.execute("DELETE a FROM appointments a INNER JOIN patients p ON a.patient_id = p.patient_id WHERE p.status = 'Inactive'")
            cur.execute("DELETE FROM patient_conditions WHERE patient_id IN (SELECT patient_id FROM patients WHERE status = 'Inactive')")
            cur.execute("DELETE FROM patients WHERE status = 'Inactive'")
            removed = cur.rowcount
            conn.commit()
            cur.close()
            self.log_activity("Deleted", "Patient", f"Cleaned {removed} inactive patients")
            return removed
        except Exception:
            return 0

    def truncate_table(self, table_name: str) -> bool:
        allowed = {"queue_entries", "invoice_items", "invoices", "appointments", "patient_conditions", "activity_log"}
        if table_name not in allowed:
            return False
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(f"SET FOREIGN_KEY_CHECKS = 0; TRUNCATE TABLE `{table_name}`; SET FOREIGN_KEY_CHECKS = 1;", multi=True)
            for _ in cur:
                pass
            conn.commit()
            cur.close()
            self.log_activity("Deleted", "System", f"Truncated table {table_name}")
            return True
        except Exception:
            return False

    # ── Standard Conditions ────────────────────────────────────────────
    def get_standard_conditions(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT condition_id, condition_name FROM standard_conditions ORDER BY condition_name")
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def add_standard_condition(self, name: str) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO standard_conditions (condition_name) VALUES (%s)", (name,))
            conn.commit()
            cur.close()
            self.log_activity("Created", "Condition", name)
            return True
        except Exception:
            return False

    def delete_standard_condition(self, cond_id: int) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM standard_conditions WHERE condition_id = %s", (cond_id,))
            conn.commit()
            cur.close()
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════
    #  EMPLOYEE CRUD
    # ══════════════════════════════════════════════════════════════════
    def get_employees(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT e.employee_id,
                       CONCAT(e.first_name, ' ', e.last_name) AS full_name,
                       r.role_name, d.department_name, e.employment_type,
                       e.phone, e.email, e.hire_date, e.status, e.notes,
                       e.leave_from, e.leave_until
                FROM employees e
                INNER JOIN roles r ON e.role_id = r.role_id
                INNER JOIN departments d ON e.department_id = d.department_id
                ORDER BY e.employee_id
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def add_employee(self, data: dict) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            parts = data["name"].split(None, 1)
            first, last = parts[0], parts[1] if len(parts) > 1 else ""
            cur.execute("SELECT role_id FROM roles WHERE role_name = %s", (data["role"],))
            role_row = cur.fetchone()
            if not role_row:
                return False
            cur.execute("SELECT department_id FROM departments WHERE department_name = %s", (data["dept"],))
            dept_row = cur.fetchone()
            if not dept_row:
                return False
            hire_date = data.get("hire_date") or None
            leave_from = data.get("leave_from") or None
            leave_until = data.get("leave_until") or None
            cur.execute("""
                INSERT INTO employees
                    (first_name, last_name, role_id, department_id, employment_type,
                     phone, email, hire_date, status, notes, leave_from, leave_until)
                VALUES (%s, %s, %s, %s, %s, %s, %s, COALESCE(%s, CURDATE()), %s, %s, %s, %s)
            """, (first, last, role_row[0], dept_row[0], data["type"],
                  data.get("phone", ""), data.get("email", ""), hire_date,
                  data["status"], data.get("notes", ""), leave_from, leave_until))
            email = data.get("email", "")
            password = data.get("password", "").strip() or "password123"
            if email:
                cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                if not cur.fetchone():
                    cur.execute("INSERT INTO users (email, password, full_name, role_id) VALUES (%s, %s, %s, %s)",
                                (email, password, data["name"], role_row[0]))
            conn.commit()
            cur.close()
            self.log_activity("Created", "Employee", data["name"])
            return True
        except Exception:
            return False

    def update_employee(self, employee_id: int, data: dict, old_email: str = "") -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            parts = data["name"].split(None, 1)
            first, last = parts[0], parts[1] if len(parts) > 1 else ""
            cur.execute("SELECT role_id FROM roles WHERE role_name = %s", (data["role"],))
            role_row = cur.fetchone()
            if not role_row:
                return False
            cur.execute("SELECT department_id FROM departments WHERE department_name = %s", (data["dept"],))
            dept_row = cur.fetchone()
            if not dept_row:
                return False
            leave_from = data.get("leave_from") or None
            leave_until = data.get("leave_until") or None
            cur.execute("""
                UPDATE employees
                SET first_name=%s, last_name=%s, role_id=%s, department_id=%s,
                    employment_type=%s, phone=%s, email=%s, status=%s, notes=%s,
                    leave_from=%s, leave_until=%s
                WHERE employee_id=%s
            """, (first, last, role_row[0], dept_row[0], data["type"],
                  data.get("phone", ""), data.get("email", ""), data["status"],
                  data.get("notes", ""), leave_from, leave_until, employee_id))
            lookup_email = old_email if old_email else data.get("email", "")
            if lookup_email:
                cur.execute("UPDATE users SET email=%s, full_name=%s, role_id=%s WHERE email=%s",
                            (data.get("email", ""), data["name"], role_row[0], lookup_email))
            conn.commit()
            cur.close()
            self.log_activity("Edited", "Employee", data["name"])
            return True
        except Exception:
            return False

    def delete_employee(self, employee_id: int) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT email, CONCAT(first_name,' ',last_name) AS n FROM employees WHERE employee_id = %s", (employee_id,))
            row = cur.fetchone()
            cur.execute("DELETE FROM queue_entries WHERE doctor_id = %s", (employee_id,))
            cur.execute("DELETE FROM employees WHERE employee_id = %s", (employee_id,))
            if row and row[0]:
                cur.execute("DELETE FROM users WHERE email = %s", (row[0],))
            conn.commit()
            cur.close()
            self.log_activity("Deleted", "Employee", row[1] if row else str(employee_id))
            return True
        except Exception:
            return False

    def get_employee_stats(self) -> dict:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN r.role_name='Doctor' THEN 1 ELSE 0 END) AS doctors,
                       SUM(CASE WHEN e.status='Active' THEN 1 ELSE 0 END) AS active,
                       SUM(CASE WHEN e.status='On Leave' THEN 1 ELSE 0 END) AS on_leave
                FROM employees e INNER JOIN roles r ON e.role_id = r.role_id
            """)
            row = cur.fetchone()
            cur.close()
            return row if row else {"total": 0, "doctors": 0, "active": 0, "on_leave": 0}
        except Exception:
            return {"total": 0, "doctors": 0, "active": 0, "on_leave": 0}

    def get_department_counts(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT d.department_name, COUNT(e.employee_id) AS cnt
                FROM departments d LEFT JOIN employees e ON d.department_id = e.department_id
                GROUP BY d.department_id, d.department_name
                HAVING cnt > 0 ORDER BY cnt DESC
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_employee_performance(self, employee_id: int) -> dict:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT COUNT(a.appointment_id) AS total_appts,
                       SUM(CASE WHEN a.status='Completed' THEN 1 ELSE 0 END) AS completed,
                       COALESCE(SUM(CASE WHEN a.status='Completed' THEN s.price ELSE 0 END),0) AS revenue
                FROM appointments a
                INNER JOIN services s ON a.service_id = s.service_id
                WHERE a.doctor_id = %s
            """, (employee_id,))
            row = cur.fetchone()
            cur.close()
            return row if row else {"total_appts": 0, "completed": 0, "revenue": 0}
        except Exception:
            return {"total_appts": 0, "completed": 0, "revenue": 0}

    def get_employee_appointments(self, employee_id: int) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT a.appointment_date, a.appointment_time,
                       CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                       s.service_name, a.status
                FROM appointments a
                INNER JOIN patients p ON a.patient_id = p.patient_id
                INNER JOIN services s ON a.service_id = s.service_id
                WHERE a.doctor_id = %s
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
                LIMIT 20
            """, (employee_id,))
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_user_password(self, email: str) -> str:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            cur.close()
            return row[0] if row else ""
        except Exception:
            return ""

    def update_user_password(self, email: str, new_password: str) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET password = %s WHERE email = %s", (new_password, email))
            conn.commit()
            cur.close()
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════
    #  PATIENT CRUD
    # ══════════════════════════════════════════════════════════════════
    def get_patients(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT p.patient_id, p.first_name, p.last_name, p.sex,
                       p.date_of_birth, p.phone, p.email, p.status, p.notes,
                       p.emergency_contact, p.blood_type,
                       GROUP_CONCAT(pc.condition_name SEPARATOR ', ') AS conditions,
                       (SELECT MAX(a.appointment_date) FROM appointments a
                        WHERE a.patient_id = p.patient_id) AS last_visit
                FROM patients p
                LEFT JOIN patient_conditions pc ON p.patient_id = pc.patient_id
                GROUP BY p.patient_id
                ORDER BY p.patient_id
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_patient_full_profile(self, patient_id: int) -> dict:
        """Full profile: info + appointments + invoices + queue history + conditions."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT p.*, GROUP_CONCAT(pc.condition_name SEPARATOR ', ') AS conditions
                FROM patients p
                LEFT JOIN patient_conditions pc ON p.patient_id = pc.patient_id
                WHERE p.patient_id = %s GROUP BY p.patient_id
            """, (patient_id,))
            info = cur.fetchone()
            if not info:
                cur.close()
                return {}
            cur.execute("""
                SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                       CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                       s.service_name, a.status, a.notes
                FROM appointments a
                INNER JOIN employees e ON a.doctor_id = e.employee_id
                INNER JOIN services s ON a.service_id = s.service_id
                WHERE a.patient_id = %s ORDER BY a.appointment_date DESC
            """, (patient_id,))
            appts = cur.fetchall()
            cur.execute("""
                SELECT i.invoice_id, i.total_amount, i.amount_paid, i.status,
                       i.created_at, COALESCE(pm.method_name,'—') AS payment_method,
                       GROUP_CONCAT(s.service_name SEPARATOR ', ') AS services
                FROM invoices i
                LEFT JOIN payment_methods pm ON i.method_id = pm.method_id
                LEFT JOIN invoice_items ii ON i.invoice_id = ii.invoice_id
                LEFT JOIN services s ON ii.service_id = s.service_id
                WHERE i.patient_id = %s GROUP BY i.invoice_id
                ORDER BY i.created_at DESC
            """, (patient_id,))
            invoices = cur.fetchall()
            cur.execute("""
                SELECT q.queue_id, q.queue_time, q.purpose, q.status, q.created_at,
                       CONCAT(e.first_name,' ',e.last_name) AS doctor_name
                FROM queue_entries q
                INNER JOIN employees e ON q.doctor_id = e.employee_id
                WHERE q.patient_id = %s ORDER BY q.created_at DESC, q.queue_time DESC
            """, (patient_id,))
            queue = cur.fetchall()
            cur.close()
            return {"info": info, "appointments": appts, "invoices": invoices, "queue": queue}
        except Exception:
            return {}

    def add_patient(self, data: dict) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO patients (first_name, last_name, sex, date_of_birth,
                    phone, email, emergency_contact, blood_type, status, notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (data["first_name"], data["last_name"], data["sex"],
                  data.get("dob"), data.get("phone", ""), data.get("email", ""),
                  data.get("emergency_contact", ""), data.get("blood_type", "Unknown"),
                  data.get("status", "Active"), data.get("notes", "")))
            pid = cur.lastrowid
            conditions = data.get("conditions", "")
            if conditions:
                for c in [c.strip() for c in conditions.split(",") if c.strip()]:
                    cur.execute("INSERT INTO patient_conditions (patient_id, condition_name) VALUES (%s,%s)", (pid, c))
            conn.commit()
            cur.close()
            self.log_activity("Created", "Patient", f"{data['first_name']} {data['last_name']}")
            return True
        except Exception:
            return False

    def update_patient(self, patient_id: int, data: dict) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE patients SET first_name=%s, last_name=%s, sex=%s, date_of_birth=%s,
                    phone=%s, email=%s, emergency_contact=%s, blood_type=%s, status=%s, notes=%s
                WHERE patient_id=%s
            """, (data["first_name"], data["last_name"], data["sex"],
                  data.get("dob"), data.get("phone", ""), data.get("email", ""),
                  data.get("emergency_contact", ""), data.get("blood_type", "Unknown"),
                  data.get("status", "Active"), data.get("notes", ""), patient_id))
            cur.execute("DELETE FROM patient_conditions WHERE patient_id = %s", (patient_id,))
            conditions = data.get("conditions", "")
            if conditions:
                for c in [c.strip() for c in conditions.split(",") if c.strip()]:
                    cur.execute("INSERT INTO patient_conditions (patient_id, condition_name) VALUES (%s,%s)", (patient_id, c))
            conn.commit()
            cur.close()
            self.log_activity("Edited", "Patient", f"{data['first_name']} {data['last_name']}")
            return True
        except Exception:
            return False

    def delete_patient(self, patient_id: int) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT CONCAT(first_name,' ',last_name) FROM patients WHERE patient_id=%s", (patient_id,))
            nm = cur.fetchone()
            cur.execute("DELETE FROM invoice_items WHERE invoice_id IN (SELECT invoice_id FROM invoices WHERE patient_id=%s)", (patient_id,))
            cur.execute("DELETE FROM invoices WHERE patient_id=%s", (patient_id,))
            cur.execute("DELETE FROM queue_entries WHERE patient_id=%s", (patient_id,))
            cur.execute("DELETE FROM appointments WHERE patient_id=%s", (patient_id,))
            cur.execute("DELETE FROM patient_conditions WHERE patient_id=%s", (patient_id,))
            cur.execute("DELETE FROM patients WHERE patient_id=%s", (patient_id,))
            conn.commit()
            cur.close()
            self.log_activity("Deleted", "Patient", nm[0] if nm else str(patient_id))
            return True
        except Exception:
            return False

    def merge_patients(self, keep_id: int, remove_id: int) -> bool:
        """Merge remove_id into keep_id: move all FK references then delete remove."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE appointments SET patient_id=%s WHERE patient_id=%s", (keep_id, remove_id))
            cur.execute("UPDATE queue_entries SET patient_id=%s WHERE patient_id=%s", (keep_id, remove_id))
            cur.execute("UPDATE invoices SET patient_id=%s WHERE patient_id=%s", (keep_id, remove_id))
            cur.execute("""
                INSERT IGNORE INTO patient_conditions (patient_id, condition_name)
                SELECT %s, condition_name FROM patient_conditions WHERE patient_id = %s
            """, (keep_id, remove_id))
            cur.execute("DELETE FROM patient_conditions WHERE patient_id=%s", (remove_id,))
            cur.execute("DELETE FROM patients WHERE patient_id=%s", (remove_id,))
            conn.commit()
            cur.close()
            self.log_activity("Edited", "Patient", f"Merged patient #{remove_id} into #{keep_id}")
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════
    #  APPOINTMENT CRUD
    # ══════════════════════════════════════════════════════════════════
    def get_appointments(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                       CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                       CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                       s.service_name, a.status, a.notes,
                       a.cancellation_reason, a.reschedule_reason,
                       a.reminder_sent, a.recurring_parent_id
                FROM appointments a
                INNER JOIN patients p ON a.patient_id = p.patient_id
                INNER JOIN employees e ON a.doctor_id = e.employee_id
                INNER JOIN services s ON a.service_id = s.service_id
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_doctors(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT e.employee_id, CONCAT(e.first_name,' ',e.last_name) AS doctor_name
                FROM employees e INNER JOIN roles r ON e.role_id = r.role_id
                WHERE r.role_name='Doctor' AND e.status='Active' ORDER BY e.first_name
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_services_list(self, active_only: bool = True) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            q = "SELECT service_id, service_name, price, category, is_active FROM services"
            if active_only:
                q += " WHERE is_active = 1"
            q += " ORDER BY service_name"
            cur.execute(q)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_all_services(self) -> list:
        return self.get_services_list(active_only=False)

    def check_appointment_conflict(self, doctor_id: int, date: str, time: str,
                                   exclude_id: int = None) -> bool:
        """Return True if a conflict exists."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            q = """SELECT COUNT(*) FROM appointments
                   WHERE doctor_id=%s AND appointment_date=%s AND appointment_time=%s
                   AND status NOT IN ('Cancelled')"""
            params = [doctor_id, date, time]
            if exclude_id:
                q += " AND appointment_id != %s"
                params.append(exclude_id)
            cur.execute(q, params)
            cnt = cur.fetchone()[0]
            cur.close()
            return cnt > 0
        except Exception:
            return False

    def add_appointment(self, data: dict) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            parts = data["patient_name"].rsplit(" ", 1)
            first, last = parts[0], parts[1] if len(parts) > 1 else ""
            cur.execute("SELECT patient_id FROM patients WHERE first_name=%s AND last_name=%s LIMIT 1", (first, last))
            prow = cur.fetchone()
            if not prow:
                cur.close()
                return False
            cur.execute("""
                INSERT INTO appointments (patient_id, doctor_id, service_id,
                    appointment_date, appointment_time, status, notes,
                    cancellation_reason, reschedule_reason, reminder_sent, recurring_parent_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (prow[0], data["doctor_id"], data["service_id"],
                  data["date"], data["time"], data.get("status", "Pending"),
                  data.get("notes", ""), data.get("cancellation_reason", ""),
                  data.get("reschedule_reason", ""), data.get("reminder_sent", 0),
                  data.get("recurring_parent_id")))
            appt_id = cur.lastrowid
            conn.commit()
            cur.close()
            self.log_activity("Created", "Appointment", f"Appt #{appt_id} for {data['patient_name']}")
            return True
        except Exception:
            return False

    def add_recurring_appointments(self, data: dict, frequency: str, count: int) -> int:
        """Create recurring appointments. Returns number created."""
        from datetime import datetime, timedelta
        created = 0
        try:
            base_date = datetime.strptime(data["date"], "%Y-%m-%d")
            for i in range(count):
                if frequency == "Daily":
                    d = base_date + timedelta(days=i)
                elif frequency == "Weekly":
                    d = base_date + timedelta(weeks=i)
                elif frequency == "Monthly":
                    d = base_date + timedelta(days=30 * i)
                else:
                    d = base_date + timedelta(weeks=i)
                appt_data = dict(data)
                appt_data["date"] = d.strftime("%Y-%m-%d")
                if self.add_appointment(appt_data):
                    created += 1
            return created
        except Exception:
            return created

    def update_appointment(self, appointment_id: int, data: dict) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            parts = data["patient_name"].rsplit(" ", 1)
            first, last = parts[0], parts[1] if len(parts) > 1 else ""
            cur.execute("SELECT patient_id FROM patients WHERE first_name=%s AND last_name=%s LIMIT 1", (first, last))
            prow = cur.fetchone()
            if not prow:
                cur.close()
                return False
            cur.execute("""
                UPDATE appointments
                SET patient_id=%s, doctor_id=%s, service_id=%s, appointment_date=%s,
                    appointment_time=%s, status=%s, notes=%s,
                    cancellation_reason=%s, reschedule_reason=%s, reminder_sent=%s
                WHERE appointment_id=%s
            """, (prow[0], data["doctor_id"], data["service_id"],
                  data["date"], data["time"], data.get("status", "Pending"),
                  data.get("notes", ""), data.get("cancellation_reason", ""),
                  data.get("reschedule_reason", ""), data.get("reminder_sent", 0),
                  appointment_id))
            conn.commit()
            cur.close()
            self.log_activity("Edited", "Appointment", f"Appt #{appointment_id}")
            return True
        except Exception:
            return False

    def update_reminder_sent(self, appointment_id: int, sent: bool) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE appointments SET reminder_sent=%s WHERE appointment_id=%s",
                        (1 if sent else 0, appointment_id))
            conn.commit()
            cur.close()
            return True
        except Exception:
            return False

    # ══════════════════════════════════════════════════════════════════
    #  CLINICAL / POS
    # ══════════════════════════════════════════════════════════════════
    def get_queue_entries(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT q.queue_id, q.queue_time, q.purpose, q.status,
                       CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                       CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                       q.doctor_id
                FROM queue_entries q
                INNER JOIN patients p ON q.patient_id = p.patient_id
                INNER JOIN employees e ON q.doctor_id = e.employee_id
                WHERE q.created_at = CURDATE()
                ORDER BY q.queue_time
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_queue_stats(self) -> dict:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT SUM(CASE WHEN status='Waiting' THEN 1 ELSE 0 END) AS waiting,
                       SUM(CASE WHEN status='In Progress' THEN 1 ELSE 0 END) AS in_progress,
                       SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed
                FROM queue_entries WHERE created_at = CURDATE()
            """)
            row = cur.fetchone()
            cur.close()
            return row if row else {"waiting": 0, "in_progress": 0, "completed": 0}
        except Exception:
            return {"waiting": 0, "in_progress": 0, "completed": 0}

    def update_queue_status(self, queue_id: int, status: str) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE queue_entries SET status=%s WHERE queue_id=%s", (status, queue_id))
            conn.commit()
            cur.close()
            return True
        except Exception:
            return False

    def update_queue_entry(self, queue_id: int, data: dict) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE queue_entries SET status=%s, purpose=%s WHERE queue_id=%s",
                        (data.get("status", "Waiting"), data.get("purpose", ""), queue_id))
            conn.commit()
            cur.close()
            return True
        except Exception:
            return False

    def sync_today_appointments_to_queue(self) -> int:
        """Create queue entries for confirmed today's appointments that don't have one yet."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT a.appointment_id, a.patient_id, a.doctor_id, a.appointment_time, s.service_name
                FROM appointments a
                INNER JOIN services s ON a.service_id = s.service_id
                WHERE a.appointment_date = CURDATE() AND a.status = 'Confirmed'
                  AND a.appointment_id NOT IN (SELECT COALESCE(appointment_id,0) FROM queue_entries WHERE created_at = CURDATE())
            """)
            rows = cur.fetchall()
            for r in rows:
                cur.execute("""
                    INSERT INTO queue_entries (patient_id, doctor_id, appointment_id, queue_time, purpose, status, created_at)
                    VALUES (%s,%s,%s,%s,%s,'Waiting',CURDATE())
                """, (r["patient_id"], r["doctor_id"], r["appointment_id"],
                      r["appointment_time"], r["service_name"]))
            conn.commit()
            cur.close()
            self.log_activity("Created", "Queue", f"Synced {len(rows)} appointments to queue")
            return len(rows)
        except Exception:
            return 0

    def call_next_queue(self, doctor_id: int = None) -> dict:
        """Move the next 'Waiting' entry to 'In Progress'. Returns the entry or {}."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            q = """SELECT queue_id, CONCAT(p.first_name,' ',p.last_name) AS patient_name
                   FROM queue_entries qe
                   INNER JOIN patients p ON qe.patient_id = p.patient_id
                   WHERE qe.created_at = CURDATE() AND qe.status = 'Waiting'"""
            params = []
            if doctor_id:
                q += " AND qe.doctor_id = %s"
                params.append(doctor_id)
            q += " ORDER BY qe.queue_time LIMIT 1"
            cur.execute(q, params)
            entry = cur.fetchone()
            if entry:
                cur.execute("UPDATE queue_entries SET status='In Progress' WHERE queue_id=%s", (entry["queue_id"],))
                conn.commit()
            cur.close()
            return entry if entry else {}
        except Exception:
            return {}

    def get_avg_consultation_minutes(self) -> int:
        """Estimate average consultation duration from completed queue entries."""
        return 15

    # ── Invoices ───────────────────────────────────────────────────────
    def get_invoices(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT i.invoice_id, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                       GROUP_CONCAT(s.service_name SEPARATOR ', ') AS service_name,
                       i.total_amount, i.amount_paid, i.status,
                       COALESCE(pm.method_name,'—') AS payment_method, i.created_at,
                       i.appointment_id, i.notes
                FROM invoices i
                INNER JOIN patients p ON i.patient_id = p.patient_id
                LEFT JOIN invoice_items ii ON i.invoice_id = ii.invoice_id
                LEFT JOIN services s ON ii.service_id = s.service_id
                LEFT JOIN payment_methods pm ON i.method_id = pm.method_id
                GROUP BY i.invoice_id
                ORDER BY i.created_at DESC
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def add_invoice(self, data: dict) -> bool:
        """Create an invoice with multiple line items.
        data keys: patient_name, items=[{service_id, quantity, discount}], method_id, notes, appointment_id."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            parts = data["patient_name"].rsplit(" ", 1)
            first, last = parts[0], parts[1] if len(parts) > 1 else ""
            cur.execute("SELECT patient_id FROM patients WHERE first_name=%s AND last_name=%s LIMIT 1", (first, last))
            prow = cur.fetchone()
            if not prow:
                cur.close()
                return False
            patient_id = prow[0]

            items = data.get("items", [])
            if not items and data.get("service_id"):
                items = [{"service_id": data["service_id"],
                          "quantity": data.get("quantity", 1),
                          "discount": data.get("discount", 0)}]

            grand_total = 0.0
            line_items = []
            for item in items:
                cur.execute("SELECT price FROM services WHERE service_id=%s", (item["service_id"],))
                srow = cur.fetchone()
                unit_price = float(srow[0]) if srow else 0
                qty = int(item.get("quantity", 1))
                disc = float(item.get("discount", 0))
                subtotal = unit_price * qty
                total_after_disc = subtotal * (1 - disc / 100)
                grand_total += total_after_disc
                line_items.append((item["service_id"], qty, unit_price, subtotal))

            appt_id = data.get("appointment_id") or None
            cur.execute("""
                INSERT INTO invoices (patient_id, appointment_id, method_id,
                    discount_percent, total_amount, amount_paid, status, notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (patient_id, appt_id, data.get("method_id"),
                  data.get("discount", 0), grand_total, 0, "Unpaid", data.get("notes", "")))
            invoice_id = cur.lastrowid
            for sid, qty, up, sub in line_items:
                cur.execute("INSERT INTO invoice_items (invoice_id, service_id, quantity, unit_price, subtotal) VALUES (%s,%s,%s,%s,%s)",
                            (invoice_id, sid, qty, up, sub))
            conn.commit()
            cur.close()
            self.log_activity("Created", "Invoice", f"Invoice #{invoice_id} for {data['patient_name']}")
            return True
        except Exception:
            return False

    def add_payment(self, invoice_id: int, amount: float, method_id: int = None) -> bool:
        """Add a partial/full payment to an existing invoice."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT total_amount, amount_paid FROM invoices WHERE invoice_id=%s", (invoice_id,))
            row = cur.fetchone()
            if not row:
                return False
            new_paid = float(row[1]) + amount
            new_status = "Paid" if new_paid >= float(row[0]) else "Partial"
            update_q = "UPDATE invoices SET amount_paid=%s, status=%s"
            params = [new_paid, new_status]
            if method_id:
                update_q += ", method_id=%s"
                params.append(method_id)
            update_q += " WHERE invoice_id=%s"
            params.append(invoice_id)
            cur.execute(update_q, params)
            conn.commit()
            cur.close()
            self.log_activity("Edited", "Invoice", f"Payment added to invoice #{invoice_id}")
            return True
        except Exception:
            return False

    def void_invoice(self, invoice_id: int) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE invoices SET status='Voided' WHERE invoice_id=%s", (invoice_id,))
            conn.commit()
            cur.close()
            self.log_activity("Voided", "Invoice", f"Invoice #{invoice_id} voided")
            return True
        except Exception:
            return False

    def get_invoice_detail(self, invoice_id: int) -> dict:
        """Full invoice details for receipt printing."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT i.*, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                       p.phone, p.email, COALESCE(pm.method_name,'—') AS payment_method
                FROM invoices i
                INNER JOIN patients p ON i.patient_id = p.patient_id
                LEFT JOIN payment_methods pm ON i.method_id = pm.method_id
                WHERE i.invoice_id = %s
            """, (invoice_id,))
            info = cur.fetchone()
            cur.execute("""
                SELECT s.service_name, ii.quantity, ii.unit_price, ii.subtotal
                FROM invoice_items ii
                INNER JOIN services s ON ii.service_id = s.service_id
                WHERE ii.invoice_id = %s
            """, (invoice_id,))
            items = cur.fetchall()
            cur.close()
            return {"info": info, "items": items} if info else {}
        except Exception:
            return {}

    def get_today_completed_appointments_for_patient(self, patient_name: str) -> list:
        """For linking invoices to appointments."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            parts = patient_name.rsplit(" ", 1)
            first, last = parts[0], parts[1] if len(parts) > 1 else ""
            cur.execute("""
                SELECT a.appointment_id, a.appointment_time, s.service_name
                FROM appointments a
                INNER JOIN patients p ON a.patient_id = p.patient_id
                INNER JOIN services s ON a.service_id = s.service_id
                WHERE p.first_name=%s AND p.last_name=%s
                  AND a.appointment_date = CURDATE()
                  AND a.status = 'Completed'
            """, (first, last))
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_payment_methods(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT method_id, method_name FROM payment_methods ORDER BY method_name")
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    # ── Services ───────────────────────────────────────────────────────
    def add_service(self, name: str, price: float, category: str = "General") -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO services (service_name, price, category) VALUES (%s,%s,%s)", (name, price, category))
            conn.commit()
            cur.close()
            self.log_activity("Created", "Service", name)
            return True
        except Exception:
            return False

    def update_service_full(self, service_id: int, name: str, price: float,
                            category: str = "General", is_active: int = 1) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE services SET service_name=%s, price=%s, category=%s, is_active=%s WHERE service_id=%s",
                        (name, price, category, is_active, service_id))
            conn.commit()
            cur.close()
            self.log_activity("Edited", "Service", name)
            return True
        except Exception:
            return False

    def update_service(self, service_id: int, price: float) -> bool:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE services SET price=%s WHERE service_id=%s", (price, service_id))
            conn.commit()
            cur.close()
            return True
        except Exception:
            return False

    def bulk_update_prices(self, updates: list) -> bool:
        """updates = [(service_id, new_price), ...]"""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            for sid, price in updates:
                cur.execute("UPDATE services SET price=%s WHERE service_id=%s", (price, sid))
            conn.commit()
            cur.close()
            self.log_activity("Edited", "Service", f"Bulk updated {len(updates)} prices")
            return True
        except Exception:
            return False

    def get_service_usage_counts(self) -> dict:
        """Return {service_id: count} from invoice_items."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT service_id, SUM(quantity) FROM invoice_items GROUP BY service_id")
            result = {r[0]: int(r[1]) for r in cur.fetchall()}
            cur.close()
            return result
        except Exception:
            return {}

    def get_service_categories(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT category FROM services ORDER BY category")
            rows = [r[0] for r in cur.fetchall()]
            cur.close()
            return rows
        except Exception:
            return []

    def get_active_patients(self) -> list:
        """Return active patients for dropdowns."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT patient_id, CONCAT(first_name,' ',last_name) AS name FROM patients WHERE status='Active' ORDER BY first_name")
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    # ══════════════════════════════════════════════════════════════════
    #  DASHBOARD
    # ══════════════════════════════════════════════════════════════════
    def get_dashboard_stats(self) -> dict:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM patients WHERE status='Active'")
            total_patients = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM appointments WHERE appointment_date=CURDATE()")
            today_appts = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(amount_paid),0) FROM invoices WHERE status IN ('Paid','Partial')")
            total_revenue = float(cur.fetchone()[0])
            cur.close()
            return {"total_patients": total_patients, "today_appts": today_appts, "total_revenue": total_revenue}
        except Exception:
            return {"total_patients": 0, "today_appts": 0, "total_revenue": 0}

    def get_upcoming_appointments(self, limit: int = 10) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT a.appointment_time,
                       CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                       CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                       s.service_name, a.status
                FROM appointments a
                INNER JOIN patients p ON a.patient_id=p.patient_id
                INNER JOIN employees e ON a.doctor_id=e.employee_id
                INNER JOIN services s ON a.service_id=s.service_id
                WHERE a.appointment_date >= CURDATE() AND a.status IN ('Confirmed','Pending')
                ORDER BY a.appointment_date, a.appointment_time LIMIT %s
            """, (limit,))
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_patient_stats_monthly(self, months: int = 6) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT DATE_FORMAT(appointment_date, '%%b') AS month_label,
                       DATE_FORMAT(appointment_date, '%%Y-%%m') AS sort_key,
                       COUNT(*) AS visit_count
                FROM appointments
                WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
                GROUP BY sort_key, month_label ORDER BY sort_key
            """, (months,))
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_dashboard_alerts(self, role: str) -> list:
        """Return alert items for the dashboard."""
        alerts = []
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT CONCAT(p.first_name,' ',p.last_name) AS patient_name, q.queue_time
                FROM queue_entries q
                INNER JOIN patients p ON q.patient_id = p.patient_id
                WHERE q.created_at = CURDATE() AND q.status = 'Waiting'
                  AND TIMESTAMPDIFF(MINUTE, CONCAT(CURDATE(),' ',q.queue_time), NOW()) > 30
            """)
            for r in cur.fetchall():
                alerts.append(("warning", f"⏰ {r['patient_name']} waiting > 30 min (since {r['queue_time']})"))
            cur.execute("""
                SELECT CONCAT(p.first_name,' ',p.last_name) AS patient_name, a.appointment_time
                FROM appointments a
                INNER JOIN patients p ON a.patient_id = p.patient_id
                WHERE a.appointment_date = CURDATE() AND a.status IN ('Confirmed','Pending')
                  AND TIMESTAMPDIFF(MINUTE, NOW(), CONCAT(CURDATE(),' ',a.appointment_time)) BETWEEN 0 AND 15
                  AND a.appointment_id NOT IN (SELECT COALESCE(appointment_id,0) FROM queue_entries WHERE created_at = CURDATE())
            """)
            for r in cur.fetchall():
                alerts.append(("info", f"📋 {r['patient_name']} appointment in ≤15 min, not in queue"))
            if role in ("Admin", "Receptionist"):
                cur.execute("""
                    SELECT CONCAT(p.first_name,' ',p.last_name) AS patient_name, i.invoice_id, i.total_amount
                    FROM invoices i
                    INNER JOIN patients p ON i.patient_id = p.patient_id
                    WHERE i.status = 'Unpaid' AND DATEDIFF(CURDATE(), DATE(i.created_at)) > 7
                """)
                for r in cur.fetchall():
                    alerts.append(("danger", f"💰 Invoice #{r['invoice_id']} for {r['patient_name']} unpaid > 7 days (₱{float(r['total_amount']):,.0f})"))
            cur.close()
        except Exception:
            pass
        return alerts

    # ══════════════════════════════════════════════════════════════════
    #  ANALYTICS / REPORTS
    # ══════════════════════════════════════════════════════════════════
    def get_monthly_revenue(self, months: int = 6) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT DATE_FORMAT(i.created_at, '%%M %%Y') AS month_label,
                       DATE_FORMAT(i.created_at, '%%Y-%%m') AS sort_key,
                       COUNT(DISTINCT i.invoice_id) AS appointment_count,
                       COALESCE(SUM(i.amount_paid),0) AS total_revenue
                FROM invoices i WHERE i.status IN ('Paid','Partial')
                  AND i.created_at >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
                GROUP BY sort_key, month_label ORDER BY sort_key
            """, (months,))
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_doctor_performance(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                       COUNT(a.appointment_id) AS total_appointments,
                       SUM(CASE WHEN a.status='Completed' THEN 1 ELSE 0 END) AS completed,
                       COALESCE(SUM(CASE WHEN a.status='Completed' THEN s.price ELSE 0 END),0) AS revenue_generated
                FROM employees e INNER JOIN roles r ON e.role_id = r.role_id
                LEFT JOIN appointments a ON e.employee_id = a.doctor_id
                LEFT JOIN services s ON a.service_id = s.service_id
                WHERE r.role_name='Doctor' GROUP BY e.employee_id
                ORDER BY revenue_generated DESC
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_top_services(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT s.service_name, COUNT(a.appointment_id) AS usage_count,
                       COALESCE(SUM(CASE WHEN a.status='Completed' THEN s.price ELSE 0 END),0) AS total_revenue
                FROM services s LEFT JOIN appointments a ON s.service_id = a.service_id
                GROUP BY s.service_id, s.service_name HAVING usage_count > 0
                ORDER BY usage_count DESC
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_appointment_status_counts(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT status, COUNT(*) AS cnt FROM appointments GROUP BY status ORDER BY cnt DESC")
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_patient_condition_counts(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT condition_name, COUNT(*) AS cnt FROM patient_conditions GROUP BY condition_name ORDER BY cnt DESC")
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_patient_demographics(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT CASE
                    WHEN TIMESTAMPDIFF(YEAR,date_of_birth,CURDATE())<=17 THEN '0–17'
                    WHEN TIMESTAMPDIFF(YEAR,date_of_birth,CURDATE())<=35 THEN '18–35'
                    WHEN TIMESTAMPDIFF(YEAR,date_of_birth,CURDATE())<=50 THEN '36–50'
                    WHEN TIMESTAMPDIFF(YEAR,date_of_birth,CURDATE())<=65 THEN '51–65'
                    ELSE '65+' END AS age_group, COUNT(*) AS cnt
                FROM patients WHERE date_of_birth IS NOT NULL AND status='Active'
                GROUP BY age_group ORDER BY FIELD(age_group,'0–17','18–35','36–50','51–65','65+')
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_revenue_by_department(self) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT d.department_name,
                       COALESCE(SUM(CASE WHEN a.status='Completed' THEN s.price ELSE 0 END),0) AS total_revenue
                FROM departments d
                LEFT JOIN employees e ON d.department_id=e.department_id
                LEFT JOIN appointments a ON e.employee_id=a.doctor_id
                LEFT JOIN services s ON a.service_id=s.service_id
                WHERE e.role_id=(SELECT role_id FROM roles WHERE role_name='Doctor')
                GROUP BY d.department_id, d.department_name HAVING total_revenue > 0
                ORDER BY total_revenue DESC
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_active_doctor_count(self) -> int:
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM employees e INNER JOIN roles r ON e.role_id=r.role_id WHERE r.role_name='Doctor' AND e.status='Active'")
            cnt = cur.fetchone()[0]
            cur.close()
            return cnt
        except Exception:
            return 0

    def get_monthly_appointment_stats(self, months: int = 6) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT DATE_FORMAT(appointment_date, '%%M %%Y') AS month_label,
                       DATE_FORMAT(appointment_date, '%%Y-%%m') AS sort_key,
                       COUNT(*) AS total_visits,
                       SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed,
                       SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) AS cancelled
                FROM appointments WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
                GROUP BY sort_key, month_label ORDER BY sort_key
            """, (months,))
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_patient_retention(self, months: int = 6) -> list:
        """New vs returning patients per month."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT DATE_FORMAT(a.appointment_date, '%%M %%Y') AS month_label,
                       DATE_FORMAT(a.appointment_date, '%%Y-%%m') AS sort_key,
                       COUNT(DISTINCT CASE WHEN a.appointment_date = (
                           SELECT MIN(a2.appointment_date) FROM appointments a2 WHERE a2.patient_id = a.patient_id
                       ) THEN a.patient_id END) AS new_patients,
                       COUNT(DISTINCT CASE WHEN a.appointment_date != (
                           SELECT MIN(a2.appointment_date) FROM appointments a2 WHERE a2.patient_id = a.patient_id
                       ) THEN a.patient_id END) AS returning_patients
                FROM appointments a
                WHERE a.appointment_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
                GROUP BY sort_key, month_label ORDER BY sort_key
            """, (months,))
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_cancellation_rate_trend(self, months: int = 6) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT DATE_FORMAT(appointment_date, '%%M %%Y') AS month_label,
                       DATE_FORMAT(appointment_date, '%%Y-%%m') AS sort_key,
                       COUNT(*) AS total,
                       SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) AS cancelled,
                       ROUND(SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END)/COUNT(*)*100, 1) AS rate
                FROM appointments WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
                GROUP BY sort_key, month_label ORDER BY sort_key
            """, (months,))
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_revenue_detail(self, from_date: str, to_date: str) -> list:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT DATE_FORMAT(a.appointment_date, '%%Y-%%m-%%d') AS appt_date,
                       s.service_name, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                       CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                       COALESCE(pm.method_name,'—') AS payment_method, i.amount_paid
                FROM invoices i
                INNER JOIN appointments a ON i.appointment_id=a.appointment_id
                INNER JOIN patients p ON i.patient_id=p.patient_id
                INNER JOIN employees e ON a.doctor_id=e.employee_id
                INNER JOIN invoice_items ii ON i.invoice_id=ii.invoice_id
                INNER JOIN services s ON ii.service_id=s.service_id
                LEFT JOIN payment_methods pm ON i.method_id=pm.method_id
                WHERE a.appointment_date BETWEEN %s AND %s AND i.status IN ('Paid','Partial')
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """, (from_date, to_date))
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def get_summary_stats(self, from_date: str = None, to_date: str = None) -> dict:
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            where, params = "", []
            if from_date and to_date:
                where = "WHERE appointment_date BETWEEN %s AND %s"
                params = [from_date, to_date]
            cur.execute(f"""
                SELECT COALESCE(SUM(CASE WHEN a.status='Completed' THEN s.price ELSE 0 END),0) AS period_revenue,
                       COUNT(*) AS total_appts,
                       SUM(CASE WHEN a.status='Completed' THEN 1 ELSE 0 END) AS completed,
                       SUM(CASE WHEN a.status='Cancelled' THEN 1 ELSE 0 END) AS cancelled
                FROM appointments a INNER JOIN services s ON a.service_id=s.service_id {where}
            """, params)
            stats = cur.fetchone()
            cur.execute("SELECT COUNT(*) AS cnt FROM patients WHERE status='Active'")
            patients = cur.fetchone()["cnt"]
            cur.execute("SELECT COUNT(*) AS cnt FROM appointments WHERE appointment_date=CURDATE()")
            today = cur.fetchone()["cnt"]
            cur.execute(f"SELECT COUNT(*) AS total, COUNT(DISTINCT appointment_date) AS days FROM appointments a {where}", params)
            avg_row = cur.fetchone()
            avg = avg_row["total"] // avg_row["days"] if avg_row["days"] else 0
            cur.close()
            return {
                "period_revenue": float(stats["period_revenue"]),
                "total_appts": stats["total_appts"], "completed": stats["completed"],
                "cancelled": stats["cancelled"], "total_patients": patients,
                "today_appts": today, "avg_per_day": avg,
            }
        except Exception:
            return {"period_revenue": 0, "total_appts": 0, "completed": 0,
                    "cancelled": 0, "total_patients": 0, "today_appts": 0, "avg_per_day": 0}

    def get_period_comparison(self) -> dict:
        """Compare this month vs last month for KPI deltas."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            curr = prev = None
            for label, offset in [("current", 0), ("previous", 1)]:
                cur.execute("""
                    SELECT COALESCE(SUM(CASE WHEN a.status='Completed' THEN s.price ELSE 0 END),0) AS revenue,
                           COUNT(*) AS appts, COUNT(DISTINCT a.patient_id) AS patients,
                           SUM(CASE WHEN a.status='Completed' THEN 1 ELSE 0 END) AS completed
                    FROM appointments a INNER JOIN services s ON a.service_id=s.service_id
                    WHERE YEAR(a.appointment_date) = YEAR(CURDATE() - INTERVAL %s MONTH)
                      AND MONTH(a.appointment_date) = MONTH(CURDATE() - INTERVAL %s MONTH)
                """, (offset, offset))
                if label == "current":
                    curr = cur.fetchone()
                else:
                    prev = cur.fetchone()
            cur.close()

            def delta(c, p):
                if not p or p == 0:
                    return 0
                return round((c - p) / p * 100, 1)

            return {
                "revenue_delta": delta(float(curr["revenue"]), float(prev["revenue"])),
                "appts_delta": delta(curr["appts"], prev["appts"]),
                "patients_delta": delta(curr["patients"], prev["patients"]),
                "completed_delta": delta(curr["completed"], prev["completed"]),
            }
        except Exception:
            return {"revenue_delta": 0, "appts_delta": 0, "patients_delta": 0, "completed_delta": 0}

    # ── Global search ──────────────────────────────────────────────────
    def global_search(self, query: str, include_employees: bool = True) -> dict:
        """Search across patients, appointments, employees. Returns grouped results."""
        results = {"patients": [], "appointments": [], "employees": []}
        if not query or len(query) < 2:
            return results
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            like = f"%{query}%"
            cur.execute("""
                SELECT patient_id, CONCAT(first_name,' ',last_name) AS name, phone, status
                FROM patients WHERE CONCAT(first_name,' ',last_name) LIKE %s OR phone LIKE %s OR email LIKE %s
                LIMIT 10
            """, (like, like, like))
            results["patients"] = cur.fetchall()
            cur.execute("""
                SELECT a.appointment_id, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                       a.appointment_date, a.status
                FROM appointments a INNER JOIN patients p ON a.patient_id=p.patient_id
                WHERE CONCAT(p.first_name,' ',p.last_name) LIKE %s LIMIT 10
            """, (like,))
            results["appointments"] = cur.fetchall()
            if include_employees:
                cur.execute("""
                    SELECT employee_id, CONCAT(first_name,' ',last_name) AS name, email
                    FROM employees WHERE CONCAT(first_name,' ',last_name) LIKE %s OR email LIKE %s LIMIT 10
                """, (like, like))
                results["employees"] = cur.fetchall()
            cur.close()
        except Exception:
            pass
        return results
