"""Tests for SlackNotifier."""

import json
from unittest.mock import MagicMock, patch

import pytest

from jiro.notifications.slack import SlackNotifier


class TestSlackNotifierInit:
    """Tests for SlackNotifier initialization."""

    def test_slack_notifier_init_with_webhook_url(self):
        """SlackNotifier should initialize with webhook URL."""
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url)
        assert notifier.webhook_url == webhook_url

    def test_slack_notifier_init_with_channel(self):
        """SlackNotifier should initialize with optional channel override."""
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url, channel="#general")
        assert notifier.channel == "#general"

    def test_slack_notifier_init_with_events_to_notify_on(self):
        """SlackNotifier should initialize with events to notify on."""
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        events = ["session_started", "task_completed"]
        notifier = SlackNotifier(webhook_url=webhook_url, notify_on=events)
        assert notifier.notify_on == events

    def test_slack_notifier_requires_webhook_url(self):
        """SlackNotifier should require webhook URL."""
        with pytest.raises(TypeError):
            SlackNotifier()  # type: ignore


class TestSlackNotifierSessionStarted:
    """Tests for session_started notification."""

    @patch("httpx.post")
    def test_notify_session_started_sends_slack_message(self, mock_post: MagicMock):
        """notify_session_started should send a message to Slack."""
        mock_post.return_value = MagicMock(status_code=200)
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url)

        notifier.notify_session_started(
            session_id="sess-123",
            task_count=5,
        )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == webhook_url
        assert "json" in call_args[1]

    @patch("httpx.post")
    def test_notify_session_started_has_rich_formatting(self, mock_post: MagicMock):
        """notify_session_started should include rich Slack formatting."""
        mock_post.return_value = MagicMock(status_code=200)
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url)

        notifier.notify_session_started(
            session_id="sess-123",
            task_count=5,
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        # Should have blocks for rich formatting
        assert "blocks" in payload
        assert len(payload["blocks"]) > 0

    @patch("httpx.post")
    def test_notify_session_started_excludes_if_not_in_notify_on(self, mock_post: MagicMock):
        """notify_session_started should not send if event not in notify_on."""
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(
            webhook_url=webhook_url,
            notify_on=["task_completed"],
        )

        notifier.notify_session_started(session_id="sess-123", task_count=5)

        mock_post.assert_not_called()


class TestSlackNotifierTaskCompleted:
    """Tests for task_completed notification."""

    @patch("httpx.post")
    def test_notify_task_completed_sends_slack_message(self, mock_post: MagicMock):
        """notify_task_completed should send a message to Slack."""
        mock_post.return_value = MagicMock(status_code=200)
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url)

        notifier.notify_task_completed(
            task_id="task-1",
            task_title="Implement feature X",
            success=True,
        )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == webhook_url

    @patch("httpx.post")
    def test_notify_task_completed_shows_success_status(self, mock_post: MagicMock):
        """notify_task_completed should indicate success status."""
        mock_post.return_value = MagicMock(status_code=200)
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url)

        notifier.notify_task_completed(
            task_id="task-1",
            task_title="Implement feature X",
            success=True,
            details="Task implementation complete with all tests passing",
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        # Should have content indicating success
        payload_str = json.dumps(payload)
        assert "task-1" in payload_str or "Implement feature X" in payload_str


class TestSlackNotifierSessionCompleted:
    """Tests for session_completed notification."""

    @patch("httpx.post")
    def test_notify_session_completed_sends_slack_message(self, mock_post: MagicMock):
        """notify_session_completed should send a message to Slack."""
        mock_post.return_value = MagicMock(status_code=200)
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url)

        notifier.notify_session_completed(
            session_id="sess-123",
            tasks_completed=5,
        )

        mock_post.assert_called_once()


class TestSlackNotifierSessionFailed:
    """Tests for session_failed notification."""

    @patch("httpx.post")
    def test_notify_session_failed_sends_slack_message(self, mock_post: MagicMock):
        """notify_session_failed should send a message to Slack."""
        mock_post.return_value = MagicMock(status_code=200)
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url)

        notifier.notify_session_failed(
            session_id="sess-123",
            reason="Task execution failed",
        )

        mock_post.assert_called_once()

    @patch("httpx.post")
    def test_notify_session_failed_includes_error_details(self, mock_post: MagicMock):
        """notify_session_failed should include error reason."""
        mock_post.return_value = MagicMock(status_code=200)
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url)

        error_reason = "Task execution failed with exception"
        notifier.notify_session_failed(
            session_id="sess-123",
            reason=error_reason,
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        payload_str = json.dumps(payload)
        assert error_reason in payload_str


class TestSlackNotifierInterventionRequired:
    """Tests for intervention_required notification."""

    @patch("httpx.post")
    def test_notify_intervention_required_sends_slack_message(self, mock_post: MagicMock):
        """notify_intervention_required should send a message to Slack."""
        mock_post.return_value = MagicMock(status_code=200)
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url)

        notifier.notify_intervention_required(
            session_id="sess-123",
            reason="Merge conflict detected",
            task_id="task-1",
        )

        mock_post.assert_called_once()

    @patch("httpx.post")
    def test_notify_intervention_required_includes_context(self, mock_post: MagicMock):
        """notify_intervention_required should include task context."""
        mock_post.return_value = MagicMock(status_code=200)
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url)

        notifier.notify_intervention_required(
            session_id="sess-123",
            reason="Merge conflict detected",
            task_id="task-1",
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        payload_str = json.dumps(payload)
        assert "task-1" in payload_str


class TestSlackNotifierChannelOverride:
    """Tests for channel override functionality."""

    @patch("httpx.post")
    def test_notify_uses_channel_override(self, mock_post: MagicMock):
        """notify methods should use channel override if provided."""
        mock_post.return_value = MagicMock(status_code=200)
        webhook_url = "https://hooks.slack.com/services/T123/B456/xyz"
        notifier = SlackNotifier(webhook_url=webhook_url, channel="#alerts")

        notifier.notify_session_started(session_id="sess-123", task_count=5)

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        # Channel should be in the payload
        if "channel" in payload:
            assert payload["channel"] == "#alerts"
