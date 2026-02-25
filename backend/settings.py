"""Settings backend – Data cleanup, table management, standard conditions."""


class SettingsMixin:

    def get_table_counts(self):
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
            with conn.cursor() as cur:
                for t in tables:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM `{t}`")
                        results.append((t, cur.fetchone()[0]))
                    except Exception:
                        results.append((t, 0))
        except Exception:
            pass
        return results

    def cleanup_completed_appointments(self, before_date):
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                for q in [
                    "DELETE ii FROM invoice_items ii INNER JOIN invoices i ON ii.invoice_id=i.invoice_id INNER JOIN appointments a ON i.appointment_id=a.appointment_id WHERE a.status='Completed' AND a.appointment_date<%s",
                    "DELETE i FROM invoices i INNER JOIN appointments a ON i.appointment_id=a.appointment_id WHERE a.status='Completed' AND a.appointment_date<%s",
                    "DELETE q FROM queue_entries q INNER JOIN appointments a ON q.appointment_id=a.appointment_id WHERE a.status='Completed' AND a.appointment_date<%s",
                    "DELETE FROM appointments WHERE status='Completed' AND appointment_date<%s",
                ]:
                    cur.execute(q, (before_date,))
                removed = cur.rowcount
                conn.commit()
            self.log_activity("Deleted", "Appointment", f"Cleaned {removed} completed appts before {before_date}")
            return removed
        except Exception:
            return 0

    def cleanup_cancelled_appointments(self):
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                for q in [
                    "DELETE ii FROM invoice_items ii INNER JOIN invoices i ON ii.invoice_id=i.invoice_id INNER JOIN appointments a ON i.appointment_id=a.appointment_id WHERE a.status='Cancelled'",
                    "DELETE i FROM invoices i INNER JOIN appointments a ON i.appointment_id=a.appointment_id WHERE a.status='Cancelled'",
                    "DELETE q FROM queue_entries q INNER JOIN appointments a ON q.appointment_id=a.appointment_id WHERE a.status='Cancelled'",
                    "DELETE FROM appointments WHERE status='Cancelled'",
                ]:
                    cur.execute(q)
                removed = cur.rowcount
                conn.commit()
            self.log_activity("Deleted", "Appointment", f"Cleaned {removed} cancelled appointments")
            return removed
        except Exception:
            return 0

    def cleanup_inactive_patients(self):
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                for q in [
                    "DELETE ii FROM invoice_items ii INNER JOIN invoices i ON ii.invoice_id=i.invoice_id INNER JOIN patients p ON i.patient_id=p.patient_id WHERE p.status='Inactive'",
                    "DELETE i FROM invoices i INNER JOIN patients p ON i.patient_id=p.patient_id WHERE p.status='Inactive'",
                    "DELETE q FROM queue_entries q INNER JOIN patients p ON q.patient_id=p.patient_id WHERE p.status='Inactive'",
                    "DELETE a FROM appointments a INNER JOIN patients p ON a.patient_id=p.patient_id WHERE p.status='Inactive'",
                    "DELETE FROM patient_conditions WHERE patient_id IN (SELECT patient_id FROM patients WHERE status='Inactive')",
                    "DELETE FROM patients WHERE status='Inactive'",
                ]:
                    cur.execute(q)
                removed = cur.rowcount
                conn.commit()
            self.log_activity("Deleted", "Patient", f"Cleaned {removed} inactive patients")
            return removed
        except Exception:
            return 0

    def truncate_table(self, table_name):
        allowed = {"queue_entries", "invoice_items", "invoices", "appointments", "patient_conditions", "activity_log"}
        if table_name not in allowed:
            return False
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(f"SET FOREIGN_KEY_CHECKS = 0; TRUNCATE TABLE `{table_name}`; SET FOREIGN_KEY_CHECKS = 1;", multi=True)
                for _ in cur:
                    pass
                conn.commit()
            self.log_activity("Deleted", "System", f"Truncated table {table_name}")
            return True
        except Exception:
            return False

    # ── Standard Conditions ────────────────────────────────────────────
    def get_standard_conditions(self):
        return self.fetch("SELECT condition_id, condition_name FROM standard_conditions ORDER BY condition_name")

    def add_standard_condition(self, name):
        ok = self.exec("INSERT INTO standard_conditions (condition_name) VALUES (%s)", (name,))
        if ok:
            self.log_activity("Created", "Condition", name)
        return ok

    def delete_standard_condition(self, cond_id):
        return self.exec("DELETE FROM standard_conditions WHERE condition_id = %s", (cond_id,))
