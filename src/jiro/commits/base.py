"""Commit ABC and CommitResult dataclass.

This module provides the abstract base class for creating strongly typed
commits and the dataclass for commit results. Each step type has a
corresponding Commit subclass that handles storing metadata and creating
the git commit.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from jiro.results.base import Result
from jiro.verifications.base import VerificationResult


@dataclass
class CommitResult:
    """Result of commit creation.

    Captures the outcome of creating a git commit for a step.

    Attributes:
        sha: The git commit SHA
        message: The rendered commit message
    """

    sha: str
    message: str


class Commit(ABC):
    """Base class for creating strongly typed commits.

    Each step type has a corresponding Commit subclass that knows how to:
    - Store metadata in the database
    - Render the commit message template
    - Create the git commit with appropriate files
    """

    @abstractmethod
    def create(
        self,
        *,
        result: Result,
        verification: VerificationResult,
        e2e_time: float,
    ) -> CommitResult:
        """Store metadata in DB, render template, create git commit.

        Args:
            result: The result from the Command execution
            verification: The result from verification
            e2e_time: Total end-to-end time for the step in seconds

        Returns:
            CommitResult with the commit SHA and rendered message
        """
        ...
