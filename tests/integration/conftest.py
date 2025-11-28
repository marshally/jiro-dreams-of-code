"""Conftest for integration tests."""

import pytest


@pytest.fixture
def integration_fixture() -> str:
    """Sample integration test fixture."""
    return "integration"
