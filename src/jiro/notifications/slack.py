"""Slack notifier implementation."""

from datetime import datetime
from typing import Any

import httpx  # type: ignore[import-not-found]
import structlog

from jiro.notifications.base import Notifier

logger = structlog.get_logger()


class SlackNotifier(Notifier):
    """Send notifications to Slack channels."""

    def __init__(
        self,
        webhook_url: str,
        channel: str | None = None,
        notify_on: list[str] | None = None,
    ) -> None:
        """Initialize SlackNotifier.

        Args:
            webhook_url: The Slack webhook URL for sending messages.
            channel: Optional channel override (e.g., "#alerts").
            notify_on: Optional list of events to notify on. If not provided,
                      all events are notified.
        """
        self.webhook_url = webhook_url
        self.channel = channel
        self.notify_on = notify_on or [
            "session_started",
            "task_completed",
            "session_completed",
            "session_failed",
            "intervention_required",
        ]

    def _should_notify(self, event_type: str) -> bool:
        """Check if this event type should be notified.

        Args:
            event_type: The type of event.

        Returns:
            True if the event should be notified, False otherwise.
        """
        return event_type in self.notify_on

    def _send_slack_message(self, payload: dict[str, Any]) -> bool:
        """Send a message to Slack.

        Args:
            payload: The Slack message payload.

        Returns:
            True if the message was sent successfully, False otherwise.
        """
        try:
            response = httpx.post(
                self.webhook_url,
                json=payload,
                timeout=10.0,
            )
            if response.status_code == 200:
                logger.debug("slack_message_sent")
                return True
            else:
                logger.warning(
                    "slack_message_failed",
                    status_code=response.status_code,
                    response_text=response.text,
                )
                return False
        except Exception as e:
            logger.error("slack_message_error", error=str(e))
            return False

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
        if not self._should_notify("session_started"):
            return

        payload = self._build_session_started_payload(session_id, task_count)
        self._send_slack_message(payload)

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
        if not self._should_notify("task_completed"):
            return

        payload = self._build_task_completed_payload(
            task_id,
            task_title,
            success,
            details,
        )
        self._send_slack_message(payload)

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
        if not self._should_notify("session_completed"):
            return

        payload = self._build_session_completed_payload(session_id, tasks_completed)
        self._send_slack_message(payload)

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
        if not self._should_notify("session_failed"):
            return

        payload = self._build_session_failed_payload(session_id, reason)
        self._send_slack_message(payload)

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
        if not self._should_notify("intervention_required"):
            return

        payload = self._build_intervention_required_payload(
            session_id,
            reason,
            task_id,
        )
        self._send_slack_message(payload)

    def _build_session_started_payload(
        self,
        session_id: str,
        task_count: int,
    ) -> dict[str, Any]:
        """Build a Slack message payload for session started event.

        Args:
            session_id: The session identifier.
            task_count: The number of tasks.

        Returns:
            A Slack message payload with rich formatting.
        """
        payload: dict[str, Any] = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Session Started",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Session ID:*\n{session_id}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Tasks:*\n{task_count}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Started:*\n{datetime.now().isoformat()}",
                        },
                    ],
                },
            ]
        }

        if self.channel:
            payload["channel"] = self.channel

        return payload

    def _build_task_completed_payload(
        self,
        task_id: str,
        task_title: str,
        success: bool,
        details: str | None = None,
    ) -> dict[str, Any]:
        """Build a Slack message payload for task completed event.

        Args:
            task_id: The task identifier.
            task_title: The task title.
            success: Whether the task succeeded.
            details: Optional details.

        Returns:
            A Slack message payload with rich formatting.
        """
        status_emoji = ":white_check_mark:" if success else ":x:"
        status_text = "Completed" if success else "Failed"

        payload: dict[str, Any] = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Task Completed",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Task ID:*\n{task_id}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Title:*\n{task_title}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"{status_emoji} *Status:*\n{status_text}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Completed:*\n{datetime.now().isoformat()}",
                        },
                    ],
                },
            ]
        }

        if details:
            payload["blocks"].append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Details:*\n{details}",
                    },
                }
            )

        if self.channel:
            payload["channel"] = self.channel

        return payload

    def _build_session_completed_payload(
        self,
        session_id: str,
        tasks_completed: int,
    ) -> dict[str, Any]:
        """Build a Slack message payload for session completed event.

        Args:
            session_id: The session identifier.
            tasks_completed: The number of tasks completed.

        Returns:
            A Slack message payload with rich formatting.
        """
        payload: dict[str, Any] = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":tada: Session Completed",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Session ID:*\n{session_id}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Tasks Completed:*\n{tasks_completed}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Completed:*\n{datetime.now().isoformat()}",
                        },
                    ],
                },
            ]
        }

        if self.channel:
            payload["channel"] = self.channel

        return payload

    def _build_session_failed_payload(
        self,
        session_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """Build a Slack message payload for session failed event.

        Args:
            session_id: The session identifier.
            reason: The failure reason.

        Returns:
            A Slack message payload with rich formatting.
        """
        payload: dict[str, Any] = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":warning: Session Failed",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Session ID:*\n{session_id}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Reason:*\n{reason}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Failed:*\n{datetime.now().isoformat()}",
                        },
                    ],
                },
            ]
        }

        if self.channel:
            payload["channel"] = self.channel

        return payload

    def _build_intervention_required_payload(
        self,
        session_id: str,
        reason: str,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        """Build a Slack message payload for intervention required event.

        Args:
            session_id: The session identifier.
            reason: The reason intervention is required.
            task_id: Optional task identifier.

        Returns:
            A Slack message payload with rich formatting.
        """
        payload: dict[str, Any] = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":raised_hand: Human Intervention Required",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Session ID:*\n{session_id}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Reason:*\n{reason}",
                        },
                    ],
                },
            ]
        }

        if task_id:
            payload["blocks"][1]["fields"].append(
                {
                    "type": "mrkdwn",
                    "text": f"*Task ID:*\n{task_id}",
                }
            )

        if self.channel:
            payload["channel"] = self.channel

        return payload
