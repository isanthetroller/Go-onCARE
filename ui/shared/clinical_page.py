# Clinical page - Queue, Billing/POS, Services tabs

from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QComboBox, QStackedWidget, QGraphicsDropShadowEffect, QDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from ui.styles import configure_table, make_table_btn, make_table_btn_danger
from ui.shared.clinical_dialogs import (
    QueueEditDialog, ServiceEditDialog, NewInvoiceDialog,
    PaymentDialog, BulkPriceDialog,
)


# ══════════════════════════════════════════════════════════════════════
#  Clinical Page
# ══════════════════════════════════════════════════════════════════════
class ClinicalPage(QWidget):
    _TAB_STYLE = (
        "QPushButton {{ background: {bg}; color: {fg}; border: none;"
        " border-radius: 8px; padding: 8px 20px;"
        " font-size: 13px; font-weight: bold; }}"
        " QPushButton:hover {{ background: {hv}; }}"
    )
    _TAB_ACTIVE   = _TAB_STYLE.format(bg="#388087", fg="#FFFFFF", hv="#2C6A70")
    _TAB_INACTIVE = _TAB_STYLE.format(bg="#FFFFFF", fg="#2C3E50", hv="#BADFE7")

    def __init__(self, backend=None, role: str = "Admin"):
        super().__init__()
        self._backend = backend
        self._role = role
        self._tab_buttons: dict[str, QPushButton] = {}
        self._queue_ids: list[int] = []
        self._service_ids: list[int] = []
        self._invoice_ids: list[int] = []
        self._build()
        # Auto-refresh data every 10 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.refresh)
        self._refresh_timer.start(10_000)

    def refresh(self):
        """Reload data for all clinical tabs, auto-sync appointments."""
        try:
            if self._backend:
                self._backend.sync_today_appointments_to_queue()
            self._load_queue()
        except Exception:
            pass
        try:
            self._load_billing()
        except Exception:
            pass
        try:
            self._load_services()
        except Exception:
            pass

    # ── Build ──────────────────────────────────────────────────────
    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner.setObjectName("pageInner")
        lay = QVBoxLayout(inner)
        lay.setSpacing(20)
        lay.setContentsMargins(28, 28, 28, 28)

        # ── Header Banner ─────────────────────────────────────────
        banner = QFrame()
        banner.setObjectName("pageBanner")
        banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(32, 20, 32, 20)
        banner_lay.setSpacing(0)
        tc = QVBoxLayout(); tc.setSpacing(4)
        title = QLabel("Clinical Workflow & Billing")
        title.setObjectName("bannerTitle")
        sub = QLabel("Patient queue, consultations, and point-of-sale")
        sub.setObjectName("bannerSubtitle")
        tc.addWidget(title); tc.addWidget(sub)
        banner_lay.addLayout(tc)
        lay.addWidget(banner)

        # ── Tab row ───────────────────────────────────────────────
        tab_row = QHBoxLayout(); tab_row.setSpacing(8)
        self._stack = QStackedWidget()
        tab_labels: list[str] = []
        if self._role in ("Admin", "Doctor"):
            tab_labels.append("Patient Queue")
            self._stack.addWidget(self._build_queue_tab())
        if self._role in ("Admin", "Receptionist", "Cashier"):
            tab_labels.append("Billing / POS")
            self._stack.addWidget(self._build_billing_tab())
        if self._role == "Admin":
            tab_labels.append("Services & Pricing")
            self._stack.addWidget(self._build_services_tab())

        for i, label in enumerate(tab_labels):
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(38)
            btn.clicked.connect(lambda checked, idx=i, lbl=label: self._switch_tab(idx, lbl))
            self._tab_buttons[label] = btn
            tab_row.addWidget(btn)
        tab_row.addStretch()
        lay.addLayout(tab_row)
        lay.addWidget(self._stack)
        if tab_labels:
            self._switch_tab(0, tab_labels[0])

        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

    def _switch_tab(self, index: int, label: str):
        self._stack.setCurrentIndex(index)
        for name, btn in self._tab_buttons.items():
            btn.setStyleSheet(self._TAB_ACTIVE if name == label else self._TAB_INACTIVE)

    # ══════════════════════════════════════════════════════════════
    #  QUEUE TAB
    # ══════════════════════════════════════════════════════════════
    def _build_queue_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(16); lay.setContentsMargins(16, 16, 16, 16)

        # Status cards
        status_row = QHBoxLayout()
        stats = {"waiting": 0, "in_progress": 0, "completed": 0}
        if self._backend:
            stats = self._backend.get_queue_stats()
        self._queue_stat_labels = {}
        for key, label, color in [
            ("waiting",     "Waiting",          "#E8B931"),
            ("in_progress", "In Progress",      "#388087"),
            ("completed",   "Completed Today",  "#5CB85C"),
        ]:
            card = QFrame(); card.setObjectName("card")
            cl = QVBoxLayout(card); cl.setContentsMargins(16, 14, 16, 14); cl.setSpacing(4)
            strip = QFrame(); strip.setFixedHeight(3)
            strip.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
            v = QLabel(str(stats.get(key, 0) or 0)); v.setObjectName("statValue")
            self._queue_stat_labels[key] = v
            l = QLabel(label); l.setObjectName("statLabel")
            cl.addWidget(strip); cl.addWidget(v); cl.addWidget(l)
            status_row.addWidget(card)

        # Estimated wait time card
        avg_min = self._backend.get_avg_consultation_minutes() if self._backend else 15
        waiting_cnt = int(stats.get("waiting", 0) or 0)
        est_wait = waiting_cnt * avg_min
        wait_card = QFrame(); wait_card.setObjectName("card")
        wcl = QVBoxLayout(wait_card); wcl.setContentsMargins(16, 14, 16, 14); wcl.setSpacing(4)
        ws = QFrame(); ws.setFixedHeight(3)
        ws.setStyleSheet("background-color: #6FB3B8; border-radius: 1px;")
        self._wait_lbl = QLabel(f"~{est_wait} min"); self._wait_lbl.setObjectName("statValue")
        wl = QLabel("Est. Wait"); wl.setObjectName("statLabel")
        wcl.addWidget(ws); wcl.addWidget(self._wait_lbl); wcl.addWidget(wl)
        status_row.addWidget(wait_card)
        lay.addLayout(status_row)

        # Toolbar: call next, doctor filter
        toolbar = QHBoxLayout(); toolbar.setSpacing(10)

        call_btn = QPushButton("📢  Call Next")
        call_btn.setObjectName("actionBtn"); call_btn.setMinimumHeight(40)
        call_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        call_btn.clicked.connect(self._on_call_next)
        toolbar.addWidget(call_btn)

        toolbar.addStretch()

        self._queue_doc_filter = QComboBox()
        self._queue_doc_filter.setObjectName("formCombo")
        self._queue_doc_filter.setMinimumHeight(40); self._queue_doc_filter.setMinimumWidth(180)
        self._queue_doc_filter.addItem("All Doctors", None)
        if self._backend:
            for d in self._backend.get_doctors():
                self._queue_doc_filter.addItem(d["doctor_name"], d["employee_id"])
        self._queue_doc_filter.currentIndexChanged.connect(lambda _: self._filter_queue())
        toolbar.addWidget(self._queue_doc_filter)
        lay.addLayout(toolbar)

        # Queue table
        cols = ["Queue #", "Patient", "Time", "Doctor", "Purpose", "Status", "Actions"]
        self._queue_table = QTableWidget(0, len(cols))
        self._queue_table.setHorizontalHeaderLabels(cols)
        self._queue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._queue_table.horizontalHeader().setSectionResizeMode(len(cols)-1, QHeaderView.ResizeMode.Fixed)
        self._queue_table.setColumnWidth(len(cols)-1, 80)
        self._queue_table.horizontalHeader().setStretchLastSection(False)
        self._queue_table.verticalHeader().setVisible(False)
        self._queue_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._queue_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._queue_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._queue_table.setAlternatingRowColors(True)
        self._queue_table.setMinimumHeight(420)
        self._queue_table.verticalHeader().setDefaultSectionSize(48)
        configure_table(self._queue_table)
        # Auto-sync appointments into queue on first load
        if self._backend:
            try:
                self._backend.sync_today_appointments_to_queue()
            except Exception:
                pass
        self._load_queue()
        lay.addWidget(self._queue_table)
        return page

    def _load_queue(self):
        self._queue_table.setRowCount(0)
        self._queue_ids = []
        self._queue_doctor_ids = []
        if not self._backend:
            return
        rows = self._backend.get_queue_entries() or []
        for entry in rows:
            r = self._queue_table.rowCount()
            self._queue_table.insertRow(r)
            self._queue_ids.append(entry.get("queue_id", 0))
            self._queue_doctor_ids.append(entry.get("doctor_id", 0))
            t = entry.get("queue_time", "")
            if hasattr(t, "total_seconds"):
                total = int(t.total_seconds()); h, m = divmod(total // 60, 60)
                t = f"{h:02d}:{m:02d}"
            elif hasattr(t, "strftime"):
                t = t.strftime("%H:%M")
            values = [
                str(entry.get("queue_id", "")),
                entry.get("patient_name", ""),
                str(t),
                entry.get("doctor_name", ""),
                entry.get("purpose", "") or "",
                entry.get("status", ""),
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                if c == 5:
                    color_map = {"Waiting": "#E8B931", "In Progress": "#388087",
                                 "Completed": "#5CB85C", "Cancelled": "#D9534F"}
                    if val in color_map:
                        item.setForeground(QColor(color_map[val]))
                self._queue_table.setItem(r, c, item)
            act_w = QWidget(); act_lay = QHBoxLayout(act_w)
            act_lay.setContentsMargins(0,0,0,0); act_lay.setSpacing(6)
            edit_btn = make_table_btn("Edit"); edit_btn.setFixedWidth(52)
            edit_btn.clicked.connect(lambda checked, ri=r: self._on_edit_queue(ri))
            act_lay.addWidget(edit_btn)
            self._queue_table.setCellWidget(r, 6, act_w)

        # Update stat cards
        stats = self._backend.get_queue_stats()
        for key, lbl in self._queue_stat_labels.items():
            lbl.setText(str(stats.get(key, 0) or 0))
        # Update est wait
        avg_min = self._backend.get_avg_consultation_minutes()
        waiting_cnt = int(stats.get("waiting", 0) or 0)
        self._wait_lbl.setText(f"~{waiting_cnt * avg_min} min")
        self._filter_queue()

    def _filter_queue(self):
        doc_id = self._queue_doc_filter.currentData()
        for r in range(self._queue_table.rowCount()):
            if doc_id is None:
                self._queue_table.setRowHidden(r, False)
            else:
                hidden = (r < len(self._queue_doctor_ids) and self._queue_doctor_ids[r] != doc_id)
                self._queue_table.setRowHidden(r, hidden)

    def _on_sync_queue(self):
        if not self._backend:
            return
        n = self._backend.sync_today_appointments_to_queue()
        self._load_queue()
        QMessageBox.information(self, "Sync Complete", f"{n} appointment(s) added to today's queue.")

    def _on_call_next(self):
        if not self._backend:
            return
        doc_id = self._queue_doc_filter.currentData()
        entry = self._backend.call_next_queue(doctor_id=doc_id)
        if entry:
            self._load_queue()
            QMessageBox.information(self, "Called",
                                    f"Now seeing: {entry.get('patient_name', 'Unknown')}")
        else:
            QMessageBox.information(self, "Queue", "No waiting patients in queue.")

    def _on_edit_queue(self, row):
        data = {}
        keys = ["queue", "patient", "time", "doctor", "purpose", "status"]
        for c, key in enumerate(keys):
            data[key] = self._queue_table.item(row, c).text() if self._queue_table.item(row, c) else ""
        dlg = QueueEditDialog(self, data=data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if self._backend and row < len(self._queue_ids):
                self._backend.update_queue_entry(self._queue_ids[row], d)
            self._load_queue()
            QMessageBox.information(self, "Success", f"Queue entry '{d['queue']}' updated.")

    # ══════════════════════════════════════════════════════════════
    #  BILLING TAB
    # ══════════════════════════════════════════════════════════════
    def _build_billing_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(16); lay.setContentsMargins(16, 16, 16, 16)

        bar = QHBoxLayout()
        self._billing_search = QLineEdit()
        self._billing_search.setObjectName("searchBar")
        self._billing_search.setPlaceholderText("🔍  Search invoices…")
        self._billing_search.setMinimumHeight(42)
        self._billing_search.textChanged.connect(self._apply_billing_filters)
        bar.addWidget(self._billing_search)

        new_btn = QPushButton("＋  New Invoice")
        new_btn.setObjectName("actionBtn"); new_btn.setMinimumHeight(42)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self._on_new_invoice)
        bar.addWidget(new_btn)
        lay.addLayout(bar)

        # ── Sort & filter bar ─────────────────────────────────────
        sort_bar = QHBoxLayout(); sort_bar.setSpacing(10)

        self._billing_sort_combo = QComboBox()
        self._billing_sort_combo.setObjectName("formCombo")
        self._billing_sort_combo.addItems(["Sort By", "Patient", "Services", "Total", "Status"])
        self._billing_sort_combo.setMinimumHeight(42); self._billing_sort_combo.setMinimumWidth(140)
        self._billing_sort_combo.currentTextChanged.connect(self._apply_billing_filters)
        sort_bar.addWidget(self._billing_sort_combo)

        self._billing_order_combo = QComboBox()
        self._billing_order_combo.setObjectName("formCombo")
        self._billing_order_combo.addItems(["↑ Ascending", "↓ Descending"])
        self._billing_order_combo.setMinimumHeight(42); self._billing_order_combo.setMinimumWidth(140)
        self._billing_order_combo.currentTextChanged.connect(self._apply_billing_filters)
        sort_bar.addWidget(self._billing_order_combo)

        self._billing_status_filter = QComboBox()
        self._billing_status_filter.setObjectName("formCombo")
        self._billing_status_filter.addItems(["All Status", "Paid", "Unpaid", "Partial", "Voided"])
        self._billing_status_filter.setMinimumHeight(42); self._billing_status_filter.setMinimumWidth(140)
        self._billing_status_filter.currentTextChanged.connect(self._apply_billing_filters)
        sort_bar.addWidget(self._billing_status_filter)

        sort_bar.addStretch()
        lay.addLayout(sort_bar)

        cols = ["Inv #", "Patient", "Services", "Total", "Paid", "Status", "Actions"]
        self._billing_table = QTableWidget(0, len(cols))
        self._billing_table.setHorizontalHeaderLabels(cols)
        self._billing_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._billing_table.horizontalHeader().setSectionResizeMode(len(cols)-1, QHeaderView.ResizeMode.Fixed)
        self._billing_table.setColumnWidth(len(cols)-1, 160)
        self._billing_table.horizontalHeader().setStretchLastSection(False)
        self._billing_table.verticalHeader().setVisible(False)
        self._billing_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._billing_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._billing_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._billing_table.setAlternatingRowColors(True)
        self._billing_table.setMinimumHeight(420)
        self._billing_table.verticalHeader().setDefaultSectionSize(48)
        configure_table(self._billing_table)
        self._all_invoices: list[dict] = []
        self._load_billing()
        lay.addWidget(self._billing_table)
        return page

    def _load_billing(self):
        self._all_invoices = []
        self._invoice_ids = []
        if not self._backend:
            self._render_billing_table([])
            return
        self._all_invoices = self._backend.get_invoices() or []
        self._apply_billing_filters()

    def _apply_billing_filters(self, _=None):
        """Filter by search text + status, then sort, then render."""
        text = self._billing_search.text().strip().lower()
        status_filter = self._billing_status_filter.currentText()
        sort_by = self._billing_sort_combo.currentText()
        descending = self._billing_order_combo.currentText().startswith("↓")

        # ── Filter ────────────────────────────────────────────────
        filtered = []
        for inv in self._all_invoices:
            # Status filter
            if status_filter != "All Status" and inv.get("status", "") != status_filter:
                continue
            # Text search
            if text:
                haystack = " ".join([
                    str(inv.get("invoice_id", "")),
                    inv.get("patient_name", ""),
                    inv.get("service_name", "") or "",
                    inv.get("status", ""),
                ]).lower()
                if text not in haystack:
                    continue
            filtered.append(inv)

        # ── Sort ──────────────────────────────────────────────────
        sort_key_map = {
            "Patient":  lambda inv: (inv.get("patient_name", "") or "").lower(),
            "Services": lambda inv: (inv.get("service_name", "") or "").lower(),
            "Total":    lambda inv: float(inv.get("total_amount", 0) or 0),
            "Status":   lambda inv: (inv.get("status", "") or "").lower(),
        }
        if sort_by in sort_key_map:
            filtered.sort(key=sort_key_map[sort_by], reverse=descending)

        self._render_billing_table(filtered)

    def _render_billing_table(self, invoices: list[dict]):
        """Populate the billing table with the given (sorted/filtered) invoices."""
        self._billing_table.setRowCount(0)
        self._invoice_ids = []
        for inv in invoices:
            r = self._billing_table.rowCount()
            self._billing_table.insertRow(r)
            inv_id = inv.get("invoice_id", 0)
            self._invoice_ids.append(inv_id)
            total = inv.get("total_amount", 0) or 0
            paid = inv.get("amount_paid", 0) or 0
            status = inv.get("status", "")
            values = [
                str(inv_id),
                inv.get("patient_name", ""),
                inv.get("service_name", "") or "",
                f"₱{float(total):,.2f}",
                f"₱{float(paid):,.2f}",
                status,
            ]
            for c, val in enumerate(values):
                item = QTableWidgetItem(val)
                if c == 5:
                    clr = {"Paid": "#5CB85C", "Unpaid": "#D9534F", "Partial": "#E8B931",
                           "Voided": "#7F8C8D"}.get(val, "#7F8C8D")
                    item.setForeground(QColor(clr))
                self._billing_table.setItem(r, c, item)

            # Actions: Pay | Print | Void
            act_w = QWidget()
            act_lay = QHBoxLayout(act_w); act_lay.setContentsMargins(0,0,0,0); act_lay.setSpacing(6)
            if status not in ("Paid", "Voided"):
                pay_btn = make_table_btn("Pay"); pay_btn.setFixedWidth(46)
                pay_btn.clicked.connect(lambda checked, iid=inv_id: self._on_add_payment(iid))
                act_lay.addWidget(pay_btn)
            if status == "Paid":
                prt_btn = make_table_btn("Print"); prt_btn.setFixedWidth(52)
                prt_btn.clicked.connect(lambda checked, iid=inv_id: self._on_print_receipt(iid))
                act_lay.addWidget(prt_btn)
            if status != "Voided":
                void_btn = make_table_btn_danger("Void"); void_btn.setFixedWidth(46)
                void_btn.clicked.connect(lambda checked, iid=inv_id: self._on_void_invoice(iid))
                act_lay.addWidget(void_btn)
            self._billing_table.setCellWidget(r, 6, act_w)

    def _on_new_invoice(self):
        services = self._backend.get_services_list() if self._backend else []
        methods = self._backend.get_payment_methods() if self._backend else []
        patients = self._backend.get_active_patients() if self._backend else []
        dlg = NewInvoiceDialog(self, services=services, payment_methods=methods,
                               patients=patients, backend=self._backend, role=self._role)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if self._backend:
                ok = self._backend.add_invoice(d)
                if not ok:
                    QMessageBox.warning(self, "Error", "Failed to create invoice. Check patient name.")
                    return
            self._load_billing()
            QMessageBox.information(self, "Success", f"Invoice for '{d['patient_name']}' created.")

    def _on_add_payment(self, invoice_id: int):
        if not self._backend:
            return
        detail = self._backend.get_invoice_detail(invoice_id)
        if not detail:
            return
        info = detail["info"]
        balance = float(info["total_amount"]) - float(info["amount_paid"])
        if balance <= 0:
            QMessageBox.information(self, "Paid", "This invoice is already fully paid.")
            return
        methods = self._backend.get_payment_methods()
        dlg = PaymentDialog(self, invoice_id=invoice_id, balance=balance, payment_methods=methods)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            self._backend.add_payment(invoice_id, d["amount"], d.get("method_id"))
            self._load_billing()
            msg = f"Payment recorded.\n\n"
            msg += f"  Amount Tendered:  ₱{d['tendered']:,.2f}\n"
            msg += f"  Applied to Invoice:  ₱{d['amount']:,.2f}\n"
            if d.get("change", 0) > 0:
                msg += f"  Change:  ₱{d['change']:,.2f}\n"
            QMessageBox.information(self, "Payment Recorded", msg)

    def _on_void_invoice(self, invoice_id: int):
        reply = QMessageBox.question(
            self, "Void Invoice",
            f"Void invoice #{invoice_id}? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._backend:
                self._backend.void_invoice(invoice_id)
            self._load_billing()
            QMessageBox.information(self, "Done", f"Invoice #{invoice_id} voided.")

    def _on_print_receipt(self, invoice_id: int):
        if not self._backend:
            return
        detail = self._backend.get_invoice_detail(invoice_id)
        if not detail:
            QMessageBox.warning(self, "Error", "Could not load invoice details.")
            return
        info = detail["info"]
        items = detail["items"]

        total_amount = float(info.get("total_amount", 0))
        amount_paid = float(info.get("amount_paid", 0))
        discount_pct = float(info.get("discount_percent", 0))

        # Calculate raw subtotal from line items
        raw_subtotal = sum(
            float(it.get("unit_price", 0)) * int(it.get("quantity", 1))
            for it in items
        )
        discount_amount = raw_subtotal - total_amount

        balance = total_amount - amount_paid
        # If fully paid, the change is whatever was overpaid (stored as amount_paid == total)
        change = max(0, amount_paid - total_amount) if info.get("status") == "Paid" else 0

        w = 48  # receipt width
        lines = [
            "=" * w,
            "C A R E C R U D".center(w),
            "HEALTHCARE MANAGEMENT SYSTEM".center(w),
            "=" * w,
            f"  Invoice #:     {info.get('invoice_id', '')}",
            f"  Date:          {info.get('created_at', '')}",
            f"  Patient:       {info.get('patient_name', '')}",
            f"  Phone:         {info.get('phone', '') or '—'}",
            f"  Payment Mode:  {info.get('payment_method', '—')}",
            "-" * w,
            f"  {'Service':<20} {'Qty':>4} {'Unit':>9} {'Sub':>9}",
            "-" * w,
        ]
        for it in items:
            sname = it.get("service_name", "")
            qty = int(it.get("quantity", 1))
            unit = float(it.get("unit_price", 0))
            sub = float(it.get("subtotal", 0))
            # Truncate long service names
            if len(sname) > 20:
                sname = sname[:18] + ".."
            lines.append(
                f"  {sname:<20} {qty:>4} ₱{unit:>8,.2f} ₱{sub:>8,.2f}"
            )

        lines.append("-" * w)

        if discount_amount > 0:
            lines.append(f"  {'Subtotal':<28} ₱{raw_subtotal:>12,.2f}")
            lines.append(f"  {'Discount':<28} -₱{discount_amount:>11,.2f}")

        lines += [
            f"  {'TOTAL':<28} ₱{total_amount:>12,.2f}",
            f"  {'AMOUNT PAID':<28} ₱{amount_paid:>12,.2f}",
        ]

        if balance > 0:
            lines.append(f"  {'BALANCE DUE':<28} ₱{balance:>12,.2f}")

        if change > 0:
            lines.append(f"  {'CHANGE':<28} ₱{change:>12,.2f}")

        lines += [
            f"  Status: {info.get('status', '')}",
            "=" * w,
            "Thank you for choosing us!".center(w),
            "=" * w,
        ]
        text = "\n".join(lines)
        QMessageBox.information(self, f"Receipt – Invoice #{invoice_id}", text)

    # ══════════════════════════════════════════════════════════════
    #  SERVICES TAB
    # ══════════════════════════════════════════════════════════════
    def _build_services_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page); lay.setSpacing(16); lay.setContentsMargins(16, 16, 16, 16)

        bar = QHBoxLayout()
        self._svc_search = QLineEdit()
        self._svc_search.setObjectName("searchBar")
        self._svc_search.setPlaceholderText("🔍  Search services…")
        self._svc_search.setMinimumHeight(42)
        self._svc_search.textChanged.connect(self._on_svc_search)
        bar.addWidget(self._svc_search)

        self._svc_cat_filter = QComboBox()
        self._svc_cat_filter.setObjectName("formCombo")
        self._svc_cat_filter.setMinimumHeight(42); self._svc_cat_filter.setMinimumWidth(150)
        self._svc_cat_filter.addItem("All Categories")
        if self._backend:
            for c in self._backend.get_service_categories():
                self._svc_cat_filter.addItem(c)
        self._svc_cat_filter.currentTextChanged.connect(lambda _: self._apply_svc_filters())
        bar.addWidget(self._svc_cat_filter)

        add_btn = QPushButton("＋  Add Service")
        add_btn.setObjectName("actionBtn"); add_btn.setMinimumHeight(42)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._on_add_service)
        bar.addWidget(add_btn)

        bulk_btn = QPushButton("💲  Bulk Price Update")
        bulk_btn.setObjectName("actionBtn"); bulk_btn.setMinimumHeight(42)
        bulk_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bulk_btn.clicked.connect(self._on_bulk_price)
        bar.addWidget(bulk_btn)
        lay.addLayout(bar)

        cols = ["Service Name", "Category", "Price", "Usage", "Active", "Actions"]
        self._svc_table = QTableWidget(0, len(cols))
        self._svc_table.setHorizontalHeaderLabels(cols)
        self._svc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._svc_table.horizontalHeader().setSectionResizeMode(len(cols)-1, QHeaderView.ResizeMode.Fixed)
        self._svc_table.setColumnWidth(len(cols)-1, 80)
        self._svc_table.horizontalHeader().setStretchLastSection(False)
        self._svc_table.verticalHeader().setVisible(False)
        self._svc_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._svc_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._svc_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._svc_table.setAlternatingRowColors(True)
        self._svc_table.setMinimumHeight(420)
        self._svc_table.verticalHeader().setDefaultSectionSize(48)
        configure_table(self._svc_table)
        self._load_services()
        lay.addWidget(self._svc_table)
        return page

    def _load_services(self):
        self._svc_table.setRowCount(0)
        self._service_ids = []
        if not self._backend:
            return
        rows = self._backend.get_all_services() or []
        usage = self._backend.get_service_usage_counts() or {}
        for svc in rows:
            r = self._svc_table.rowCount()
            self._svc_table.insertRow(r)
            sid = svc.get("service_id", 0)
            self._service_ids.append(sid)
            price = svc.get("price", 0) or 0
            is_active = svc.get("is_active", 1)
            cat = svc.get("category", "General") or "General"
            use_cnt = usage.get(sid, 0)

            self._svc_table.setItem(r, 0, QTableWidgetItem(svc.get("service_name", "")))
            self._svc_table.setItem(r, 1, QTableWidgetItem(cat))
            self._svc_table.setItem(r, 2, QTableWidgetItem(f"₱{float(price):,.2f}"))
            self._svc_table.setItem(r, 3, QTableWidgetItem(str(use_cnt)))
            active_item = QTableWidgetItem("Yes" if is_active else "No")
            active_item.setForeground(QColor("#5CB85C" if is_active else "#D9534F"))
            self._svc_table.setItem(r, 4, active_item)

            act_w = QWidget(); act_lay = QHBoxLayout(act_w)
            act_lay.setContentsMargins(0,0,0,0); act_lay.setSpacing(6)
            edit_btn = make_table_btn("Edit"); edit_btn.setFixedWidth(52)
            edit_btn.clicked.connect(lambda checked, ri=r: self._on_edit_service(ri))
            act_lay.addWidget(edit_btn)
            self._svc_table.setCellWidget(r, 5, act_w)

    def _on_svc_search(self, _text: str = ""):
        self._apply_svc_filters()

    def _apply_svc_filters(self):
        text = self._svc_search.text().strip().lower()
        cat = self._svc_cat_filter.currentText()
        for r in range(self._svc_table.rowCount()):
            text_match = True
            if text:
                text_match = any(
                    text in (self._svc_table.item(r, c).text().lower() if self._svc_table.item(r, c) else "")
                    for c in range(5)
                )
            cat_match = True
            if cat != "All Categories":
                cell = self._svc_table.item(r, 1)
                cat_match = (cell.text() == cat) if cell else False
            self._svc_table.setRowHidden(r, not (text_match and cat_match))

    def _on_add_service(self):
        cats = self._backend.get_service_categories() if self._backend else []
        if not cats:
            cats = ["General"]
        dlg = ServiceEditDialog(self, categories=cats)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Service name is required.")
                return
            try:
                price = float(d["price"].replace("₱", "").replace(",", ""))
            except (ValueError, AttributeError):
                price = 0
            if self._backend:
                ok = self._backend.add_service(d["name"], price, d["category"])
                if not ok:
                    QMessageBox.warning(self, "Error", "Failed to add service.")
                    return
            self._load_services()
            QMessageBox.information(self, "Success", f"Service '{d['name']}' added.")

    def _on_edit_service(self, row):
        data = {
            "name":      self._svc_table.item(row, 0).text() if self._svc_table.item(row, 0) else "",
            "category":  self._svc_table.item(row, 1).text() if self._svc_table.item(row, 1) else "General",
            "price":     (self._svc_table.item(row, 2).text().replace("₱", "").replace(",", "")
                          if self._svc_table.item(row, 2) else ""),
            "is_active": (self._svc_table.item(row, 4).text() == "Yes") if self._svc_table.item(row, 4) else True,
        }
        cats = self._backend.get_service_categories() if self._backend else ["General"]
        dlg = ServiceEditDialog(self, data=data, categories=cats)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Service name is required.")
                return
            try:
                price = float(d["price"].replace("₱", "").replace(",", ""))
            except (ValueError, AttributeError):
                price = 0
            if self._backend and row < len(self._service_ids):
                ok = self._backend.update_service_full(
                    self._service_ids[row], d["name"], price,
                    d["category"], 1 if d["is_active"] else 0,
                )
                if not ok:
                    QMessageBox.warning(self, "Error", "Failed to update service.")
                    return
            self._load_services()
            QMessageBox.information(self, "Success", f"Service '{d['name']}' updated.")

    def _on_bulk_price(self):
        if not self._backend:
            return
        services = self._backend.get_all_services() or []
        dlg = BulkPriceDialog(self, services=services)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updates = dlg.get_updates()
            if updates:
                self._backend.bulk_update_prices(updates)
                self._load_services()
                QMessageBox.information(self, "Done", f"{len(updates)} price(s) updated.")
            else:
                QMessageBox.information(self, "No Changes", "No prices were modified.")
