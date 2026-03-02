# Queue, invoices, billing, services


class ClinicalMixin:

    # ── Queue ──────────────────────────────────────────────────────────
    def get_queue_entries(self):
        return self.fetch("""
            SELECT q.queue_id, q.queue_time, q.purpose, q.status,
                   CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                   CONCAT(e.first_name,' ',e.last_name) AS doctor_name, q.doctor_id
            FROM queue_entries q
            INNER JOIN patients p ON q.patient_id = p.patient_id
            INNER JOIN employees e ON q.doctor_id = e.employee_id
            WHERE q.created_at = CURDATE() ORDER BY q.queue_time
        """)

    def get_queue_stats(self):
        row = self.fetch("""
            SELECT SUM(CASE WHEN status='Waiting' THEN 1 ELSE 0 END) AS waiting,
                   SUM(CASE WHEN status='In Progress' THEN 1 ELSE 0 END) AS in_progress,
                   SUM(CASE WHEN status='Completed' THEN 1 ELSE 0 END) AS completed
            FROM queue_entries WHERE created_at = CURDATE()
        """, one=True)
        return row if row and row.get("waiting") is not None else {"waiting": 0, "in_progress": 0, "completed": 0}

    def update_queue_status(self, queue_id, status):
        return self.exec("UPDATE queue_entries SET status=%s WHERE queue_id=%s", (status, queue_id))

    def update_queue_entry(self, queue_id, data):
        return self.exec("UPDATE queue_entries SET status=%s, purpose=%s WHERE queue_id=%s",
                         (data.get("status", "Waiting"), data.get("purpose", ""), queue_id))

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

    def call_next_queue(self, doctor_id=None):
        try:
            conn = self._get_connection()
            with conn.cursor(dictionary=True) as cur:
                q = """SELECT queue_id, CONCAT(p.first_name,' ',p.last_name) AS patient_name
                       FROM queue_entries qe INNER JOIN patients p ON qe.patient_id = p.patient_id
                       WHERE qe.created_at = CURDATE() AND qe.status = 'Waiting'"""
                params = []
                if doctor_id:
                    q += " AND qe.doctor_id = %s"
                    params.append(doctor_id)
                cur.execute(q + " ORDER BY qe.queue_time LIMIT 1", params)
                entry = cur.fetchone()
                if entry:
                    cur.execute("UPDATE queue_entries SET status='In Progress' WHERE queue_id=%s", (entry["queue_id"],))
                    conn.commit()
            return entry or {}
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            return {}

    def get_avg_consultation_minutes(self):
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
                cur.execute("SELECT patient_id, discount_type_id FROM patients WHERE CONCAT(first_name,' ',last_name)=%s LIMIT 1", (data["patient_name"],))
                prow = cur.fetchone()
                if not prow:
                    return False
                patient_id = prow[0]
                discount_type_id = prow[1]

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
                """, (patient_id, data.get("appointment_id") or None, data.get("method_id"),
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

    def update_service(self, service_id, price):
        return self.exec("UPDATE services SET price=%s WHERE service_id=%s", (price, service_id))

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
