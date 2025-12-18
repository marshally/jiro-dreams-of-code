"""Tests for EmailNotifier."""

from unittest.mock import MagicMock, patch

import pytest

from jiro.notifications.email import EmailNotifier


def create_mock_smtp():
    """Create a mock SMTP object that supports context manager."""
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)
    return mock_smtp


class TestEmailNotifierInit:
    """Tests for EmailNotifier initialization."""

    def test_email_notifier_init_with_required_params(self):
        """EmailNotifier should initialize with SMTP host, port, and recipients."""
        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )
        assert notifier.smtp_host == "smtp.example.com"
        assert notifier.smtp_port == 587
        assert notifier.sender_email == "bot@example.com"
        assert notifier.recipients == ["user@example.com"]

    def test_email_notifier_init_with_credentials(self):
        """EmailNotifier should initialize with optional SMTP credentials."""
        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
            smtp_username="user",
            smtp_password="pass",
        )
        assert notifier.smtp_username == "user"
        assert notifier.smtp_password == "pass"

    def test_email_notifier_init_with_multiple_recipients(self):
        """EmailNotifier should support multiple recipients."""
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=recipients,
        )
        assert notifier.recipients == recipients

    def test_email_notifier_requires_smtp_host(self):
        """EmailNotifier should require SMTP host."""
        with pytest.raises(TypeError):
            EmailNotifier(
                smtp_port=587,
                sender_email="bot@example.com",
                recipients=["user@example.com"],
            )  # type: ignore

    def test_email_notifier_requires_recipients(self):
        """EmailNotifier should require at least one recipient."""
        with pytest.raises(ValueError):
            EmailNotifier(
                smtp_host="smtp.example.com",
                smtp_port=587,
                sender_email="bot@example.com",
                recipients=[],
            )


class TestEmailNotifierSessionStarted:
    """Tests for session_started notification."""

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_session_started_sends_email(self, mock_smtp_class: MagicMock):
        """notify_session_started should send an email."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        notifier.notify_session_started(session_id="sess-123", task_count=5)

        # SMTP connection should be established
        mock_smtp_class.assert_called_once_with("smtp.example.com", 587)
        # Email should be sent
        mock_smtp.sendmail.assert_called_once()

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_session_started_has_html_content(self, mock_smtp_class: MagicMock):
        """notify_session_started should include HTML formatted email."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        notifier.notify_session_started(session_id="sess-123", task_count=5)

        # Get the email message that was sent
        call_args = mock_smtp.sendmail.call_args
        message = call_args[0][2]

        # Should contain HTML content
        assert "html" in message.lower() or "<" in message

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_session_started_excludes_if_not_in_notify_on(self, mock_smtp_class: MagicMock):
        """notify_session_started should not send if event not in notify_on."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
            notify_on=["task_completed"],
        )

        notifier.notify_session_started(session_id="sess-123", task_count=5)

        mock_smtp.sendmail.assert_not_called()


class TestEmailNotifierTaskCompleted:
    """Tests for task_completed notification."""

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_task_completed_sends_email(self, mock_smtp_class: MagicMock):
        """notify_task_completed should send an email."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        notifier.notify_task_completed(
            task_id="task-1",
            task_title="Implement feature X",
            success=True,
        )

        mock_smtp.sendmail.assert_called_once()

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_task_completed_shows_success_status(self, mock_smtp_class: MagicMock):
        """notify_task_completed should indicate success status."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        notifier.notify_task_completed(
            task_id="task-1",
            task_title="Implement feature X",
            success=True,
            details="Task implementation complete with all tests passing",
        )

        call_args = mock_smtp.sendmail.call_args
        message = call_args[0][2]

        # Should contain task information
        assert "task-1" in message or "Implement feature X" in message


class TestEmailNotifierSessionCompleted:
    """Tests for session_completed notification."""

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_session_completed_sends_email(self, mock_smtp_class: MagicMock):
        """notify_session_completed should send an email."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        notifier.notify_session_completed(session_id="sess-123", tasks_completed=5)

        mock_smtp.sendmail.assert_called_once()


class TestEmailNotifierSessionFailed:
    """Tests for session_failed notification."""

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_session_failed_sends_email(self, mock_smtp_class: MagicMock):
        """notify_session_failed should send an email."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        notifier.notify_session_failed(
            session_id="sess-123",
            reason="Task execution failed",
        )

        mock_smtp.sendmail.assert_called_once()

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_session_failed_includes_error_details(self, mock_smtp_class: MagicMock):
        """notify_session_failed should include error reason."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        error_reason = "Task execution failed with exception"
        notifier.notify_session_failed(
            session_id="sess-123",
            reason=error_reason,
        )

        call_args = mock_smtp.sendmail.call_args
        message = call_args[0][2]
        assert error_reason in message


class TestEmailNotifierInterventionRequired:
    """Tests for intervention_required notification."""

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_intervention_required_sends_email(self, mock_smtp_class: MagicMock):
        """notify_intervention_required should send an email."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        notifier.notify_intervention_required(
            session_id="sess-123",
            reason="Merge conflict detected",
            task_id="task-1",
        )

        mock_smtp.sendmail.assert_called_once()

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_intervention_required_includes_context(self, mock_smtp_class: MagicMock):
        """notify_intervention_required should include task context."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        notifier.notify_intervention_required(
            session_id="sess-123",
            reason="Merge conflict detected",
            task_id="task-1",
        )

        call_args = mock_smtp.sendmail.call_args
        message = call_args[0][2]
        assert "task-1" in message


class TestEmailNotifierMultipleRecipients:
    """Tests for multiple recipients functionality."""

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_sends_to_all_recipients(self, mock_smtp_class: MagicMock):
        """notify methods should send to all recipients."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=recipients,
        )

        notifier.notify_session_started(session_id="sess-123", task_count=5)

        # Should send to all recipients
        call_args = mock_smtp.sendmail.call_args
        sent_to = call_args[0][1]
        assert sent_to == recipients


class TestEmailNotifierCredentials:
    """Tests for SMTP credentials."""

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_uses_smtp_login_when_credentials_provided(self, mock_smtp_class: MagicMock):
        """notify methods should login with credentials if provided."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
            smtp_username="testuser",
            smtp_password="testpass",
        )

        notifier.notify_session_started(session_id="sess-123", task_count=5)

        # Should call login with credentials
        mock_smtp.login.assert_called_once_with("testuser", "testpass")

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_skips_login_when_no_credentials(self, mock_smtp_class: MagicMock):
        """notify methods should not login if no credentials provided."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        notifier.notify_session_started(session_id="sess-123", task_count=5)

        # Should not call login
        mock_smtp.login.assert_not_called()


class TestEmailNotifierNotifyOnFilter:
    """Tests for notify_on event filtering."""

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_on_filters_events(self, mock_smtp_class: MagicMock):
        """notify methods should filter events based on notify_on."""
        mock_smtp = create_mock_smtp()
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
            notify_on=["session_completed", "session_failed"],
        )

        # Should not notify for session_started
        notifier.notify_session_started(session_id="sess-123", task_count=5)
        assert mock_smtp.sendmail.call_count == 0

        # Should notify for session_completed
        notifier.notify_session_completed(session_id="sess-123", tasks_completed=5)
        assert mock_smtp.sendmail.call_count == 1

        # Should not notify for task_completed
        notifier.notify_task_completed(
            task_id="task-1",
            task_title="Test",
            success=True,
        )
        assert mock_smtp.sendmail.call_count == 1

        # Should notify for session_failed
        notifier.notify_session_failed(session_id="sess-123", reason="Test")
        assert mock_smtp.sendmail.call_count == 2


class TestEmailNotifierErrorHandling:
    """Tests for error handling."""

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_handles_smtp_error_gracefully(self, mock_smtp_class: MagicMock):
        """notify methods should handle SMTP errors gracefully."""
        mock_smtp = create_mock_smtp()
        mock_smtp.sendmail.side_effect = Exception("SMTP error")
        mock_smtp_class.return_value = mock_smtp

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        # Should not raise an exception
        notifier.notify_session_started(session_id="sess-123", task_count=5)

    @patch("jiro.notifications.email.smtplib.SMTP")
    def test_notify_handles_connection_error_gracefully(self, mock_smtp_class: MagicMock):
        """notify methods should handle connection errors gracefully."""
        mock_smtp_class.side_effect = Exception("Connection failed")

        notifier = EmailNotifier(
            smtp_host="smtp.example.com",
            smtp_port=587,
            sender_email="bot@example.com",
            recipients=["user@example.com"],
        )

        # Should not raise an exception
        notifier.notify_session_started(session_id="sess-123", task_count=5)
