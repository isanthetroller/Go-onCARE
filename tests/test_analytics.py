"""Tests for AnalyticsMixin – revenue, performance, demographics."""


class TestAnalytics:
    def test_get_monthly_revenue(self, backend):
        data = backend.get_monthly_revenue(months=3)
        assert isinstance(data, list)

    def test_get_doctor_performance(self, backend):
        data = backend.get_doctor_performance()
        assert isinstance(data, list)

    def test_get_top_services(self, backend):
        data = backend.get_top_services()
        assert isinstance(data, list)

    def test_get_appointment_status_counts(self, backend):
        data = backend.get_appointment_status_counts()
        assert isinstance(data, list)

    def test_get_patient_condition_counts(self, backend):
        data = backend.get_patient_condition_counts()
        assert isinstance(data, list)

    def test_get_patient_demographics(self, backend):
        data = backend.get_patient_demographics()
        assert isinstance(data, list)

    def test_get_summary_stats(self, backend):
        data = backend.get_summary_stats()
        assert isinstance(data, dict)

    def test_get_period_comparison(self, backend):
        data = backend.get_period_comparison()
        assert isinstance(data, dict)
