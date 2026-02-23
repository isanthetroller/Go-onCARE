"""Clinical Workflow & Point-of-Sale page."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QScrollArea,
    QComboBox, QTabWidget, QTextEdit, QSpinBox, QDoubleSpinBox,
    QGraphicsDropShadowEffect, QDialog, QFormLayout, QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from ui.styles import configure_table, make_table_btn


# ── Sample data ────────────────────────────────────────────────────────
_QUEUE = [
    ("Q-001", "Maria Santos",    "09:00 AM", "Dr. Reyes", "General Checkup",  "Waiting"),
    ("Q-002", "Juan Dela Cruz",  "09:30 AM", "Dr. Tan",   "Follow-up Visit",       "In Progress"),
    ("Q-003", "Ana Reyes",       "10:00 AM", "Dr. Reyes", "Lab Results Review",    "Waiting"),
    ("Q-004", "Carlos Garcia",   "10:30 AM", "Dr. Lim",   "Dental Cleaning",  "Waiting"),
]

_BILLING = [
    ("INV-2001", "Maria Santos",   "General Checkup",  "₱ 800.00",  "₱ 800.00",  "Paid"),
    ("INV-2002", "Juan Dela Cruz", "Follow-up Visit",  "₱ 500.00",  "₱ 0.00",    "Unpaid"),
    ("INV-2003", "Ana Reyes",      "Lab Tests (CBC)",  "₱ 1,200.00","₱ 1,200.00","Paid"),
    ("INV-2004", "Carlos Garcia",  "Dental Cleaning",  "₱ 2,500.00","₱ 1,000.00","Partial"),
]

_SERVICES = [
    ("General Checkup",             "₱ 800.00"),
    ("Follow-up Visit",             "₱ 500.00"),
    ("Lab Tests – CBC",             "₱ 1,200.00"),
    ("Lab Tests – Urinalysis",      "₱ 600.00"),
    ("Dental Cleaning",             "₱ 2,500.00"),
    ("X-Ray",                       "₱ 1,500.00"),
    ("ECG",                         "₱ 1,000.00"),
    ("Physical Therapy Session",    "₱ 1,800.00"),
]


class QueueEditDialog(QDialog):
    """Dialog to edit a patient queue entry."""
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Queue Entry")
        self.setMinimumWidth(480)
        self.setStyleSheet(
            "QDialog { background: #FFFFFF; }"
            " QLabel { color: #2C3E50; font-size: 13px; }"
        )
        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.queue_num = QLineEdit(data.get("queue", "") if data else "")
        self.queue_num.setObjectName("formInput"); self.queue_num.setMinimumHeight(38)
        self.patient_edit = QLineEdit(data.get("patient", "") if data else "")
        self.patient_edit.setObjectName("formInput"); self.patient_edit.setMinimumHeight(38)
        self.time_edit = QLineEdit(data.get("time", "") if data else "")
        self.time_edit.setObjectName("formInput"); self.time_edit.setMinimumHeight(38)
        self.doctor_combo = QComboBox()
        self.doctor_combo.setObjectName("formCombo")
        self.doctor_combo.addItems(["Dr. Reyes", "Dr. Tan", "Dr. Lim", "Dr. Santos"])
        self.doctor_combo.setMinimumHeight(38)
        if data and data.get("doctor"):
            idx = self.doctor_combo.findText(data["doctor"])
            if idx >= 0:
                self.doctor_combo.setCurrentIndex(idx)
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

        form.addRow("Queue #", self.queue_num)
        form.addRow("Patient", self.patient_edit)
        form.addRow("Time", self.time_edit)
        form.addRow("Doctor", self.doctor_combo)
        form.addRow("Purpose", self.purpose_edit)
        form.addRow("Status", self.status_combo)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def get_data(self) -> dict:
        """Return the current form values as a dict."""
        return {
            "queue":   self.queue_num.text(),
            "patient": self.patient_edit.text(),
            "time":    self.time_edit.text(),
            "doctor":  self.doctor_combo.currentText(),
            "purpose": self.purpose_edit.text(),
            "status":  self.status_combo.currentText(),
        }


class ServiceEditDialog(QDialog):
    """Dialog to edit a service entry."""
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Service")
        self.setMinimumWidth(420)
        self.setStyleSheet(
            "QDialog { background: #FFFFFF; }"
            " QLabel { color: #2C3E50; font-size: 13px; }"
        )
        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.name_edit = QLineEdit(data.get("name", "") if data else "")
        self.name_edit.setObjectName("formInput"); self.name_edit.setMinimumHeight(38)
        self.price_edit = QLineEdit(data.get("price", "") if data else "")
        self.price_edit.setObjectName("formInput"); self.price_edit.setMinimumHeight(38)

        form.addRow("Service Name", self.name_edit)
        form.addRow("Price", self.price_edit)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def get_data(self) -> dict:
        """Return the current form values as a dict."""
        return {
            "name":  self.name_edit.text(),
            "price": self.price_edit.text(),
        }


class NewInvoiceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Invoice")
        self.setMinimumWidth(500)
        self.setStyleSheet("QDialog { background: #FFFFFF; } QLabel { color: #2C3E50; font-size: 13px; }")

        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(28, 28, 28, 28)

        self.patient_edit = QLineEdit()
        self.patient_edit.setObjectName("formInput")
        self.patient_edit.setPlaceholderText("Patient name")
        self.patient_edit.setMinimumHeight(38)

        self.service_combo = QComboBox()
        self.service_combo.setObjectName("formCombo")
        self.service_combo.addItems([s[0] for s in _SERVICES])
        self.service_combo.setMinimumHeight(38)

        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(99)
        self.qty_spin.setValue(1)
        self.qty_spin.setMinimumHeight(38)

        self.discount = QDoubleSpinBox()
        self.discount.setMinimum(0)
        self.discount.setMaximum(100)
        self.discount.setSuffix(" %")
        self.discount.setMinimumHeight(38)

        self.payment_combo = QComboBox()
        self.payment_combo.setObjectName("formCombo")
        self.payment_combo.addItems(["Cash", "Credit Card", "GCash", "Maya", "Insurance"])
        self.payment_combo.setMinimumHeight(38)

        self.notes = QTextEdit()
        self.notes.setObjectName("formInput")
        self.notes.setMaximumHeight(70)

        form.addRow("Patient",        self.patient_edit)
        form.addRow("Service",        self.service_combo)
        form.addRow("Quantity",       self.qty_spin)
        form.addRow("Discount",       self.discount)
        form.addRow("Payment Method", self.payment_combo)
        form.addRow("Notes",          self.notes)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)


class ClinicalPage(QWidget):
    def __init__(self, role: str = "Admin"):
        super().__init__()
        self._role = role
        self._build()

    def _build(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #F6F6F2; }")
        inner = QWidget()
        inner.setObjectName("pageInner")
        inner.setStyleSheet("QWidget#pageInner { background-color: #F6F6F2; }")
        lay = QVBoxLayout(inner)
        lay.setSpacing(20)
        lay.setContentsMargins(28, 28, 28, 28)

        # ── Header Banner ──────────────────────────────────────────
        banner = QFrame()
        banner.setObjectName("pageBanner")
        banner.setMinimumHeight(100)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 15))
        banner.setGraphicsEffect(shadow)
        banner.setStyleSheet(
            "QFrame#pageBanner { background: qlineargradient("
            "x1:0, y1:0, x2:1, y2:0,"
            "stop:0 #388087, stop:1 #6FB3B8);"
            "border-radius: 12px; }"
        )
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(32, 20, 32, 20)
        banner_lay.setSpacing(0)
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("Clinical Workflow & Billing")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #FFFFFF; background: transparent;")
        sub = QLabel("Patient queue, consultations, and point-of-sale")
        sub.setStyleSheet("font-size: 13px; color: rgba(255,255,255,0.8); background: transparent;")
        title_col.addWidget(title)
        title_col.addWidget(sub)
        banner_lay.addLayout(title_col)
        lay.addWidget(banner)

        # ── Tabs ───────────────────────────────────────────────────────
        tabs = QTabWidget()
        if self._role in ("Admin", "Doctor", "Nurse"):
            tabs.addTab(self._build_queue_tab(),    "Patient Queue")
        if self._role in ("Admin", "Receptionist"):
            tabs.addTab(self._build_billing_tab(),  "Billing / POS")
        if self._role == "Admin":
            tabs.addTab(self._build_services_tab(), "Services & Pricing")
        lay.addWidget(tabs)

        lay.addStretch()
        scroll.setWidget(inner)
        wrapper = QVBoxLayout(self)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.addWidget(scroll)

    # ── Queue tab ──────────────────────────────────────────────────────
    def _build_queue_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(16)
        lay.setContentsMargins(16, 16, 16, 16)

        # Status cards row
        status_row = QHBoxLayout()
        for label, val, color in [
            ("Waiting", "3", "#E8B931"),
            ("In Progress", "1", "#388087"),
            ("Completed Today", "8", "#5CB85C"),
        ]:
            card = QFrame(); card.setObjectName("card")
            cl = QVBoxLayout(card); cl.setContentsMargins(16, 14, 16, 14); cl.setSpacing(4)
            strip = QFrame(); strip.setFixedHeight(3)
            strip.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
            v = QLabel(val); v.setObjectName("statValue"); v.setStyleSheet("font-size: 22px;")
            l = QLabel(label); l.setObjectName("statLabel")
            cl.addWidget(strip); cl.addWidget(v); cl.addWidget(l)
            status_row.addWidget(card)
        lay.addLayout(status_row)

        cols = ["Queue #", "Patient", "Time", "Doctor", "Purpose", "Status", "Actions"]
        table = QTableWidget(len(_QUEUE), len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(len(cols)-1, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(len(cols)-1, 120)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(260)
        table.verticalHeader().setDefaultSectionSize(48)
        configure_table(table)

        for r, row in enumerate(_QUEUE):
            for c, val in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(val))
            view_btn = make_table_btn("Edit")
            view_btn.clicked.connect(lambda checked, tbl=table, ri=r: self._on_edit_queue(tbl, ri))
            table.setCellWidget(r, len(row), view_btn)
        lay.addWidget(table)
        return page

    # ── Billing tab ────────────────────────────────────────────────────
    def _build_billing_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(16)
        lay.setContentsMargins(16, 16, 16, 16)

        bar = QHBoxLayout()
        search = QLineEdit()
        search.setObjectName("searchBar")
        search.setPlaceholderText("🔍  Search invoices…")
        search.setMinimumHeight(42)
        bar.addWidget(search)

        new_btn = QPushButton("＋  New Invoice")
        new_btn.setObjectName("actionBtn")
        new_btn.setMinimumHeight(42)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(lambda: NewInvoiceDialog(self).exec())
        bar.addWidget(new_btn)
        lay.addLayout(bar)

        cols = ["Invoice #", "Patient", "Service", "Total", "Paid", "Status"]
        table = QTableWidget(len(_BILLING), len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(260)
        configure_table(table)

        for r, row in enumerate(_BILLING):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                if c == 5:  # status column colour
                    if val == "Paid":
                        item.setForeground(QColor("#5CB85C"))
                    elif val == "Unpaid":
                        item.setForeground(QColor("#D9534F"))
                    else:
                        item.setForeground(QColor("#E8B931"))
                table.setItem(r, c, item)
        lay.addWidget(table)
        return page

    # ── Services tab ───────────────────────────────────────────────────
    def _build_services_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setSpacing(16)
        lay.setContentsMargins(16, 16, 16, 16)

        bar = QHBoxLayout()
        search = QLineEdit()
        search.setObjectName("searchBar")
        search.setPlaceholderText("🔍  Search services…")
        search.setMinimumHeight(42)
        bar.addWidget(search)
        add_btn = QPushButton("＋  Add Service")
        add_btn.setObjectName("actionBtn")
        add_btn.setMinimumHeight(42)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bar.addWidget(add_btn)
        lay.addLayout(bar)

        cols = ["Service Name", "Price", "Actions"]
        table = QTableWidget(len(_SERVICES), len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(2, 120)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(360)
        table.verticalHeader().setDefaultSectionSize(48)
        configure_table(table)

        for r, (name, price) in enumerate(_SERVICES):
            table.setItem(r, 0, QTableWidgetItem(name))
            table.setItem(r, 1, QTableWidgetItem(price))
            view_btn = make_table_btn("Edit")
            view_btn.clicked.connect(lambda checked, tbl=table, ri=r: self._on_edit_service(tbl, ri))
            table.setCellWidget(r, 2, view_btn)
        lay.addWidget(table)
        return page

    # ── Edit handlers ──────────────────────────────────────────────────
    def _on_edit_queue(self, table, row):
        from PyQt6.QtWidgets import QMessageBox
        data = {
            "queue": table.item(row, 0).text() if table.item(row, 0) else "",
            "patient": table.item(row, 1).text() if table.item(row, 1) else "",
            "time": table.item(row, 2).text() if table.item(row, 2) else "",
            "doctor": table.item(row, 3).text() if table.item(row, 3) else "",
            "purpose": table.item(row, 4).text() if table.item(row, 4) else "",
            "status": table.item(row, 5).text() if table.item(row, 5) else "",
        }
        dlg = QueueEditDialog(self, data=data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            values = [d["queue"], d["patient"], d["time"], d["doctor"], d["purpose"], d["status"]]
            for c, val in enumerate(values):
                table.setItem(row, c, QTableWidgetItem(val))
            QMessageBox.information(self, "Success", f"Queue entry '{d['queue']}' updated successfully.")

    def _on_edit_service(self, table, row):
        from PyQt6.QtWidgets import QMessageBox
        data = {
            "name": table.item(row, 0).text() if table.item(row, 0) else "",
            "price": table.item(row, 1).text() if table.item(row, 1) else "",
        }
        dlg = ServiceEditDialog(self, data=data)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Service name is required.")
                return
            table.setItem(row, 0, QTableWidgetItem(d["name"]))
            table.setItem(row, 1, QTableWidgetItem(d["price"]))
            QMessageBox.information(self, "Success", f"Service '{d['name']}' updated successfully.")
