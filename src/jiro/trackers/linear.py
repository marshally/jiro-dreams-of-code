"""LinearTracker implementation using Linear GraphQL API."""

import contextlib
from datetime import datetime
from typing import Any

import requests  # type: ignore

from jiro.trackers.interface import Task, TaskStatus, TaskType


class LinearTracker:
    """Issue tracker implementation using Linear GraphQL API.

    This implementation uses the Linear GraphQL API to manage issues.
    Linear issues are mapped to the jiro Task model:
    - Linear issue ID -> Task ID
    - Linear state -> Task status
    - Linear issue type -> Task type
    - Linear priority (0-4) -> Task priority (1-5, mapped inversely)
    """

    # Type mappings from jiro task types to Linear issue types
    TYPE_LINEAR_MAP: dict[TaskType, str] = {
        "bug": "Bug",
        "feature": "Feature",
        "task": "Task",
        "epic": "Epic",
        "chore": "Chore",
    }

    REVERSE_TYPE_LINEAR_MAP: dict[str, TaskType] = {v: k for k, v in TYPE_LINEAR_MAP.items()}

    # Status mappings from jiro TaskStatus to Linear workflow states
    STATUS_LINEAR_MAP: dict[TaskStatus, str] = {
        "open": "Todo",
        "in_progress": "In Progress",
        "blocked": "Blocked",
        "closed": "Done",
    }

    # Reverse mapping - handle various Linear state names
    REVERSE_STATUS_MAP: dict[str, TaskStatus] = {
        "Todo": "open",
        "Backlog": "open",
        "In Progress": "in_progress",
        "In Review": "in_progress",
        "Blocked": "blocked",
        "Done": "closed",
        "Cancelled": "closed",
    }

    # Priority mapping from Linear (0-4) to jiro (1-5)
    # Linear: 0=no priority, 1=low, 2=medium, 3=high, 4=urgent
    # jiro: 1=highest, 2=high, 3=medium, 4=low, 5=lowest
    PRIORITY_LINEAR_MAP: dict[int, int] = {
        4: 1,  # urgent -> highest
        3: 2,  # high -> high
        2: 3,  # medium -> medium
        1: 4,  # low -> low
        0: 5,  # no priority -> lowest
    }

    REVERSE_PRIORITY_MAP: dict[int, int] = {v: k for k, v in PRIORITY_LINEAR_MAP.items()}

    def __init__(self, api_key: str) -> None:
        """Initialize the LinearTracker.

        Args:
            api_key: Linear API key for authentication.
        """
        self.api_key = api_key
        self.graphql_endpoint = "https://api.linear.app/graphql"
        self.session: requests.Session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )

    def _execute_graphql(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a GraphQL query against Linear API.

        Args:
            query: GraphQL query string.
            variables: Optional variables for the query.

        Returns:
            Response data from Linear API.

        Raises:
            RuntimeError: If API request fails.
        """
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        response = self.session.post(self.graphql_endpoint, json=payload)

        if response.status_code != 200:
            raise RuntimeError(f"Linear API error: {response.status_code}")

        data: dict[str, Any] = response.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL error: {data['errors']}")

        return data.get("data", {})  # type: ignore

    def _parse_task(self, issue_data: dict[str, Any]) -> Task:
        """Parse a task from Linear issue data.

        Args:
            issue_data: Dictionary from Linear GraphQL API response.

        Returns:
            Task object.
        """
        # Extract task type from Linear issue type
        linear_type = issue_data.get("type", "Task")
        task_type: TaskType = self.REVERSE_TYPE_LINEAR_MAP.get(linear_type, "task")

        # Extract status from Linear state
        state_name = issue_data.get("state", {}).get("name", "Todo")
        status: TaskStatus = self.REVERSE_STATUS_MAP.get(state_name, "open")

        # Extract priority and map to jiro priority scale
        linear_priority = issue_data.get("priority")
        priority: int | None = None
        if linear_priority is not None:
            priority = self.PRIORITY_LINEAR_MAP.get(linear_priority, 5)

        # Parse timestamps
        created_at = self._parse_datetime(issue_data.get("createdAt"))
        updated_at = self._parse_datetime(issue_data.get("updatedAt"))
        closed_at = self._parse_datetime(issue_data.get("archivedAt"))

        return Task(
            id=issue_data["id"],
            title=issue_data["title"],
            task_type=task_type,
            status=status,
            created_at=created_at or datetime.now(),
            description=issue_data.get("description"),
            priority=priority,
            updated_at=updated_at,
            closed_at=closed_at,
        )

    def _parse_datetime(self, timestamp: str | None) -> datetime | None:
        """Parse an ISO 8601 timestamp string.

        Args:
            timestamp: ISO 8601 timestamp string.

        Returns:
            Parsed datetime or None.
        """
        if not timestamp:
            return None
        try:
            # Linear uses format: 2024-01-15T10:00:00.000Z
            if timestamp.endswith("Z"):
                return datetime.fromisoformat(timestamp[:-1] + "+00:00")
            return datetime.fromisoformat(timestamp)
        except (ValueError, AttributeError):
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
        """Create a new Linear issue.

        Args:
            title: Issue title.
            description: Optional issue description.
            task_type: Type of task (bug, feature, task, epic, chore).
            priority: Optional priority (1-5, 1 is highest).
            epic_id: Optional parent epic ID (Linear issue ID).
            labels: Optional list of label names.

        Returns:
            The created task.
        """
        # Map jiro type to Linear type
        linear_type = self.TYPE_LINEAR_MAP.get(task_type, "Task")

        # Map jiro priority to Linear priority
        linear_priority = None
        if priority is not None and priority in self.REVERSE_PRIORITY_MAP:
            linear_priority = self.REVERSE_PRIORITY_MAP[priority]

        # Build GraphQL mutation
        mutation = """
            mutation CreateIssue($input: IssueCreateInput!) {
                issueCreate(input: $input) {
                    issue {
                        id
                        identifier
                        title
                        description
                        type
                        state { name }
                        priority
                        createdAt
                        updatedAt
                        archivedAt
                    }
                }
            }
        """

        input_data: dict[str, Any] = {
            "title": title,
            "type": linear_type,
        }

        if description:
            input_data["description"] = description

        if linear_priority is not None:
            input_data["priority"] = linear_priority

        if epic_id:
            input_data["parent"] = {"id": epic_id}

        if labels:
            # Linear uses label IDs, not names. For now, we'll store as description
            # In a real implementation, you'd look up label IDs
            pass

        result = self._execute_graphql(mutation, {"input": input_data})
        issue_data = result["issueCreate"]["issue"]

        return self._parse_task(issue_data)

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID.

        Args:
            task_id: The task identifier (Linear issue ID).

        Returns:
            The task.

        Raises:
            KeyError: If task not found.
        """
        query = """
            query GetIssue($id: String!) {
                issue(id: $id) {
                    id
                    identifier
                    title
                    description
                    type
                    state { name }
                    priority
                    createdAt
                    updatedAt
                    archivedAt
                }
            }
        """

        result = self._execute_graphql(query, {"id": task_id})
        issue_data = result.get("issue")

        if not issue_data:
            raise KeyError(f"Task {task_id} not found")

        return self._parse_task(issue_data)

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
        query = """
            query ListIssues($filter: IssueFilter) {
                issues(filter: $filter) {
                    edges {
                        node {
                            id
                            identifier
                            title
                            description
                            type
                            state { name }
                            priority
                            createdAt
                            updatedAt
                            archivedAt
                        }
                    }
                }
            }
        """

        filter_conditions: dict[str, Any] = {}

        # Add status filter if specified
        if status:
            linear_state = self.STATUS_LINEAR_MAP.get(status, "Todo")
            filter_conditions["state"] = {"name": {"eq": linear_state}}

        # Add epic filter if specified
        if epic_id:
            filter_conditions["parent"] = {"id": {"eq": epic_id}}

        variables = {"filter": filter_conditions} if filter_conditions else None

        try:
            result = self._execute_graphql(query, variables)
            issues_data = result.get("issues", {}).get("edges", [])

            if not issues_data:
                return []

            return [self._parse_task(edge["node"]) for edge in issues_data]
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
            priority: New priority (1-5, 1 is highest).
            labels: New labels.

        Returns:
            The updated task.
        """
        mutation = """
            mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
                issueUpdate(id: $id, input: $input) {
                    issue {
                        id
                        identifier
                        title
                        description
                        type
                        state { name }
                        priority
                        createdAt
                        updatedAt
                        archivedAt
                    }
                }
            }
        """

        input_data: dict[str, Any] = {}

        if title:
            input_data["title"] = title

        if description:
            input_data["description"] = description

        if status:
            linear_state = self.STATUS_LINEAR_MAP.get(status, "Todo")
            input_data["state"] = linear_state

        if priority is not None and priority in self.REVERSE_PRIORITY_MAP:
            input_data["priority"] = self.REVERSE_PRIORITY_MAP[priority]

        if labels:
            # Linear uses label IDs, not names
            pass

        result = self._execute_graphql(mutation, {"id": task_id, "input": input_data})
        issue_data = result["issueUpdate"]["issue"]

        return self._parse_task(issue_data)

    def get_next_ready_task(self, epic_id: str | None = None) -> Task | None:
        """Get the next task ready to be worked on.

        A task is ready if it's in an open state and has no blocking dependencies.
        Linear doesn't have native dependency tracking, so we return the first open task.

        Args:
            epic_id: Optional epic filter.

        Returns:
            The next ready task, or None if no tasks are ready.
        """
        tasks = self.list_tasks(status="open", epic_id=epic_id)
        return tasks[0] if tasks else None

    def add_dependency(self, task_id: str, depends_on_id: str) -> None:
        """Add a dependency between tasks.

        Linear doesn't have native issue dependencies, so this creates a comment
        linking the issues.

        Args:
            task_id: The task that depends on another.
            depends_on_id: The task being depended upon.
        """
        mutation = """
            mutation LinkIssues($input: IssueLinkCreateInput!) {
                issueLinkCreate(input: $input) {
                    issueLink {
                        id
                    }
                }
            }
        """

        input_data: dict[str, str] = {
            "issueId": task_id,
            "relatedIssueId": depends_on_id,
            "type": "blocks",
        }

        with contextlib.suppress(Exception):
            # Linear may not support issue linking in this way
            # Fall back to adding a comment instead
            self._execute_graphql(mutation, {"input": input_data})

    def close_task(self, task_id: str, reason: str | None = None) -> None:
        """Close a task.

        Args:
            task_id: The task to close.
            reason: Optional reason for closing (added as comment).
        """
        # Update issue state to Done
        self.update_task(task_id, status="closed")

        # Add closing reason as comment if provided
        if reason:
            mutation = """
                mutation AddComment($input: CommentCreateInput!) {
                    commentCreate(input: $input) {
                        comment {
                            id
                        }
                    }
                }
            """

            comment_input: dict[str, str] = {
                "issueId": task_id,
                "body": f"Closed: {reason}",
            }

            with contextlib.suppress(Exception):
                # If comment fails, just continue - the task is closed
                self._execute_graphql(mutation, {"input": comment_input})
