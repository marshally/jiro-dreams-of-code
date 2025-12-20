"""Root conftest for all tests."""

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest


@pytest.fixture
def sample_fixture() -> str:
    """Sample fixture for testing."""
    return "test"


def _blocked_query(*args: Any, **kwargs: Any) -> None:
    """Raise an error if real API is called during tests."""
    raise RuntimeError(
        "Real API call attempted during tests! "
        "Use @pytest.mark.allow_api to allow real API calls, "
        "or mock the query function properly."
    )


@pytest.fixture(autouse=True)
def block_real_api_calls(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Block real API calls in all tests by default.

    This fixture automatically patches claude_agent_sdk.query to raise
    an error if called, preventing accidental API token consumption.

    To allow real API calls (e.g., for integration tests with live API):
        @pytest.mark.allow_api
        def test_with_real_api():
            ...

    To run only tests that use real API:
        pytest -m allow_api

    To skip tests that use real API:
        pytest -m "not allow_api"
    """
    # Skip blocking if test is marked to allow API calls
    if request.node.get_closest_marker("allow_api"):
        yield
        return

    # Block the SDK query function at both import locations
    with (
        patch("claude_agent_sdk.query", side_effect=_blocked_query),
        patch("jiro.agents.client.query", side_effect=_blocked_query),
    ):
        yield
