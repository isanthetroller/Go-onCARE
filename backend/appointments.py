# Appointment CRUD + scheduling logic


class AppointmentMixin:

    def get_appointments(self, doctor_email=None):
        """Return appointments. Optionally filter by doctor_email."""
        where = "WHERE e.email = %s" if doctor_email else ""
        params = (doctor_email,) if doctor_email else ()
        return self.fetch(f"""
            SELECT a.appointment_id, a.appointment_date, a.appointment_time,
                   CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                   CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                   s.service_name, a.status, a.notes,
                   a.cancellation_reason, a.reschedule_reason,
                   CASE
                       WHEN i.invoice_id IS NULL THEN 'No Invoice'
                       ELSE i.status
                   END AS billing_status
            FROM appointments a
            INNER JOIN patients p ON a.patient_id = p.patient_id
            INNER JOIN employees e ON a.doctor_id = e.employee_id
            INNER JOIN services s ON a.service_id = s.service_id
            LEFT JOIN invoices i ON a.appointment_id = i.appointment_id
            {where}
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """, params)

    def get_appointments_for_doctor(self, doctor_email):
        """Convenience alias."""
        return self.get_appointments(doctor_email=doctor_email)

    def get_doctors(self):
        return self.fetch("""
            SELECT e.employee_id, CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                   e.department_id
            FROM employees e INNER JOIN roles r ON e.role_id = r.role_id
            WHERE r.role_name='Doctor' AND e.status='Active' ORDER BY e.first_name
        """)

    def get_doctors_available_today(self):
        """Return all active doctors, with schedule info for those available today."""
        return self.fetch("""
            SELECT DISTINCT e.employee_id, CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                   e.department_id,
                   TIME_FORMAT(ds.start_time, '%h:%i %p') AS sched_start,
                   TIME_FORMAT(ds.end_time, '%h:%i %p') AS sched_end
            FROM employees e
            INNER JOIN roles r ON e.role_id = r.role_id
            LEFT JOIN doctor_schedules ds ON e.employee_id = ds.doctor_id
              AND ds.day_of_week = DAYNAME(CURDATE())
            WHERE r.role_name = 'Doctor'
              AND e.status = 'Active'
            ORDER BY ds.start_time IS NULL, e.first_name
        """)

    def get_doctor_availability_overview(self):
        """Return all active doctors with today's availability status and appointment count.

        Sorted so available-today doctors appear first, then by name.
        """
        return self.fetch("""
            SELECT e.employee_id,
                   CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                   COALESCE(d.department_name, '\u2014') AS department,
                   ds.day_of_week,
                   TIME_FORMAT(ds.start_time, '%h:%i %p') AS sched_start,
                   TIME_FORMAT(ds.end_time, '%h:%i %p')   AS sched_end,
                   CASE 
                       WHEN lr.request_id IS NOT NULL THEN 'On Leave'
                       WHEN ds.schedule_id IS NOT NULL THEN 'Available'
                       ELSE 'Not Available'
                   END AS availability,
                   COALESCE(ac.appt_count, 0) AS appt_count
            FROM employees e
            INNER JOIN roles r ON e.role_id = r.role_id
            LEFT  JOIN departments d ON e.department_id = d.department_id
            LEFT  JOIN doctor_schedules ds
                       ON e.employee_id = ds.doctor_id
                      AND ds.day_of_week = DAYNAME(CURDATE())
            LEFT  JOIN leave_requests lr
                       ON e.employee_id = lr.employee_id
                      AND lr.status = 'Approved'
                      AND CURDATE() BETWEEN lr.leave_from AND lr.leave_until
            LEFT  JOIN (
                SELECT doctor_id, COUNT(*) AS appt_count
                FROM appointments
                WHERE appointment_date = CURDATE()
                GROUP BY doctor_id
            ) ac ON e.employee_id = ac.doctor_id
            WHERE r.role_name = 'Doctor' AND e.status = 'Active'
            ORDER BY 
                CASE 
                    WHEN lr.request_id IS NOT NULL THEN 0 
                    WHEN ds.schedule_id IS NOT NULL THEN 1 
                    ELSE 0 
                END DESC, 
                e.first_name
        """)

    def get_services_list(self, active_only=True):
        q = "SELECT service_id, service_name, price, category, is_active FROM services"
        if active_only:
            q += " WHERE is_active = 1"
        return self.fetch(q + " ORDER BY service_name")

    def get_services_for_doctor(self, doctor_id):
        """Return active services available for a doctor based on their department.

        Uses service_departments junction table.  Only returns services that
        are explicitly mapped to this doctor's department.
        """
        return self.fetch("""
            SELECT s.service_id, s.service_name, s.price, s.category
            FROM services s
            WHERE s.is_active = 1
              AND (
                  EXISTS (
                      SELECT 1 FROM service_departments sd
                      WHERE sd.service_id = s.service_id
                        AND sd.department_id = (
                            SELECT e.department_id FROM employees e WHERE e.employee_id = %s
                        )
                  )
                  OR NOT EXISTS (
                      SELECT 1 FROM service_departments sd2
                      WHERE sd2.service_id = s.service_id
                  )
              )
            ORDER BY s.service_name
        """, (doctor_id,))

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

    def check_daily_quota(self, doctor_id, date, exclude_id=None):
        q = """SELECT COUNT(*) AS cnt FROM appointments
               WHERE doctor_id=%s AND appointment_date=%s
               AND status NOT IN ('Cancelled')"""
        params = [doctor_id, date]
        if exclude_id:
            q += " AND appointment_id != %s"
            params.append(exclude_id)
        row = self.fetch(q, params, one=True)
        count = row["cnt"] if row else 0
        max_quota = 20
        return (count < max_quota, count, max_quota)

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
        appt_date = data.get("date")
        if not appt_date:
            from datetime import date as _date
            appt_date = _date.today().strftime("%Y-%m-%d")

        pid = data.get("patient_id") or self._lookup_patient_id(data["patient_name"])
        if not pid:
            return False
        conn = None
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO appointments (patient_id, doctor_id, service_id,
                        appointment_date, appointment_time, status, notes,
                        cancellation_reason, reschedule_reason)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (pid, data["doctor_id"], data["service_id"],
                      appt_date, data["time"], "Confirmed",
                      data.get("notes", ""), data.get("cancellation_reason", ""),
                      data.get("reschedule_reason", "")))
                appt_id = cur.lastrowid
                conn.commit()
            doctor_name = data.get('doctor', '')
            if not doctor_name and data.get('doctor_id'):
                doctor_name = self._get_employee_name(data['doctor_id'])

            from datetime import date as _date
            is_today = appt_date == _date.today().strftime("%Y-%m-%d")
            log_type = "Walk-in" if is_today else "Scheduled Appointment"
            self.log_activity("Created", "Appointment",
                              f"{log_type} #{appt_id} for {data['patient_name']} with Dr. {doctor_name}")
            return True
        except Exception:
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
            return False
        finally:
            if conn:
                conn.close()

    def update_appointment(self, appointment_id, data):
        # Validate date range only if date changed from original
        original = self.fetch("SELECT appointment_date FROM appointments WHERE appointment_id=%s",
                              (appointment_id,), one=True)
        original_date = str(original["appointment_date"]) if original else ""
        if data["date"] != original_date:
            ok, err = self._validate_appointment_date(data["date"])
            if not ok:
                return False
        pid = data.get("patient_id") or self._lookup_patient_id(data["patient_name"])
        if not pid:
            return False
        ok = self.exec("""
            UPDATE appointments
            SET patient_id=%s, doctor_id=%s, service_id=%s, appointment_date=%s,
                appointment_time=%s, status=%s, notes=%s,
                cancellation_reason=%s, reschedule_reason=%s
            WHERE appointment_id=%s
        """, (pid, data["doctor_id"], data["service_id"],
              data["date"], data["time"], data.get("status", "Pending"),
              data.get("notes", ""), data.get("cancellation_reason", ""),
              data.get("reschedule_reason", ""),
              appointment_id))
        if ok:
            doctor_name = data.get('doctor', '')
            if not doctor_name and data.get('doctor_id'):
                doctor_name = self._get_employee_name(data['doctor_id'])
            self.log_activity("Edited", "Appointment",
                              f"Appt #{appointment_id} for {data.get('patient_name','')} with Dr. {doctor_name}")
        return ok

    def check_appointment_id_proof(self, appointment_id):
        """Check if the patient for this appointment needs ID proof for their discount.

        Returns the discount type name if ID is required but missing, or None if OK.
        """
        row = self.fetch("""
            SELECT dt.type_name, dt.requires_id_proof, p.id_proof_path
            FROM appointments a
            INNER JOIN patients p ON a.patient_id = p.patient_id
            LEFT JOIN discount_types dt ON p.discount_type_id = dt.discount_id AND dt.is_active = 1
            WHERE a.appointment_id = %s
        """, (appointment_id,), one=True)
        if not row:
            return None
        if row.get("requires_id_proof") and not row.get("id_proof_path"):
            return row.get("type_name", "Unknown")
        return None

