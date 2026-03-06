"""Tests for EmployeeMixin – employee listing and HR stats."""


class TestEmployeeRead:
    def test_get_employees_returns_list(self, backend):
        emps = backend.get_employees()
        assert isinstance(emps, list)

    def test_get_employees_has_fields(self, backend):
        emps = backend.get_employees()
        if emps:
            e = emps[0]
            for key in ("employee_id", "full_name", "role_name", "department_name", "status"):
                assert key in e, f"Missing field: {key}"

    def test_get_employees_detailed_has_salary(self, backend):
        emps = backend.get_employees_detailed()
        if emps:
            assert "salary" in emps[0]
            assert "emergency_contact" in emps[0]

    def test_get_leave_employees(self, backend):
        leave = backend.get_leave_employees()
        assert isinstance(leave, list)

    def test_get_hr_stats(self, backend):
        stats = backend.get_hr_stats()
        assert isinstance(stats, dict)
        for key in ("total", "doctors", "active", "on_leave", "inactive"):
            assert key in stats

    def test_get_payroll_summary(self, backend):
        payroll = backend.get_payroll_summary()
        assert isinstance(payroll, list)

    def test_get_employment_type_counts(self, backend):
        counts = backend.get_employment_type_counts()
        assert isinstance(counts, list)
