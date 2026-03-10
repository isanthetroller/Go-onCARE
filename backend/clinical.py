# Queue, invoices, billing, services


class ClinicalMixin:

    # ── Queue ──────────────────────────────────────────────────────────
    def get_queue_entries(self, doctor_id=None):
        sql = """
            SELECT q.queue_id, q.queue_time, q.purpose, q.status,
                   CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                   CONCAT(e.first_name,' ',e.last_name) AS doctor_name, q.doctor_id,
                   q.blood_pressure, q.height_cm, q.weight_kg, q.temperature,
                   q.nurse_notes
            FROM queue_entries q
            INNER JOIN patients p ON q.patient_id = p.patient_id
            INNER JOIN employees e ON q.doctor_id = e.employee_id
            WHERE q.created_at = CURDATE()
        """
        params = ()
        if doctor_id is not None:
            sql += " AND q.doctor_id = %s"
            params = (doctor_id,)
        sql += " ORDER BY q.queue_time"
        return self.fetch(sql, params)

    def get_queue_stats(self, doctor_id=None):
        sql = """
            SELECT SUM(CASE WHEN status='Waiting' THEN 1 ELSE 0 END) AS waiting,
                   SUM(CASE WHEN status='Triaged' THEN 1 ELSE 0 END) AS triaged,
                   SUM(CASE WHEN status='In Progress' THEN 1 ELSE 0 END) AS in_progress,
                   SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed
            FROM queue_entries WHERE created_at = CURDATE()
        """
        params = ()
        if doctor_id is not None:
            sql += " AND doctor_id = %s"
            params = (doctor_id,)
        row = self.fetch(sql, params, one=True)
        return row if row and row.get("waiting") is not None else {"waiting": 0, "triaged": 0, "in_progress": 0, "completed": 0}

    def update_queue_entry(self, queue_id, data):
        ok = self.exec("UPDATE queue_entries SET status=%s, purpose=%s, updated_at=NOW() WHERE queue_id=%s",
                       (data.get("status", "Waiting"), data.get("purpose", ""), queue_id))
        if ok:
            self.log_activity("Edited", "Queue", f"Queue #{queue_id} updated (status={data.get('status','Waiting')})")
        return ok

    def record_vitals(self, queue_id, blood_pressure, height_cm, weight_kg, temperature, nurse_notes=None):
        """Nurse records vitals and triage notes. Auto-sets status to 'Triaged' if currently 'Waiting'."""
        # Check current status to decide whether to auto-triage
        cur_entry = self.fetch("SELECT status FROM queue_entries WHERE queue_id=%s", (queue_id,), one=True)
        new_status_clause = ""
        if cur_entry and cur_entry.get("status") == "Waiting":
            new_status_clause = ", status='Triaged'"
        ok = self.exec(
            f"UPDATE queue_entries SET blood_pressure=%s, height_cm=%s, weight_kg=%s, temperature=%s, "
            f"nurse_notes=%s, updated_at=NOW(){new_status_clause} WHERE queue_id=%s",
            (blood_pressure or None, height_cm or None, weight_kg or None, temperature or None,
             nurse_notes or None, queue_id))
        if ok:
            self.log_activity("Edited", "Queue", f"Vitals recorded for queue #{queue_id}")
        return ok

    def create_invoice_from_queue(self, queue_id):
        """Auto-create an unpaid invoice when a queue entry is completed."""
        try:
            conn = self._get_connection()
            with conn.cursor(dictionary=True) as cur:
                cur.execute("""
                    SELECT q.patient_id, q.appointment_id
                    FROM queue_entries q WHERE q.queue_id = %s
                """, (queue_id,))
                qe = cur.fetchone()
                if not qe or not qe["appointment_id"]:
                    return False

                cur.execute("""
                    SELECT a.service_id, a.patient_id
                    FROM appointments a WHERE a.appointment_id = %s
                """, (qe["appointment_id"],))
                appt = cur.fetchone()
                if not appt:
                    return False

                cur.execute("SELECT price FROM services WHERE service_id = %s", (appt["service_id"],))
                svc = cur.fetchone()
                if not svc:
                    return False
                unit_price = float(svc["price"])

                # Check patient discount
                cur.execute("SELECT discount_type_id FROM patients WHERE patient_id = %s", (qe["patient_id"],))
                pt = cur.fetchone()
                discount = 0.0
                if pt and pt["discount_type_id"]:
                    cur.execute("SELECT discount_percent FROM discount_types WHERE discount_id = %s AND is_active = 1",
                                (pt["discount_type_id"],))
                    dt = cur.fetchone()
                    if dt:
                        discount = float(dt["discount_percent"])

                total = unit_price * (1 - discount / 100)

                # Check if invoice already exists for this appointment
                cur.execute("SELECT invoice_id FROM invoices WHERE appointment_id = %s", (qe["appointment_id"],))
                if cur.fetchone():
                    return False

                cur.execute("""
                    INSERT INTO invoices (patient_id, appointment_id, discount_percent,
                        total_amount, amount_paid, status, notes)
                    VALUES (%s, %s, %s, %s, 0, 'Unpaid', 'Auto-generated on queue completion')
                """, (qe["patient_id"], qe["appointment_id"], discount, total))
                inv_id = cur.lastrowid
                cur.execute("""
                    INSERT INTO invoice_items (invoice_id, service_id, quantity, unit_price, subtotal)
                    VALUES (%s, %s, 1, %s, %s)
                """, (inv_id, appt["service_id"], unit_price, total))

                # Mark appointment as Completed
                cur.execute("UPDATE appointments SET status = 'Completed' WHERE appointment_id = %s",
                            (qe["appointment_id"],))

                conn.commit()
            self.log_activity("Created", "Invoice", f"Invoice #{inv_id} auto-created from queue #{queue_id}")
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False

    def complete_appointment_from_queue(self, queue_id):
        """Mark the appointment linked to a queue entry as Completed."""
        row = self.fetch("SELECT appointment_id FROM queue_entries WHERE queue_id=%s", (queue_id,), one=True)
        if row and row.get("appointment_id"):
            return self.exec("UPDATE appointments SET status='Completed' WHERE appointment_id=%s",
                             (row["appointment_id"],))
        return False

    def cancel_appointment_from_queue(self, queue_id):
        """Mark the appointment linked to a queue entry as Cancelled."""
        row = self.fetch("SELECT appointment_id FROM queue_entries WHERE queue_id=%s", (queue_id,), one=True)
        if row and row.get("appointment_id"):
            return self.exec("UPDATE appointments SET status='Cancelled' WHERE appointment_id=%s",
                             (row["appointment_id"],))
        return False

    def sync_today_appointments_to_queue(self):
        try:
            conn = self._get_connection()
            with conn.cursor(dictionary=True) as cur:
                cur.execute("""
                    SELECT a.appointment_id, a.patient_id, a.doctor_id, a.appointment_time, s.service_name
                    FROM appointments a INNER JOIN services s ON a.service_id = s.service_id
                    WHERE a.appointment_date = CURDATE() AND a.status = 'Confirmed'
                      AND a.appointment_id NOT IN (SELECT COALESCE(appointment_id,0) FROM queue_entries WHERE created_at = CURDATE())
                """)
                rows = cur.fetchall()
                for r in rows:
                    cur.execute("""
                        INSERT INTO queue_entries (patient_id, doctor_id, appointment_id, queue_time, purpose, status, created_at)
                        VALUES (%s,%s,%s,%s,%s,'Waiting',CURDATE())
                    """, (r["patient_id"], r["doctor_id"], r["appointment_id"], r["appointment_time"], r["service_name"]))
                conn.commit()
            if rows:
                self.log_activity("Created", "Queue", f"Synced {len(rows)} appointments to queue")
            return len(rows)
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return 0

    def call_next_queue(self, doctor_id=None, role=None):
        try:
            conn = self._get_connection()
            entry = None
            with conn.cursor(dictionary=True) as cur:
                # Doctor prefers Triaged patients first (nurse has prepared them),
                # then falls back to Waiting. Nurse only picks Waiting.
                if role == "Nurse":
                    status_order = ["Waiting"]
                else:
                    status_order = ["Triaged", "Waiting"]
                for target_status in status_order:
                    q = """SELECT queue_id, CONCAT(p.first_name,' ',p.last_name) AS patient_name
                           FROM queue_entries qe INNER JOIN patients p ON qe.patient_id = p.patient_id
                           WHERE qe.created_at = CURDATE() AND qe.status = %s"""
                    params = [target_status]
                    if doctor_id is not None:
                        q += " AND qe.doctor_id = %s"
                        params.append(doctor_id)
                    cur.execute(q + " ORDER BY qe.queue_time LIMIT 1", params)
                    entry = cur.fetchone()
                    if entry:
                        break
                if entry:
                    new_status = "In Progress" if role != "Nurse" else "Waiting"
                    cur.execute("UPDATE queue_entries SET status=%s, updated_at=NOW() WHERE queue_id=%s",
                                (new_status, entry["queue_id"]))
                    conn.commit()
            if entry:
                self.log_activity("Edited", "Queue", f"Called next: {entry['patient_name']} (queue #{entry['queue_id']})")
            return entry or {}
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return {}

    def get_avg_consultation_minutes(self):
        row = self.fetch("""
            SELECT AVG(TIMESTAMPDIFF(MINUTE, q.queue_time, q.updated_at)) AS avg_min
            FROM queue_entries q
            WHERE q.status = 'Completed' AND q.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
              AND q.updated_at IS NOT NULL
        """, one=True)
        if row and row.get("avg_min"):
            return max(5, int(row["avg_min"]))
        return 15

    # ── Invoices ───────────────────────────────────────────────────────
    def get_invoices(self):
        return self.fetch("""
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
            GROUP BY i.invoice_id ORDER BY i.created_at DESC
        """)

    def add_invoice(self, data):
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                pid = self._lookup_patient_id(data["patient_name"])
                if not pid:
                    return False
                cur.execute("SELECT discount_type_id FROM patients WHERE patient_id=%s", (pid,))
                dt_row = cur.fetchone()
                discount_type_id = dt_row[0] if dt_row else None

                # Always resolve the actual discount % from DB (admin-controlled)
                enforced_discount = 0.0
                if discount_type_id:
                    cur.execute("SELECT discount_percent FROM discount_types WHERE discount_id=%s AND is_active=1", (discount_type_id,))
                    dt_row = cur.fetchone()
                    if dt_row:
                        enforced_discount = float(dt_row[0])

                items = data.get("items", [])
                if not items and data.get("service_id"):
                    items = [{"service_id": data["service_id"], "quantity": data.get("quantity", 1), "discount": data.get("discount", 0)}]

                grand_total, total_before_discount, line_items = 0.0, 0.0, []
                for item in items:
                    cur.execute("SELECT price FROM services WHERE service_id=%s", (item["service_id"],))
                    srow = cur.fetchone()
                    up = float(srow[0]) if srow else 0
                    qty = int(item.get("quantity", 1))
                    # Use the DB-enforced discount instead of trusting UI value
                    disc = enforced_discount
                    sub_raw = up * qty
                    sub = sub_raw * (1 - disc / 100)
                    total_before_discount += sub_raw
                    grand_total += sub
                    line_items.append((item["service_id"], qty, up, sub))

                effective_discount = round((1 - grand_total / total_before_discount) * 100, 2) if total_before_discount > 0 else 0
                cur.execute("""
                    INSERT INTO invoices (patient_id, appointment_id, method_id,
                        discount_percent, total_amount, amount_paid, status, notes)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """, (pid, data.get("appointment_id") or None, data.get("method_id"),
                      effective_discount, grand_total, 0, "Unpaid", data.get("notes", "")))
                inv_id = cur.lastrowid
                for sid, qty, up, sub in line_items:
                    cur.execute("INSERT INTO invoice_items (invoice_id, service_id, quantity, unit_price, subtotal) VALUES (%s,%s,%s,%s,%s)",
                                (inv_id, sid, qty, up, sub))
                conn.commit()
            self.log_activity("Created", "Invoice", f"Invoice #{inv_id} for {data['patient_name']}")
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False

    def add_payment(self, invoice_id, amount, method_id=None):
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT total_amount, amount_paid FROM invoices WHERE invoice_id=%s", (invoice_id,))
                row = cur.fetchone()
                if not row:
                    return False
                total_amount = float(row[0])
                current_paid = float(row[1])
                remaining = total_amount - current_paid
                if remaining <= 0:
                    return False
                actual_amount = min(amount, remaining)
                new_paid = current_paid + actual_amount
                status = "Paid" if new_paid >= total_amount else "Partial"
                q, p = "UPDATE invoices SET amount_paid=%s, status=%s", [new_paid, status]
                if method_id:
                    q += ", method_id=%s"
                    p.append(method_id)
                cur.execute(q + " WHERE invoice_id=%s", p + [invoice_id])
                conn.commit()
            self.log_activity("Edited", "Invoice", f"Payment added to invoice #{invoice_id}")
            return True
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return False

    def void_invoice(self, invoice_id):
        ok = self.exec("UPDATE invoices SET status='Voided' WHERE invoice_id=%s", (invoice_id,))
        if ok:
            self.log_activity("Voided", "Invoice", f"Invoice #{invoice_id} voided")
        return ok

    def get_invoice_detail(self, invoice_id):
        info = self.fetch("""
            SELECT i.*, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                   p.phone, p.email, COALESCE(pm.method_name,'—') AS payment_method
            FROM invoices i INNER JOIN patients p ON i.patient_id = p.patient_id
            LEFT JOIN payment_methods pm ON i.method_id = pm.method_id
            WHERE i.invoice_id = %s
        """, (invoice_id,), one=True)
        if not info:
            return {}
        items = self.fetch("""
            SELECT s.service_name, ii.quantity, ii.unit_price, ii.subtotal
            FROM invoice_items ii INNER JOIN services s ON ii.service_id = s.service_id
            WHERE ii.invoice_id = %s
        """, (invoice_id,))
        return {"info": info, "items": items}

    def get_today_completed_appointments_for_patient(self, patient_name):
        return self.fetch("""
            SELECT a.appointment_id, a.appointment_time, s.service_name,
                   CONCAT(e.first_name,' ',e.last_name) AS doctor_name
            FROM appointments a
            INNER JOIN patients p ON a.patient_id = p.patient_id
            INNER JOIN services s ON a.service_id = s.service_id
            INNER JOIN employees e ON a.doctor_id = e.employee_id
            WHERE CONCAT(p.first_name,' ',p.last_name)=%s
              AND a.appointment_date = CURDATE()
              AND a.status IN ('Completed','Confirmed')
        """, (patient_name,))

    def get_payment_methods(self):
        return self.fetch("SELECT method_id, method_name FROM payment_methods ORDER BY method_name")

    # ── Services ───────────────────────────────────────────────────────
    def add_service(self, name, price, category="General"):
        ok = self.exec("INSERT INTO services (service_name, price, category) VALUES (%s,%s,%s)", (name, price, category))
        if ok:
            self.log_activity("Created", "Service", name)
        return ok

    def update_service_full(self, service_id, name, price, category="General", is_active=1):
        ok = self.exec("UPDATE services SET service_name=%s, price=%s, category=%s, is_active=%s WHERE service_id=%s",
                       (name, price, category, is_active, service_id))
        if ok:
            self.log_activity("Edited", "Service", name)
        return ok

    def bulk_update_prices(self, updates):
        queries = [("UPDATE services SET price=%s WHERE service_id=%s", (price, sid)) for sid, price in updates]
        ok = self.exec_many(queries)
        if ok is not False:
            self.log_activity("Edited", "Service", f"Bulk updated {len(updates)} prices")
            return True
        return False

    def get_service_usage_counts(self):
        rows = self.fetch("SELECT service_id, SUM(quantity) AS cnt FROM invoice_items GROUP BY service_id")
        return {r["service_id"]: int(r["cnt"]) for r in rows}

    def get_service_categories(self):
        rows = self.fetch("SELECT DISTINCT category FROM services ORDER BY category")
        return [r["category"] for r in rows]
