# Patient CRUD + profile queries


class PatientMixin:

    def get_patients(self):
        return self.fetch("""
            SELECT p.patient_id, p.first_name, p.last_name, p.sex,
                   p.date_of_birth, p.phone, p.email, p.status, p.notes,
                   p.emergency_contact, p.blood_type,
                   GROUP_CONCAT(pc.condition_name SEPARATOR ', ') AS conditions,
                   (SELECT MAX(a.appointment_date) FROM appointments a
                    WHERE a.patient_id = p.patient_id) AS last_visit
            FROM patients p
            LEFT JOIN patient_conditions pc ON p.patient_id = pc.patient_id
            GROUP BY p.patient_id ORDER BY p.patient_id
        """)

    def get_patient_full_profile(self, patient_id):
        info = self.fetch("""
            SELECT p.*, GROUP_CONCAT(pc.condition_name SEPARATOR ', ') AS conditions
            FROM patients p LEFT JOIN patient_conditions pc ON p.patient_id = pc.patient_id
            WHERE p.patient_id = %s GROUP BY p.patient_id
        """, (patient_id,), one=True)
        if not info:
            return {}
        appts = self.fetch("""
            SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                   CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                   s.service_name, a.status, a.notes
            FROM appointments a
            INNER JOIN employees e ON a.doctor_id = e.employee_id
            INNER JOIN services s ON a.service_id = s.service_id
            WHERE a.patient_id = %s ORDER BY a.appointment_date DESC
        """, (patient_id,))
        invoices = self.fetch("""
            SELECT i.invoice_id, i.total_amount, i.amount_paid, i.status,
                   i.created_at, COALESCE(pm.method_name,'—') AS payment_method,
                   GROUP_CONCAT(s.service_name SEPARATOR ', ') AS services
            FROM invoices i
            LEFT JOIN payment_methods pm ON i.method_id = pm.method_id
            LEFT JOIN invoice_items ii ON i.invoice_id = ii.invoice_id
            LEFT JOIN services s ON ii.service_id = s.service_id
            WHERE i.patient_id = %s GROUP BY i.invoice_id ORDER BY i.created_at DESC
        """, (patient_id,))
        queue = self.fetch("""
            SELECT q.queue_id, q.queue_time, q.purpose, q.status, q.created_at,
                   CONCAT(e.first_name,' ',e.last_name) AS doctor_name
            FROM queue_entries q INNER JOIN employees e ON q.doctor_id = e.employee_id
            WHERE q.patient_id = %s ORDER BY q.created_at DESC, q.queue_time DESC
        """, (patient_id,))
        return {"info": info, "appointments": appts, "invoices": invoices, "queue": queue}

    def _save_conditions(self, cur, patient_id, conditions_str):
        cur.execute("DELETE FROM patient_conditions WHERE patient_id=%s", (patient_id,))
        if conditions_str:
            for c in [c.strip() for c in conditions_str.split(",") if c.strip()]:
                cur.execute("INSERT INTO patient_conditions (patient_id, condition_name) VALUES (%s,%s)", (patient_id, c))

    def add_patient(self, data):
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO patients (first_name, last_name, sex, date_of_birth,
                        phone, email, emergency_contact, blood_type, status, notes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (data["first_name"], data["last_name"], data["sex"],
                      data.get("dob"), data.get("phone",""), data.get("email",""),
                      data.get("emergency_contact",""), data.get("blood_type","Unknown"),
                      data.get("status","Active"), data.get("notes","")))
                pid = cur.lastrowid
                self._save_conditions(cur, pid, data.get("conditions",""))
                conn.commit()
            self.log_activity("Created", "Patient", f"{data['first_name']} {data['last_name']}")
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False

    def update_patient(self, patient_id, data):
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE patients SET first_name=%s, last_name=%s, sex=%s, date_of_birth=%s,
                        phone=%s, email=%s, emergency_contact=%s, blood_type=%s, status=%s, notes=%s
                    WHERE patient_id=%s
                """, (data["first_name"], data["last_name"], data["sex"],
                      data.get("dob"), data.get("phone",""), data.get("email",""),
                      data.get("emergency_contact",""), data.get("blood_type","Unknown"),
                      data.get("status","Active"), data.get("notes",""), patient_id))
                self._save_conditions(cur, patient_id, data.get("conditions",""))
                conn.commit()
            self.log_activity("Edited", "Patient", f"{data['first_name']} {data['last_name']}")
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False

    def delete_patient(self, patient_id):
        nm = self.fetch("SELECT CONCAT(first_name,' ',last_name) AS n FROM patients WHERE patient_id=%s",
                        (patient_id,), one=True)
        result = self.exec_many([
            ("DELETE FROM invoice_items WHERE invoice_id IN (SELECT invoice_id FROM invoices WHERE patient_id=%s)", (patient_id,)),
            ("DELETE FROM invoices WHERE patient_id=%s", (patient_id,)),
            ("DELETE FROM queue_entries WHERE patient_id=%s", (patient_id,)),
            ("DELETE FROM appointments WHERE patient_id=%s", (patient_id,)),
            ("DELETE FROM patient_conditions WHERE patient_id=%s", (patient_id,)),
            ("DELETE FROM patients WHERE patient_id=%s", (patient_id,)),
        ])
        if result is not False:
            self.log_activity("Deleted", "Patient", nm["n"] if nm else str(patient_id))
            return True
        return False

    def merge_patients(self, keep_id, remove_id):
        result = self.exec_many([
            ("UPDATE appointments SET patient_id=%s WHERE patient_id=%s", (keep_id, remove_id)),
            ("UPDATE queue_entries SET patient_id=%s WHERE patient_id=%s", (keep_id, remove_id)),
            ("UPDATE invoices SET patient_id=%s WHERE patient_id=%s", (keep_id, remove_id)),
            ("INSERT IGNORE INTO patient_conditions (patient_id, condition_name) SELECT %s, condition_name FROM patient_conditions WHERE patient_id=%s", (keep_id, remove_id)),
            ("DELETE FROM patient_conditions WHERE patient_id=%s", (remove_id,)),
            ("DELETE FROM patients WHERE patient_id=%s", (remove_id,)),
        ])
        if result is not False:
            self.log_activity("Edited", "Patient", f"Merged patient #{remove_id} into #{keep_id}")
            return True
        return False

    def get_patients_for_doctor(self, email):
        """Return only patients who have appointments with the doctor identified by *email*."""
        return self.fetch("""
            SELECT DISTINCT p.patient_id, p.first_name, p.last_name, p.sex,
                   p.date_of_birth, p.phone, p.email, p.status, p.notes,
                   p.emergency_contact, p.blood_type,
                   GROUP_CONCAT(DISTINCT pc.condition_name SEPARATOR ', ') AS conditions,
                   (SELECT MAX(a2.appointment_date) FROM appointments a2
                    WHERE a2.patient_id = p.patient_id) AS last_visit
            FROM patients p
            INNER JOIN appointments a ON p.patient_id = a.patient_id
            INNER JOIN employees e ON a.doctor_id = e.employee_id
            LEFT JOIN patient_conditions pc ON p.patient_id = pc.patient_id
            WHERE e.email = %s
            GROUP BY p.patient_id ORDER BY p.patient_id
        """, (email,))

    def get_active_patients(self):
        return self.fetch("SELECT patient_id, CONCAT(first_name,' ',last_name) AS name FROM patients WHERE status='Active' ORDER BY first_name")
