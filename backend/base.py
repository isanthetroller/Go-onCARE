"""Base backend – DB connection, helpers, and activity logging."""

import mysql.connector
from mysql.connector import Error


class DatabaseBase:
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

    # ── Query helpers ─────────────────────────────────────────────
    def fetch(self, sql, params=None, one=False):
        """SELECT helper. Returns list of dicts, or single dict if one=True."""
        try:
            conn = self._get_connection()
            with conn.cursor(dictionary=True) as cur:
                cur.execute(sql, params or ())
                return cur.fetchone() if one else cur.fetchall()
        except Error:
            return None if one else []

    def exec(self, sql, params=None):
        """INSERT/UPDATE/DELETE helper. Commits and returns lastrowid or rowcount."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                conn.commit()
                return cur.lastrowid or cur.rowcount
        except Error:
            return False

    def exec_many(self, queries):
        """Run multiple write queries in one transaction.
        queries = [(sql, params), ...]. Returns rowcount or False."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                for sql, params in queries:
                    cur.execute(sql, params or ())
                conn.commit()
                return cur.rowcount
        except Error:
            return False

    # ── Activity Log ──────────────────────────────────────────────
    def log_activity(self, action, record_type, detail=""):
        self.exec(
            "INSERT INTO activity_log (user_email, user_role, action, record_type, record_detail) VALUES (%s,%s,%s,%s,%s)",
            (self._current_user_email, self._current_user_role, action, record_type, detail)
        )

    def get_activity_log(self, limit=200, user_filter="", action_filter="",
                         record_type_filter="", from_date="", to_date=""):
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
        params.append(limit)
        return self.fetch(f"""
            SELECT log_id, user_email, user_role, action, record_type, record_detail, created_at
            FROM activity_log WHERE {' AND '.join(where)}
            ORDER BY created_at DESC LIMIT %s
        """, params)
