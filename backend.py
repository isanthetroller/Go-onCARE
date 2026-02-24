"""CareCRUD Backend – Database connection and authentication."""

import mysql.connector
from mysql.connector import Error


class AuthBackend:
    """Handles database connection and user authentication."""

    DB_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "",            # XAMPP default (no password)
        "database": "carecrud_db",
        "connection_timeout": 5,    # seconds
        "use_pure": True,           # avoid C-extension crash inside Qt event loop
    }

    def __init__(self):
        self._conn = None

    # ── Connection ─────────────────────────────────────────────────────
    def _get_connection(self):
        """Return an active MySQL connection (lazy, auto-reconnect)."""
        try:
            if self._conn is None or not self._conn.is_connected():
                self._conn = mysql.connector.connect(**self.DB_CONFIG)
            return self._conn
        except Error as e:
            raise ConnectionError(f"Cannot connect to database.\n\n{e}")

    # ── Authentication ─────────────────────────────────────────────────
    def login(self, email: str, password: str) -> tuple:
        """
        Authenticate a user against the database.
        Returns (success, role_name, full_name, message).
        """
        if not email:
            return False, "", "", "Please enter your email address."
        if not password:
            return False, "", "", "Please enter your password."

        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT u.user_id, u.full_name, u.password, r.role_name
                FROM users u
                INNER JOIN roles r ON u.role_id = r.role_id
                WHERE u.email = %s
                """,
                (email,),
            )
            user = cursor.fetchone()
            cursor.close()

            if user is None:
                return False, "", "", "No account found with that email."

            if user["password"] != password:
                return False, "", "", "Incorrect password."

            return True, user["role_name"], user["full_name"], "Login successful."

        except ConnectionError as e:
            return False, "", "", str(e)
        except Error as e:
            return False, "", "", f"Database error: {e}"
        except Exception as e:
            return False, "", "", f"Unexpected error: {e}"

    # ── Data-cleanup helpers (Admin settings) ────────────────────────
    def get_table_counts(self) -> list[tuple[str, int]]:
        """Return [(table_name, row_count), …] for every base table."""
        tables = [
            "patients", "patient_conditions", "appointments",
            "queue_entries", "invoices", "invoice_items",
            "employees", "users", "services",
            "departments", "roles", "payment_methods",
        ]
        results = []
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM `{t}`")
                results.append((t, cur.fetchone()[0]))
            cur.close()
        except Exception:
            pass
        return results

    def cleanup_completed_appointments(self, before_date: str) -> int:
        """Delete completed appointments (and linked queue/invoices)
        with appointment_date < *before_date* (YYYY-MM-DD).
        Returns the number of appointments removed."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            # Delete invoice items linked to those invoices
            cur.execute("""
                DELETE ii FROM invoice_items ii
                INNER JOIN invoices i  ON ii.invoice_id = i.invoice_id
                INNER JOIN appointments a ON i.appointment_id = a.appointment_id
                WHERE a.status = 'Completed' AND a.appointment_date < %s
            """, (before_date,))
            # Delete invoices
            cur.execute("""
                DELETE i FROM invoices i
                INNER JOIN appointments a ON i.appointment_id = a.appointment_id
                WHERE a.status = 'Completed' AND a.appointment_date < %s
            """, (before_date,))
            # Delete queue entries
            cur.execute("""
                DELETE q FROM queue_entries q
                INNER JOIN appointments a ON q.appointment_id = a.appointment_id
                WHERE a.status = 'Completed' AND a.appointment_date < %s
            """, (before_date,))
            # Delete appointments
            cur.execute("""
                DELETE FROM appointments
                WHERE status = 'Completed' AND appointment_date < %s
            """, (before_date,))
            removed = cur.rowcount
            conn.commit()
            cur.close()
            return removed
        except Exception:
            return 0

    def cleanup_cancelled_appointments(self) -> int:
        """Delete all cancelled appointments and their linked records."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("""
                DELETE ii FROM invoice_items ii
                INNER JOIN invoices i  ON ii.invoice_id = i.invoice_id
                INNER JOIN appointments a ON i.appointment_id = a.appointment_id
                WHERE a.status = 'Cancelled'
            """)
            cur.execute("""
                DELETE i FROM invoices i
                INNER JOIN appointments a ON i.appointment_id = a.appointment_id
                WHERE a.status = 'Cancelled'
            """)
            cur.execute("""
                DELETE q FROM queue_entries q
                INNER JOIN appointments a ON q.appointment_id = a.appointment_id
                WHERE a.status = 'Cancelled'
            """)
            cur.execute("DELETE FROM appointments WHERE status = 'Cancelled'")
            removed = cur.rowcount
            conn.commit()
            cur.close()
            return removed
        except Exception:
            return 0

    def cleanup_inactive_patients(self) -> int:
        """Delete inactive patients and their linked data."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            # Remove linked invoice_items → invoices → queue → appointments → conditions
            cur.execute("""
                DELETE ii FROM invoice_items ii
                INNER JOIN invoices i ON ii.invoice_id = i.invoice_id
                INNER JOIN patients p ON i.patient_id = p.patient_id
                WHERE p.status = 'Inactive'
            """)
            cur.execute("""
                DELETE i FROM invoices i
                INNER JOIN patients p ON i.patient_id = p.patient_id
                WHERE p.status = 'Inactive'
            """)
            cur.execute("""
                DELETE q FROM queue_entries q
                INNER JOIN patients p ON q.patient_id = p.patient_id
                WHERE p.status = 'Inactive'
            """)
            cur.execute("""
                DELETE a FROM appointments a
                INNER JOIN patients p ON a.patient_id = p.patient_id
                WHERE p.status = 'Inactive'
            """)
            cur.execute("""
                DELETE FROM patient_conditions
                WHERE patient_id IN (SELECT patient_id FROM patients WHERE status = 'Inactive')
            """)
            cur.execute("DELETE FROM patients WHERE status = 'Inactive'")
            removed = cur.rowcount
            conn.commit()
            cur.close()
            return removed
        except Exception:
            return 0

    def truncate_table(self, table_name: str) -> bool:
        """Truncate (empty) a specific table. Returns True on success."""
        allowed = {
            "queue_entries", "invoice_items", "invoices",
            "appointments", "patient_conditions",
        }
        if table_name not in allowed:
            return False
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            cur.execute(f"TRUNCATE TABLE `{table_name}`")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1")
            conn.commit()
            cur.close()
            return True
        except Exception:
            return False

    # ── Employee CRUD ─────────────────────────────────────────────────
    def get_employees(self) -> list[dict]:
        """Return all employees joined with role and department names."""
        try:
            conn = self._get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT
                    e.employee_id,
                    CONCAT(e.first_name, ' ', e.last_name) AS full_name,
                    r.role_name,
                    d.department_name,
                    e.employment_type,
                    e.phone,
                    e.email,
                    e.hire_date,
                    e.status,
                    e.notes
                FROM employees e
                INNER JOIN roles r       ON e.role_id       = r.role_id
                INNER JOIN departments d ON e.department_id = d.department_id
                ORDER BY e.employee_id
            """)
            rows = cur.fetchall()
            cur.close()
            return rows
        except Exception:
            return []

    def add_employee(self, data: dict) -> bool:
        """Insert a new employee. *data* keys: name, role, dept, type, phone, email, status, notes."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            parts = data["name"].split(None, 1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""
            cur.execute("SELECT role_id FROM roles WHERE role_name = %s", (data["role"],))
            role_row = cur.fetchone()
            if not role_row:
                return False
            cur.execute("SELECT department_id FROM departments WHERE department_name = %s", (data["dept"],))
            dept_row = cur.fetchone()
            if not dept_row:
                return False
            cur.execute("""
                INSERT INTO employees
                    (first_name, last_name, role_id, department_id, employment_type, phone, email, hire_date, status, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURDATE(), %s, %s)
            """, (first, last, role_row[0], dept_row[0], data["type"],
                  data.get("phone", ""), data.get("email", ""), data["status"],
                  data.get("notes", "")))
            conn.commit()
            cur.close()
            return True
        except Exception:
            return False

    def update_employee(self, employee_id: int, data: dict, old_email: str = "") -> bool:
        """Update an existing employee and sync the users table if email/name changed."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            parts = data["name"].split(None, 1)
            first = parts[0]
            last = parts[1] if len(parts) > 1 else ""
            cur.execute("SELECT role_id FROM roles WHERE role_name = %s", (data["role"],))
            role_row = cur.fetchone()
            if not role_row:
                return False
            cur.execute("SELECT department_id FROM departments WHERE department_name = %s", (data["dept"],))
            dept_row = cur.fetchone()
            if not dept_row:
                return False
            cur.execute("""
                UPDATE employees
                SET first_name = %s, last_name = %s, role_id = %s, department_id = %s,
                    employment_type = %s, phone = %s, email = %s, status = %s, notes = %s
                WHERE employee_id = %s
            """, (first, last, role_row[0], dept_row[0], data["type"],
                  data.get("phone", ""), data.get("email", ""), data["status"],
                  data.get("notes", ""), employee_id))
            # Sync users table: update email and full_name
            lookup_email = old_email if old_email else data.get("email", "")
            if lookup_email:
                cur.execute("""
                    UPDATE users SET email = %s, full_name = %s, role_id = %s
                    WHERE email = %s
                """, (data.get("email", ""), data["name"], role_row[0], lookup_email))
            conn.commit()
            cur.close()
            return True
        except Exception:
            return False

    def get_user_password(self, email: str) -> str:
        """Return the plain-text password for a user account, or empty string."""
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
        """Change a user's password."""
        try:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE users SET password = %s WHERE email = %s", (new_password, email))
            conn.commit()
            cur.close()
            return True
        except Exception:
            return False

    def close(self):
        """Close the database connection."""
        if self._conn and self._conn.is_connected():
            self._conn.close()
            self._conn = None
