"""Tests for Verification ABC and VerificationResult."""

from abc import ABC
from dataclasses import is_dataclass
from pathlib import Path

import pytest

from jiro.results.base import Result
from jiro.verifications.base import Verification, VerificationResult


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_verification_result_is_dataclass(self):
        """VerificationResult should be a dataclass."""
        assert is_dataclass(VerificationResult)

    def test_verification_result_has_required_fields(self):
        """VerificationResult should have all required fields."""
        result = VerificationResult(
            success=True,
            verification_command="pytest tests/test_foo.py",
            verification_output="1 passed",
            verification_time=0.5,
        )
        assert result.success is True
        assert result.verification_command == "pytest tests/test_foo.py"
        assert result.verification_output == "1 passed"
        assert result.verification_time == 0.5

    def test_verification_result_success_false(self):
        """VerificationResult should handle failure case."""
        result = VerificationResult(
            success=False,
            verification_command="pytest tests/test_foo.py",
            verification_output="FAILED tests/test_foo.py::test_login",
            verification_time=1.2,
        )
        assert result.success is False
        assert "FAILED" in result.verification_output

    def test_verification_result_equality(self):
        """VerificationResult instances with same values should be equal."""
        result1 = VerificationResult(
            success=True,
            verification_command="cmd",
            verification_output="out",
            verification_time=1.0,
        )
        result2 = VerificationResult(
            success=True,
            verification_command="cmd",
            verification_output="out",
            verification_time=1.0,
        )
        assert result1 == result2


class TestVerificationABC:
    """Tests for Verification abstract base class."""

    def test_verification_is_abc(self):
        """Verification should be an abstract base class."""
        assert issubclass(Verification, ABC)

    def test_verification_cannot_be_instantiated_directly(self):
        """Verification should not be instantiable directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            Verification()  # type: ignore[abstract]

    def test_verification_has_verify_abstract_method(self):
        """Verification should have abstract verify method."""
        assert hasattr(Verification, "verify")
        assert getattr(Verification.verify, "__isabstractmethod__", False)


class TestVerificationSubclass:
    """Tests for Verification subclass implementation."""

    def test_subclass_must_implement_verify(self):
        """Subclass must implement verify method."""

        class IncompleteVerification(Verification):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteVerification()  # type: ignore[abstract]

    def test_subclass_can_implement_verification(self):
        """Subclass can properly implement Verification."""

        class TestVerification(Verification):
            def verify(self, *, result: Result) -> VerificationResult:
                return VerificationResult(
                    success=True,
                    verification_command="echo 'test'",
                    verification_output="test",
                    verification_time=0.1,
                )

        verifier = TestVerification()
        assert isinstance(verifier, Verification)

    def test_verify_receives_result_parameter(self):
        """verify() should receive result parameter."""

        class TestVerification(Verification):
            def verify(self, *, result: Result) -> VerificationResult:
                # Access the result to verify it was passed
                file_count = len(result.changed_files)
                return VerificationResult(
                    success=file_count > 0,
                    verification_command=f"check {file_count} files",
                    verification_output=f"Checked {file_count} files",
                    verification_time=0.2,
                )

        verifier = TestVerification()
        result = Result(changed_files=[Path("src/foo.py"), Path("src/bar.py")])
        verification = verifier.verify(result=result)

        assert verification.success is True
        assert "2" in verification.verification_command
        assert "2" in verification.verification_output

    def test_verify_returns_verification_result(self):
        """verify() should return a VerificationResult."""

        class TestVerification(Verification):
            def verify(self, *, result: Result) -> VerificationResult:
                return VerificationResult(
                    success=True,
                    verification_command="pytest",
                    verification_output="All tests passed",
                    verification_time=5.5,
                )

        verifier = TestVerification()
        result = Result(changed_files=[])
        verification = verifier.verify(result=result)

        assert isinstance(verification, VerificationResult)
        assert verification.success is True
        assert verification.verification_time == 5.5
