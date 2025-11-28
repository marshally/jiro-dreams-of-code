"""Conftest for end-to-end tests."""

import pytest


@pytest.fixture
def e2e_fixture() -> str:
    """Sample e2e test fixture."""
    return "e2e"
