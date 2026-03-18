# Dialogs for clinical page - queue edit, service edit, invoice, payment, bulk price

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QTextEdit, QComboBox,
    QDialogButtonBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox,
    QDoubleSpinBox, QCheckBox, QFrame, QMessageBox, QWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from ui.styles import configure_table, style_dialog_btns
from ui.validators import PriceValidator, validate_required, validate_price


def _svg_icon(filename: str):
    """Load an SVG icon widget with fallback."""
    import os
    path = os.path.join(
        os.path.dirname(__file__), "..", "styles", filename)
    try:
        from PyQt6.QtSvgWidgets import QSvgWidget
        w = QSvgWidget(os.path.normpath(path))
        w.setFixedSize(28, 28)
        w.setStyleSheet("background: transparent;")
        return w
    except ImportError:
        lbl = QLabel("\U0001F4CB")
        lbl.setFixedSize(28, 28)
        lbl.setStyleSheet(
            "font-size: 20px; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl


def _gradient_header(title: str, subtitle: str,
                     icon_file: str = "icon-service.svg"):
    """Build a reusable gradient header bar."""
    bar = QFrame()
    bar.setStyleSheet(
        "QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
        " stop:0 #388087, stop:1 #6FB3B8); }")
    bar.setFixedHeight(52)
    lay = QHBoxLayout(bar)
    lay.setContentsMargins(24, 0, 24, 0)
    lay.addWidget(_svg_icon(icon_file))
    lay.addSpacing(10)
    t = QLabel(title)
    t.setStyleSheet(
        "font-size: 18px; font-weight: bold; color: #FFFFFF;"
        " background: transparent;")
    s = QLabel(subtitle)
    s.setStyleSheet(
        "font-size: 11px; color: rgba(255,255,255,0.8);"
        " background: transparent;")
    col = QVBoxLayout(); col.setSpacing(0)
    col.addWidget(t); col.addWidget(s)
    lay.addLayout(col); lay.addStretch()
    return bar


def _footer_buttons(dialog, save_text="Save",
                    on_save=None, on_cancel=None):
    """Build a reusable footer button bar that matches V3 style."""
    sep = QFrame()
    sep.setFixedHeight(1)
    sep.setStyleSheet("background: #E8F0F1;")

    bar = QWidget()
    bar.setObjectName("btnBar")
    bar.setStyleSheet("QWidget#btnBar { background: #FAFBFB; }")
    row = QHBoxLayout(bar)
    row.setContentsMargins(24, 10, 24, 10)
    row.setSpacing(14)
    row.addStretch()

    cancel = QPushButton("Cancel")
    cancel.setMinimumHeight(38); cancel.setMinimumWidth(120)
    cancel.setCursor(Qt.CursorShape.PointingHandCursor)
    cancel.setObjectName("dialogCancelBtn")
    cancel.clicked.connect(on_cancel or dialog.reject)

    save = QPushButton(save_text)
    save.setMinimumHeight(38); save.setMinimumWidth(120)
    save.setCursor(Qt.CursorShape.PointingHandCursor)
    save.setObjectName("dialogSaveBtn")
    save.clicked.connect(on_save or dialog.accept)

    row.addWidget(cancel); row.addWidget(save)
    return sep, bar


_INPUT_SS = (
    "QLineEdit, QTextEdit { padding: 8px 14px; border: 2px solid #BADFE7;"
    " border-radius: 10px; font-size: 13px; background: #FFF;"
    " color: #2C3E50; }"
    "QLineEdit:focus, QTextEdit:focus { border: 2px solid #388087; }"
)


# ══════════════════════════════════════════════════════════════════════
#  Queue Edit Dialog — V3
# ══════════════════════════════════════════════════════════════════════
class QueueEditDialog(QDialog):
    """Dialog to edit a patient queue entry."""

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Queue Entry")
        self.setMinimumWidth(580)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(_gradient_header(
            "Edit Queue Entry",
            "Update status, purpose or notes"))

        content = QWidget()
        content.setStyleSheet("background: #FFFFFF;")
        form = QFormLayout(content)
        form.setSpacing(12)
        form.setContentsMargins(28, 20, 28, 16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        d = data or {}
        self.queue_num = QLineEdit(d.get("queue", ""))
        self.queue_num.setStyleSheet(_INPUT_SS)
        self.queue_num.setMinimumHeight(40); self.queue_num.setReadOnly(True)
        self.patient_edit = QLineEdit(d.get("patient", ""))
        self.patient_edit.setStyleSheet(_INPUT_SS)
        self.patient_edit.setMinimumHeight(40); self.patient_edit.setReadOnly(True)
        self.time_edit = QLineEdit(d.get("time", ""))
        self.time_edit.setStyleSheet(_INPUT_SS)
        self.time_edit.setMinimumHeight(40); self.time_edit.setReadOnly(True)
        self.doctor_edit = QLineEdit(d.get("doctor", ""))
        self.doctor_edit.setStyleSheet(_INPUT_SS)
        self.doctor_edit.setMinimumHeight(40); self.doctor_edit.setReadOnly(True)
        self.purpose_edit = QLineEdit(d.get("purpose", ""))
        self.purpose_edit.setStyleSheet(_INPUT_SS)
        self.purpose_edit.setMinimumHeight(40)
        self.purpose_edit.setMaxLength(200)
        self.status_combo = QComboBox()
        self.status_combo.setObjectName("formCombo")
        self.status_combo.addItems(
            ["Waiting", "In Progress", "Completed", "Cancelled"])
        self.status_combo.setMinimumHeight(40)
        if d.get("status"):
            idx = self.status_combo.findText(d["status"])
            if idx >= 0: self.status_combo.setCurrentIndex(idx)
        self.notes_edit = QTextEdit()
        self.notes_edit.setStyleSheet(_INPUT_SS)
        self.notes_edit.setMaximumHeight(70)
        self.notes_edit.setPlainText(d.get("notes", ""))

        form.addRow("Queue #",  self.queue_num)
        form.addRow("Patient",  self.patient_edit)
        form.addRow("Time",     self.time_edit)
        form.addRow("Doctor",   self.doctor_edit)
        form.addRow("Purpose",  self.purpose_edit)
        form.addRow("Status",   self.status_combo)
        form.addRow("Notes",    self.notes_edit)
        outer.addWidget(content, 1)

        s, b = _footer_buttons(self)
        outer.addWidget(s); outer.addWidget(b)

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
#  Service Edit Dialog — V3 (gradient header, polished form)
# ══════════════════════════════════════════════════════════════════════
class ServiceEditDialog(QDialog):
    """Dialog to add/edit a service with category and active toggle."""

    def __init__(self, parent=None, data=None, categories=None, departments=None, selected_departments=None):
        super().__init__(parent)
        is_edit = data is not None
        self.setWindowTitle("Edit Service" if is_edit else "Add Service")
        self.setMinimumWidth(540)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(_gradient_header(
            "Edit Service" if is_edit else "Add Service",
            "Update service details" if is_edit
            else "Create a new service offering",
            "icon-service.svg"))

        content = QWidget()
        content.setStyleSheet("background: #FFFFFF;")
        form = QFormLayout(content)
        form.setSpacing(14)
        form.setContentsMargins(28, 24, 28, 16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.name_edit = QLineEdit(data.get("name", "") if data else "")
        self.name_edit.setStyleSheet(_INPUT_SS)
        self.name_edit.setMinimumHeight(40)
        self.name_edit.setMaxLength(150)
        self.name_edit.setPlaceholderText("Service name")

        # Price with peso prefix frame
        self._price_frame = QFrame()
        self._price_frame.setObjectName("priceFrame")
        self._price_frame.setStyleSheet(
            "QFrame#priceFrame { border: 2px solid #BADFE7;"
            " border-radius: 10px; background: #FFFFFF; }")
        self._price_frame.setFixedHeight(42)
        from PyQt6.QtWidgets import QSizePolicy
        self._price_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        pl = QHBoxLayout(self._price_frame)
        pl.setContentsMargins(0, 0, 0, 0); pl.setSpacing(0)
        prefix = QLabel("\u20b1")
        prefix.setStyleSheet(
            "QLabel { padding: 0 10px; border: none; font-size: 14px;"
            " font-weight: bold; background: #F0F7F8;"
            " border-top-left-radius: 8px;"
            " border-bottom-left-radius: 8px; color: #2C3E50; }")
        self.price_edit = QLineEdit(
            data.get("price", "") if data else "")
        self.price_edit.setStyleSheet(
            "QLineEdit { padding: 0 14px; border: none;"
            " font-size: 13px; background: transparent;"
            " color: #2C3E50; }")
        self.price_edit.setPlaceholderText("0.00")
        self.price_edit.setValidator(PriceValidator())
        self.price_edit.setMaxLength(12)
        pl.addWidget(prefix)
        pl.addWidget(self.price_edit, 1)

        self.cat_combo = QComboBox()
        self.cat_combo.setObjectName("formCombo")
        self.cat_combo.setEditable(True)
        self.cat_combo.setMinimumHeight(40)
        cats = categories or ["General"]
        self.cat_combo.addItems(cats)
        if data and data.get("category"):
            idx = self.cat_combo.findText(data["category"])
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
            else:
                self.cat_combo.setCurrentText(data["category"])

        self.dept_container = QFrame()
        self.dept_container.setObjectName("deptListFrame")
        self.dept_container.setStyleSheet(
            "QFrame#deptListFrame { border: 2px solid #BADFE7; border-radius: 8px; background: #FAFAFA; }"
        )
        self.dept_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        
        from PyQt6.QtWidgets import QGridLayout
        dept_layout = QGridLayout(self.dept_container)
        dept_layout.setContentsMargins(12, 12, 12, 12)
        dept_layout.setSpacing(10)

        self.departments = departments or []
        self._dept_checkboxes = []
        selected_deps = set(selected_departments or [])
        
        # Calculate columns based on width or just use a fixed 2 columns for a neat grid
        cols = 2 
        for i, dept in enumerate(self.departments):
            cb = QCheckBox(dept["department_name"])
            cb.setProperty("dept_id", dept["department_id"])
            if dept["department_id"] in selected_deps:
                cb.setChecked(True)
            cb.setStyleSheet(
                "QCheckBox { font-size: 13px; color: #2C3E50; padding: 4px; }"
                "QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #BADFE7; border-radius: 4px; }"
                "QCheckBox::indicator:checked { background: #388087; border-color: #388087; }"
            )
            self._dept_checkboxes.append(cb)
            dept_layout.addWidget(cb, i // cols, i % cols)

        self.active_check = QCheckBox("Active")
        self.active_check.setChecked(
            data.get("is_active", True) if data else True)
        self.active_check.setStyleSheet(
            "QCheckBox { font-size: 13px; spacing: 8px; }"
            " QCheckBox::indicator { width: 18px; height: 18px;"
            " border: 2px solid #BADFE7; border-radius: 4px; }"
            " QCheckBox::indicator:checked { background: #388087;"
            " border-color: #388087; }")

        form.addRow("Service Name", self.name_edit)
        form.addRow("Price",        self._price_frame)
        form.addRow("Category",     self.cat_combo)
        if self.departments:
            form.addRow("Departments",  self.dept_container)
        form.addRow("",             self.active_check)
        outer.addWidget(content, 1)

        s, b = _footer_buttons(
            self, save_text="Save",
            on_save=self._validate_and_accept)
        outer.addWidget(s); outer.addWidget(b)

    def _validate_and_accept(self):
        err = validate_required(self.name_edit.text(), "Service Name")
        if err:
            QMessageBox.warning(self, "Validation", err); return
        err = validate_price(self.price_edit.text(), "Price")
        if err:
            QMessageBox.warning(self, "Validation", err); return
        self.accept()

    def get_data(self) -> dict:
        selected_deps = []
        if hasattr(self, '_dept_checkboxes'):
            for cb in self._dept_checkboxes:
                if cb.isChecked():
                    dept_id = cb.property("dept_id")
                    if dept_id is not None:
                        selected_deps.append(dept_id)

        return {
            "name":      self.name_edit.text(),
            "price":     self.price_edit.text(),
            "category":  self.cat_combo.currentText(),
            "is_active": self.active_check.isChecked(),
            "departments": selected_deps
        }


# ══════════════════════════════════════════════════════════════════════
#  New Invoice Dialog (V3 – appointment link with doctor, line items,
#  per-item discount, remove items, running totals)
# ══════════════════════════════════════════════════════════════════════
class NewInvoiceDialog(QDialog):
    """Create an invoice with multi-item support and optional appointment link."""

    def __init__(self, parent=None, *, services=None, payment_methods=None,
                 patients=None, backend=None, role="Admin"):
        super().__init__(parent)
        self.setWindowTitle("Create Invoice")
        self.setMinimumWidth(700)

        self._services = services or []
        self._payment_methods = payment_methods or []
        self._patients = patients or []
        self._backend = backend
        self._role = role
        self._line_items: list[dict] = []
        self._patient_discount_pct = 0.0
        self._patient_discount_type = ""

        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(28, 24, 28, 24)

        # ── Title ─────────────────────────────────────────────────
        title = QLabel("Create Invoice")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #388087;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        lay.addSpacing(4)

        # ── Patient + Appointment row ─────────────────────────────
        top_form = QHBoxLayout(); top_form.setSpacing(12)

        # Patient
        pt_col = QVBoxLayout(); pt_col.setSpacing(4)
        pt_col.addWidget(QLabel("Patient"))
        self.patient_combo = QComboBox()
        self.patient_combo.setObjectName("formCombo")
        self.patient_combo.setEditable(True)
        self.patient_combo.setMinimumHeight(38)
        for p in self._patients:
            self.patient_combo.addItem(p["name"], p.get("patient_id"))
        self.patient_combo.currentTextChanged.connect(self._on_patient_changed)
        pt_col.addWidget(self.patient_combo)
        top_form.addLayout(pt_col, 1)

        # Appointment link
        appt_col = QVBoxLayout(); appt_col.setSpacing(4)
        appt_col.addWidget(QLabel("Link to Appointment"))
        self.appt_combo = QComboBox()
        self.appt_combo.setObjectName("formCombo")
        self.appt_combo.setMinimumHeight(38)
        self.appt_combo.addItem("— None —", None)
        appt_col.addWidget(self.appt_combo)
        top_form.addLayout(appt_col, 1)

        lay.addLayout(top_form)

        # ── Discount info badge ───────────────────────────────────
        self._discount_badge = QLabel("No discount applied")
        self._discount_badge.setStyleSheet(
            "font-size: 12px; color: #7F8C8D; padding: 6px 12px;"
            " background: #F0F0F0; border-radius: 4px;")
        self._discount_badge.setAlignment(Qt.AlignmentFlag.AlignLeft)
        lay.addWidget(self._discount_badge)

        # ── Line Items Section ────────────────────────────────────
        items_frame = QFrame()
        items_frame.setObjectName("card")
        items_lay = QVBoxLayout(items_frame)
        items_lay.setContentsMargins(14, 14, 14, 14)
        items_lay.setSpacing(10)

        hdr = QHBoxLayout()
        lbl = QLabel("Line Items")
        lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #2C3E50;")
        hdr.addWidget(lbl)
        hdr.addStretch()
        items_lay.addLayout(hdr)

        # Add-line row
        add_row = QHBoxLayout(); add_row.setSpacing(8)

        svc_col = QVBoxLayout(); svc_col.setSpacing(2)
        svc_col.addWidget(QLabel("Service"))
        self.svc_combo = QComboBox(); self.svc_combo.setObjectName("formCombo")
        self.svc_combo.setMinimumHeight(34)
        for svc in self._services:
            self.svc_combo.addItem(
                f"{svc['service_name']} — ₱{float(svc.get('price', 0)):,.0f}",
                svc["service_id"])
        svc_col.addWidget(self.svc_combo)
        add_row.addLayout(svc_col, 3)

        qty_col = QVBoxLayout(); qty_col.setSpacing(2)
        qty_col.addWidget(QLabel("Qty"))
        self.qty_spin = QSpinBox(); self.qty_spin.setMinimum(1); self.qty_spin.setMaximum(99)
        self.qty_spin.setValue(1); self.qty_spin.setMinimumHeight(34)
        qty_col.addWidget(self.qty_spin)
        add_row.addLayout(qty_col)

        disc_col = QVBoxLayout(); disc_col.setSpacing(2)
        disc_col.addWidget(QLabel("Discount"))
        self.disc_spin = QDoubleSpinBox(); self.disc_spin.setMinimum(0)
        self.disc_spin.setMaximum(100); self.disc_spin.setSuffix(" %")
        self.disc_spin.setMinimumHeight(34)
        # Non-admin roles: discount is locked from patient's discount type
        if self._role != "Admin":
            self.disc_spin.setReadOnly(True)
            self.disc_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
            self.disc_spin.setEnabled(False)
        disc_col.addWidget(self.disc_spin)
        add_row.addLayout(disc_col)

        btn_col = QVBoxLayout(); btn_col.setSpacing(2)
        btn_col.addWidget(QLabel(" "))  # spacer for alignment
        add_btn = QPushButton("＋ Add")
        add_btn.setMinimumHeight(34)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(
            "QPushButton { background: #388087; color: #fff; border: none;"
            " border-radius: 4px; padding: 4px 14px; font-weight:bold; }"
            " QPushButton:hover { background: #2C6A70; }")
        add_btn.clicked.connect(self._add_line)
        btn_col.addWidget(add_btn)
        add_row.addLayout(btn_col)

        items_lay.addLayout(add_row)

        # Items table (Service, Qty, Unit Price, Discount, Subtotal, Remove)
        self._items_table = QTableWidget(0, 6)
        self._items_table.setHorizontalHeaderLabels(
            ["Service", "Qty", "Unit Price", "Discount", "Subtotal", ""])
        h = self._items_table.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._items_table.setColumnWidth(5, 50)
        h.setStretchLastSection(False)
        self._items_table.verticalHeader().setVisible(False)
        self._items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._items_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._items_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._items_table.setAlternatingRowColors(True)
        self._items_table.setMinimumHeight(120)
        self._items_table.setMaximumHeight(200)
        self._items_table.verticalHeader().setDefaultSectionSize(34)
        configure_table(self._items_table)
        items_lay.addWidget(self._items_table)

        # Totals summary
        totals_row = QHBoxLayout()
        totals_row.addStretch()
        totals_col = QVBoxLayout(); totals_col.setSpacing(2)
        self._subtotal_lbl = QLabel("Subtotal: ₱0.00")
        self._subtotal_lbl.setStyleSheet("font-size: 12px; color: #7F8C8D;")
        self._subtotal_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._discount_lbl = QLabel("Discount: − ₱0.00")
        self._discount_lbl.setStyleSheet("font-size: 12px; color: #D9534F;")
        self._discount_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._total_lbl = QLabel("Total: ₱0.00")
        self._total_lbl.setStyleSheet("font-weight: bold; font-size: 15px; color: #388087;")
        self._total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        totals_col.addWidget(self._subtotal_lbl)
        totals_col.addWidget(self._discount_lbl)
        totals_col.addWidget(self._total_lbl)
        totals_row.addLayout(totals_col)
        items_lay.addLayout(totals_row)

        lay.addWidget(items_frame)

        # ── Payment + Notes row ───────────────────────────────────
        bot_form = QHBoxLayout(); bot_form.setSpacing(12)

        pm_col = QVBoxLayout(); pm_col.setSpacing(4)
        pm_col.addWidget(QLabel("Payment Method"))
        self.payment_combo = QComboBox()
        self.payment_combo.setObjectName("formCombo")
        self.payment_combo.setMinimumHeight(38)
        for pm in self._payment_methods:
            self.payment_combo.addItem(pm["method_name"], pm["method_id"])
        pm_col.addWidget(self.payment_combo)
        bot_form.addLayout(pm_col, 1)

        notes_col = QVBoxLayout(); notes_col.setSpacing(4)
        notes_col.addWidget(QLabel("Notes"))
        self.notes = QLineEdit()
        self.notes.setObjectName("formInput")
        self.notes.setMinimumHeight(38)
        self.notes.setPlaceholderText("Optional notes…")
        self.notes.setMaxLength(300)
        notes_col.addWidget(self.notes)
        bot_form.addLayout(notes_col, 2)

        lay.addLayout(bot_form)

        # ── Buttons ───────────────────────────────────────────────
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setMinimumHeight(38)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #FFFFFF; color: #2C3E50; border: 2px solid #BADFE7;"
            " border-radius: 8px; padding: 8px 24px; font-size: 13px; font-weight: bold; }"
            " QPushButton:hover { background-color: #F0F7F8; border-color: #388087; }")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Create Invoice"); save_btn.setMinimumHeight(38)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            "QPushButton { background-color: #388087; color: #FFF; border: none;"
            " border-radius: 8px; padding: 8px 24px; font-size: 13px; font-weight: bold; }"
            " QPushButton:hover { background-color: #2C6A70; }")
        save_btn.clicked.connect(self._validate_and_accept)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(save_btn)
        lay.addLayout(btn_row)

    # ── helpers ────────────────────────────────────────────────────
    def _on_patient_changed(self, text: str):
        self.appt_combo.clear()
        self.appt_combo.addItem("— None —", None)
        # Look up patient's discount type
        self._patient_discount_pct = 0.0
        self._patient_discount_type = ""
        if self._backend and text.strip():
            disc_info = self._backend.get_patient_discount_percent(text.strip())
            self._patient_discount_pct = float(disc_info.get("discount_percent", 0))
            self._patient_discount_type = disc_info.get("discount_type", "")
        # Update discount badge
        if self._patient_discount_pct > 0 and self._patient_discount_type:
            self._discount_badge.setText(
                f"🏷  {self._patient_discount_type} — {self._patient_discount_pct:.0f}% discount applied automatically")
            self._discount_badge.setStyleSheet(
                "font-size: 12px; color: #388087; padding: 6px 12px;"
                " background: #E0F2F1; border-radius: 4px; font-weight: bold;")
        else:
            self._discount_badge.setText("No discount applied")
            self._discount_badge.setStyleSheet(
                "font-size: 12px; color: #7F8C8D; padding: 6px 12px;"
                " background: #F0F0F0; border-radius: 4px;")
        # Set the discount spin to the patient's discount (locked for non-admin)
        if self._role != "Admin":
            self.disc_spin.setValue(self._patient_discount_pct)
        else:
            self.disc_spin.setValue(self._patient_discount_pct)
        # Re-apply discount to existing line items when patient changes
        self._recalculate_all_items()
        # Load appointments
        if self._backend and text.strip():
            appts = self._backend.get_today_completed_appointments_for_patient(text.strip())
            for a in appts:
                t = a.get("appointment_time", "")
                if hasattr(t, "total_seconds"):
                    total = int(t.total_seconds())
                    h, m = divmod(total // 60, 60)
                    t = f"{h:02d}:{m:02d}"
                doc = a.get("doctor_name", "")
                doc_part = f" – Dr. {doc.split()[-1]}" if doc else ""
                self.appt_combo.addItem(
                    f"#{a['appointment_id']} – {a['service_name']}{doc_part} @ {t}",
                    a["appointment_id"],
                )

    def _add_line(self):
        sid = self.svc_combo.currentData()
        svc_text = self.svc_combo.currentText()
        qty = self.qty_spin.value()
        # For non-admin, always use the patient's discount (locked)
        if self._role != "Admin":
            disc = self._patient_discount_pct
        else:
            disc = self.disc_spin.value()
        price = 0
        for s in self._services:
            if s["service_id"] == sid:
                price = float(s.get("price", 0))
                break
        raw = price * qty
        sub = raw * (1 - disc / 100)
        self._line_items.append({
            "service_id": sid, "quantity": qty, "discount": disc,
            "unit_price": price, "raw": raw, "subtotal": sub,
        })
        r = self._items_table.rowCount()
        self._items_table.insertRow(r)
        name_only = svc_text.split(" — ₱")[0] if " — ₱" in svc_text else svc_text
        self._items_table.setItem(r, 0, QTableWidgetItem(name_only))
        self._items_table.setItem(r, 1, QTableWidgetItem(str(qty)))
        self._items_table.setItem(r, 2, QTableWidgetItem(f"₱{price:,.2f}"))
        disc_item = QTableWidgetItem(f"{disc:.0f}%")
        if disc > 0:
            disc_item.setForeground(QColor("#D9534F"))
        self._items_table.setItem(r, 3, disc_item)
        self._items_table.setItem(r, 4, QTableWidgetItem(f"₱{sub:,.2f}"))
        # Remove button
        rm_btn = QPushButton("✕")
        rm_btn.setFixedSize(30, 28)
        rm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rm_btn.setStyleSheet(
            "QPushButton { background: #D9534F; color: #fff; border: none;"
            " border-radius: 4px; font-weight: bold; font-size: 13px; }"
            " QPushButton:hover { background: #C9302C; }")
        rm_btn.clicked.connect(lambda checked, row=r: self._remove_line(row))
        self._items_table.setCellWidget(r, 5, rm_btn)
        self._update_totals()
        # Reset qty only; discount stays locked for non-admin
        self.qty_spin.setValue(1)
        if self._role == "Admin":
            self.disc_spin.setValue(self._patient_discount_pct)

    def _remove_line(self, row):
        if row < len(self._line_items):
            self._line_items.pop(row)
        self._items_table.removeRow(row)
        # Rebind remove buttons with updated row indices
        for r in range(self._items_table.rowCount()):
            rm_btn = QPushButton("✕")
            rm_btn.setFixedSize(30, 28)
            rm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            rm_btn.setStyleSheet(
                "QPushButton { background: #D9534F; color: #fff; border: none;"
                " border-radius: 4px; font-weight: bold; font-size: 13px; }"
                " QPushButton:hover { background: #C9302C; }")
            rm_btn.clicked.connect(lambda checked, ri=r: self._remove_line(ri))
            self._items_table.setCellWidget(r, 5, rm_btn)
        self._update_totals()

    def _recalculate_all_items(self):
        """Re-apply current patient discount to all existing line items."""
        disc = self._patient_discount_pct if self._role != "Admin" else self.disc_spin.value()
        for i, it in enumerate(self._line_items):
            it["discount"] = disc
            it["subtotal"] = it["raw"] * (1 - disc / 100)
            # Update table display
            disc_item = QTableWidgetItem(f"{disc:.0f}%")
            if disc > 0:
                disc_item.setForeground(QColor("#D9534F"))
            self._items_table.setItem(i, 3, disc_item)
            self._items_table.setItem(i, 4, QTableWidgetItem(f"₱{it['subtotal']:,.2f}"))
        self._update_totals()

    def _update_totals(self):
        raw_total = sum(it.get("raw", 0) for it in self._line_items)
        disc_total = sum(it.get("raw", 0) - it.get("subtotal", 0) for it in self._line_items)
        grand_total = raw_total - disc_total
        self._subtotal_lbl.setText(f"Subtotal: ₱{raw_total:,.2f}")
        self._discount_lbl.setText(f"Discount: − ₱{disc_total:,.2f}")
        self._total_lbl.setText(f"Total: ₱{grand_total:,.2f}")

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
            "items":          [{"service_id": it["service_id"], "quantity": it["quantity"],
                                "discount": it["discount"]} for it in self._line_items],
            "method_id":      self.payment_combo.currentData(),
            "notes":          self.notes.text(),
            "appointment_id": self.appt_combo.currentData(),
        }


# ══════════════════════════════════════════════════════════════════════
#  Payment Dialog (V2 – amount tendered, change calculation)
# ══════════════════════════════════════════════════════════════════════
class PaymentDialog(QDialog):
    def __init__(self, parent=None, *, invoice_id=0, balance=0.0, payment_methods=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add Payment – Invoice #{invoice_id}")
        self.setMinimumWidth(440)
        self._balance = balance

        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(28, 24, 28, 24)

        title = QLabel(f"Payment for Invoice #{invoice_id}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #388087;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        # Balance due
        bal_lbl = QLabel(f"Balance Due: ₱{balance:,.2f}")
        bal_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #D9534F;")
        bal_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(bal_lbl)
        lay.addSpacing(6)

        form = QFormLayout(); form.setSpacing(12)

        # Amount tendered (what the customer hands over)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMinimum(0.01)
        self.amount_spin.setMaximum(999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setPrefix("₱ ")
        self.amount_spin.setValue(balance)
        self.amount_spin.setMinimumHeight(38)
        self.amount_spin.valueChanged.connect(self._update_change)

        self.method_combo = QComboBox(); self.method_combo.setObjectName("formCombo")
        self.method_combo.setMinimumHeight(38)
        for pm in (payment_methods or []):
            self.method_combo.addItem(pm["method_name"], pm["method_id"])

        form.addRow("Amount Tendered", self.amount_spin)
        form.addRow("Payment Method", self.method_combo)
        lay.addLayout(form)

        # Change display
        self._change_lbl = QLabel("Change: ₱0.00")
        self._change_lbl.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #5CB85C;"
            " padding: 8px; background: #E8F5E9; border-radius: 6px;")
        self._change_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._change_lbl)

        # Effective amount applied
        self._applied_lbl = QLabel(f"Applied to invoice: ₱{balance:,.2f}")
        self._applied_lbl.setStyleSheet("font-size: 12px; color: #7F8C8D;")
        self._applied_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self._applied_lbl)

        # Buttons
        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel"); cancel_btn.setMinimumHeight(38)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: #FFFFFF; color: #2C3E50; border: 2px solid #BADFE7;"
            " border-radius: 8px; padding: 8px 24px; font-size: 13px; font-weight: bold; }"
            " QPushButton:hover { background-color: #F0F7F8; border-color: #388087; }")
        cancel_btn.clicked.connect(self.reject)
        pay_btn = QPushButton("Confirm Payment"); pay_btn.setMinimumHeight(38)
        pay_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pay_btn.setStyleSheet(
            "QPushButton { background-color: #388087; color: #FFF; border: none;"
            " border-radius: 8px; padding: 8px 24px; font-size: 13px; font-weight: bold; }"
            " QPushButton:hover { background-color: #2C6A70; }")
        pay_btn.clicked.connect(self._on_confirm)
        btn_row.addWidget(cancel_btn); btn_row.addWidget(pay_btn)
        lay.addLayout(btn_row)

        self._update_change()

    def _update_change(self):
        tendered = self.amount_spin.value()
        change = max(0, tendered - self._balance)
        applied = min(tendered, self._balance)
        self._change_lbl.setText(f"Change: ₱{change:,.2f}")
        self._applied_lbl.setText(f"Applied to invoice: ₱{applied:,.2f}")
        if change > 0:
            self._change_lbl.setStyleSheet(
                "font-size: 15px; font-weight: bold; color: #388087;"
                " padding: 8px; background: #E0F2F1; border-radius: 6px;")
        else:
            self._change_lbl.setStyleSheet(
                "font-size: 15px; font-weight: bold; color: #5CB85C;"
                " padding: 8px; background: #E8F5E9; border-radius: 6px;")

    def _on_confirm(self):
        if self.amount_spin.value() <= 0:
            QMessageBox.warning(self, "Validation", "Enter an amount greater than zero.")
            return
        self.accept()

    def get_data(self):
        tendered = self.amount_spin.value()
        applied = min(tendered, self._balance)
        change = max(0, tendered - self._balance)
        return {
            "amount": applied,
            "tendered": tendered,
            "change": change,
            "method_id": self.method_combo.currentData(),
        }


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
        self._table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._table.setAlternatingRowColors(True)
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
