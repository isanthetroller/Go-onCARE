"""Clinical Workflow & Point-of-Sale page – V2

Queue:   auto-sync from today's confirmed appointments, doctor filter,
         call-next button, estimated wait time, notes column.
Billing: patient dropdown, multi-item invoice, partial payment, receipt
         print, void/refund, link-to-appointment, payment history.
Services: categories, deactivation toggle, usage count, bulk price update.
"""

import csv, io, textwrap
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QComboBox, QStackedWidget, QTextEdit, QSpinBox, QDoubleSpinBox,
    QGraphicsDropShadowEffect, QDialog, QFormLayout, QDialogButtonBox,
    QMessageBox, QCheckBox, QFileDialog, QTabWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from ui.styles import configure_table, make_table_btn, make_table_btn_danger, style_dialog_btns


# ══════════════════════════════════════════════════════════════════════
#  Queue Edit Dialog
# ══════════════════════════════════════════════════════════════════════
class QueueEditDialog(QDialog):
    """Dialog to edit a patient queue entry (status, purpose, notes)."""

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Queue Entry")
        self.setMinimumWidth(480)
        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.queue_num = QLineEdit(data.get("queue", "") if data else "")
        self.queue_num.setObjectName("formInput"); self.queue_num.setMinimumHeight(38)
        self.queue_num.setReadOnly(True)
        self.patient_edit = QLineEdit(data.get("patient", "") if data else "")
        self.patient_edit.setObjectName("formInput"); self.patient_edit.setMinimumHeight(38)
        self.patient_edit.setReadOnly(True)
        self.time_edit = QLineEdit(data.get("time", "") if data else "")
        self.time_edit.setObjectName("formInput"); self.time_edit.setMinimumHeight(38)
        self.time_edit.setReadOnly(True)
        self.doctor_edit = QLineEdit(data.get("doctor", "") if data else "")
        self.doctor_edit.setObjectName("formInput"); self.doctor_edit.setMinimumHeight(38)
        self.doctor_edit.setReadOnly(True)
        self.purpose_edit = QLineEdit(data.get("purpose", "") if data else "")
        self.purpose_edit.setObjectName("formInput"); self.purpose_edit.setMinimumHeight(38)
        self.status_combo = QComboBox()
        self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(["Waiting", "In Progress", "Completed", "Cancelled"])
        self.status_combo.setMinimumHeight(38)
        if data and data.get("status"):
            idx = self.status_combo.findText(data["status"])
            if idx >= 0:
                self.status_combo.setCurrentIndex(idx)
        self.notes_edit = QTextEdit()
        self.notes_edit.setObjectName("formInput")
        self.notes_edit.setMaximumHeight(70)
        self.notes_edit.setPlainText(data.get("notes", "") if data else "")

        form.addRow("Queue #", self.queue_num)
        form.addRow("Patient", self.patient_edit)
        form.addRow("Time", self.time_edit)
        form.addRow("Doctor", self.doctor_edit)
        form.addRow("Purpose", self.purpose_edit)
        form.addRow("Status", self.status_combo)
        form.addRow("Notes", self.notes_edit)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        style_dialog_btns(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def get_data(self) -> dict:
        return {
            "queue":   self.queue_num.text(),
            "patient": self.patient_edit.text(),
            "time":    self.time_edit.text(),
            "doctor":  self.doctor_edit.text(),
            "purpose": self.purpose_edit.text(),
            "status":  self.status_combo.currentText(),
            "notes":   self.notes_edit.toPlainText(),
        }


# ══════════════════════════════════════════════════════════════════════
#  Service Edit Dialog (V2 – category, active toggle)
# ══════════════════════════════════════════════════════════════════════
class ServiceEditDialog(QDialog):
    """Dialog to add/edit a service with category and active toggle."""

    def __init__(self, parent=None, data=None, categories=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Service" if data else "Add Service")
        self.setMinimumWidth(440)
        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.name_edit = QLineEdit(data.get("name", "") if data else "")
        self.name_edit.setObjectName("formInput"); self.name_edit.setMinimumHeight(38)
        self.price_edit = QLineEdit(data.get("price", "") if data else "")
        self.price_edit.setObjectName("formInput"); self.price_edit.setMinimumHeight(38)
        self.cat_combo = QComboBox(); self.cat_combo.setObjectName("formCombo")
        self.cat_combo.setEditable(True)
        self.cat_combo.setMinimumHeight(38)
        cats = categories or ["General"]
        self.cat_combo.addItems(cats)
        if data and data.get("category"):
            idx = self.cat_combo.findText(data["category"])
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
            else:
                self.cat_combo.setCurrentText(data["category"])
        self.active_check = QCheckBox("Active")
        self.active_check.setChecked(data.get("is_active", True) if data else True)

        form.addRow("Service Name", self.name_edit)
        form.addRow("Price", self.price_edit)
        form.addRow("Category", self.cat_combo)
        form.addRow("", self.active_check)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        style_dialog_btns(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def get_data(self) -> dict:
        return {
            "name":      self.name_edit.text(),
            "price":     self.price_edit.text(),
            "category":  self.cat_combo.currentText(),
            "is_active": self.active_check.isChecked(),
        }


# ══════════════════════════════════════════════════════════════════════
#  New Invoice Dialog (V2 – patient dropdown, multi-line, link-to-appt)
# ══════════════════════════════════════════════════════════════════════
class NewInvoiceDialog(QDialog):
    """Create an invoice with multi-item support and optional appointment link."""

    def __init__(self, parent=None, *, services=None, payment_methods=None,
                 patients=None, backend=None):
        super().__init__(parent)
        self.setWindowTitle("Create Invoice")
        self.setMinimumWidth(580)

        self._services = services or []
        self._payment_methods = payment_methods or []
        self._patients = patients or []
        self._backend = backend
        self._line_items: list[dict] = []

        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        # Patient dropdown
        self.patient_combo = QComboBox()
        self.patient_combo.setObjectName("formCombo")
        self.patient_combo.setEditable(True)
        self.patient_combo.setMinimumHeight(38)
        for p in self._patients:
            self.patient_combo.addItem(p["name"], p.get("patient_id"))
        self.patient_combo.currentTextChanged.connect(self._on_patient_changed)

        # Link to appointment
        self.appt_combo = QComboBox()
        self.appt_combo.setObjectName("formCombo")
        self.appt_combo.setMinimumHeight(38)
        self.appt_combo.addItem("— None —", None)

        # Line items section
        items_frame = QFrame()
        items_frame.setObjectName("card")
        items_lay = QVBoxLayout(items_frame)
        items_lay.setContentsMargins(12, 12, 12, 12)
        items_lay.setSpacing(8)

        lbl = QLabel("Line Items")
        lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #2C3E50;")
        items_lay.addWidget(lbl)

        # Add-line row
        add_row = QHBoxLayout()
        self.svc_combo = QComboBox(); self.svc_combo.setObjectName("formCombo")
        self.svc_combo.setMinimumHeight(34)
        for svc in self._services:
            self.svc_combo.addItem(f"{svc['service_name']} (₱{float(svc.get('price',0)):,.0f})", svc["service_id"])
        add_row.addWidget(self.svc_combo, 2)
        self.qty_spin = QSpinBox(); self.qty_spin.setMinimum(1); self.qty_spin.setMaximum(99)
        self.qty_spin.setValue(1); self.qty_spin.setMinimumHeight(34)
        add_row.addWidget(self.qty_spin)
        self.disc_spin = QDoubleSpinBox(); self.disc_spin.setMinimum(0)
        self.disc_spin.setMaximum(100); self.disc_spin.setSuffix(" %"); self.disc_spin.setMinimumHeight(34)
        add_row.addWidget(self.disc_spin)
        add_btn = QPushButton("＋ Add")
        add_btn.setMinimumHeight(34)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            "QPushButton { background: #388087; color: #fff; border: none; border-radius: 4px; padding: 4px 12px; font-weight:bold; }"
            " QPushButton:hover { background: #2C6A70; }"
        )
        add_btn.clicked.connect(self._add_line)
        add_row.addWidget(add_btn)
        items_lay.addLayout(add_row)

        # Items table
        self._items_table = QTableWidget(0, 5)
        self._items_table.setHorizontalHeaderLabels(["Service", "Qty", "Unit Price", "Discount", "Subtotal"])
        self._items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._items_table.verticalHeader().setVisible(False)
        self._items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._items_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._items_table.setMaximumHeight(140)
        self._items_table.verticalHeader().setDefaultSectionSize(32)
        configure_table(self._items_table)
        items_lay.addWidget(self._items_table)

        self._total_lbl = QLabel("Total: ₱0.00")
        self._total_lbl.setStyleSheet("font-weight: bold; font-size: 14px; color: #388087;")
        self._total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        items_lay.addWidget(self._total_lbl)

        # Payment method
        self.payment_combo = QComboBox()
        self.payment_combo.setObjectName("formCombo")
        for pm in self._payment_methods:
            self.payment_combo.addItem(pm["method_name"], pm["method_id"])
        self.payment_combo.setMinimumHeight(38)

        self.notes = QTextEdit()
        self.notes.setObjectName("formInput")
        self.notes.setMaximumHeight(70)

        form.addRow("Patient", self.patient_combo)
        form.addRow("Link to Appointment", self.appt_combo)
        form.addRow(items_frame)
        form.addRow("Payment Method", self.payment_combo)
        form.addRow("Notes", self.notes)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        style_dialog_btns(btns)
        btns.accepted.connect(self._validate_and_accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    # ── helpers ────────────────────────────────────────────────────
    def _on_patient_changed(self, text: str):
        """Update appointment dropdown when patient changes."""
        self.appt_combo.clear()
        self.appt_combo.addItem("— None —", None)
        if self._backend and text.strip():
            appts = self._backend.get_today_completed_appointments_for_patient(text.strip())
            for a in appts:
                t = a.get("appointment_time", "")
                if hasattr(t, "total_seconds"):
                    total = int(t.total_seconds())
                    h, m = divmod(total // 60, 60)
                    t = f"{h:02d}:{m:02d}"
                self.appt_combo.addItem(
                    f"#{a['appointment_id']} – {a['service_name']} @ {t}",
                    a["appointment_id"],
                )

    def _add_line(self):
        sid = self.svc_combo.currentData()
        svc_text = self.svc_combo.currentText()
        qty = self.qty_spin.value()
        disc = self.disc_spin.value()
        # Find price
        price = 0
        for s in self._services:
            if s["service_id"] == sid:
                price = float(s.get("price", 0))
                break
        sub = price * qty * (1 - disc / 100)
        self._line_items.append({"service_id": sid, "quantity": qty, "discount": disc})
        r = self._items_table.rowCount()
        self._items_table.insertRow(r)
        name_only = svc_text.split(" (₱")[0] if " (₱" in svc_text else svc_text
        self._items_table.setItem(r, 0, QTableWidgetItem(name_only))
        self._items_table.setItem(r, 1, QTableWidgetItem(str(qty)))
        self._items_table.setItem(r, 2, QTableWidgetItem(f"₱{price:,.2f}"))
        self._items_table.setItem(r, 3, QTableWidgetItem(f"{disc:.0f}%"))
        self._items_table.setItem(r, 4, QTableWidgetItem(f"₱{sub:,.2f}"))
        self._update_total()

    def _update_total(self):
        total = 0
        for r in range(self._items_table.rowCount()):
            txt = self._items_table.item(r, 4).text().replace("₱", "").replace(",", "")
            try:
                total += float(txt)
            except ValueError:
                pass
        self._total_lbl.setText(f"Total: ₱{total:,.2f}")

    def _validate_and_accept(self):
        if not self.patient_combo.currentText().strip():
            QMessageBox.warning(self, "Validation", "Patient is required.")
            return
        if not self._line_items:
            QMessageBox.warning(self, "Validation", "Add at least one line item.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "patient_name":   self.patient_combo.currentText().strip(),
            "items":          self._line_items,
            "method_id":      self.payment_combo.currentData(),
            "notes":          self.notes.toPlainText(),
            "appointment_id": self.appt_combo.currentData(),
        }


# ══════════════════════════════════════════════════════════════════════
#  Payment Dialog (partial payment)
# ══════════════════════════════════════════════════════════════════════
class PaymentDialog(QDialog):
    def __init__(self, parent=None, *, invoice_id=0, balance=0.0, payment_methods=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add Payment – Invoice #{invoice_id}")
        self.setMinimumWidth(400)
        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMinimum(0.01)
        self.amount_spin.setMaximum(999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("₱ ")
        self.amount_spin.setValue(balance)
        self.amount_spin.setMinimumHeight(38)

        self.method_combo = QComboBox(); self.method_combo.setObjectName("formCombo")
        self.method_combo.setMinimumHeight(38)
        for pm in (payment_methods or []):
            self.method_combo.addItem(pm["method_name"], pm["method_id"])

        form.addRow("Amount", self.amount_spin)
        form.addRow("Method", self.method_combo)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        style_dialog_btns(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def get_data(self):
        return {"amount": self.amount_spin.value(), "method_id": self.method_combo.currentData()}


# ══════════════════════════════════════════════════════════════════════
#  Bulk Price Update Dialog
# ══════════════════════════════════════════════════════════════════════
class BulkPriceDialog(QDialog):
    def __init__(self, parent=None, services=None):
        super().__init__(parent)
        self.setWindowTitle("Bulk Price Update")
        self.setMinimumWidth(520)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 28, 28, 28)
        lay.setSpacing(14)
        lbl = QLabel("Adjust prices for all services. Leave unchanged to skip.")
        lbl.setStyleSheet("color:#7F8C8D; font-size:12px;")
        lay.addWidget(lbl)

        self._table = QTableWidget(len(services or []), 3)
        self._table.setHorizontalHeaderLabels(["Service", "Current Price", "New Price"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(36)
        self._table.setMinimumHeight(min(len(services or []) * 36 + 44, 400))
        configure_table(self._table)

        self._svc_ids = []
        for r, svc in enumerate(services or []):
            self._svc_ids.append(svc["service_id"])
            self._table.setItem(r, 0, QTableWidgetItem(svc.get("service_name", "")))
            old_price = float(svc.get("price", 0))
            item = QTableWidgetItem(f"₱{old_price:,.2f}")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._table.setItem(r, 1, item)
            self._table.setItem(r, 2, QTableWidgetItem(""))
        lay.addWidget(self._table)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        style_dialog_btns(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_updates(self) -> list:
        """Return [(service_id, new_price), ...] for rows that were changed."""
        updates = []
        for r in range(self._table.rowCount()):
            txt = (self._table.item(r, 2).text().replace("₱", "").replace(",", "").strip()
                   if self._table.item(r, 2) else "")
            if txt:
                try:
                    updates.append((self._svc_ids[r], float(txt)))
                except ValueError:
                    pass
        return updates


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

        # Toolbar: sync, call next, doctor filter
        toolbar = QHBoxLayout(); toolbar.setSpacing(10)
        sync_btn = QPushButton("🔄  Sync Appointments")
        sync_btn.setObjectName("actionBtn"); sync_btn.setMinimumHeight(40)
        sync_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sync_btn.clicked.connect(self._on_sync_queue)
        toolbar.addWidget(sync_btn)

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
        self._queue_table.setColumnWidth(len(cols)-1, 170)
        self._queue_table.verticalHeader().setVisible(False)
        self._queue_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._queue_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._queue_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._queue_table.setAlternatingRowColors(True)
        self._queue_table.setMinimumHeight(420)
        self._queue_table.verticalHeader().setDefaultSectionSize(48)
        configure_table(self._queue_table)
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
            act_lay.setContentsMargins(4, 4, 4, 4); act_lay.setSpacing(4)
            edit_btn = make_table_btn("Edit")
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
        self._billing_search.textChanged.connect(self._on_billing_search)
        bar.addWidget(self._billing_search)

        new_btn = QPushButton("＋  New Invoice")
        new_btn.setObjectName("actionBtn"); new_btn.setMinimumHeight(42)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self._on_new_invoice)
        bar.addWidget(new_btn)

        export_btn = QPushButton("⬇  Export CSV")
        export_btn.setObjectName("actionBtn"); export_btn.setMinimumHeight(42)
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self._export_billing_csv)
        bar.addWidget(export_btn)
        lay.addLayout(bar)

        cols = ["Inv #", "Patient", "Services", "Total", "Paid", "Status", "Actions"]
        self._billing_table = QTableWidget(0, len(cols))
        self._billing_table.setHorizontalHeaderLabels(cols)
        self._billing_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._billing_table.horizontalHeader().setSectionResizeMode(len(cols)-1, QHeaderView.ResizeMode.Fixed)
        self._billing_table.setColumnWidth(len(cols)-1, 170)
        self._billing_table.verticalHeader().setVisible(False)
        self._billing_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._billing_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._billing_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._billing_table.setAlternatingRowColors(True)
        self._billing_table.setMinimumHeight(420)
        self._billing_table.verticalHeader().setDefaultSectionSize(48)
        configure_table(self._billing_table)
        self._load_billing()
        lay.addWidget(self._billing_table)
        return page

    def _load_billing(self):
        self._billing_table.setRowCount(0)
        self._invoice_ids = []
        if not self._backend:
            return
        rows = self._backend.get_invoices() or []
        for inv in rows:
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
            act_lay = QHBoxLayout(act_w); act_lay.setContentsMargins(4, 4, 4, 4); act_lay.setSpacing(4)
            if status not in ("Paid", "Voided"):
                pay_btn = make_table_btn("Pay")
                pay_btn.clicked.connect(lambda checked, iid=inv_id: self._on_add_payment(iid))
                act_lay.addWidget(pay_btn)
            prt_btn = make_table_btn("Print")
            prt_btn.clicked.connect(lambda checked, iid=inv_id: self._on_print_receipt(iid))
            act_lay.addWidget(prt_btn)
            if status != "Voided":
                void_btn = make_table_btn_danger("Void")
                void_btn.clicked.connect(lambda checked, iid=inv_id: self._on_void_invoice(iid))
                act_lay.addWidget(void_btn)
            self._billing_table.setCellWidget(r, 6, act_w)

    def _on_billing_search(self, text: str):
        text = text.lower()
        for r in range(self._billing_table.rowCount()):
            match = any(
                text in (self._billing_table.item(r, c).text().lower() if self._billing_table.item(r, c) else "")
                for c in range(self._billing_table.columnCount() - 1)
            )
            self._billing_table.setRowHidden(r, not match)

    def _on_new_invoice(self):
        services = self._backend.get_services_list() if self._backend else []
        methods = self._backend.get_payment_methods() if self._backend else []
        patients = self._backend.get_active_patients() if self._backend else []
        dlg = NewInvoiceDialog(self, services=services, payment_methods=methods,
                               patients=patients, backend=self._backend)
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
        methods = self._backend.get_payment_methods()
        dlg = PaymentDialog(self, invoice_id=invoice_id, balance=balance, payment_methods=methods)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            self._backend.add_payment(invoice_id, d["amount"], d.get("method_id"))
            self._load_billing()
            QMessageBox.information(self, "Success", f"Payment of ₱{d['amount']:,.2f} recorded.")

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
        lines = [
            "=" * 44,
            "               C A R E C R U D",
            "          HEALTHCARE MANAGEMENT SYSTEM",
            "=" * 44,
            f"  Invoice #:     {info.get('invoice_id', '')}",
            f"  Date:          {info.get('created_at', '')}",
            f"  Patient:       {info.get('patient_name', '')}",
            f"  Phone:         {info.get('phone', '') or '—'}",
            f"  Payment:       {info.get('payment_method', '—')}",
            "-" * 44,
            f"  {'Service':<20} {'Qty':>4} {'Unit':>8} {'Sub':>8}",
            "-" * 44,
        ]
        for it in items:
            lines.append(
                f"  {it.get('service_name',''):<20} {it.get('quantity',1):>4} "
                f"₱{float(it.get('unit_price',0)):>7,.0f} ₱{float(it.get('subtotal',0)):>7,.0f}"
            )
        lines += [
            "-" * 44,
            f"  {'TOTAL':<28} ₱{float(info.get('total_amount', 0)):>10,.2f}",
            f"  {'PAID':<28} ₱{float(info.get('amount_paid', 0)):>10,.2f}",
            f"  {'BALANCE':<28} ₱{float(info.get('total_amount',0)) - float(info.get('amount_paid',0)):>10,.2f}",
            f"  Status: {info.get('status', '')}",
            "=" * 44,
            "            Thank you for choosing us!",
            "=" * 44,
        ]
        text = "\n".join(lines)
        QMessageBox.information(self, f"Receipt – Invoice #{invoice_id}", text)

    def _export_billing_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Invoices", "invoices.csv", "CSV (*.csv)")
        if not path:
            return
        rows = self._backend.get_invoices() if self._backend else []
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Invoice #", "Patient", "Services", "Total", "Paid", "Status"])
            for inv in rows:
                w.writerow([
                    inv.get("invoice_id", ""),
                    inv.get("patient_name", ""),
                    inv.get("service_name", ""),
                    inv.get("total_amount", ""),
                    inv.get("amount_paid", ""),
                    inv.get("status", ""),
                ])
        QMessageBox.information(self, "Exported", f"Invoices exported to:\n{path}")

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
        self._svc_table.setColumnWidth(len(cols)-1, 200)
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
            act_lay.setContentsMargins(4, 4, 4, 4); act_lay.setSpacing(4)
            edit_btn = make_table_btn("Edit")
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
