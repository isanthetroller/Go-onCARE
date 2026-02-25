"""CareCRUD – Healthcare Management & Scheduling System
Entry point: shows auth window, then the main application on login.
"""

import sys
sys.dont_write_bytecode = True
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QPalette, QColor

from ui.auth_window import AuthWindow
from ui.main_window import MainWindow
from ui.styles import MAIN_STYLE, DARK_MAIN_STYLE, set_active_palette
from backend import AuthBackend


def _global_exception_hook(exc_type, exc_value, exc_tb):
    """Catch ANY unhandled exception and show it instead of silently dying."""
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(msg, file=sys.stderr, flush=True)
    QMessageBox.critical(None, "Unhandled Error", msg)


sys.excepthook = _global_exception_hook


class App:
    def __init__(self):
        self.qapp = QApplication(sys.argv)
        self.qapp.setStyle("Fusion")
        self.qapp.setQuitOnLastWindowClosed(False)
        self._backend = AuthBackend()

        # Set light palette (default)
        self._apply_light_palette()

        self.auth_win = AuthWindow()
        self.main_win = None

        self.auth_win.login_success.connect(self._on_login)
        self.auth_win.show()

    def _apply_light_palette(self):
        palette = self.qapp.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#FFFFFF"))
        palette.setColor(QPalette.ColorRole.Window, QColor("#F6F6F2"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#2C3E50"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#2C3E50"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#2C3E50"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#BADFE7"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#2C3E50"))
        self.qapp.setPalette(palette)

    def _apply_dark_palette(self):
        palette = self.qapp.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor("#2A2A3C"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#2A2A3C"))
        palette.setColor(QPalette.ColorRole.Window, QColor("#1E1E2E"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#E0E0E0"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#E0E0E0"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#E0E0E0"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#3A4A5C"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#E0E0E0"))
        self.qapp.setPalette(palette)

    # ── Slots ──────────────────────────────────────────────────────────
    def _on_login(self, email: str, role: str, full_name: str):
        try:
            self.auth_win.hide()
            # Check dark mode preference
            dark = self._backend.get_dark_mode(email)
            if dark:
                set_active_palette(True)
                self._apply_dark_palette()
            else:
                set_active_palette(False)
                self._apply_light_palette()
            self.main_win = MainWindow(user_email=email, user_role=role, user_name=full_name)
            if dark:
                self.main_win.setStyleSheet(DARK_MAIN_STYLE)
            self.main_win.logout_requested.connect(self._on_logout)
            self.main_win.showMaximized()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(None, "Startup Error", str(e))
            self.auth_win.show()

    def _on_logout(self):
        set_active_palette(False)
        self._apply_light_palette()
        self.auth_win = AuthWindow()
        self.auth_win.login_success.connect(self._on_login)
        self.auth_win.show()
        if self.main_win:
            self.main_win.close()
            self.main_win = None

    def run(self) -> int:
        ret = self.qapp.exec()
        return ret


def main():
    app = App()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
