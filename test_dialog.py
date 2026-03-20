import sys
import traceback
sys.path.insert(0, '.')

try:
    from PyQt6.QtWidgets import QApplication
    from ui.shared.appointment_dialog import CancelAppointmentDialog
    app = QApplication(sys.argv)
    dlg = CancelAppointmentDialog(None, "Jane Smith")
    print('Success')
except Exception as e:
    with open("error_log.txt", "w") as f:
        traceback.print_exc(file=f)
