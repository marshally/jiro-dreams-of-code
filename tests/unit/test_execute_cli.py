"""Tests for execute CLI command."""

import pytest

from jiro.core.session import HaltError


class TestHaltError:
    """Tests for HaltError exception."""

    @pytest.mark.unit
    def test_halt_error_stores_reason(self) -> None:
        """HaltError should store the halt reason."""
        reason = "Review failed: test failure"
        error = HaltError(reason)
        assert error.reason == reason

    @pytest.mark.unit
    def test_halt_error_has_message(self) -> None:
        """HaltError should have descriptive message."""
        reason = "Execution error"
        error = HaltError(reason)
        assert "halted" in str(error).lower()
        assert reason in str(error)
