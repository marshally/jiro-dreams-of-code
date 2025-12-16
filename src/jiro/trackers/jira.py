"""JiraTracker implementation using Jira REST API."""

import contextlib
from datetime import datetime

from jira import JIRA

from jiro.trackers.interface import Task, TaskStatus, TaskType


class JiraTracker:
    """Issue tracker implementation using Jira REST API.

    This implementation uses the python-jira library to interact with Jira
    and converts Jira issues to Task objects.
    Jira issues are mapped to the jiro Task model:
    - Jira issue key -> Task ID
    - Jira status -> Task status
    - Jira issue type -> Task type
    """

    # Type mappings from jiro task types to Jira issue types
    TYPE_JIRA_MAP: dict[TaskType, str] = {
        "bug": "Bug",
        "feature": "Story",
        "task": "Task",
        "epic": "Epic",
        "chore": "Task",
    }

    # Reverse mapping - prefer "task" for Task type
    REVERSE_TYPE_JIRA_MAP: dict[str, TaskType] = {
        "Bug": "bug",
        "Story": "feature",
        "Task": "task",
        "Epic": "epic",
    }

    # Status mappings from Jira statuses to jiro TaskStatus
    STATUS_JIRA_MAP: dict[TaskStatus, str] = {
        "open": "Open",
        "in_progress": "In Progress",
        "blocked": "Blocked",
        "closed": "Done",
    }

    REVERSE_STATUS_MAP: dict[str, TaskStatus] = {
        "Open": "open",
        "In Progress": "in_progress",
        "In Review": "in_progress",
        "In QA": "in_progress",
        "Blocked": "blocked",
        "On Hold": "blocked",
        "Done": "closed",
        "Closed": "closed",
        "Resolved": "closed",
        "Cancelled": "closed",
    }

    # Priority mapping from Jira to jiro (1-5, 1 is highest)
    # Jira typically uses: Highest=1, High=2, Medium=3, Low=4, Lowest=5
    PRIORITY_JIRA_MAP: dict[int, str] = {
        1: "Highest",
        2: "High",
        3: "Medium",
        4: "Low",
        5: "Lowest",
    }

    REVERSE_PRIORITY_MAP: dict[str, int] = {v: k for k, v in PRIORITY_JIRA_MAP.items()}

    def __init__(
        self,
        server_url: str,
        username: str | None = None,
        api_token: str | None = None,
        oauth_token: str | None = None,
    ):
        """Initialize the JiraTracker.

        Args:
            server_url: The Jira server URL (e.g., https://jira.example.com).
            username: Username for basic auth (used with api_token).
            api_token: API token for basic auth (used with username).
            oauth_token: OAuth token for authentication (alternative to basic auth).

        Raises:
            ValueError: If neither basic auth nor OAuth token is provided.
        """
        self.server_url = server_url
        self.username = username
        self.api_token = api_token
        self.oauth_token = oauth_token

        # Initialize Jira client
        if oauth_token:
            self.jira = JIRA(
                server=server_url,
                token_auth=oauth_token,
            )
        elif username and api_token:
            self.jira = JIRA(
                server=server_url,
                basic_auth=(username, api_token),
            )
        else:
            raise ValueError("Either oauth_token or (username, api_token) must be provided")

    def _parse_task(self, issue: object) -> Task:
        """Parse a task from a Jira issue object.

        Args:
            issue: A Jira Issue object.

        Returns:
            Task object.
        """
        # Extract issue key and fields
        issue_key: str = getattr(issue, "key", "")
        fields: object = getattr(issue, "fields", {})

        # Extract summary and description
        title: str = getattr(fields, "summary", "")
        description: str | None = getattr(fields, "description", None)

        # Parse status
        status_name: str = getattr(getattr(fields, "status", {}), "name", "Open")
        status: TaskStatus = self.REVERSE_STATUS_MAP.get(status_name, "open")

        # Parse issue type
        issue_type_name: str = getattr(getattr(fields, "issuetype", {}), "name", "Task")
        task_type: TaskType = self.REVERSE_TYPE_JIRA_MAP.get(issue_type_name, "task")

        # Parse priority - may be stored in custom field
        priority: int | None = None
        custom_priority = getattr(fields, "customfield_priority", None)
        if custom_priority:
            priority = int(custom_priority)
        else:
            priority_obj = getattr(fields, "priority", None)
            if priority_obj:
                priority_name = getattr(priority_obj, "name", None)
                priority = self.REVERSE_PRIORITY_MAP.get(priority_name) if priority_name else None

        # Parse timestamps
        created_at = self._parse_datetime(getattr(fields, "created", None))
        updated_at = self._parse_datetime(getattr(fields, "updated", None))
        closed_at = None

        # Check if issue is closed/done
        if status in ("closed", "blocked"):
            closed_at = updated_at

        return Task(
            id=issue_key,
            title=title,
            task_type=task_type,
            status=status,
            created_at=created_at or datetime.now(),
            description=description,
            priority=priority,
            updated_at=updated_at,
            closed_at=closed_at,
        )

    def _parse_datetime(self, timestamp: str | None) -> datetime | None:
        """Parse a Jira timestamp string to datetime.

        Jira uses ISO 8601 format with timezone info:
        2024-01-15T10:00:00.000-0500

        Args:
            timestamp: Jira timestamp string.

        Returns:
            Parsed datetime or None.
        """
        if not timestamp:
            return None

        try:
            # Remove the trailing .000 milliseconds and handle timezone
            # Jira format: 2024-01-15T10:00:00.000-0500
            # Python fromisoformat needs: 2024-01-15T10:00:00-05:00
            if "." in timestamp:
                # Split at milliseconds
                parts = timestamp.split(".")
                base = parts[0]
                # Get milliseconds and timezone from second part
                rest = parts[1]
                # Extract timezone (last 5 chars like -0500 or +0000)
                tz = rest[-5:]
                # Insert colon in timezone: -0500 -> -05:00
                tz_formatted = tz[:-2] + ":" + tz[-2:]
                iso_string = base + tz_formatted
            else:
                # No milliseconds, just handle timezone
                iso_string = timestamp

            return datetime.fromisoformat(iso_string)
        except (ValueError, AttributeError, IndexError):
            return None

    def create_task(
        self,
        title: str,
        description: str | None = None,
        task_type: TaskType = "task",
        priority: int | None = None,
        epic_id: str | None = None,
        labels: list[str] | None = None,
    ) -> Task:
        """Create a new Jira issue.

        Args:
            title: Issue summary/title.
            description: Optional issue description.
            task_type: Type of task (bug, feature, task, epic, chore).
            priority: Optional priority (1-5, 1 is highest).
            epic_id: Optional parent epic ID (Jira issue key).
            labels: Optional list of labels.

        Returns:
            The created task.
        """
        # Map task type to Jira issue type
        jira_issue_type = self.TYPE_JIRA_MAP.get(task_type, "Task")

        # Build issue creation fields
        issue_dict: dict[str, object] = {
            "project": self._extract_project_key(),
            "summary": title,
            "issuetype": {"name": jira_issue_type},
        }

        if description:
            issue_dict["description"] = description

        # Add priority if specified
        if priority is not None and priority in self.PRIORITY_JIRA_MAP:
            issue_dict["priority"] = {"name": self.PRIORITY_JIRA_MAP[priority]}

        # Add epic link if specified
        if epic_id:
            # Try common custom field names for epic links
            issue_dict["customfield_10000"] = epic_id  # Common Jira epic link field

        # Add labels if specified
        if labels:
            issue_dict["labels"] = labels

        # Create the issue
        created_issue = self.jira.create_issue(**issue_dict)

        # Parse and return the created task
        return self._parse_task(created_issue)

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID (Jira issue key).

        Args:
            task_id: The task identifier (Jira issue key, e.g., PROJ-123).

        Returns:
            The task.

        Raises:
            KeyError: If task not found.
        """
        try:
            issue = self.jira.issue(task_id)
            return self._parse_task(issue)
        except Exception as e:
            raise KeyError(f"Task {task_id} not found") from e

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        epic_id: str | None = None,
    ) -> list[Task]:
        """List tasks with optional filters.

        Args:
            status: Filter by status (open/closed/in_progress/blocked).
            epic_id: Filter by parent epic.

        Returns:
            List of matching tasks.
        """
        # Build JQL query
        jql_parts = []

        # Add status filter if specified
        if status:
            jira_status = self.STATUS_JIRA_MAP.get(status, "Open")
            jql_parts.append(f'status = "{jira_status}"')

        # Add epic filter if specified
        if epic_id:
            jql_parts.append(f'parent = "{epic_id}"')

        jql = " AND ".join(jql_parts) if jql_parts else None

        try:
            # Search for issues
            issues = (
                self.jira.search_issues(jql)
                if jql
                else self.jira.search_issues("ORDER BY created DESC")
            )
            return [self._parse_task(issue) for issue in issues]
        except Exception:
            return []

    def update_task(
        self,
        task_id: str,
        status: TaskStatus | None = None,
        title: str | None = None,
        description: str | None = None,
        priority: int | None = None,
        labels: list[str] | None = None,
    ) -> Task:
        """Update a task.

        Args:
            task_id: The task identifier.
            status: New status (open/closed/in_progress/blocked).
            title: New title.
            description: New description.
            priority: New priority.
            labels: New labels.

        Returns:
            The updated task.
        """
        issue = self.jira.issue(task_id)

        # Update title if provided
        if title:
            issue.update(summary=title)

        # Update description if provided
        if description:
            issue.update(description=description)

        # Update priority if provided
        if priority is not None and priority in self.PRIORITY_JIRA_MAP:
            issue.update(priority={"name": self.PRIORITY_JIRA_MAP[priority]})

        # Update labels if provided
        if labels:
            issue.update(labels=labels)

        # Handle status transitions
        if status:
            self._transition_issue_to_status(task_id, status)

        # Fetch and return updated task
        return self.get_task(task_id)

    def get_next_ready_task(self, epic_id: str | None = None) -> Task | None:
        """Get the next task ready to be worked on.

        A task is ready if it's open and has no blocking dependencies.
        Jira doesn't have native issue dependencies, so we consider
        all open tasks as ready.

        Args:
            epic_id: Optional epic filter.

        Returns:
            The next ready task, or None if no tasks are ready.
        """
        tasks = self.list_tasks(status="open", epic_id=epic_id)
        return tasks[0] if tasks else None

    def add_dependency(self, task_id: str, depends_on_id: str) -> None:
        """Add a dependency between tasks.

        In Jira, we link issues using the "blocks" or "depends on" link type.

        Args:
            task_id: The task that depends on another.
            depends_on_id: The task being depended upon.
        """
        with contextlib.suppress(Exception):
            # Link the issues with "blocks" relationship
            # task_id depends on depends_on_id, which means depends_on_id blocks task_id
            self.jira.create_issue_link(
                type="blocks",
                inwardIssue=depends_on_id,
                outwardIssue=task_id,
            )

    def close_task(self, task_id: str, reason: str | None = None) -> None:
        """Close a task.

        Args:
            task_id: The task to close.
            reason: Optional reason for closing (added as comment).
        """
        # Transition the issue to Done/Closed status
        self._transition_issue_to_status(task_id, "closed")

        # Add closing reason as comment if provided
        if reason:
            with contextlib.suppress(Exception):
                self.jira.add_comment(task_id, f"Closed: {reason}")

    def _transition_issue_to_status(self, task_id: str, status: TaskStatus) -> None:
        """Transition a Jira issue to the specified status.

        Args:
            task_id: The task ID (Jira issue key).
            status: The target status.
        """
        # Map jiro status to Jira workflow transition
        target_jira_status = self.STATUS_JIRA_MAP.get(status, "Open")

        try:
            # Get available transitions for this issue
            transitions = self.jira.transitions(task_id)

            # Find transition that matches target status
            for transition in transitions:
                if transition["to"]["name"] == target_jira_status:
                    self.jira.transition_issue(task_id, transition["id"])
                    return

            # If exact match not found, try common transitions
            if status == "closed":
                # Try to find Done, Resolved, or Closed transitions
                for transition in transitions:
                    if transition["to"]["name"] in ("Done", "Resolved", "Closed"):
                        self.jira.transition_issue(task_id, transition["id"])
                        return
            elif status == "in_progress":
                # Try to find In Progress transitions
                for transition in transitions:
                    if transition["to"]["name"] in ("In Progress", "In Review", "In QA"):
                        self.jira.transition_issue(task_id, transition["id"])
                        return
        except Exception:
            # If transitions fail, continue - the issue may not support transitions
            pass

    def _extract_project_key(self) -> str:
        """Extract the project key from server URL or use default.

        This is a simplified approach. In a real implementation, you might
        want to pass the project key as a parameter to __init__.

        Returns:
            The project key (e.g., 'PROJ').
        """
        # For now, we'll use a default. In practice, this should be configurable
        return "PROJ"
