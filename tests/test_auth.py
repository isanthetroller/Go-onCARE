"""Tests for AuthMixin – login, password management, user accounts.

These tests depend on sample data being loaded (database/sample_data.sql).
If no users exist in the database, data-dependent tests will be skipped.
"""

import pytest


class TestLoginValidation:
    """Input validation – these work regardless of data."""

    def test_login_empty_email(self, backend):
        ok, role, name, msg = backend.login("", "pass123")[:4]
        assert not ok
        assert "email" in msg.lower()

    def test_login_empty_password(self, backend):
        ok, role, name, msg = backend.login("some@email.com", "")[:4]
        assert not ok
        assert "password" in msg.lower()


class TestLoginWithData:
    """Tests that require sample data in the users table."""

    def _has_users(self, backend):
        rows = backend.fetch("SELECT COUNT(*) AS cnt FROM users", one=True)
        return rows and rows["cnt"] > 0

    def test_login_wrong_email(self, backend):
        if not self._has_users(backend):
            pytest.skip("No users in DB")
        ok, *_ = backend.login("nobody-fake-xyz@test.com", "x")
        assert not ok

    def test_login_wrong_password(self, backend):
        if not self._has_users(backend):
            pytest.skip("No users in DB")
        user = backend.fetch("SELECT email FROM users LIMIT 1", one=True)
        ok, *_ = backend.login(user["email"], "__WRONG_PASSWORD__")
        assert not ok

    def test_login_success(self, backend):
        """Try to log in with the first user found in the DB."""
        user = backend.fetch(
            "SELECT email, password FROM users LIMIT 1", one=True
        )
        if not user:
            pytest.skip("No users in DB")
        result = backend.login(user["email"], user["password"])
        ok, role, name, msg = result[:4]
        assert ok, f"Login failed for {user['email']}: {msg}"
        assert role
        assert name


class TestUserAccounts:
    def test_get_all_roles(self, backend):
        roles = backend.get_all_roles()
        assert isinstance(roles, list)
        if not roles:
            pytest.skip("Roles table is empty – run database/carecrud.sql")

    def test_get_all_user_accounts(self, backend):
        accounts = backend.get_all_user_accounts()
        assert isinstance(accounts, list)
        if accounts:
            assert "email" in accounts[0]

    def test_get_user_full_name(self, backend):
        user = backend.fetch("SELECT email FROM users LIMIT 1", one=True)
        if not user:
            pytest.skip("No users in DB")
        name = backend.get_user_full_name(user["email"])
        assert name is not None
        assert len(name) > 0
