"""Tests for DashboardMixin – summary stats and upcoming appointments."""


class TestDashboard:
    def test_get_dashboard_summary(self, backend):
        summary = backend.get_dashboard_summary()
        assert isinstance(summary, dict)
        for key in ("active_patients", "today_appts"):
            assert key in summary, f"Missing key: {key}"

    def test_get_upcoming_appointments(self, backend):
        upcoming = backend.get_upcoming_appointments(limit=5)
        assert isinstance(upcoming, list)

    def test_get_patient_stats_monthly(self, backend):
        stats = backend.get_patient_stats_monthly(months=3)
        assert isinstance(stats, list)
