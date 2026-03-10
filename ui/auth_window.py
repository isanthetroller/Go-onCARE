# Login window + forced password change dialog

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame,
    QGraphicsDropShadowEffect, QDialog, QFormLayout, QAbstractButton,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QRectF, QPointF
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QPainterPath, QLinearGradient


class _EyeToggleButton(QAbstractButton):
    """Custom-painted eye icon button for password visibility toggle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._visible = False          # password is hidden by default
        self.setFixedSize(46, 46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Show / Hide password")

    @property
    def showing(self) -> bool:
        return self._visible

    @showing.setter
    def showing(self, val: bool):
        self._visible = val
        self.update()

    def sizeHint(self):
        return QSize(46, 46)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(QColor("#388087"), 2.0)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        cx, cy = self.width() / 2, self.height() / 2
        ew, eh = 22.0, 12.0  # eye width / height

        # Draw eye shape (two arcs)
        path = QPainterPath()
        path.moveTo(cx - ew / 2, cy)
        path.quadTo(cx, cy - eh, cx + ew / 2, cy)
        path.quadTo(cx, cy + eh, cx - ew / 2, cy)
        p.drawPath(path)

        # Pupil
        p.setBrush(QBrush(QColor("#388087")))
        p.drawEllipse(QPointF(cx, cy), 3.5, 3.5)

        # Slash line when password is hidden
        if not self._visible:
            slash_pen = QPen(QColor("#388087"), 2.2)
            p.setPen(slash_pen)
            p.drawLine(QPointF(cx - 10, cy + 8), QPointF(cx + 10, cy - 8))

        p.end()

from ui.styles import AUTH_STYLE
from backend import AuthBackend


class _MedicalCrossWidget(QWidget):
    """Renders a teal medical cross icon."""

    def __init__(self, size: int = 64, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._size
        # Circle background
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#388087")))
        p.drawEllipse(0, 0, s, s)
        # White cross
        p.setBrush(QBrush(QColor("#FFFFFF")))
        arm_w = s * 0.24
        arm_h = s * 0.58
        cx, cy = s / 2, s / 2
        # Vertical bar
        p.drawRoundedRect(
            QRect(int(cx - arm_w / 2), int(cy - arm_h / 2), int(arm_w), int(arm_h)),
            int(arm_w * 0.2), int(arm_w * 0.2))
        # Horizontal bar
        p.drawRoundedRect(
            QRect(int(cx - arm_h / 2), int(cy - arm_w / 2), int(arm_h), int(arm_w)),
            int(arm_w * 0.2), int(arm_w * 0.2))
        p.end()


class _BrandPanel(QWidget):
    """Left-side teal panel with logo, brand name, and tagline."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(340)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Gradient background
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor("#2C6A70"))
        grad.setColorAt(0.5, QColor("#388087"))
        grad.setColorAt(1.0, QColor("#6FB3B8"))
        p.fillRect(0, 0, w, h, QBrush(grad))

        # Subtle decorative circles
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 12)))
        p.drawEllipse(QRectF(-60, h * 0.55, 260, 260))
        p.setBrush(QBrush(QColor(255, 255, 255, 8)))
        p.drawEllipse(QRectF(w * 0.5, -40, 200, 200))

        p.end()


class AuthWindow(QMainWindow):
    """Login window.  Emits *login_success* when the user signs in."""

    login_success = pyqtSignal(str, str, str)  # email, role, full_name

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Go-onCare \u2013 Login")
        self.setFixedSize(860, 580)
        self.setStyleSheet(AUTH_STYLE)
        self._backend = AuthBackend()

        bg = QWidget()
        bg.setObjectName("authBg")
        self.setCentralWidget(bg)
        root = QHBoxLayout(bg)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_brand_panel())
        root.addWidget(self._build_form_panel(), 1)

    # ── Left brand panel ───────────────────────────────────────────────
    def _build_brand_panel(self) -> QWidget:
        panel = _BrandPanel()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(36, 0, 36, 0)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Medical cross logo (larger)
        cross = _MedicalCrossWidget(80)
        lay.addWidget(cross, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addSpacing(20)

        brand = QLabel("Go-onCare")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: #FFFFFF;"
            " font-family: 'Segoe UI', sans-serif; background: transparent;")
        lay.addWidget(brand)
        lay.addSpacing(6)

        tagline = QLabel("Healthcare Management\nSystem")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet(
            "font-size: 14px; color: rgba(255,255,255,0.8);"
            " font-family: 'Segoe UI', sans-serif; background: transparent;"
            " line-height: 1.5;")
        lay.addWidget(tagline)
        lay.addSpacing(32)

        # Feature highlights
        for text in [
            "Patient records & appointments",
            "Clinical queue & billing",
            "Analytics & reporting",
        ]:
            row = QHBoxLayout()
            row.setSpacing(10)
            dot = QLabel("\u2713")
            dot.setFixedWidth(20)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setStyleSheet(
                "color: #C2EDCE; font-size: 15px; font-weight: bold;"
                " background: transparent;")
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color: rgba(255,255,255,0.85); font-size: 13px;"
                " background: transparent;")
            row.addWidget(dot)
            row.addWidget(lbl, 1)
            lay.addLayout(row)
            lay.addSpacing(6)

        return panel

    # ── Right form panel ───────────────────────────────────────────────
    def _build_form_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("formPanel")
        panel.setStyleSheet("QWidget#formPanel { background-color: #FFFFFF; }")
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form_w = QWidget()
        form_w.setFixedWidth(360)
        lay = QVBoxLayout(form_w)
        lay.setSpacing(16)
        lay.setContentsMargins(0, 0, 0, 0)

        lay.addWidget(self._title("Welcome Back"))
        lay.addWidget(self._subtitle("Sign in to your account"))
        lay.addSpacing(12)

        # Email field with label
        email_lbl = QLabel("Email")
        email_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #2C3E50;"
            " margin-bottom: 2px;")
        lay.addWidget(email_lbl)
        self.login_email = self._input("Enter your email address")
        self.login_email.setMaxLength(150)
        self.login_email.returnPressed.connect(self._on_login)
        lay.addWidget(self.login_email)
        lay.addSpacing(4)

        # Password field with label
        pw_lbl = QLabel("Password")
        pw_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #2C3E50;"
            " margin-bottom: 2px;")
        lay.addWidget(pw_lbl)
        self.login_pw = self._input("Enter your password", password=True)
        self.login_pw.returnPressed.connect(self._on_login)
        pw_row = QHBoxLayout()
        pw_row.setSpacing(0)
        pw_row.addWidget(self.login_pw)
        self._pw_toggle = _EyeToggleButton()
        self._pw_toggle.clicked.connect(self._toggle_login_pw)
        pw_row.addWidget(self._pw_toggle)
        lay.addLayout(pw_row)

        lay.addSpacing(8)

        btn = QPushButton("Sign In")
        btn.setObjectName("primaryBtn")
        btn.setMinimumHeight(48)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._on_login)
        lay.addWidget(btn)

        # ── BEGIN QUICK LOGIN (TEMPORARY – delete this block to remove) ──
        lay.addSpacing(12)
        ql_sep = QFrame()
        ql_sep.setFrameShape(QFrame.Shape.HLine)
        ql_sep.setStyleSheet("color: #BADFE7;")
        lay.addWidget(ql_sep)
        ql_label = QLabel("Quick Login (dev only)")
        ql_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ql_label.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #7F8C8D;"
            " letter-spacing: 1px;")
        lay.addWidget(ql_label)
        _quick_accounts = [
            ("Admin",        "admin@carecrud.com",       "admin123",     "#388087"),
            ("Doctor",       "ana.reyes@carecrud.com",   "doctor123",    "#5CB85C"),
            ("Nurse",        "sofia.reyes@carecrud.com", "nurse123",     "#6FB3B8"),
            ("Receptionist", "james.cruz@carecrud.com",  "reception123", "#E8B931"),
            ("HR",           "hr@carecrud.com",          "hr123",        "#C2EDCE"),
        ]
        ql_row1 = QHBoxLayout(); ql_row1.setSpacing(6)
        ql_row2 = QHBoxLayout(); ql_row2.setSpacing(6)
        for i, (role, email, pw, color) in enumerate(_quick_accounts):
            qb = QPushButton(role)
            qb.setMinimumHeight(34)
            qb.setCursor(Qt.CursorShape.PointingHandCursor)
            fg = "#FFFFFF" if role != "HR" else "#2C3E50"
            qb.setStyleSheet(
                f"QPushButton {{ background-color: {color}; color: {fg};"
                f" border: none; border-radius: 8px; padding: 6px 10px;"
                f" font-size: 12px; font-weight: bold; }}"
                f" QPushButton:hover {{ opacity: 0.85; }}")
            qb.clicked.connect(
                lambda checked, e=email, p=pw: self._quick_login(e, p))
            if i < 3:
                ql_row1.addWidget(qb)
            else:
                ql_row2.addWidget(qb)
        ql_row2.addStretch()
        lay.addLayout(ql_row1)
        lay.addLayout(ql_row2)
        # ── END QUICK LOGIN (TEMPORARY) ──────────────────────────────

        outer.addWidget(form_w)
        return panel

    # ── Handlers ───────────────────────────────────────────────────────
    def _on_login(self):
        import re
        email = self.login_email.text().strip()
        pw    = self.login_pw.text().strip()
        if not email:
            return self._err("Please enter your email address.")
        if not re.match(r'^[\w.+-]+@[\w-]+\.[\w.]+$', email):
            return self._err("Please enter a valid email address.")
        if not pw:
            return self._err("Please enter your password.")
        try:
            result = self._backend.login(email, pw)
            success, role, full_name, message = result[0], result[1], result[2], result[3]
            must_change = result[4] if len(result) > 4 else False
        except Exception as e:
            return self._err(f"Connection failed:\n{e}")
        if not success:
            return self._err(message)
        # Force password change for new accounts
        if must_change:
            dlg = _ForcePasswordChangeDialog(self, email=email, backend=self._backend)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return  # User cancelled — don't log in
        self.login_success.emit(email, role, full_name)

    # ── BEGIN QUICK LOGIN handler (TEMPORARY – delete to remove) ───
    def _quick_login(self, email: str, password: str):
        """Bypass the input fields and log in directly."""
        self.login_email.setText(email)
        self.login_pw.setText(password)
        self._on_login()
    # ── END QUICK LOGIN handler ────────────────────────────────────

    # ── Widget helpers ─────────────────────────────────────────────────
    def _card(self) -> QWidget:
        w = QWidget()
        w.setObjectName("cardWidget")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 50))
        w.setGraphicsEffect(shadow)
        return w

    @staticmethod
    def _title(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("titleLabel")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    @staticmethod
    def _subtitle(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("subtitleLabel")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    @staticmethod
    def _input(placeholder: str, *, password: bool = False) -> QLineEdit:
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        le.setMinimumHeight(46)
        if password:
            le.setEchoMode(QLineEdit.EchoMode.Password)
        return le

    def _toggle_login_pw(self):
        if self.login_pw.echoMode() == QLineEdit.EchoMode.Password:
            self.login_pw.setEchoMode(QLineEdit.EchoMode.Normal)
            self._pw_toggle.showing = True
        else:
            self.login_pw.setEchoMode(QLineEdit.EchoMode.Password)
            self._pw_toggle.showing = False

    def _err(self, msg: str):
        QMessageBox.warning(self, "Validation Error", msg)


# ══════════════════════════════════════════════════════════════════════
#  Forced Password Change Dialog (shown on first login)
# ══════════════════════════════════════════════════════════════════════
class _ForcePasswordChangeDialog(QDialog):
    """Modal dialog that forces a new user to set their own password."""

    def __init__(self, parent=None, *, email: str, backend):
        super().__init__(parent)
        self.setWindowTitle("Change Your Password")
        self.setFixedWidth(420)
        self.setModal(True)
        self._email = email
        self._backend = backend

        lay = QVBoxLayout(self)
        lay.setSpacing(16)
        lay.setContentsMargins(32, 28, 32, 28)

        title = QLabel("Password Change Required")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #388087;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        info = QLabel("This is your first login. Please set a new password to continue.")
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 13px; color: #555;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(info)
        lay.addSpacing(8)

        form = QFormLayout()
        form.setSpacing(12)

        self.new_pw = QLineEdit()
        self.new_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_pw.setPlaceholderText("New password")
        self.new_pw.setMinimumHeight(42)
        self.new_pw.setStyleSheet(
            "QLineEdit { padding: 10px 14px; border: 2px solid #BADFE7;"
            " border-radius: 8px; font-size: 13px; background: #FFF; }"
            "QLineEdit:focus { border: 2px solid #388087; }")

        self.confirm_pw = QLineEdit()
        self.confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pw.setPlaceholderText("Confirm new password")
        self.confirm_pw.setMinimumHeight(42)
        self.confirm_pw.setStyleSheet(self.new_pw.styleSheet())

        # New password row with toggle
        new_pw_row = QHBoxLayout(); new_pw_row.setSpacing(0)
        new_pw_row.addWidget(self.new_pw)
        self._new_pw_toggle = _EyeToggleButton()
        self._new_pw_toggle.setFixedSize(42, 42)
        self._new_pw_toggle.clicked.connect(lambda: self._toggle_pw_field(self.new_pw, self._new_pw_toggle))
        new_pw_row.addWidget(self._new_pw_toggle)

        # Confirm password row with toggle
        confirm_pw_row = QHBoxLayout(); confirm_pw_row.setSpacing(0)
        confirm_pw_row.addWidget(self.confirm_pw)
        self._confirm_pw_toggle = _EyeToggleButton()
        self._confirm_pw_toggle.setFixedSize(42, 42)
        self._confirm_pw_toggle.clicked.connect(lambda: self._toggle_pw_field(self.confirm_pw, self._confirm_pw_toggle))
        confirm_pw_row.addWidget(self._confirm_pw_toggle)

        form.addRow("New Password", new_pw_row)
        form.addRow("Confirm", confirm_pw_row)
        lay.addLayout(form)
        lay.addSpacing(8)

        save_btn = QPushButton("Set Password")
        save_btn.setMinimumHeight(44)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            "QPushButton { background-color: #388087; color: #FFF; border: none;"
            " border-radius: 8px; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #2C6A70; }")
        save_btn.clicked.connect(self._on_save)
        lay.addWidget(save_btn)

    def _on_save(self):
        new_pw = self.new_pw.text().strip()
        confirm = self.confirm_pw.text().strip()
        if not new_pw:
            QMessageBox.warning(self, "Validation", "Please enter a new password.")
            return
        if len(new_pw) < 4:
            QMessageBox.warning(self, "Validation", "Password must be at least 4 characters.")
            return
        if new_pw != confirm:
            QMessageBox.warning(self, "Validation", "Passwords do not match.")
            return
        # Update password and clear the must_change flag
        self._backend.force_change_password(self._email, new_pw)
        QMessageBox.information(self, "Success", "Password changed successfully!\nYou can now log in with your new password.")
        self.accept()

    @staticmethod
    def _toggle_pw_field(field: QLineEdit, btn: _EyeToggleButton):
        if field.echoMode() == QLineEdit.EchoMode.Password:
            field.setEchoMode(QLineEdit.EchoMode.Normal)
            btn.showing = True
        else:
            field.setEchoMode(QLineEdit.EchoMode.Password)
            btn.showing = False
