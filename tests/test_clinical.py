"""Tests for ClinicalMixin – queue management and invoices."""


class TestQueue:
    def test_get_queue_entries(self, backend):
        q = backend.get_queue_entries()
        assert isinstance(q, list)

    def test_get_queue_stats(self, backend):
        stats = backend.get_queue_stats()
        assert isinstance(stats, dict)
        for key in ("waiting", "in_progress", "completed"):
            assert key in stats

    def test_get_avg_consultation_minutes(self, backend):
        m = backend.get_avg_consultation_minutes()
        assert isinstance(m, (int, float))
        assert m > 0


class TestInvoices:
    def test_get_invoices_returns_list(self, backend):
        invoices = backend.get_invoices()
        assert isinstance(invoices, list)

    def test_invoice_fields(self, backend):
        invoices = backend.get_invoices()
        if invoices:
            inv = invoices[0]
            for key in ("invoice_id", "patient_name", "total_amount", "amount_paid", "status"):
                assert key in inv, f"Missing field: {key}"
