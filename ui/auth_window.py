"""Authentication window – Login screen with forced password change."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame,
    QGraphicsDropShadowEffect, QDialog, QFormLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QPainterPath

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


class AuthWindow(QMainWindow):
    """Login window.  Emits *login_success* when the user signs in."""

    login_success = pyqtSignal(str, str, str)  # email, role, full_name

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CareCRUD – Login")
        self.setFixedSize(500, 520)
        self.setStyleSheet(AUTH_STYLE)
        self._backend = AuthBackend()

        bg = QWidget()
        bg.setObjectName("authBg")
        self.setCentralWidget(bg)
        root = QVBoxLayout(bg)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.setContentsMargins(32, 32, 32, 32)

        root.addWidget(self._build_login())

    # ── Login ──────────────────────────────────────────────────────────
    def _build_login(self) -> QWidget:
        card = self._card()
        lay = QVBoxLayout(card)
        lay.setSpacing(16)
        lay.setContentsMargins(40, 36, 40, 36)

        # Medical cross logo
        cross = _MedicalCrossWidget(64)
        lay.addWidget(cross, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addSpacing(4)

        lay.addWidget(self._title("Welcome Back"))
        lay.addWidget(self._subtitle("Sign in to continue to CareCRUD"))
        lay.addSpacing(8)

        self.login_email = self._input("Email address")
        self.login_pw    = self._input("Password", password=True)
        lay.addWidget(self.login_email)
        lay.addWidget(self.login_pw)

        lay.addSpacing(4)

        btn = QPushButton("Sign In")
        btn.setObjectName("primaryBtn")
        btn.setMinimumHeight(46)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._on_login)
        lay.addWidget(btn)

        return card

    # ── Handlers ───────────────────────────────────────────────────────
    def _on_login(self):
        email = self.login_email.text().strip()
        pw    = self.login_pw.text().strip()
        if not email:
            return self._err("Please enter your email address.")
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
            " border-radius: 10px; font-size: 13px; background: #FFF; }"
            "QLineEdit:focus { border: 2px solid #388087; }")

        self.confirm_pw = QLineEdit()
        self.confirm_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pw.setPlaceholderText("Confirm new password")
        self.confirm_pw.setMinimumHeight(42)
        self.confirm_pw.setStyleSheet(self.new_pw.styleSheet())

        form.addRow("New Password", self.new_pw)
        form.addRow("Confirm", self.confirm_pw)
        lay.addLayout(form)
        lay.addSpacing(8)

        save_btn = QPushButton("Set Password")
        save_btn.setMinimumHeight(44)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(
            "QPushButton { background-color: #388087; color: #FFF; border: none;"
            " border-radius: 10px; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #2C6B70; }")
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
        self._backend.exec(
            "UPDATE users SET password=%s, must_change_password=0 WHERE email=%s",
            (new_pw, self._email))
        QMessageBox.information(self, "Success", "Password changed successfully!\nYou can now log in with your new password.")
        self.accept()
