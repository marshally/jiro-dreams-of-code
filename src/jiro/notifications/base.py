"""Base notifier protocol for session events."""

from abc import ABC, abstractmethod


class Notifier(ABC):
    """Abstract base class for notification handlers."""

    @abstractmethod
    def notify_session_started(
        self,
        session_id: str,
        task_count: int,
    ) -> None:
        """Notify that a session has started.

        Args:
            session_id: The unique session identifier.
            task_count: The number of tasks in the session.
        """

    @abstractmethod
    def notify_task_completed(
        self,
        task_id: str,
        task_title: str,
        success: bool,
        details: str | None = None,
    ) -> None:
        """Notify that a task has been completed.

        Args:
            task_id: The unique task identifier.
            task_title: The title of the task.
            success: Whether the task completed successfully.
            details: Optional additional details about the completion.
        """

    @abstractmethod
    def notify_session_completed(
        self,
        session_id: str,
        tasks_completed: int,
    ) -> None:
        """Notify that a session has been completed.

        Args:
            session_id: The unique session identifier.
            tasks_completed: The number of tasks completed in the session.
        """

    @abstractmethod
    def notify_session_failed(
        self,
        session_id: str,
        reason: str,
    ) -> None:
        """Notify that a session has failed or been halted.

        Args:
            session_id: The unique session identifier.
            reason: The reason the session failed or was halted.
        """

    @abstractmethod
    def notify_intervention_required(
        self,
        session_id: str,
        reason: str,
        task_id: str | None = None,
    ) -> None:
        """Notify that human intervention is required.

        Args:
            session_id: The unique session identifier.
            reason: The reason intervention is required.
            task_id: Optional task identifier if intervention relates to a specific task.
        """
