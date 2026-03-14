# Go-onCare - main entry point

import sys
sys.dont_write_bytecode = True
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QPalette, QColor

from ui.auth_window import AuthWindow
from ui.main_window import MainWindow
from ui.styles import MAIN_STYLE, set_active_palette
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

    # ── Slots ──────────────────────────────────────────────────────────
    def _on_login(self, email: str, role: str, full_name: str):
        try:
            # Auto clock-in employee when they log in to the App
            emp_id = self._backend.get_employee_id_by_email(email)
            if emp_id:
                self._backend.clock_in(emp_id)

            self.auth_win.hide()
            set_active_palette(False)
            self._apply_light_palette()
            self.current_user_email = email
            self.main_win = MainWindow(user_email=email, user_role=role, user_name=full_name)
            self.main_win.logout_requested.connect(self._on_logout)
            self.main_win.showMaximized()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(None, "Startup Error", str(e))
            self.auth_win.show()

    def _on_logout(self):
        # Auto clock-out employee when they log out of the App
        if hasattr(self, 'current_user_email') and self.current_user_email:
            emp_id = self._backend.get_employee_id_by_email(self.current_user_email)
            if emp_id:
                self._backend.clock_out(emp_id)
            self.current_user_email = None

        set_active_palette(False)
        self._apply_light_palette()
        self.auth_win = AuthWindow()
        self.auth_win.login_success.connect(self._on_login)
        self.auth_win.show()
        if self.main_win:
            self.main_win.close()
            self.main_win = None

    def _on_app_quit(self):
        # Ensure they are clocked out if they just close the app window
        if hasattr(self, 'current_user_email') and self.current_user_email:
            emp_id = self._backend.get_employee_id_by_email(self.current_user_email)
            if emp_id:
                self._backend.clock_out(emp_id)

    def run(self) -> int:
        self.qapp.aboutToQuit.connect(self._on_app_quit)
        ret = self.qapp.exec()
        return ret


def main():
    app = App()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
