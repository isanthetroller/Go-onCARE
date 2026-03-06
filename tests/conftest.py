"""Shared pytest fixtures – creates a real AuthBackend wired to the live DB.

REQUIREMENTS
  • MySQL running on localhost with the carecrud_db database set up.
  • pip install pytest
"""

import pytest
import sys, os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import AuthBackend


@pytest.fixture(scope="session")
def backend():
    """One shared backend instance for the whole test session."""
    be = AuthBackend()
    be.set_current_user("tester@carecrud.com", "Admin")
    yield be
    be.close()
