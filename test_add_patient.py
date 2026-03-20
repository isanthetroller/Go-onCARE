import sys
sys.path.insert(0, '.')
from backend import AuthBackend

b = AuthBackend()
data = {
    "first_name": "Test",
    "last_name": "Patient",
    "sex": "Male",
    "dob": "1990-01-01",
    "phone": "09123456789",
    "email": "test@example.com",
    "address": "123 Test St",
    "civil_status": "Single",
    "emergency_contact": "John Doe",
    "blood_type": "O+",
    "discount_type_id": None,
    "id_proof_path": None,
    "conditions": "Cancer, Asthma",
    "status": "Active",
    "notes": "Test notes"
}
res = b.add_patient(data)
print("Add patient result:", res)
pats = b.get_patients()
print("Patient conditions:", pats[-1].get('conditions'))
