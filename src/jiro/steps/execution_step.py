"""ExecutionStep orchestrator for strongly typed commits.

This module provides the ExecutionStep class that orchestrates the full
execution flow: Command → Verification → Commit for each step type.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from jiro.commits.base import CommitResult
from jiro.steps.discovery import discover_command, discover_commit, discover_verification
from jiro.steps.logging import StepLogger
from jiro.steps.types import PlanStep, StepType

if TYPE_CHECKING:
    from sqlite_utils import Database

    from jiro.commands.base import Command
    from jiro.commits.base import Commit
    from jiro.db.models import Session
    from jiro.trackers.interface import Task
    from jiro.verifications.base import Verification


class ExecutionStep:
    """Orchestrates Command → Verification → Commit for a step type.

    This class is the central orchestrator for executing a single step.
    It uses the discovery convention to find the appropriate Command,
    Verification, and Commit classes for the given step type.

    Attributes:
        step_type: The type of step being executed
        session: The current execution session
        db: Database connection for storing metadata
    """

    def __init__(
        self,
        step_type: StepType,
        session: Session,
        db: Database,
    ) -> None:
        """Initialize ExecutionStep.

        Args:
            step_type: The type of step to execute
            session: The current execution session
            db: Database connection for storing metadata
        """
        self.step_type = step_type
        self.session = session
        self.db = db

    @classmethod
    def for_type(
        cls,
        step_type: StepType,
        **context: object,
    ) -> ExecutionStep:
        """Factory method to create ExecutionStep for a step type.

        Args:
            step_type: The type of step to execute
            **context: Additional context (session, db, etc.)

        Returns:
            An ExecutionStep configured for the given step type
        """
        return cls(step_type, **context)  # type: ignore[arg-type]

    @property
    def command(self) -> Command:
        """Get the Command instance for this step type.

        Uses discover_command to dynamically load the appropriate class.

        Returns:
            The Command instance for this step type
        """
        return discover_command(self.step_type)

    @property
    def verify(self) -> Verification:
        """Get the Verification instance for this step type.

        Uses discover_verification to dynamically load the appropriate class.

        Returns:
            The Verification instance for this step type
        """
        return discover_verification(self.step_type)

    @property
    def commit(self) -> Commit:
        """Get the Commit instance for this step type.

        Uses discover_commit to dynamically load the appropriate class.

        Returns:
            The Commit instance for this step type
        """
        return discover_commit(self.step_type)

    async def execute(self, plan_step: PlanStep, task: Task) -> CommitResult:
        """Execute the full step: command → verify → commit.

        This method orchestrates the complete execution flow:
        1. Execute the command (spawns subagent, does work)
        2. Verify the work (raises exception on failure → HALT)
        3. Create the commit (stores in DB, renders template, git commit)

        Args:
            plan_step: The plan step containing context for execution
            task: The task being executed

        Returns:
            CommitResult with the commit SHA and rendered message

        Raises:
            VerificationError: If verification fails
        """
        start = time.monotonic()
        logger = StepLogger(self.step_type)

        try:
            logger.log_step_start()

            # 1. Execute (spawns subagent, does work)
            logger.log_command_start()
            command_start = time.monotonic()
            try:
                result = await self.command.execute(step=plan_step, task=task)
                command_duration = time.monotonic() - command_start
                logger.log_command_success(command_duration, result)
            except Exception as e:
                command_duration = time.monotonic() - command_start
                logger.log_command_error(command_duration, e)
                raise

            # 2. Verify (raises exception on failure → HALT)
            logger.log_verify_start()
            verify_start = time.monotonic()
            try:
                verification = self.verify.verify(result=result)
                verify_duration = time.monotonic() - verify_start
                logger.log_verify_success(verify_duration, verification)
            except Exception as e:
                verify_duration = time.monotonic() - verify_start
                logger.log_verify_error(verify_duration, e)
                raise

            # 3. Commit (stores in DB, renders template, git commit)
            logger.log_commit_start()
            commit_start = time.monotonic()
            try:
                commit_result = self.commit.create(
                    result=result,
                    verification=verification,
                    e2e_time=time.monotonic() - start,
                )
                commit_duration = time.monotonic() - commit_start
                logger.log_commit_success(commit_duration, commit_result)

                # Log step completion
                total_duration = time.monotonic() - start
                logger.log_step_complete(total_duration, commit_result.sha)

                return commit_result
            except Exception as e:
                commit_duration = time.monotonic() - commit_start
                logger.log_commit_error(commit_duration, e)
                raise

        except Exception as e:
            # Log step error
            total_duration = time.monotonic() - start
            logger.log_step_error(total_duration, e)
            raise
