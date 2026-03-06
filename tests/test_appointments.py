"""Tests for AppointmentMixin – scheduling, conflict checking, validation."""

from datetime import date, timedelta


class TestAppointmentRead:
    def test_get_appointments_returns_list(self, backend):
        appts = backend.get_appointments()
        assert isinstance(appts, list)

    def test_get_appointments_has_expected_fields(self, backend):
        appts = backend.get_appointments()
        if appts:
            a = appts[0]
            for key in ("appointment_id", "appointment_date", "patient_name", "doctor_name", "status"):
                assert key in a, f"Missing field: {key}"

    def test_get_doctors_returns_list(self, backend):
        docs = backend.get_doctors()
        assert isinstance(docs, list)
        if docs:
            assert "doctor_name" in docs[0]
            assert "employee_id" in docs[0]

    def test_get_services_list(self, backend):
        services = backend.get_services_list()
        assert isinstance(services, list)
        if services:
            assert "service_name" in services[0]
            assert "price" in services[0]


class TestAppointmentValidation:
    def test_validate_past_date_rejected(self, backend):
        ok, msg = backend._validate_appointment_date("2020-01-01")
        assert not ok
        assert "past" in msg.lower()

    def test_validate_today_accepted(self, backend):
        ok, msg = backend._validate_appointment_date(date.today().strftime("%Y-%m-%d"))
        assert ok

    def test_validate_far_future_rejected(self, backend):
        far = date.today() + timedelta(days=365)
        ok, msg = backend._validate_appointment_date(far.strftime("%Y-%m-%d"))
        assert not ok

    def test_validate_bad_format(self, backend):
        ok, msg = backend._validate_appointment_date("not-a-date")
        assert not ok


class TestConflictCheck:
    def test_no_conflict_with_fake_ids(self, backend):
        conflict = backend.check_appointment_conflict(-1, "2099-01-01", "08:00:00")
        assert conflict is False
