# Appointment CRUD + scheduling logic


class AppointmentMixin:

    def get_appointments(self):
        return self.fetch("""
            SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                   CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                   CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                   s.service_name, a.status, a.notes,
                   a.cancellation_reason, a.reschedule_reason,
                   a.reminder_sent, a.recurring_parent_id,
                   CASE
                       WHEN i.invoice_id IS NULL THEN 'No Invoice'
                       ELSE i.status
                   END AS billing_status
            FROM appointments a
            INNER JOIN patients p ON a.patient_id = p.patient_id
            INNER JOIN employees e ON a.doctor_id = e.employee_id
            INNER JOIN services s ON a.service_id = s.service_id
            LEFT JOIN invoices i ON a.appointment_id = i.appointment_id
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """)

    def get_appointments_for_doctor(self, doctor_email):
        """Return appointments assigned to the logged-in doctor."""
        return self.fetch("""
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
            WHERE e.email = %s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """, (doctor_email,))

    def get_doctors(self):
        return self.fetch("""
            SELECT e.employee_id, CONCAT(e.first_name,' ',e.last_name) AS doctor_name
            FROM employees e INNER JOIN roles r ON e.role_id = r.role_id
            WHERE r.role_name='Doctor' AND e.status='Active' ORDER BY e.first_name
        """)

    def get_services_list(self, active_only=True):
        q = "SELECT service_id, service_name, price, category, is_active FROM services"
        if active_only:
            q += " WHERE is_active = 1"
        return self.fetch(q + " ORDER BY service_name")

    def get_all_services(self):
        return self.get_services_list(active_only=False)

    def check_appointment_conflict(self, doctor_id, date, time, exclude_id=None):
        q = """SELECT COUNT(*) AS cnt FROM appointments
               WHERE doctor_id=%s AND appointment_date=%s AND appointment_time=%s
               AND status NOT IN ('Cancelled')"""
        params = [doctor_id, date, time]
        if exclude_id:
            q += " AND appointment_id != %s"
            params.append(exclude_id)
        row = self.fetch(q, params, one=True)
        return row["cnt"] > 0 if row else False

    def _lookup_patient_id(self, name):
        row = self.fetch(
            "SELECT patient_id FROM patients WHERE CONCAT(first_name,' ',last_name)=%s LIMIT 1",
            (name,), one=True)
        return row["patient_id"] if row else None

    def _validate_appointment_date(self, date_str):
        """Return (ok, error_msg). Date must be today or later, within current or next month."""
        from datetime import date, datetime
        import calendar
        try:
            appt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return False, "Invalid date format."
        today = date.today()
        if appt_date < today:
            return False, "Cannot schedule an appointment in the past."
        # Max = last day of next month
        if today.month == 12:
            next_y, next_m = today.year + 1, 1
        else:
            next_y, next_m = today.year, today.month + 1
        max_day = calendar.monthrange(next_y, next_m)[1]
        max_date = date(next_y, next_m, max_day)
        if appt_date > max_date:
            return False, f"Appointments can only be scheduled up to {max_date.strftime('%B %d, %Y')}."
        return True, ""

    def add_appointment(self, data):
        # Validate date range
        ok, err = self._validate_appointment_date(data["date"])
        if not ok:
            return False
        pid = self._lookup_patient_id(data["patient_name"])
        if not pid:
            return False
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO appointments (patient_id, doctor_id, service_id,
                        appointment_date, appointment_time, status, notes,
                        cancellation_reason, reschedule_reason, reminder_sent, recurring_parent_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (pid, data["doctor_id"], data["service_id"],
                      data["date"], data["time"], data.get("status", "Pending"),
                      data.get("notes", ""), data.get("cancellation_reason", ""),
                      data.get("reschedule_reason", ""), data.get("reminder_sent", 0),
                      data.get("recurring_parent_id")))
                appt_id = cur.lastrowid
                conn.commit()
            doctor_name = data.get('doctor', '')
            if not doctor_name and data.get('doctor_id'):
                doc_row = self.fetch(
                    "SELECT CONCAT(first_name,' ',last_name) AS n FROM employees WHERE employee_id=%s",
                    (data['doctor_id'],), one=True)
                doctor_name = doc_row['n'] if doc_row else ''
            self.log_activity("Created", "Appointment",
                              f"Appt #{appt_id} for {data['patient_name']} with Dr. {doctor_name}")
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False

    def add_recurring_appointments(self, data, frequency, count):
        from datetime import datetime, timedelta, date as date_cls
        import calendar
        created, base = 0, datetime.strptime(data["date"], "%Y-%m-%d")
        deltas = {"Daily": timedelta(days=1), "Weekly": timedelta(weeks=1), "Monthly": timedelta(days=30)}
        delta = deltas.get(frequency, timedelta(weeks=1))
        # Calculate max allowed date (end of next month)
        today = date_cls.today()
        if today.month == 12:
            next_y, next_m = today.year + 1, 1
        else:
            next_y, next_m = today.year, today.month + 1
        max_day = calendar.monthrange(next_y, next_m)[1]
        max_date = date_cls(next_y, next_m, max_day)
        for i in range(count):
            appt_date = (base + delta * i).date()
            if appt_date < today:
                continue  # skip past dates
            if appt_date > max_date:
                break  # stop once we exceed the allowed range
            appt = dict(data, date=appt_date.strftime("%Y-%m-%d"))
            if self.add_appointment(appt):
                created += 1
        return created

    def update_appointment(self, appointment_id, data):
        # Validate date range
        ok, err = self._validate_appointment_date(data["date"])
        if not ok:
            return False
        pid = self._lookup_patient_id(data["patient_name"])
        if not pid:
            return False
        ok = self.exec("""
            UPDATE appointments
            SET patient_id=%s, doctor_id=%s, service_id=%s, appointment_date=%s,
                appointment_time=%s, status=%s, notes=%s,
                cancellation_reason=%s, reschedule_reason=%s, reminder_sent=%s
            WHERE appointment_id=%s
        """, (pid, data["doctor_id"], data["service_id"],
              data["date"], data["time"], data.get("status", "Pending"),
              data.get("notes", ""), data.get("cancellation_reason", ""),
              data.get("reschedule_reason", ""), data.get("reminder_sent", 0),
              appointment_id))
        if ok:
            doctor_name = data.get('doctor', '')
            if not doctor_name and data.get('doctor_id'):
                doc_row = self.fetch(
                    "SELECT CONCAT(first_name,' ',last_name) AS n FROM employees WHERE employee_id=%s",
                    (data['doctor_id'],), one=True)
                doctor_name = doc_row['n'] if doc_row else ''
            self.log_activity("Edited", "Appointment",
                              f"Appt #{appointment_id} for {data.get('patient_name','')} with Dr. {doctor_name}")
        return ok

    def update_reminder_sent(self, appointment_id, sent):
        return self.exec("UPDATE appointments SET reminder_sent=%s WHERE appointment_id=%s",
                         (1 if sent else 0, appointment_id))
