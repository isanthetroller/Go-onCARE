"""Dashboard backend – summary stats, upcoming appointments, monthly trends."""


class DashboardMixin:

    def get_dashboard_summary(self):
        """Today-focused KPI summary for the dashboard."""
        s = {}
        try:
            p = self.fetch(
                "SELECT COUNT(*) AS c FROM patients WHERE status='Active'", one=True)
            s["active_patients"] = p["c"] if p else 0

            np = self.fetch(
                "SELECT COUNT(*) AS c FROM patients "
                "WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)", one=True)
            s["new_patients_week"] = np["c"] if np else 0

            a = self.fetch("""
                SELECT COUNT(*) AS total,
                       COALESCE(SUM(status='Confirmed'),0)  AS confirmed,
                       COALESCE(SUM(status='Pending'),0)    AS pending,
                       COALESCE(SUM(status='Completed'),0)  AS completed
                FROM appointments WHERE appointment_date = CURDATE()
            """, one=True)
            s["today_appts"]     = a["total"]     if a else 0
            s["today_confirmed"] = int(a["confirmed"]) if a else 0
            s["today_pending"]   = int(a["pending"])   if a else 0
            s["today_completed"] = int(a["completed"]) if a else 0

            r = self.fetch(
                "SELECT COALESCE(SUM(amount_paid),0) AS c FROM invoices "
                "WHERE status IN ('Paid','Partial') AND DATE(created_at)=CURDATE()",
                one=True)
            s["today_revenue"] = float(r["c"]) if r else 0

            tr = self.fetch(
                "SELECT COALESCE(SUM(amount_paid),0) AS c FROM invoices "
                "WHERE status IN ('Paid','Partial')", one=True)
            s["total_revenue"] = float(tr["c"]) if tr else 0

            e = self.fetch(
                "SELECT COUNT(*) AS c FROM employees WHERE status='Active'",
                one=True)
            s["active_staff"] = e["c"] if e else 0
        except Exception:
            for k in ("active_patients", "new_patients_week", "today_appts",
                      "today_confirmed", "today_pending", "today_completed",
                      "today_revenue", "total_revenue", "active_staff"):
                s.setdefault(k, 0)
        return s

    def get_upcoming_appointments(self, limit=10):
        return self.fetch("""
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

    def get_patient_stats_monthly(self, months=6):
        return self.fetch("""
            SELECT MONTHNAME(appointment_date) AS month_label,
                   DATE_FORMAT(appointment_date, '%%Y-%%m') AS sort_key,
                   COUNT(*) AS visit_count
            FROM appointments
            WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
            GROUP BY sort_key, month_label ORDER BY sort_key
        """, (months,))
