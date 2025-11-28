"""Conftest for unit tests."""

import pytest


@pytest.fixture
def unit_fixture() -> str:
    """Sample unit test fixture."""
    return "unit"
