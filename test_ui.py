import sys, os
sys.path.append(os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from backend import AuthBackend
from ui.shared.clinical_page import ClinicalPage
from ui.shared.patients_page import PatientsPage

app = QApplication(sys.argv)
backend = AuthBackend()

# 1. Nurse Clinical Page
clin = ClinicalPage(backend=backend, role="Nurse", user_email="nurse@carecrud.com")
clin_dump = []
def dump_tree(widget, depth=0):
    clin_dump.append("  " * depth + f"{widget.__class__.__name__} (objName: {widget.objectName()}, text: {getattr(widget, 'text', lambda: '')()})")
    for child in widget.children():
        if hasattr(child, "children"):
            dump_tree(child, depth + 1)
dump_tree(clin)

# 2. Nurse Patients Page
pat = PatientsPage(backend=backend, role="Nurse", user_email="nurse@carecrud.com")
pat_dump = []
def dump_tree_p(widget, depth=0):
    pat_dump.append("  " * depth + f"{widget.__class__.__name__} (objName: {widget.objectName()}, text: {getattr(widget, 'text', lambda: '')()})")
    for child in widget.children():
        if hasattr(child, "children"):
            dump_tree_p(child, depth + 1)
dump_tree_p(pat)

with open("test_ui_dump.txt", "w", encoding="utf-8") as f:
    f.write("--- CLINICAL PAGE ---\n")
    f.write("\n".join(clin_dump))
    f.write("\n\n--- PATIENTS PAGE ---\n")
    f.write("\n".join(pat_dump))

print("Dumped.")
