"""Tests for Commit ABC and CommitResult."""

from abc import ABC
from dataclasses import is_dataclass
from pathlib import Path

import pytest

from jiro.commits.base import Commit, CommitResult
from jiro.results.base import Result
from jiro.verifications.base import VerificationResult


class TestCommitResult:
    """Tests for CommitResult dataclass."""

    def test_commit_result_is_dataclass(self):
        """CommitResult should be a dataclass."""
        assert is_dataclass(CommitResult)

    def test_commit_result_has_required_fields(self):
        """CommitResult should have sha and message fields."""
        result = CommitResult(
            sha="abc123def456",
            message="feat: add login validation",
        )
        assert result.sha == "abc123def456"
        assert result.message == "feat: add login validation"

    def test_commit_result_equality(self):
        """CommitResult instances with same values should be equal."""
        result1 = CommitResult(sha="abc123", message="test message")
        result2 = CommitResult(sha="abc123", message="test message")
        assert result1 == result2

    def test_commit_result_different_sha(self):
        """CommitResult instances with different sha should not be equal."""
        result1 = CommitResult(sha="abc123", message="test message")
        result2 = CommitResult(sha="def456", message="test message")
        assert result1 != result2


class TestCommitABC:
    """Tests for Commit abstract base class."""

    def test_commit_is_abc(self):
        """Commit should be an abstract base class."""
        assert issubclass(Commit, ABC)

    def test_commit_cannot_be_instantiated_directly(self):
        """Commit should not be instantiable directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            Commit()  # type: ignore[abstract]

    def test_commit_has_create_abstract_method(self):
        """Commit should have abstract create method."""
        assert hasattr(Commit, "create")
        assert getattr(Commit.create, "__isabstractmethod__", False)


class TestCommitSubclass:
    """Tests for Commit subclass implementation."""

    def test_subclass_must_implement_create(self):
        """Subclass must implement create method."""

        class IncompleteCommit(Commit):
            pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteCommit()  # type: ignore[abstract]

    def test_subclass_can_implement_commit(self):
        """Subclass can properly implement Commit."""

        class TestCommit(Commit):
            def create(
                self,
                *,
                result: Result,
                verification: VerificationResult,
                e2e_time: float,
            ) -> CommitResult:
                return CommitResult(
                    sha="abc123",
                    message="test commit",
                )

        committer = TestCommit()
        assert isinstance(committer, Commit)

    def test_create_receives_all_parameters(self):
        """create() should receive result, verification, and e2e_time."""

        class TestCommit(Commit):
            def create(
                self,
                *,
                result: Result,
                verification: VerificationResult,
                e2e_time: float,
            ) -> CommitResult:
                # Access all parameters to verify they were passed
                file_count = len(result.changed_files)
                was_success = verification.success
                return CommitResult(
                    sha="test123",
                    message=f"Changed {file_count} files, success={was_success}, time={e2e_time}s",
                )

        committer = TestCommit()
        result = Result(changed_files=[Path("src/foo.py"), Path("src/bar.py")])
        verification = VerificationResult(
            success=True,
            verification_command="pytest",
            verification_output="passed",
            verification_time=1.0,
        )

        commit_result = committer.create(
            result=result,
            verification=verification,
            e2e_time=5.5,
        )

        assert "2 files" in commit_result.message
        assert "success=True" in commit_result.message
        assert "time=5.5s" in commit_result.message

    def test_create_returns_commit_result(self):
        """create() should return a CommitResult."""

        class TestCommit(Commit):
            def create(
                self,
                *,
                result: Result,
                verification: VerificationResult,
                e2e_time: float,
            ) -> CommitResult:
                return CommitResult(
                    sha="deadbeef",
                    message="🔴 Add failing test for login",
                )

        committer = TestCommit()
        result = Result(changed_files=[])
        verification = VerificationResult(
            success=True,
            verification_command="check",
            verification_output="ok",
            verification_time=0.1,
        )

        commit_result = committer.create(
            result=result,
            verification=verification,
            e2e_time=10.0,
        )

        assert isinstance(commit_result, CommitResult)
        assert commit_result.sha == "deadbeef"
        assert "🔴" in commit_result.message
