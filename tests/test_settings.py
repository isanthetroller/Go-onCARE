"""Tests for SettingsMixin – table counts, conditions, discount types."""


class TestSettings:
    def test_get_table_counts(self, backend):
        counts = backend.get_table_counts()
        assert isinstance(counts, (list, dict))

    def test_get_standard_conditions(self, backend):
        conds = backend.get_standard_conditions()
        assert isinstance(conds, list)

    def test_get_discount_types(self, backend):
        types = backend.get_discount_types()
        assert isinstance(types, list)

    def test_get_discount_types_active_only(self, backend):
        types = backend.get_discount_types(active_only=True)
        assert isinstance(types, list)
