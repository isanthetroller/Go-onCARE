# DB connection + helper functions

import mysql.connector
from mysql.connector import Error
from backend.db_config import DB_CONFIG


class DatabaseBase:
    DB_CONFIG = DB_CONFIG

    def __init__(self):
        self._conn = None
        self._current_user_email = ""
        self._current_user_role = ""
        self._ensure_schema()

    def set_current_user(self, email, role):
        self._current_user_email = email
        self._current_user_role = role

    # ── Connection ────────────────────────────────────────────────
    def _get_connection(self):
        if self._conn is None or not self._conn.is_connected():
            self._conn = mysql.connector.connect(**self.DB_CONFIG)
        return self._conn

    def close(self):
        if self._conn and self._conn.is_connected():
            self._conn.close()
            self._conn = None

    # ── Schema auto-migration ─────────────────────────────────────
    def _ensure_schema(self):
        """Create any missing tables or columns so the app works on older DBs."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # discount_types table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS discount_types (
                        discount_id      INT AUTO_INCREMENT PRIMARY KEY,
                        type_name        VARCHAR(100) NOT NULL UNIQUE,
                        discount_percent DECIMAL(5,2) NOT NULL DEFAULT 0.00,
                        legal_basis      VARCHAR(255) DEFAULT '',
                        is_active        TINYINT(1) NOT NULL DEFAULT 1
                    )
                """)
                # discount_type_id column on patients
                cur.execute("SHOW COLUMNS FROM patients LIKE 'discount_type_id'")
                if not cur.fetchone():
                    cur.execute("ALTER TABLE patients ADD COLUMN discount_type_id INT DEFAULT NULL")
                    cur.execute(
                        "ALTER TABLE patients ADD CONSTRAINT fk_patient_discount "
                        "FOREIGN KEY (discount_type_id) REFERENCES discount_types(discount_id)"
                    )
                # address column on patients
                cur.execute("SHOW COLUMNS FROM patients LIKE 'address'")
                if not cur.fetchone():
                    cur.execute("ALTER TABLE patients ADD COLUMN address VARCHAR(300) DEFAULT ''")
                # civil_status column on patients
                cur.execute("SHOW COLUMNS FROM patients LIKE 'civil_status'")
                if not cur.fetchone():
                    cur.execute("ALTER TABLE patients ADD COLUMN civil_status ENUM('Single','Married','Widowed','Separated') DEFAULT 'Single'")
                # doctor_schedules table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS doctor_schedules (
                        schedule_id  INT AUTO_INCREMENT PRIMARY KEY,
                        doctor_id    INT NOT NULL,
                        day_of_week  ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') NOT NULL,
                        start_time   TIME NOT NULL,
                        end_time     TIME NOT NULL,
                        FOREIGN KEY (doctor_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
                        UNIQUE KEY uq_doctor_day (doctor_id, day_of_week)
                    )
                """)
                # vitals columns on queue_entries
                for col, typedef in [
                    ('blood_pressure', 'VARCHAR(20) DEFAULT NULL'),
                    ('height_cm', 'DECIMAL(5,1) DEFAULT NULL'),
                    ('weight_kg', 'DECIMAL(5,1) DEFAULT NULL'),
                    ('temperature', 'DECIMAL(4,1) DEFAULT NULL'),
                ]:
                    cur.execute(f"SHOW COLUMNS FROM queue_entries LIKE '{col}'")
                    if not cur.fetchone():
                        cur.execute(f"ALTER TABLE queue_entries ADD COLUMN {col} {typedef}")
                # updated_at column on queue_entries (for consultation duration tracking)
                cur.execute("SHOW COLUMNS FROM queue_entries LIKE 'updated_at'")
                if not cur.fetchone():
                    cur.execute("ALTER TABLE queue_entries ADD COLUMN updated_at DATETIME DEFAULT NULL")
                # nurse_notes column on queue_entries (triage observations)
                cur.execute("SHOW COLUMNS FROM queue_entries LIKE 'nurse_notes'")
                if not cur.fetchone():
                    cur.execute("ALTER TABLE queue_entries ADD COLUMN nurse_notes TEXT DEFAULT NULL")
                # Add 'Triaged' to queue_entries status ENUM (nurse triage workflow)
                cur.execute("SHOW COLUMNS FROM queue_entries LIKE 'status'")
                col_info = cur.fetchone()
                if col_info and 'Triaged' not in str(col_info.get('Type', '')):
                    cur.execute("ALTER TABLE queue_entries MODIFY COLUMN status ENUM('Waiting','Triaged','In Progress','Completed','Cancelled') NOT NULL DEFAULT 'Waiting'")
                # Ensure Nurse role exists
                cur.execute("SELECT role_id FROM roles WHERE role_name='Nurse'")
                if not cur.fetchone():
                    cur.execute("INSERT INTO roles (role_name) VALUES ('Nurse')")
                # Ensure Finance role exists
                cur.execute("SELECT role_id FROM roles WHERE role_name='Finance'")
                if not cur.fetchone():
                    cur.execute("INSERT INTO roles (role_name) VALUES ('Finance')")
                # paycheck_requests table (HR→Finance payroll workflow)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paycheck_requests (
                        request_id         INT AUTO_INCREMENT PRIMARY KEY,
                        employee_id        INT NOT NULL,
                        amount             DECIMAL(10,2) NOT NULL,
                        period_from        DATE NOT NULL,
                        period_until       DATE NOT NULL,
                        requested_by       INT NOT NULL,
                        status             ENUM('Pending','Approved','Rejected','Disbursed')
                                           NOT NULL DEFAULT 'Pending',
                        finance_decided_by INT DEFAULT NULL,
                        finance_note       TEXT DEFAULT NULL,
                        decided_at         DATETIME DEFAULT NULL,
                        disbursed_at       DATETIME DEFAULT NULL,
                        created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
                        FOREIGN KEY (requested_by) REFERENCES employees(employee_id),
                        FOREIGN KEY (finance_decided_by) REFERENCES employees(employee_id)
                    )
                """)
                # tax_settings table (admin-configurable deduction rates)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tax_settings (
                        setting_id  INT AUTO_INCREMENT PRIMARY KEY,
                        setting_key VARCHAR(50) UNIQUE NOT NULL,
                        value       DECIMAL(6,3) NOT NULL,
                        description VARCHAR(200) DEFAULT NULL,
                        updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                # Seed default Philippine rates if table is empty
                cur.execute("SELECT COUNT(*) AS cnt FROM tax_settings")
                cnt_row = cur.fetchone()
                cnt = cnt_row.get("cnt", 0) if isinstance(cnt_row, dict) else cnt_row[0]
                if cnt == 0:
                    cur.execute("""
                        INSERT INTO tax_settings (setting_key, value, description) VALUES
                        ('sss_rate', 4.500,
                         'SSS Employee Share (%) – RA 11199, 2025 schedule: 14% total, 4.5% employee'),
                        ('philhealth_rate', 2.500,
                         'PhilHealth Employee Share (%) – 5% premium split 50/50 (PhilHealth Circular 2024-0009)'),
                        ('hospital_share_rate', 10.000,
                         'Hospital/Company Share (%) – portion retained by the hospital')
                    """)
                # Add deduction columns to paycheck_requests
                for col, typedef in [
                    ('sss_deduction',        'DECIMAL(10,2) NOT NULL DEFAULT 0.00'),
                    ('philhealth_deduction',  'DECIMAL(10,2) NOT NULL DEFAULT 0.00'),
                    ('hospital_share',        'DECIMAL(10,2) NOT NULL DEFAULT 0.00'),
                    ('net_amount',            'DECIMAL(10,2) NOT NULL DEFAULT 0.00'),
                ]:
                    cur.execute(f"SHOW COLUMNS FROM paycheck_requests LIKE '{col}'")
                    if not cur.fetchone():
                        cur.execute(f"ALTER TABLE paycheck_requests ADD COLUMN {col} {typedef}")

                # service_departments junction table (links services to departments)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS service_departments (
                        service_id    INT NOT NULL,
                        department_id INT NOT NULL,
                        PRIMARY KEY (service_id, department_id),
                        FOREIGN KEY (service_id) REFERENCES services(service_id)
                            ON DELETE CASCADE,
                        FOREIGN KEY (department_id) REFERENCES departments(department_id)
                            ON DELETE CASCADE
                    )
                """)
                # Seed service_departments if table is empty
                cur.execute("SELECT COUNT(*) AS cnt FROM service_departments")
                sd_cnt = cur.fetchone()
                if (sd_cnt.get("cnt", 0) if isinstance(sd_cnt, dict) else sd_cnt[0]) == 0:
                    cur.execute("""
                        INSERT IGNORE INTO service_departments (service_id, department_id)
                        SELECT s.service_id, d.department_id
                        FROM services s
                        CROSS JOIN departments d
                        WHERE (s.category = 'Lab'     AND d.department_name = 'Laboratory')
                           OR (s.category = 'Dental'  AND d.department_name = 'Dentistry')
                    """)

                # Ensure default Finance employee + user account exists
                cur.execute("SELECT role_id FROM roles WHERE role_name='Finance'")
                fin_role_row = cur.fetchone()
                if fin_role_row:
                    fin_role_id = fin_role_row.get("role_id") or fin_role_row[0]
                    cur.execute("SELECT user_id FROM users WHERE email='finance@carecrud.com'")
                    if not cur.fetchone():
                        # Check if Management department exists, else use first dept
                        cur.execute("SELECT department_id FROM departments WHERE department_name='Management'")
                        dept_row = cur.fetchone()
                        dept_id = (dept_row.get("department_id") if dept_row else None) or 7
                        cur.execute(
                            "INSERT INTO employees (first_name, last_name, role_id, department_id, "
                            "employment_type, phone, email, hire_date, status, salary) "
                            "VALUES ('Maria', 'Garcia', %s, %s, 'Full-time', '09173334455', "
                            "'finance@carecrud.com', '2021-03-01', 'Active', 42000.00)",
                            (fin_role_id, dept_id))
                        cur.execute(
                            "INSERT INTO users (email, password, full_name, role_id, must_change_password) "
                            "VALUES ('finance@carecrud.com', 'finance123', 'Maria Garcia', %s, 0)",
                            (fin_role_id,))
                conn.commit()
        except Exception:
            pass

    # ── Query helpers ─────────────────────────────────────────────
    def fetch(self, sql, params=None, one=False):
        """SELECT helper. Returns list of dicts, or single dict if one=True."""
        try:
            conn = self._get_connection()
            with conn.cursor(dictionary=True) as cur:
                cur.execute(sql, params)
                return cur.fetchone() if one else cur.fetchall()
        except Error:
            return None if one else []

    def exec(self, sql, params=None):
        """INSERT/UPDATE/DELETE helper. Commits and returns lastrowid or rowcount."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(sql, params)
                conn.commit()
                return cur.lastrowid or cur.rowcount
        except Error:
            return False

    def exec_many(self, queries):
        """Run multiple write queries in one transaction.
        queries = [(sql, params), ...]. Returns total rowcount or False."""
        try:
            conn = self._get_connection()
            total = 0
            with conn.cursor() as cur:
                for sql, params in queries:
                    cur.execute(sql, params or ())
                    total += cur.rowcount
                conn.commit()
            return total
        except Error:
            try:
                conn.rollback()
            except Exception:
                pass
            return False

    # ── Common lookups (used by multiple mixins) ────────────────────
    def _get_employee_name(self, employee_id):
        """Return 'First Last' for an employee, or '' if not found."""
        row = self.fetch(
            "SELECT CONCAT(first_name,' ',last_name) AS n FROM employees WHERE employee_id=%s",
            (employee_id,), one=True)
        return row["n"] if row else ""

    def _lookup_patient_id(self, name):
        """Find patient_id by full name. Returns id or None."""
        row = self.fetch(
            "SELECT patient_id FROM patients WHERE CONCAT(first_name,' ',last_name)=%s LIMIT 1",
            (name,), one=True)
        return row["patient_id"] if row else None

    def _lookup_role_id(self, role_name):
        row = self.fetch("SELECT role_id FROM roles WHERE role_name = %s", (role_name,), one=True)
        return row["role_id"] if row else None

    # ── Activity Log ──────────────────────────────────────────────
    def log_activity(self, action, record_type, detail=""):
        self.exec(
            "INSERT INTO activity_log (user_email, user_role, action, record_type, record_detail) VALUES (%s,%s,%s,%s,%s)",
            (self._current_user_email, self._current_user_role, action, record_type, detail)
        )

    def get_latest_log_id(self):
        """Return the current MAX(log_id) from activity_log – lightweight check."""
        row = self.fetch("SELECT COALESCE(MAX(log_id), 0) AS max_id FROM activity_log", one=True)
        return row["max_id"] if row else 0

    def get_activity_log(self, limit=200, user_filter="", action_filter="",
                         record_type_filter="", from_date="", to_date="",
                         include_roles=None):
        where, params = ["1=1"], []
        if user_filter:
            where.append("user_email = %s"); params.append(user_filter)
        if action_filter:
            where.append("action = %s"); params.append(action_filter)
        if record_type_filter:
            where.append("record_type = %s"); params.append(record_type_filter)
        if from_date:
            where.append("DATE(created_at) >= %s"); params.append(from_date)
        if to_date:
            where.append("DATE(created_at) <= %s"); params.append(to_date)
        if include_roles:
            placeholders = ",".join(["%s"] * len(include_roles))
            where.append(f"user_role IN ({placeholders})")
            params.extend(include_roles)
        params.append(limit)
        return self.fetch(f"""
            SELECT log_id, user_email, user_role, action, record_type, record_detail, created_at
            FROM activity_log WHERE {' AND '.join(where)}
            ORDER BY created_at DESC LIMIT %s
        """, params)
