"""Tests for SearchMixin – global search across patients, appointments, employees."""


class TestSearch:
    def test_global_search_empty_returns_empty(self, backend):
        results = backend.global_search("")
        assert results == {"patients": [], "appointments": [], "employees": []}

    def test_global_search_short_query(self, backend):
        results = backend.global_search("a")  # < 2 chars
        assert results == {"patients": [], "appointments": [], "employees": []}

    def test_global_search_returns_structure(self, backend):
        results = backend.global_search("Santos")
        assert "patients" in results
        assert "appointments" in results
        assert "employees" in results
        assert isinstance(results["patients"], list)

    def test_global_search_without_employees(self, backend):
        results = backend.global_search("Santos", include_employees=False)
        assert results["employees"] == []
