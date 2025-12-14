"""Verification ABC and VerificationResult dataclass.

This module provides the abstract base class for step verification and
the dataclass for verification results. Each step type has a corresponding
Verification subclass that validates the work before committing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from jiro.results.base import Result


@dataclass
class VerificationResult:
    """Result of verification.

    Captures the outcome of running verification checks on a step's work.

    Attributes:
        success: Whether verification passed
        verification_command: The command/check that was run
        verification_output: Output from the verification
        verification_time: Time taken for verification in seconds
    """

    success: bool
    verification_command: str
    verification_output: str
    verification_time: float


class Verification(ABC):
    """Base class for step verification.

    Each step type has a corresponding Verification subclass that knows how to
    validate the work performed by the Command. Verification raises
    VerificationError on failure, which causes immediate HALT.
    """

    @abstractmethod
    def verify(self, *, result: Result) -> VerificationResult:
        """Verify the work performed by a step.

        Args:
            result: The result from the Command execution

        Returns:
            VerificationResult indicating success/failure and details

        Raises:
            VerificationError: If verification fails and work cannot proceed
        """
        ...
