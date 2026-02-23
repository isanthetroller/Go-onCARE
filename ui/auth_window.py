"""Authentication window – Login screen."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from ui.styles import AUTH_STYLE
from backend import AuthBackend


class AuthWindow(QMainWindow):
    """Login window.  Emits *login_success* when the user signs in."""

    login_success = pyqtSignal(str, str, str)  # email, role, full_name

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CareCRUD – Login")
        self.setFixedSize(500, 440)
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
        lay.setContentsMargins(40, 44, 40, 40)

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
            success, role, full_name, message = self._backend.login(email, pw)
        except Exception as e:
            return self._err(f"Connection failed:\n{e}")
        if not success:
            return self._err(message)
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
