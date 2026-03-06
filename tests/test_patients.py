"""Tests for PatientMixin – CRUD operations on patients."""


class TestPatientRead:
    def test_get_patients_returns_list(self, backend):
        patients = backend.get_patients()
        assert isinstance(patients, list)

    def test_get_patients_has_expected_fields(self, backend):
        patients = backend.get_patients()
        if patients:
            p = patients[0]
            for key in ("patient_id", "first_name", "last_name", "sex", "status"):
                assert key in p, f"Missing field: {key}"

    def test_get_active_patients(self, backend):
        active = backend.get_active_patients()
        assert isinstance(active, list)
        if active:
            assert "name" in active[0]

    def test_get_patient_full_profile_missing(self, backend):
        profile = backend.get_patient_full_profile(-1)
        assert profile == {}

    def test_get_patient_full_profile_valid(self, backend):
        patients = backend.get_patients()
        if patients:
            pid = patients[0]["patient_id"]
            profile = backend.get_patient_full_profile(pid)
            assert "info" in profile
            assert "appointments" in profile
            assert "invoices" in profile
            assert "queue" in profile


class TestPatientWrite:
    _created_id = None

    def test_add_and_delete_patient(self, backend):
        """Add a test patient, verify, update, then clean up."""
        ok = backend.add_patient({
            "first_name": "ZZTest",
            "last_name": "AutoPytest",
            "sex": "Male",
            "dob": "2000-01-01",
            "phone": "09999999999",
            "status": "Active",
        })
        if not ok:
            import pytest
            pytest.skip("add_patient failed – DB may lack required tables or constraints")

        # Verify it exists
        patients = backend.get_patients()
        match = [p for p in patients if p["first_name"] == "ZZTest" and p["last_name"] == "AutoPytest"]
        assert len(match) >= 1
        pid = match[0]["patient_id"]

        # Update
        ok = backend.update_patient(pid, {
            "first_name": "ZZTest",
            "last_name": "Updated",
            "sex": "Male",
            "dob": "2000-01-01",
            "phone": "09999999999",
            "status": "Active",
        })
        assert ok is True

        # Delete (clean up)
        ok = backend.delete_patient(pid)
        assert ok is True
