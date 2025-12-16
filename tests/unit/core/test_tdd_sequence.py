"""Tests for TDD sequence enforcement.

Tests the TDD sequence tracker to ensure strict Red→Green→Refactor ordering.
"""

import pytest

from jiro.core.tdd_sequence import TddPhase, TddSequenceState, TddSequenceTracker
from jiro.steps.types import StepType


class TestTddSequenceState:
    """Tests for TddSequenceState."""

    def test_can_execute_first_red_phase(self) -> None:
        """Test that red phase can be executed first."""
        state = TddSequenceState(task_id="task-1")
        can_execute, error = state.can_execute_phase(TddPhase.RED)
        assert can_execute is True
        assert error == ""

    def test_cannot_execute_green_before_red(self) -> None:
        """Test that green cannot execute before red."""
        state = TddSequenceState(task_id="task-1")
        can_execute, error = state.can_execute_phase(TddPhase.GREEN)
        assert can_execute is False
        assert "red phase to be completed first" in error

    def test_cannot_execute_refactor_before_green(self) -> None:
        """Test that refactor cannot execute before green."""
        state = TddSequenceState(task_id="task-1")
        can_execute, error = state.can_execute_phase(TddPhase.REFACTOR)
        assert can_execute is False
        assert "green phase to be completed first" in error

    def test_sequence_progression_red_to_green(self) -> None:
        """Test progression from red to green phase."""
        state = TddSequenceState(task_id="task-1")

        # Execute red
        can_execute, _ = state.can_execute_phase(TddPhase.RED)
        assert can_execute is True
        state.record_phase_completion(TddPhase.RED, "abc123")

        # Now green should be available
        can_execute, _ = state.can_execute_phase(TddPhase.GREEN)
        assert can_execute is True

    def test_sequence_progression_green_to_refactor(self) -> None:
        """Test progression from green to refactor phase."""
        state = TddSequenceState(task_id="task-1")

        # Complete red
        state.record_phase_completion(TddPhase.RED, "abc123")

        # Complete green
        can_execute, _ = state.can_execute_phase(TddPhase.GREEN)
        assert can_execute is True
        state.record_phase_completion(TddPhase.GREEN, "def456")

        # Now refactor should be available
        can_execute, _ = state.can_execute_phase(TddPhase.REFACTOR)
        assert can_execute is True

    def test_cannot_repeat_red_phase(self) -> None:
        """Test that red phase cannot be repeated."""
        state = TddSequenceState(task_id="task-1")
        state.record_phase_completion(TddPhase.RED, "abc123")

        # Try to execute red again
        with pytest.raises(ValueError, match="Red phase already completed"):
            state.record_phase_completion(TddPhase.RED, "def456")

    def test_cannot_repeat_green_phase(self) -> None:
        """Test that green phase cannot be repeated."""
        state = TddSequenceState(task_id="task-1")
        state.record_phase_completion(TddPhase.RED, "abc123")
        state.record_phase_completion(TddPhase.GREEN, "def456")

        # Try to execute green again
        with pytest.raises(ValueError, match="Green phase already completed"):
            state.record_phase_completion(TddPhase.GREEN, "ghi789")

    def test_multiple_refactor_phases_allowed(self) -> None:
        """Test that multiple refactor phases are allowed."""
        state = TddSequenceState(task_id="task-1")
        state.record_phase_completion(TddPhase.RED, "abc123")
        state.record_phase_completion(TddPhase.GREEN, "def456")

        # Multiple refactor phases should be allowed
        state.record_phase_completion(TddPhase.REFACTOR, "ghi789")
        state.record_phase_completion(TddPhase.REFACTOR, "jkl012")

        assert len(state.refactor_commits) == 2
        assert state.refactor_commits == ["ghi789", "jkl012"]

    def test_cannot_execute_after_complete(self) -> None:
        """Test that no phases can execute after marking complete."""
        state = TddSequenceState(task_id="task-1")
        state.record_phase_completion(TddPhase.RED, "abc123")
        state.record_phase_completion(TddPhase.GREEN, "def456")
        state.record_phase_completion(TddPhase.REFACTOR, "ghi789")
        state.mark_complete()

        # Cannot execute any phase after complete
        can_execute, error = state.can_execute_phase(TddPhase.REFACTOR)
        assert can_execute is False
        assert "already completed" in error

    def test_state_tracking_commits(self) -> None:
        """Test that state correctly tracks commit SHAs."""
        state = TddSequenceState(task_id="task-1")
        state.record_phase_completion(TddPhase.RED, "red123")
        state.record_phase_completion(TddPhase.GREEN, "green456")
        state.record_phase_completion(TddPhase.REFACTOR, "refactor789")

        assert state.red_commit == "red123"
        assert state.green_commit == "green456"
        assert state.refactor_commits == ["refactor789"]


class TestTddSequenceTracker:
    """Tests for TddSequenceTracker."""

    def test_get_or_create_sequence(self) -> None:
        """Test creating sequences for tasks."""
        tracker = TddSequenceTracker()

        seq1 = tracker.get_or_create_sequence("task-1")
        seq2 = tracker.get_or_create_sequence("task-1")

        # Should return the same instance
        assert seq1 is seq2
        assert seq1.task_id == "task-1"

    def test_separate_sequences_for_different_tasks(self) -> None:
        """Test that different tasks have separate sequences."""
        tracker = TddSequenceTracker()

        seq1 = tracker.get_or_create_sequence("task-1")
        seq2 = tracker.get_or_create_sequence("task-2")

        # Should be different instances
        assert seq1 is not seq2
        assert seq1.task_id == "task-1"
        assert seq2.task_id == "task-2"

    def test_validate_tdd_red_step(self) -> None:
        """Test validation of TDD red step."""
        tracker = TddSequenceTracker()

        is_valid, error = tracker.validate_step_phase("task-1", StepType.TDD_RED)
        assert is_valid is True
        assert error == ""

    def test_validate_tdd_green_before_red_fails(self) -> None:
        """Test that green validation fails before red."""
        tracker = TddSequenceTracker()

        is_valid, error = tracker.validate_step_phase("task-1", StepType.TDD_GREEN)
        assert is_valid is False
        assert "red phase" in error

    def test_validate_sequence_progression(self) -> None:
        """Test validating sequence progression."""
        tracker = TddSequenceTracker()

        # Red should be valid
        is_valid, _ = tracker.validate_step_phase("task-1", StepType.TDD_RED)
        assert is_valid is True

        # Record red completion
        tracker.record_step_completion("task-1", StepType.TDD_RED, "abc123")

        # Green should now be valid
        is_valid, _ = tracker.validate_step_phase("task-1", StepType.TDD_GREEN)
        assert is_valid is True

        # Record green completion
        tracker.record_step_completion("task-1", StepType.TDD_GREEN, "def456")

        # Refactor should now be valid
        is_valid, _ = tracker.validate_step_phase("task-1", StepType.TDD_REFACTOR)
        assert is_valid is True

    def test_non_tdd_steps_always_valid(self) -> None:
        """Test that non-TDD steps are always valid."""
        tracker = TddSequenceTracker()

        # Non-TDD steps should always be valid
        is_valid, error = tracker.validate_step_phase("task-1", StepType.BUG_RED)
        assert is_valid is True
        assert error == ""

        is_valid, error = tracker.validate_step_phase("task-1", StepType.DOCUMENTATION)
        assert is_valid is True
        assert error == ""

    def test_record_step_completion_non_tdd_noop(self) -> None:
        """Test that recording non-TDD steps is a no-op."""
        tracker = TddSequenceTracker()

        # Record non-TDD step (should not affect tracker)
        tracker.record_step_completion("task-1", StepType.DOCUMENTATION, "abc123")

        # Sequence should still be fresh (no commits recorded)
        seq = tracker.get_or_create_sequence("task-1")
        assert seq.red_commit is None
        assert seq.green_commit is None

    def test_multiple_tasks_independent_sequences(self) -> None:
        """Test that multiple tasks have independent sequences."""
        tracker = TddSequenceTracker()

        # Task 1: Complete red
        tracker.validate_step_phase("task-1", StepType.TDD_RED)
        tracker.record_step_completion("task-1", StepType.TDD_RED, "task1-red")

        # Task 2: Should fail on green (red not done)
        is_valid, _ = tracker.validate_step_phase("task-2", StepType.TDD_GREEN)
        assert is_valid is False

        # Task 2: Red should still be valid
        is_valid, _ = tracker.validate_step_phase("task-2", StepType.TDD_RED)
        assert is_valid is True
