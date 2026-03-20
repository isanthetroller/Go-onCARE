import os

FILE_PATH = "ui/shared/appointment_dialog.py"

dialog_code = """
# ══════════════════════════════════════════════════════════════════════
#  Cancel Appointment Dialog (Modern UI)
# ══════════════════════════════════════════════════════════════════════
class CancelAppointmentDialog(QDialog):
    def __init__(self, parent=None, patient_name: str = "Unknown"):
        super().__init__(parent)
        self.setWindowTitle("Cancel Appointment")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setMinimumWidth(480)
        
        # Modern QSS Styling
        self.setStyleSheet(\"\"\"
            QDialog {
                background-color: #F5F7FA;
            }
            QFrame#MainCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #DCDCDC;
            }
            QLabel#Breadcrumb {
                font-size: 11px;
                font-weight: 500;
                color: #8A98A5;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QLabel#TitleLabel {
                font-size: 20px;
                font-weight: 800;
                color: #2C3E50;
            }
            QLabel#SubtitleLabel {
                font-size: 15px;
                font-weight: 600;
                color: #34495E;
            }
            QLabel#ReasonLabel {
                font-size: 13px;
                font-weight: 600;
                color: #2C3E50;
            }
            QTextEdit#ReasonText {
                background-color: #FFFFFF;
                border: 1px solid #DCDCDC;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: #2C3E50;
            }
            QTextEdit#ReasonText:focus {
                border: 2px solid #388087;
                background-color: #F8FBFC;
            }
            QPushButton#ConfirmBtn {
                background-color: #E74C3C;
                color: white;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
                border: none;
            }
            QPushButton#ConfirmBtn:hover {
                background-color: #C0392B;
            }
            QPushButton#ConfirmBtn:pressed {
                background-color: #A93226;
            }
            QPushButton#GoBackBtn {
                background-color: transparent;
                color: #7F8C8D;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
                border: 1px solid #DCDCDC;
            }
            QPushButton#GoBackBtn:hover {
                background-color: #F0F3F4;
                color: #34495E;
            }
            QPushButton#GoBackBtn:pressed {
                background-color: #E5E8E8;
            }
        \"\"\")

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(24, 24, 24, 24)
        main_lay.setSpacing(0)
        
        # Card Container
        card = QFrame()
        card.setObjectName("MainCard")
        # Optional subtle drop shadow
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)
        
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(24, 24, 24, 24)
        card_lay.setSpacing(20)
        
        # --- Header Section ---
        header_lay = QVBoxLayout()
        header_lay.setSpacing(6)
        
        breadcrumb = QLabel("Appointments > Cancel Appointment")
        breadcrumb.setObjectName("Breadcrumb")
        
        title = QLabel("Cancel Appointment")
        title.setObjectName("TitleLabel")
        
        subtitle = QLabel(patient_name)
        subtitle.setObjectName("SubtitleLabel")
        
        header_lay.addWidget(breadcrumb)
        header_lay.addWidget(title)
        header_lay.addWidget(subtitle)
        
        card_lay.addLayout(header_lay)
        
        # --- Body Section ---
        body_lay = QVBoxLayout()
        body_lay.setSpacing(8)
        
        reason_lbl = QLabel("Cancellation Reason")
        reason_lbl.setObjectName("ReasonLabel")
        
        self.reason_text = QTextEdit()
        self.reason_text.setObjectName("ReasonText")
        self.reason_text.setPlaceholderText("Enter reason for cancellation...")
        self.reason_text.setMinimumHeight(100)
        self.reason_text.setMaximumHeight(140)
        
        body_lay.addWidget(reason_lbl)
        body_lay.addWidget(self.reason_text)
        
        card_lay.addLayout(body_lay)
        
        # --- Button Row ---
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(12)
        btn_lay.addStretch()
        
        go_back_btn = QPushButton("Go Back")
        go_back_btn.setObjectName("GoBackBtn")
        go_back_btn.setMinimumHeight(42)
        from PyQt6.QtCore import Qt
        go_back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        go_back_btn.clicked.connect(self.reject)
        
        confirm_btn = QPushButton("Confirm Cancellation")
        confirm_btn.setObjectName("ConfirmBtn")
        confirm_btn.setMinimumHeight(42)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.clicked.connect(self.accept)
        
        btn_lay.addWidget(go_back_btn)
        btn_lay.addWidget(confirm_btn)
        
        card_lay.addLayout(btn_lay)
        main_lay.addWidget(card)
        
    def get_reason(self) -> str:
        return self.reason_text.toPlainText().strip()
"""

with open(FILE_PATH, "a", encoding="utf-8") as f:
    f.write("\n" + dialog_code)
