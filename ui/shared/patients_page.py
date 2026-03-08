# Patients page - table with CRUD, filters, merge

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDialog, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from ui.styles import (
    make_page_layout, finish_page, make_banner, make_read_only_table,
    make_action_table, make_table_btn, make_table_btn_danger, status_color,
    make_action_cell,
)
from ui.shared.patient_dialogs import PatientDialog, PatientProfileDialog, MergeDialog


# ══════════════════════════════════════════════════════════════════════
#  Patients Page
# ══════════════════════════════════════════════════════════════════════
class PatientsPage(QWidget):
    patients_changed = pyqtSignal(list)

    def __init__(self, backend=None, role: str = "Admin", user_email: str = ""):
        super().__init__()
        self._backend = backend
        self._role = role
        self._user_email = user_email
        self._patient_ids: list[int] = []
        self._all_patients: list[dict] = []
        self._build()
        # Auto-refresh data every 10 seconds
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._load_from_db)
        self._refresh_timer.start(10_000)

    def get_patient_names(self) -> list[str]:
        names = []
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 1)
            if item and item.text().strip():
                names.append(item.text().strip())
        return names

    def _build(self):
        scroll, lay = make_page_layout()

        # ── Banner ─────────────────────────────────────────────────
        btn_text = "\uff0b  Add Patient" if self._role not in ("Cashier", "Doctor") else ""
        lay.addWidget(make_banner(
            "Patient Records", "Manage and view all patient information",
            btn_text=btn_text, btn_slot=self._on_add,
        ))

        # ── Toolbar ────────────────────────────────────────────────
        bar = QHBoxLayout(); bar.setSpacing(10)
        self.search = QLineEdit(); self.search.setObjectName("searchBar")
        self.search.setPlaceholderText("🔍  Search patients by name, ID, or condition…")
        self.search.setMinimumHeight(42); self.search.textChanged.connect(self._apply_filters)
        bar.addWidget(self.search)

        self.filter_combo = QComboBox(); self.filter_combo.setObjectName("formCombo")
        self.filter_combo.addItems(["All Status", "Active", "Inactive"])
        self.filter_combo.setMinimumHeight(42); self.filter_combo.setMinimumWidth(140)
        self.filter_combo.currentTextChanged.connect(self._apply_filters)
        bar.addWidget(self.filter_combo)

        self.sex_filter = QComboBox(); self.sex_filter.setObjectName("formCombo")
        self.sex_filter.addItems(["All Sex", "Male", "Female"])
        self.sex_filter.setMinimumHeight(42); self.sex_filter.setMinimumWidth(120)
        self.sex_filter.currentTextChanged.connect(self._apply_filters)
        bar.addWidget(self.sex_filter)

        self.blood_filter = QComboBox(); self.blood_filter.setObjectName("formCombo")
        self.blood_filter.addItems(["All Blood Type", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"])
        self.blood_filter.setMinimumHeight(42); self.blood_filter.setMinimumWidth(140)
        self.blood_filter.currentTextChanged.connect(self._apply_filters)
        bar.addWidget(self.blood_filter)

        self.cond_filter = QComboBox(); self.cond_filter.setObjectName("formCombo")
        self.cond_filter.addItems(["All Conditions"])
        self.cond_filter.setMinimumHeight(42); self.cond_filter.setMinimumWidth(160)
        self.cond_filter.currentTextChanged.connect(self._apply_filters)
        bar.addWidget(self.cond_filter)

        # Merge button (Admin / Receptionist only)
        if self._role in ("Admin", "Receptionist"):
            merge_btn = QPushButton("🔗  Merge")
            merge_btn.setObjectName("actionBtn"); merge_btn.setMinimumHeight(42)
            merge_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            merge_btn.setToolTip("Merge duplicate patient records")
            merge_btn.clicked.connect(self._on_merge)
            bar.addWidget(merge_btn)

        lay.addLayout(bar)

        # ── Table ──────────────────────────────────────────────────
        cols = ["ID", "Name", "Sex", "Age", "Phone", "Blood Type",
                "Conditions", "Last Visit", "Status", "Actions"]
        if self._role == "Cashier":
            cols = cols[:-1]  # no actions
            self.table = make_read_only_table(cols)
        else:
            self.table = make_action_table(cols, action_col_width=210)
        self.table.setSortingEnabled(True)
        self._load_from_db()
        lay.addWidget(self.table)

        lay.addStretch()
        finish_page(self, scroll)

    # ── DB Load ────────────────────────────────────────────────────
    def _load_from_db(self):
        if not self.isVisible():
            return
        self.table.setSortingEnabled(False)
        if self._backend and self._role == "Doctor" and self._user_email:
            rows = self._backend.get_patients_for_doctor(self._user_email)
        else:
            rows = self._backend.get_patients() if self._backend else []
        self._all_patients = rows
        self._patient_ids.clear()
        self.table.setRowCount(len(rows))

        # Collect unique conditions for filter
        all_conds = set()
        for p in rows:
            conds = p.get("conditions", "") or ""
            for c in conds.split(","):
                c = c.strip()
                if c:
                    all_conds.add(c)

        prev_cond = self.cond_filter.currentText()
        self.cond_filter.blockSignals(True)
        self.cond_filter.clear()
        self.cond_filter.addItem("All Conditions")
        for c in sorted(all_conds):
            self.cond_filter.addItem(c)
        idx = self.cond_filter.findText(prev_cond)
        if idx >= 0:
            self.cond_filter.setCurrentIndex(idx)
        self.cond_filter.blockSignals(False)
        for r, p in enumerate(rows):
            self._patient_ids.append(p["patient_id"])
            pid_str = f"PT-{p['patient_id']:04d}"
            name = f"{p['first_name']} {p['last_name']}"
            dob = p.get("date_of_birth")
            age = ""
            if dob:
                if isinstance(dob, date):
                    today = date.today()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                else:
                    age = ""
            last_visit = p.get("last_visit", "")
            if last_visit and hasattr(last_visit, "strftime"):
                last_visit = last_visit.strftime("%Y-%m-%d")
            values = [pid_str, name, p.get("sex",""), str(age),
                      p.get("phone","") or "", p.get("blood_type","") or "Unknown",
                      p.get("conditions","") or "",
                      str(last_visit) if last_visit else "—",
                      p.get("status","")]
            for c, val in enumerate(values):
                self.table.setItem(r, c, QTableWidgetItem(val))

            if self._role != "Cashier":
                view_btn = make_table_btn("View")
                view_btn.clicked.connect(lambda checked, ri=r: self._on_view(ri))
                if self._role == "Doctor":
                    self.table.setCellWidget(r, len(values), make_action_cell(view_btn))
                else:
                    edit_btn = make_table_btn("Edit")
                    edit_btn.clicked.connect(lambda checked, ri=r: self._on_edit(ri))
                    del_btn = make_table_btn_danger("Del")
                    del_btn.clicked.connect(lambda checked, ri=r: self._on_delete(ri))
                    self.table.setCellWidget(r, len(values), make_action_cell(view_btn, edit_btn, del_btn))
        self.table.setSortingEnabled(True)

    # ── Filters ────────────────────────────────────────────────────
    def _apply_filters(self, _=None):
        text = self.search.text().lower()
        status = self.filter_combo.currentText()
        sex = self.sex_filter.currentText()
        blood = self.blood_filter.currentText()
        cond = self.cond_filter.currentText()
        sex_col = 2
        blood_col = 5
        cond_col = 6
        status_col = 8
        for r in range(self.table.rowCount()):
            row_text = " ".join(
                self.table.item(r,c).text().lower() if self.table.item(r,c) else ""
                for c in range(self.table.columnCount()-1))
            ok_text = not text or text in row_text
            item_status = self.table.item(r, status_col)
            ok_status = status == "All Status" or (item_status and item_status.text() == status)
            item_sex = self.table.item(r, sex_col)
            ok_sex = sex == "All Sex" or (item_sex and item_sex.text() == sex)
            item_blood = self.table.item(r, blood_col)
            ok_blood = blood == "All Blood Type" or (item_blood and item_blood.text() == blood)
            item_cond = self.table.item(r, cond_col)
            ok_cond = cond == "All Conditions" or (item_cond and cond.lower() in item_cond.text().lower())
            self.table.setRowHidden(r, not (ok_text and ok_status and ok_sex and ok_blood and ok_cond))

    # ── CRUD ───────────────────────────────────────────────────────
    def _on_add(self):
        dlg = PatientDialog(self, title="Add New Patient", backend=self._backend)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Patient name is required."); return
            parts = d["name"].strip().rsplit(" ", 1)
            db_data = {
                "first_name": parts[0], "last_name": parts[1] if len(parts)>1 else "",
                "sex": d["sex"], "dob": dlg.dob_edit.date().toString("yyyy-MM-dd"),
                "phone": d["phone"], "email": d["email"],
                "emergency_contact": d["emergency_contact"],
                "blood_type": d["blood_type"],
                "discount_type_id": d.get("discount_type_id"),
                "conditions": d["conditions"], "status": d["status"],
                "notes": d["notes"],
            }
            if self._backend and self._backend.add_patient(db_data):
                QMessageBox.information(self, "Success", f"Patient '{d['name']}' added.")
                self._load_from_db(); self.patients_changed.emit(self.get_patient_names())
            else:
                QMessageBox.critical(self, "Error", "Failed to add patient.")

    def _on_edit(self, row: int):
        p = self._all_patients[row] if row < len(self._all_patients) else {}
        data = {
            "name": f"{p.get('first_name','')} {p.get('last_name','')}",
            "sex": p.get("sex",""), "phone": p.get("phone","") or "",
            "email": p.get("email","") or "",
            "emergency_contact": p.get("emergency_contact","") or "",
            "blood_type": p.get("blood_type","") or "Unknown",
            "discount_type_id": p.get("discount_type_id"),
            "conditions": p.get("conditions","") or "",
            "status": p.get("status",""),
            "notes": p.get("notes","") or "",
        }
        dlg = PatientDialog(self, title="Edit Patient", data=data, backend=self._backend)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            d = dlg.get_data()
            if not d["name"].strip():
                QMessageBox.warning(self, "Validation", "Patient name is required."); return
            parts = d["name"].strip().rsplit(" ", 1)
            patient_id = self._patient_ids[row] if row < len(self._patient_ids) else None
            db_data = {
                "first_name": parts[0], "last_name": parts[1] if len(parts)>1 else "",
                "sex": d["sex"], "dob": dlg.dob_edit.date().toString("yyyy-MM-dd"),
                "phone": d["phone"], "email": d["email"],
                "emergency_contact": d["emergency_contact"],
                "blood_type": d["blood_type"],
                "discount_type_id": d.get("discount_type_id"),
                "conditions": d["conditions"], "status": d["status"],
                "notes": d["notes"],
            }
            if patient_id and self._backend and self._backend.update_patient(patient_id, db_data):
                QMessageBox.information(self, "Success", f"Patient '{d['name']}' updated.")
                self._load_from_db(); self.patients_changed.emit(self.get_patient_names())
            else:
                QMessageBox.critical(self, "Error", "Failed to update patient.")

    def _on_delete(self, row: int):
        name = self.table.item(row,1).text() if self.table.item(row,1) else "patient"
        reply = QMessageBox.question(self, "Confirm Delete",
            f"Delete {name}? All linked appointments, invoices, and conditions will be removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            pid = self._patient_ids[row] if row < len(self._patient_ids) else None
            if pid and self._backend and self._backend.delete_patient(pid):
                QMessageBox.information(self, "Deleted", f"Patient '{name}' deleted.")
                self._load_from_db(); self.patients_changed.emit(self.get_patient_names())
            else:
                QMessageBox.critical(self, "Error", "Failed to delete patient.")

    def _on_view(self, row: int):
        pid = self._patient_ids[row] if row < len(self._patient_ids) else None
        if not pid or not self._backend: return
        profile = self._backend.get_patient_full_profile(pid)
        if not profile:
            QMessageBox.warning(self, "Error", "Could not load patient profile."); return
        dlg = PatientProfileDialog(self, profile=profile)
        dlg.exec()

    def _on_merge(self):
        patients = self._backend.get_patients() if self._backend else []
        if len(patients) < 2:
            QMessageBox.information(self, "Merge", "Need at least 2 patients to merge."); return
        dlg = MergeDialog(self, patients=patients)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            keep_id, remove_id = dlg.get_ids()
            if keep_id is None:
                QMessageBox.warning(self, "Merge", "Cannot merge a patient with itself."); return
            reply = QMessageBox.question(self, "Confirm Merge",
                f"Merge PT-{remove_id:04d} into PT-{keep_id:04d}?\nThis cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self._backend.merge_patients(keep_id, remove_id):
                    QMessageBox.information(self, "Merged", "Patients merged successfully.")
                    self._load_from_db(); self.patients_changed.emit(self.get_patient_names())
                else:
                    QMessageBox.critical(self, "Error", "Merge failed.")
