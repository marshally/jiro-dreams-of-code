"""TDD sequence enforcement for strict Red→Green→Refactor ordering.

This module tracks the TDD phase sequence to ensure steps follow the required
Red→Green→Refactor order. Each task can only have one active TDD sequence at a time.
"""

from dataclasses import dataclass, field
from enum import StrEnum

import structlog

from jiro.steps.types import StepType

logger = structlog.get_logger()


class TddPhase(StrEnum):
    """TDD phase in the sequence."""

    RED = "red"
    GREEN = "green"
    REFACTOR = "refactor"


@dataclass
class TddSequenceState:
    """Tracks the state of a TDD sequence for a task.

    Attributes:
        task_id: The task ID this sequence belongs to
        current_phase: Current phase (red, green, or refactor)
        red_commit: SHA of the red step commit
        green_commit: SHA of the green step commit
        refactor_commits: List of refactor step commits
        completed: Whether the sequence is complete
    """

    task_id: str
    current_phase: TddPhase = TddPhase.RED
    red_commit: str | None = None
    green_commit: str | None = None
    refactor_commits: list[str] = field(default_factory=list)
    completed: bool = False

    def can_execute_phase(self, phase: TddPhase) -> tuple[bool, str]:
        """Check if a phase can be executed in sequence.

        Args:
            phase: The TDD phase to check

        Returns:
            Tuple of (can_execute, error_message)
        """
        # If completed, no more phases allowed
        if self.completed:
            return False, f"TDD sequence for {self.task_id} is already completed"

        # Red must be first
        if phase == TddPhase.RED:
            if self.current_phase == TddPhase.RED:
                return True, ""
            else:
                return (
                    False,
                    f"Red phase already completed. Current phase: {self.current_phase}",
                )

        # Green must come after Red
        if phase == TddPhase.GREEN:
            if self.red_commit:
                return True, ""
            else:
                return (
                    False,
                    f"Green phase requires red phase to be completed first. "
                    f"Current phase: {self.current_phase}",
                )

        # Refactor must come after Green
        if phase == TddPhase.REFACTOR:
            if self.green_commit:
                return True, ""
            else:
                return (
                    False,
                    f"Refactor phase requires green phase to be completed first. "
                    f"Current phase: {self.current_phase}",
                )

        return False, f"Unknown phase: {phase}"

    def record_phase_completion(self, phase: TddPhase, commit_sha: str) -> None:
        """Record completion of a phase.

        Args:
            phase: The TDD phase that was completed
            commit_sha: The commit SHA for this phase

        Raises:
            ValueError: If phase cannot be recorded in current sequence state
        """
        if phase == TddPhase.RED:
            if self.red_commit:
                raise ValueError(f"Red phase already completed for {self.task_id}")
            self.red_commit = commit_sha
            self.current_phase = TddPhase.GREEN
            logger.info(
                "tdd_sequence_red_complete",
                task_id=self.task_id,
                commit_sha=commit_sha,
            )
        elif phase == TddPhase.GREEN:
            if self.green_commit:
                raise ValueError(f"Green phase already completed for {self.task_id}")
            self.green_commit = commit_sha
            self.current_phase = TddPhase.REFACTOR
            logger.info(
                "tdd_sequence_green_complete",
                task_id=self.task_id,
                commit_sha=commit_sha,
            )
        elif phase == TddPhase.REFACTOR:
            self.refactor_commits.append(commit_sha)
            logger.info(
                "tdd_sequence_refactor_complete",
                task_id=self.task_id,
                commit_sha=commit_sha,
                refactor_count=len(self.refactor_commits),
            )
        else:
            raise ValueError(f"Unknown phase: {phase}")

    def mark_complete(self) -> None:
        """Mark the sequence as completed."""
        self.completed = True
        logger.info(
            "tdd_sequence_complete",
            task_id=self.task_id,
            red_commit=self.red_commit,
            green_commit=self.green_commit,
            refactor_count=len(self.refactor_commits),
        )


class TddSequenceTracker:
    """Tracks TDD sequences for tasks.

    Maintains one active sequence per task. Enforces Red→Green→Refactor ordering.
    """

    def __init__(self) -> None:
        """Initialize the tracker."""
        self._sequences: dict[str, TddSequenceState] = {}

    def get_or_create_sequence(self, task_id: str) -> TddSequenceState:
        """Get or create a TDD sequence for a task.

        Args:
            task_id: The task ID

        Returns:
            The TddSequenceState for this task
        """
        if task_id not in self._sequences:
            self._sequences[task_id] = TddSequenceState(task_id=task_id)
            logger.info("tdd_sequence_created", task_id=task_id)
        return self._sequences[task_id]

    def validate_step_phase(self, task_id: str, step_type: StepType) -> tuple[bool, str]:
        """Validate that a step type can execute in sequence.

        Args:
            task_id: The task ID
            step_type: The step type to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Map step types to TDD phases
        phase_map = {
            StepType.TDD_RED: TddPhase.RED,
            StepType.TDD_GREEN: TddPhase.GREEN,
            StepType.TDD_REFACTOR: TddPhase.REFACTOR,
        }

        if step_type not in phase_map:
            # Non-TDD steps are always valid
            return True, ""

        phase = phase_map[step_type]
        sequence = self.get_or_create_sequence(task_id)
        can_execute, error_msg = sequence.can_execute_phase(phase)

        if not can_execute:
            logger.warning(
                "tdd_sequence_validation_failed",
                task_id=task_id,
                step_type=step_type,
                phase=phase,
                error=error_msg,
            )

        return can_execute, error_msg

    def record_step_completion(self, task_id: str, step_type: StepType, commit_sha: str) -> None:
        """Record completion of a step.

        Args:
            task_id: The task ID
            step_type: The step type that was completed
            commit_sha: The commit SHA

        Raises:
            ValueError: If step cannot be recorded
        """
        # Map step types to TDD phases
        phase_map = {
            StepType.TDD_RED: TddPhase.RED,
            StepType.TDD_GREEN: TddPhase.GREEN,
            StepType.TDD_REFACTOR: TddPhase.REFACTOR,
        }

        if step_type not in phase_map:
            # Non-TDD steps don't affect sequence
            return

        phase = phase_map[step_type]
        sequence = self.get_or_create_sequence(task_id)
        sequence.record_phase_completion(phase, commit_sha)
