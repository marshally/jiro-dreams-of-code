"""Step execution logging infrastructure.

This module provides structured logging for step execution with dual output:
- Console output: human-readable, with timing information
- File output: structured JSON for aggregation and analysis

Logging is integrated with the existing jiro logging infrastructure and provides
timing tracking for each phase (command, verify, commit).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

from jiro.core.logging import set_context_var
from jiro.core.paths import get_logs_dir
from jiro.steps.types import StepType

if TYPE_CHECKING:
    from jiro.commits.base import CommitResult
    from jiro.results.base import Result
    from jiro.verifications.base import VerificationResult


@dataclass
class PhaseLog:
    """Log entry for a single phase (command, verify, or commit)."""

    phase: str  # "command", "verify", or "commit"
    event: str  # "start", "success", or "error"
    timestamp: str
    duration_s: float | None = None
    details: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def as_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.as_dict(), default=str)


@dataclass
class StepLog:
    """Log entry for a complete step execution."""

    step_type: str
    event: str  # "start", "success", or "error"
    timestamp: str
    duration_s: float | None = None
    commit_sha: str | None = None
    details: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def as_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.as_dict(), default=str)


class StepLogger:
    """Logger for step execution with dual output (console + JSON file).

    Provides structured logging for each phase of step execution:
    - Step start/end with total duration
    - Command phase with subagent metrics
    - Verification phase with result
    - Commit phase with git SHA

    Output is written to:
    - Console: human-readable format with timing
    - File: structured JSON for analysis and aggregation
    """

    def __init__(self, step_type: StepType, project_name: str = "jiro") -> None:
        """Initialize the step logger.

        Args:
            step_type: The type of step being executed
            project_name: The project name for log file location
        """
        self.step_type = step_type
        self.project_name = project_name
        self.logger = structlog.get_logger()

        # Get log file path
        logs_dir = get_logs_dir(
            project_root=Path.cwd(),
            stealth=True,
            project_name=project_name,
        )
        logs_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = logs_dir / f"steps-{today}.jsonl"

        # Set context for this step
        set_context_var("step_type", str(step_type))

    def log_step_start(self) -> None:
        """Log the start of step execution."""
        timestamp = datetime.now().isoformat()
        log = StepLog(
            step_type=str(self.step_type),
            event="start",
            timestamp=timestamp,
        )

        # Console output
        self.logger.info(
            f"Starting step: {self.step_type}",
            step_event="step_start",
            step_type=str(self.step_type),
        )

        # File output
        self._write_json_log(log)

    def log_command_start(self) -> None:
        """Log the start of command execution."""
        timestamp = datetime.now().isoformat()
        phase_log = PhaseLog(
            phase="command",
            event="start",
            timestamp=timestamp,
        )

        self.logger.info(
            "Command: spawning subagent",
            phase_event="command_start",
            phase="command",
        )

        self._write_json_log(phase_log)

    def log_command_success(
        self,
        duration: float,
        result: Result,
        subagent_metrics: dict[str, Any] | None = None,
    ) -> None:
        """Log successful command execution.

        Args:
            duration: Time taken for command execution in seconds
            result: The result object from the command
            subagent_metrics: Optional metrics from the subagent
        """
        timestamp = datetime.now().isoformat()
        details: dict[str, Any] = {
            "changed_files": [str(f) for f in result.changed_files],
        }
        if subagent_metrics:
            details["subagent"] = subagent_metrics

        phase_log = PhaseLog(
            phase="command",
            event="success",
            timestamp=timestamp,
            duration_s=duration,
            details=details,
        )

        # Format duration for display
        duration_str = self._format_duration(duration)
        metrics_str = ""
        if subagent_metrics:
            tokens_in = subagent_metrics.get("tokens_in", 0)
            tokens_out = subagent_metrics.get("tokens_out", 0)
            metrics_str = f" ({tokens_in:,} tokens in, {tokens_out:,} out)"

        self.logger.info(
            f"Command: complete ({duration_str}{metrics_str})",
            phase_event="command_success",
            phase="command",
            duration_s=duration,
        )

        self._write_json_log(phase_log)

    def log_command_error(
        self,
        duration: float,
        error: Exception,
    ) -> None:
        """Log command execution error.

        Args:
            duration: Time taken before failure
            error: The exception that occurred
        """
        timestamp = datetime.now().isoformat()
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        phase_log = PhaseLog(
            phase="command",
            event="error",
            timestamp=timestamp,
            duration_s=duration,
            details=details,
        )

        duration_str = self._format_duration(duration)
        self.logger.error(
            f"Command: failed ({duration_str}) - {type(error).__name__}",
            phase_event="command_error",
            phase="command",
            duration_s=duration,
        )

        self._write_json_log(phase_log)

    def log_verify_start(self) -> None:
        """Log the start of verification."""
        timestamp = datetime.now().isoformat()
        phase_log = PhaseLog(
            phase="verify",
            event="start",
            timestamp=timestamp,
        )

        self.logger.info(
            "Verification: checking changes",
            phase_event="verify_start",
            phase="verify",
        )

        self._write_json_log(phase_log)

    def log_verify_success(
        self,
        duration: float,
        verification_result: VerificationResult,
    ) -> None:
        """Log successful verification.

        Args:
            duration: Time taken for verification in seconds
            verification_result: The verification result object
        """
        timestamp = datetime.now().isoformat()
        details = {
            "verification_command": verification_result.verification_command,
            "verification_time": verification_result.verification_time,
        }

        phase_log = PhaseLog(
            phase="verify",
            event="success",
            timestamp=timestamp,
            duration_s=duration,
            details=details,
        )

        duration_str = self._format_duration(duration)
        self.logger.info(
            f"Verification: passed ({duration_str})",
            phase_event="verify_success",
            phase="verify",
            duration_s=duration,
        )

        self._write_json_log(phase_log)

    def log_verify_error(
        self,
        duration: float,
        error: Exception,
    ) -> None:
        """Log verification error.

        Args:
            duration: Time taken before failure
            error: The exception that occurred
        """
        timestamp = datetime.now().isoformat()
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        phase_log = PhaseLog(
            phase="verify",
            event="error",
            timestamp=timestamp,
            duration_s=duration,
            details=details,
        )

        duration_str = self._format_duration(duration)
        self.logger.error(
            f"Verification: failed ({duration_str}) - {type(error).__name__}",
            phase_event="verify_error",
            phase="verify",
            duration_s=duration,
        )

        self._write_json_log(phase_log)

    def log_commit_start(self, message_preview: str | None = None) -> None:
        """Log the start of commit creation.

        Args:
            message_preview: Optional preview of the commit message
        """
        timestamp = datetime.now().isoformat()
        details = None
        if message_preview:
            details = {"message_preview": message_preview}

        phase_log = PhaseLog(
            phase="commit",
            event="start",
            timestamp=timestamp,
            details=details,
        )

        msg = "Commit: creating"
        if message_preview:
            # Show just the first line of the message
            first_line = message_preview.split("\n")[0]
            msg = f'Commit: creating with message "{first_line}"'

        self.logger.info(
            msg,
            phase_event="commit_start",
            phase="commit",
        )

        self._write_json_log(phase_log)

    def log_commit_success(
        self,
        duration: float,
        commit_result: CommitResult,
    ) -> None:
        """Log successful commit creation.

        Args:
            duration: Time taken for commit creation in seconds
            commit_result: The commit result object
        """
        timestamp = datetime.now().isoformat()
        details = {
            "sha": commit_result.sha,
            "message": commit_result.message,
        }

        phase_log = PhaseLog(
            phase="commit",
            event="success",
            timestamp=timestamp,
            duration_s=duration,
            details=details,
        )

        duration_str = self._format_duration(duration)
        sha_short = commit_result.sha[:7]
        self.logger.info(
            f"Commit: success (sha: {sha_short}) ({duration_str})",
            phase_event="commit_success",
            phase="commit",
            duration_s=duration,
            sha=commit_result.sha,
        )

        self._write_json_log(phase_log)

    def log_commit_error(
        self,
        duration: float,
        error: Exception,
    ) -> None:
        """Log commit creation error.

        Args:
            duration: Time taken before failure
            error: The exception that occurred
        """
        timestamp = datetime.now().isoformat()
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        phase_log = PhaseLog(
            phase="commit",
            event="error",
            timestamp=timestamp,
            duration_s=duration,
            details=details,
        )

        duration_str = self._format_duration(duration)
        self.logger.error(
            f"Commit: failed ({duration_str}) - {type(error).__name__}",
            phase_event="commit_error",
            phase="commit",
            duration_s=duration,
        )

        self._write_json_log(phase_log)

    def log_step_complete(self, duration: float, commit_sha: str) -> None:
        """Log the completion of step execution.

        Args:
            duration: Total time for the step in seconds
            commit_sha: The git commit SHA
        """
        timestamp = datetime.now().isoformat()
        log = StepLog(
            step_type=str(self.step_type),
            event="success",
            timestamp=timestamp,
            duration_s=duration,
            commit_sha=commit_sha,
        )

        duration_str = self._format_duration(duration)
        sha_short = commit_sha[:7]
        self.logger.info(
            f"Step complete: {self.step_type} ({duration_str}) [sha: {sha_short}]",
            step_event="step_complete",
            step_type=str(self.step_type),
            duration_s=duration,
            sha=commit_sha,
        )

        self._write_json_log(log)

    def log_step_error(self, duration: float, error: Exception) -> None:
        """Log step execution error.

        Args:
            duration: Time taken before failure
            error: The exception that occurred
        """
        timestamp = datetime.now().isoformat()
        log = StepLog(
            step_type=str(self.step_type),
            event="error",
            timestamp=timestamp,
            duration_s=duration,
            details={
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
        )

        duration_str = self._format_duration(duration)
        self.logger.error(
            f"Step failed: {self.step_type} ({duration_str}) - {type(error).__name__}",
            step_event="step_error",
            step_type=str(self.step_type),
            duration_s=duration,
        )

        self._write_json_log(log)

    def _write_json_log(self, log_entry: PhaseLog | StepLog) -> None:
        """Write log entry to JSON file.

        Args:
            log_entry: The log entry to write
        """
        try:
            with open(self.log_file, "a") as f:
                json.dump(log_entry.as_dict(), f)
                f.write("\n")
        except Exception as e:
            # Don't fail step execution if logging fails
            self.logger.exception(
                "Failed to write JSON log",
                exc_info=e,
                log_file=str(self.log_file),
            )

    @staticmethod
    def _format_duration(duration: float) -> str:
        """Format duration in seconds as a human-readable string.

        Args:
            duration: Duration in seconds

        Returns:
            Formatted duration string (e.g., "1.5s", "2m 30s")
        """
        if duration < 60:
            return f"{duration:.1f}s"

        minutes = int(duration // 60)
        seconds = duration % 60
        return f"{minutes}m {seconds:.0f}s"
