"""Email notifier implementation."""

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

from jiro.notifications.base import Notifier

logger = structlog.get_logger()


class EmailNotifier(Notifier):
    """Send notifications via email."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int = 587,
        sender_email: str | None = None,
        recipients: list[str] | None = None,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
        notify_on: list[str] | None = None,
    ) -> None:
        """Initialize EmailNotifier.

        Args:
            smtp_host: The SMTP server hostname.
            smtp_port: The SMTP server port (default: 587 for TLS).
            sender_email: The email address to send from.
            recipients: List of recipient email addresses.
            smtp_username: Optional SMTP authentication username.
            smtp_password: Optional SMTP authentication password.
            notify_on: Optional list of events to notify on. If not provided,
                      all events are notified.

        Raises:
            ValueError: If recipients list is empty.
        """
        if not recipients:
            raise ValueError("At least one recipient email address is required")

        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email or "jiro@localhost"
        self.recipients = recipients
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
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

    def _send_email(self, subject: str, html_body: str) -> bool:
        """Send an email message.

        Args:
            subject: The email subject line.
            html_body: The HTML email body.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = ", ".join(self.recipients)

            # Attach HTML version
            html_part = MIMEText(html_body, "html")
            msg.attach(html_part)

            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.sendmail(
                    self.sender_email,
                    self.recipients,
                    msg.as_string(),
                )

            logger.debug("email_sent", subject=subject, recipients=self.recipients)
            return True

        except Exception as e:
            logger.error(
                "email_send_error",
                subject=subject,
                error=str(e),
            )
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

        subject = f"Session Started: {session_id}"
        html_body = self._build_session_started_html(session_id, task_count)
        self._send_email(subject, html_body)

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

        status_text = "Completed" if success else "Failed"
        subject = f"Task {status_text}: {task_title}"
        html_body = self._build_task_completed_html(
            task_id,
            task_title,
            success,
            details,
        )
        self._send_email(subject, html_body)

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

        subject = f"Session Completed: {session_id}"
        html_body = self._build_session_completed_html(session_id, tasks_completed)
        self._send_email(subject, html_body)

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

        subject = f"Session Failed: {session_id}"
        html_body = self._build_session_failed_html(session_id, reason)
        self._send_email(subject, html_body)

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

        subject = f"Intervention Required: {session_id}"
        html_body = self._build_intervention_required_html(
            session_id,
            reason,
            task_id,
        )
        self._send_email(subject, html_body)

    def _build_session_started_html(
        self,
        session_id: str,
        task_count: int,
    ) -> str:
        """Build an HTML email body for session started event.

        Args:
            session_id: The session identifier.
            task_count: The number of tasks.

        Returns:
            HTML formatted email body.
        """
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #4CAF50;">Session Started</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Session ID:</td>
                            <td style="padding: 8px;">{session_id}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Tasks:</td>
                            <td style="padding: 8px;">{task_count}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Started:</td>
                            <td style="padding: 8px;">{datetime.now().isoformat()}</td>
                        </tr>
                    </table>
                </div>
            </body>
        </html>
        """

    def _build_task_completed_html(
        self,
        task_id: str,
        task_title: str,
        success: bool,
        details: str | None = None,
    ) -> str:
        """Build an HTML email body for task completed event.

        Args:
            task_id: The task identifier.
            task_title: The task title.
            success: Whether the task succeeded.
            details: Optional details.

        Returns:
            HTML formatted email body.
        """
        status_emoji = "✓" if success else "✗"
        status_text = "Completed" if success else "Failed"
        status_color = "#4CAF50" if success else "#f44336"

        details_html = ""
        if details:
            details_html = f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 8px; font-weight: bold;">Details:</td>
                <td style="padding: 8px;">{details}</td>
            </tr>
            """

        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: {status_color};">Task {status_text}</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Task ID:</td>
                            <td style="padding: 8px;">{task_id}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Title:</td>
                            <td style="padding: 8px;">{task_title}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">{status_emoji} Status:</td>
                            <td style="padding: 8px; color: {status_color};">{status_text}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Completed:</td>
                            <td style="padding: 8px;">{datetime.now().isoformat()}</td>
                        </tr>
                        {details_html}
                    </table>
                </div>
            </body>
        </html>
        """

    def _build_session_completed_html(
        self,
        session_id: str,
        tasks_completed: int,
    ) -> str:
        """Build an HTML email body for session completed event.

        Args:
            session_id: The session identifier.
            tasks_completed: The number of tasks completed.

        Returns:
            HTML formatted email body.
        """
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #4CAF50;">Session Completed</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Session ID:</td>
                            <td style="padding: 8px;">{session_id}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Tasks Completed:</td>
                            <td style="padding: 8px;">{tasks_completed}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Completed:</td>
                            <td style="padding: 8px;">{datetime.now().isoformat()}</td>
                        </tr>
                    </table>
                </div>
            </body>
        </html>
        """

    def _build_session_failed_html(
        self,
        session_id: str,
        reason: str,
    ) -> str:
        """Build an HTML email body for session failed event.

        Args:
            session_id: The session identifier.
            reason: The failure reason.

        Returns:
            HTML formatted email body.
        """
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #f44336;">Session Failed</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Session ID:</td>
                            <td style="padding: 8px;">{session_id}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Reason:</td>
                            <td style="padding: 8px;">{reason}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Failed:</td>
                            <td style="padding: 8px;">{datetime.now().isoformat()}</td>
                        </tr>
                    </table>
                </div>
            </body>
        </html>
        """

    def _build_intervention_required_html(
        self,
        session_id: str,
        reason: str,
        task_id: str | None = None,
    ) -> str:
        """Build an HTML email body for intervention required event.

        Args:
            session_id: The session identifier.
            reason: The reason intervention is required.
            task_id: Optional task identifier.

        Returns:
            HTML formatted email body.
        """
        task_html = ""
        if task_id:
            task_html = f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 8px; font-weight: bold;">Task ID:</td>
                <td style="padding: 8px;">{task_id}</td>
            </tr>
            """

        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #ff9800;">Human Intervention Required</h2>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Session ID:</td>
                            <td style="padding: 8px;">{session_id}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 8px; font-weight: bold;">Reason:</td>
                            <td style="padding: 8px;">{reason}</td>
                        </tr>
                        {task_html}
                    </table>
                </div>
            </body>
        </html>
        """
