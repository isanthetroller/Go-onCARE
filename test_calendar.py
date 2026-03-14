import sys
from PyQt6.QtWidgets import QApplication, QCalendarWidget
from PyQt6.QtCore import QDate

app = QApplication(sys.argv)
with open('ui/styles/main.qss', 'r') as f:
    app.setStyleSheet(f.read())
cal = QCalendarWidget()
cal.show()
sys.exit(app.exec())
