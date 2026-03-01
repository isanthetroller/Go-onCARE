# Analytics - revenue, performance, charts data


class AnalyticsMixin:

    def get_monthly_revenue(self, months=6):
        return self.fetch("""
            SELECT DATE_FORMAT(i.created_at, '%%M %%Y') AS month_label,
                   DATE_FORMAT(i.created_at, '%%Y-%%m') AS sort_key,
                   COUNT(DISTINCT i.invoice_id) AS appointment_count,
                   COALESCE(SUM(i.amount_paid),0) AS total_revenue
            FROM invoices i WHERE i.status IN ('Paid','Partial')
              AND i.created_at >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
            GROUP BY sort_key, month_label ORDER BY sort_key
        """, (months,))

    def get_doctor_performance(self):
        return self.fetch("""
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

    def get_doctor_own_stats(self, email):
        """Return performance + monthly revenue for the doctor identified by *email*."""
        perf = self.fetch("""
            SELECT CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
                   e.employment_type,
                   d.department_name,
                   COUNT(a.appointment_id) AS total_appointments,
                   SUM(CASE WHEN a.status='Completed' THEN 1 ELSE 0 END) AS completed,
                   SUM(CASE WHEN a.status='Cancelled' THEN 1 ELSE 0 END) AS cancelled,
                   COALESCE(SUM(CASE WHEN a.status='Completed' THEN s.price ELSE 0 END),0) AS revenue_generated
            FROM employees e
            INNER JOIN roles r ON e.role_id = r.role_id
            LEFT JOIN departments d ON e.department_id = d.department_id
            LEFT JOIN appointments a ON e.employee_id = a.doctor_id
            LEFT JOIN services s ON a.service_id = s.service_id
            WHERE e.email = %s AND r.role_name='Doctor'
            GROUP BY e.employee_id
        """, (email,), one=True)
        monthly = self.fetch("""
            SELECT DATE_FORMAT(a.appointment_date, '%%M %%Y') AS month_label,
                   DATE_FORMAT(a.appointment_date, '%%Y-%%m') AS sort_key,
                   COUNT(*) AS total_appointments,
                   SUM(CASE WHEN a.status='Completed' THEN 1 ELSE 0 END) AS completed,
                   COALESCE(SUM(CASE WHEN a.status='Completed' THEN s.price ELSE 0 END),0) AS revenue
            FROM appointments a
            INNER JOIN employees e ON a.doctor_id = e.employee_id
            LEFT JOIN services s ON a.service_id = s.service_id
            WHERE e.email = %s
              AND a.appointment_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY sort_key, month_label ORDER BY sort_key
        """, (email,))
        return {"performance": perf or {}, "monthly": monthly or []}

    def get_top_services(self):
        return self.fetch("""
            SELECT s.service_name, COUNT(a.appointment_id) AS usage_count,
                   COALESCE(SUM(CASE WHEN a.status='Completed' THEN s.price ELSE 0 END),0) AS total_revenue
            FROM services s LEFT JOIN appointments a ON s.service_id = a.service_id
            GROUP BY s.service_id, s.service_name HAVING usage_count > 0
            ORDER BY usage_count DESC
        """)

    def get_appointment_status_counts(self):
        return self.fetch("SELECT status, COUNT(*) AS cnt FROM appointments GROUP BY status ORDER BY cnt DESC")

    def get_patient_condition_counts(self):
        return self.fetch("SELECT condition_name, COUNT(*) AS cnt FROM patient_conditions GROUP BY condition_name ORDER BY cnt DESC")

    def get_patient_demographics(self):
        return self.fetch("""
            SELECT CASE
                WHEN TIMESTAMPDIFF(YEAR,date_of_birth,CURDATE())<=17 THEN '0–17'
                WHEN TIMESTAMPDIFF(YEAR,date_of_birth,CURDATE())<=35 THEN '18–35'
                WHEN TIMESTAMPDIFF(YEAR,date_of_birth,CURDATE())<=50 THEN '36–50'
                WHEN TIMESTAMPDIFF(YEAR,date_of_birth,CURDATE())<=65 THEN '51–65'
                ELSE '65+' END AS age_group, COUNT(*) AS cnt
            FROM patients WHERE date_of_birth IS NOT NULL AND status='Active'
            GROUP BY age_group ORDER BY FIELD(age_group,'0–17','18–35','36–50','51–65','65+')
        """)

    def get_revenue_by_department(self):
        return self.fetch("""
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

    def get_active_doctor_count(self):
        row = self.fetch("SELECT COUNT(*) AS c FROM employees e INNER JOIN roles r ON e.role_id=r.role_id WHERE r.role_name='Doctor' AND e.status='Active'", one=True)
        return row["c"] if row else 0

    def get_monthly_appointment_stats(self, months=6):
        return self.fetch("""
            SELECT DATE_FORMAT(appointment_date, '%%M %%Y') AS month_label,
                   DATE_FORMAT(appointment_date, '%%Y-%%m') AS sort_key,
                   COUNT(*) AS total_visits,
                   SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed,
                   SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) AS cancelled
            FROM appointments WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
            GROUP BY sort_key, month_label ORDER BY sort_key
        """, (months,))

    def get_patient_retention(self, months=6):
        return self.fetch("""
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

    def get_cancellation_rate_trend(self, months=6):
        return self.fetch("""
            SELECT DATE_FORMAT(appointment_date, '%%M %%Y') AS month_label,
                   DATE_FORMAT(appointment_date, '%%Y-%%m') AS sort_key,
                   COUNT(*) AS total,
                   SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) AS cancelled,
                   ROUND(SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END)/COUNT(*)*100, 1) AS rate
            FROM appointments WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
            GROUP BY sort_key, month_label ORDER BY sort_key
        """, (months,))

    def get_revenue_detail(self, from_date, to_date):
        return self.fetch("""
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

    def get_summary_stats(self, from_date=None, to_date=None):
        defaults = {"period_revenue": 0, "total_appts": 0, "completed": 0,
                    "cancelled": 0, "total_patients": 0, "today_appts": 0, "avg_per_day": 0}
        try:
            conn = self._get_connection()
            with conn.cursor(dictionary=True) as cur:
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
            return {
                "period_revenue": float(stats["period_revenue"]),
                "total_appts": stats["total_appts"], "completed": stats["completed"],
                "cancelled": stats["cancelled"], "total_patients": patients,
                "today_appts": today, "avg_per_day": avg,
            }
        except Exception:
            return defaults

    def get_period_comparison(self):
        defaults = {"revenue_delta": 0, "appts_delta": 0, "patients_delta": 0, "completed_delta": 0}
        try:
            conn = self._get_connection()
            with conn.cursor(dictionary=True) as cur:
                months = {}
                for label, offset in [("curr", 0), ("prev", 1)]:
                    cur.execute("""
                        SELECT COALESCE(SUM(CASE WHEN a.status='Completed' THEN s.price ELSE 0 END),0) AS revenue,
                               COUNT(*) AS appts, COUNT(DISTINCT a.patient_id) AS patients,
                               SUM(CASE WHEN a.status='Completed' THEN 1 ELSE 0 END) AS completed
                        FROM appointments a INNER JOIN services s ON a.service_id=s.service_id
                        WHERE YEAR(a.appointment_date) = YEAR(CURDATE() - INTERVAL %s MONTH)
                          AND MONTH(a.appointment_date) = MONTH(CURDATE() - INTERVAL %s MONTH)
                    """, (offset, offset))
                    months[label] = cur.fetchone()
            c, p = months["curr"], months["prev"]
            def delta(cv, pv):
                return round((cv - pv) / pv * 100, 1) if pv else 0
            return {
                "revenue_delta": delta(float(c["revenue"]), float(p["revenue"])),
                "appts_delta": delta(c["appts"], p["appts"]),
                "patients_delta": delta(c["patients"], p["patients"]),
                "completed_delta": delta(c["completed"], p["completed"]),
            }
        except Exception:
            return defaults
