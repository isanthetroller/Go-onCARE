T"""Test MainWindow construction directly."""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

app = QApplication(sys.argv)
app.setStyle("Fusion")
app.setQuitOnLastWindowClosed(False)

print("Creating MainWindow...", flush=True)
from ui.main_window import MainWindow
mw = MainWindow(user_email="admin@carecrud.com", user_role="Admin", user_name="Carlo Santos")
print("Showing...", flush=True)
mw.showMaximized()
print("Running...", flush=True)
app.exec()
print("Done", flush=True)
