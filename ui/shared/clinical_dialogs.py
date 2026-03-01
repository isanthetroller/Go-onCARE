"""Clinical workflow dialogs – Queue, Service, Invoice, Payment, Bulk Price.

Extracted from the monolithic clinical.py for better organisation.
These dialogs are used by ClinicalPage across all roles.
"""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
    QDoubleSpinBox, QCheckBox, QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from ui.styles import configure_table, style_dialog_btns


# ══════════════════════════════════════════════════════════════════════
#  Queue Edit Dialog
# ══════════════════════════════════════════════════════════════════════
class QueueEditDialog(QDialog):
    """Dialog to edit a patient queue entry (status, purpose, notes)."""

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Queue Entry")
        self.setMinimumWidth(560)
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
        self.setMinimumWidth(520)
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
        self.setMinimumWidth(640)

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
