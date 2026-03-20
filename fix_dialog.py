import os

FILE_PATH = "ui/shared/appointment_dialog.py"

with open(FILE_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Preserve exactly up to line 796. The last line index is 795. 
trimmed = lines[:796]

new_content = """    def get_data(self) -> dict:
        doc_text = self.doctor_combo.currentText()
        if "  (" in doc_text:
            doc_text = doc_text.split("  (")[0]
        appt_date = self.date_edit.date().toString("yyyy-MM-dd")
        return {
            "patient_name": self.patient_combo.currentText(),
            "patient_id":   self._get_patient_id(),
            "doctor":       doc_text,
            "doctor_id":    self.doctor_combo.currentData(),
            "date":         appt_date,
            "time":         self.time_edit.time().toString("HH:mm:ss"),
            "purpose":      self.purpose_combo.currentText(),
            "service_id":   self.purpose_combo.currentData(),
            "status":       (self.status_combo.currentText() if self._is_edit else "Confirmed"),
            "notes":        self.notes_edit.toPlainText(),
            "cancellation_reason": (self.cancel_reason.text() if self._is_edit else ""),
            "reschedule_reason": "",
        }

# ══════════════════════════════════════════════════════════════════════
#  Appointment Details Dialog (Modern read-only view)
# ══════════════════════════════════════════════════════════════════════
class AppointmentDetailsDialog(QDialog):
    def __init__(self, parent=None, appt: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Appointment Details")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setMinimumWidth(460)
        
        self.setStyleSheet(\"\"\"
            QDialog {
                background-color: #F4F7F9;
            }
            QFrame#MainCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E1E8ED;
            }
            QLabel#TitleLabel {
                font-size: 18px;
                font-weight: 700;
                color: #2C3E50;
            }
            QLabel#FieldLabel {
                font-size: 13px;
                font-weight: 600;
                color: #7F8C8D;
                padding-right: 16px;
            }
            QLabel#FieldValue {
                font-size: 14px;
                font-weight: 500;
                color: #2C3E50;
            }
            QLabel#PatientName {
                font-size: 16px;
                font-weight: 700;
                color: #1A252F;
            }
            /* Status Pills */
            QLabel#StatusConfirmed {
                background-color: #D1E7DD; color: #0F5132;
                border-radius: 12px; padding: 4px 12px;
                font-size: 12px; font-weight: bold;
            }
            QLabel#StatusPending {
                background-color: #FFF3CD; color: #664D03;
                border-radius: 12px; padding: 4px 12px;
                font-size: 12px; font-weight: bold;
            }
            QLabel#StatusCancelled {
                background-color: #F8D7DA; color: #842029;
                border-radius: 12px; padding: 4px 12px;
                font-size: 12px; font-weight: bold;
            }
            QLabel#StatusCompleted {
                background-color: #CFF4FC; color: #055160;
                border-radius: 12px; padding: 4px 12px;
                font-size: 12px; font-weight: bold;
            }
            QLabel#StatusDefault {
                background-color: #E2E3E5; color: #41464A;
                border-radius: 12px; padding: 4px 12px;
                font-size: 12px; font-weight: bold;
            }
            /* OK Button */
            QPushButton#OkButton {
                background-color: #388087;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                border: none;
            }
            QPushButton#OkButton:hover {
                background-color: #2C6B71;
            }
            QPushButton#OkButton:pressed {
                background-color: #1F5257;
            }
            /* Multi-line fields like notes */
            QTextEdit#NotesField {
                background-color: #F9FAFC;
                border: 1px solid #E1E8ED;
                border-radius: 6px;
                padding: 8px;
                color: #34495E;
                font-size: 13px;
            }
        \"\"\")
        
        appt = appt or {}
        time_str = str(appt.get('appointment_time', ''))
        try:
            from datetime import datetime
            t = datetime.strptime(time_str, "%H:%M:%S")
            time_display = t.strftime("%I:%M %p").lstrip("0")
        except Exception: 
            time_display = time_str
            
        date_display = _pretty_date(str(appt.get('appointment_date', '')))
        
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(24, 24, 24, 24)
        main_lay.setSpacing(20)
        
        # -- Main Card Container --
        card = QFrame()
        card.setObjectName("MainCard")
        # Apply drop shadow effect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)
        
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)
        
        # Header Area (Icon + Title + Status)
        hdr_w = QWidget()
        hdr_lay = QHBoxLayout(hdr_w)
        hdr_lay.setContentsMargins(24, 24, 24, 20)
        hdr_lay.setSpacing(16)
        
        # Soft circle icon container
        import os
        from PyQt6.QtSvgWidgets import QSvgWidget
        icon_container = QFrame()
        icon_container.setFixedSize(48, 48)
        icon_container.setStyleSheet("background-color: #E6F0F2; border-radius: 24px;")
        
        icon_lay = QVBoxLayout(icon_container)
        icon_lay.setContentsMargins(12, 12, 12, 12)
        
        svg_path = os.path.join(os.path.dirname(__file__), "..", "styles", "icon-info.svg")
        icon_widget = QSvgWidget(os.path.normpath(svg_path))
        icon_widget.setFixedSize(24, 24)
        icon_widget.setStyleSheet("background: transparent;")
        
        icon_lay.addWidget(icon_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        hdr_lay.addWidget(icon_container, alignment=Qt.AlignmentFlag.AlignTop)
        
        # Title and Patient Name
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        
        title_lbl = QLabel("Appointment Details")
        title_lbl.setObjectName("TitleLabel")
        patient_lbl = QLabel(appt.get('patient_name', 'Unknown Patient'))
        patient_lbl.setObjectName("PatientName")
        
        title_col.addWidget(title_lbl)
        title_col.addWidget(patient_lbl)
        hdr_lay.addLayout(title_col)
        hdr_lay.addStretch()
        
        # Status Pill
        status_val = appt.get('status', 'Pending')
        status_lbl = QLabel(status_val.upper())
        status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if status_val == "Confirmed":
            status_lbl.setObjectName("StatusConfirmed")
        elif status_val == "Pending":
            status_lbl.setObjectName("StatusPending")
        elif status_val == "Cancelled":
            status_lbl.setObjectName("StatusCancelled")
        elif status_val == "Completed":
            status_lbl.setObjectName("StatusCompleted")
        else:
            status_lbl.setObjectName("StatusDefault")
        hdr_lay.addWidget(status_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        
        card_lay.addWidget(hdr_w)
        
        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #F0F4F7; border: none;")
        div.setFixedHeight(1)
        card_lay.addWidget(div)
        
        # Details Grid
        details_w = QWidget()
        details_lay = QFormLayout(details_w)
        details_lay.setContentsMargins(24, 24, 24, 24)
        details_lay.setHorizontalSpacing(16)
        details_lay.setVerticalSpacing(16)
        
        def _add_row(label, val):
            k = QLabel(label)
            k.setObjectName("FieldLabel")
            v = QLabel(str(val))
            v.setObjectName("FieldValue")
            v.setWordWrap(True)
            details_lay.addRow(k, v)
            
        _add_row("Doctor", appt.get('doctor_name', ''))
        _add_row("Date", date_display)
        _add_row("Time", time_display)
        _add_row("Service", appt.get('service_name', ''))
        
        notes = appt.get("notes", "") or ""
        cancel_reason = appt.get("cancellation_reason", "") or ""
        
        card_lay.addWidget(details_w)
        
        # Optional Notes Section
        if notes or cancel_reason:
            notes_w = QWidget()
            notes_lay = QVBoxLayout(notes_w)
            notes_lay.setContentsMargins(24, 0, 24, 24)
            notes_lay.setSpacing(12)
            
            if notes:
                n_lbl = QLabel("Notes")
                n_lbl.setObjectName("FieldLabel")
                n_val = QTextEdit(notes)
                n_val.setObjectName("NotesField")
                n_val.setReadOnly(True)
                n_val.setMaximumHeight(60)
                notes_lay.addWidget(n_lbl)
                notes_lay.addWidget(n_val)
                
            if cancel_reason:
                c_lbl = QLabel("Cancellation Reason")
                c_lbl.setObjectName("FieldLabel")
                c_val = QTextEdit(cancel_reason)
                c_val.setObjectName("NotesField")
                c_val.setReadOnly(True)
                c_val.setMaximumHeight(60)
                c_val.setStyleSheet("QTextEdit#NotesField { border: 1px solid #F8D7DA; background-color: #FFF5F6; }")
                notes_lay.addWidget(c_lbl)
                notes_lay.addWidget(c_val)
                
            card_lay.addWidget(notes_w)
            
        main_lay.addWidget(card)
        
        # Button Row
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("OkButton")
        ok_btn.setMinimumSize(100, 40)
        ok_btn.clicked.connect(self.accept)
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_lay.addWidget(ok_btn)
        main_lay.addLayout(btn_lay)
"""

with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.writelines(trimmed)
    f.write(new_content)
    f.write("\n")
