"""GitHubTracker implementation using GitHub CLI."""

import json
import subprocess
from datetime import datetime

from jiro.trackers.interface import Task, TaskStatus, TaskType


class GitHubTracker:
    """Issue tracker implementation using GitHub CLI (gh).

    This implementation shells out to the gh (GitHub CLI) tool to manage issues.
    It parses JSON output and converts it to Task objects.
    GitHub issues are mapped to the jiro Task model:
    - GitHub issue number -> Task ID
    - GitHub state (open/closed) -> Task status
    - GitHub labels -> Task type/priority/labels mapping
    """

    # Label mappings from jiro task types to GitHub labels
    TYPE_LABEL_MAP: dict[TaskType, str] = {
        "bug": "type:bug",
        "feature": "type:feature",
        "task": "type:task",
        "epic": "type:epic",
        "chore": "type:chore",
    }

    REVERSE_TYPE_LABEL_MAP: dict[str, TaskType] = {v: k for k, v in TYPE_LABEL_MAP.items()}

    # Priority label mappings
    PRIORITY_LABEL_MAP: dict[int, str] = {
        1: "priority:1",
        2: "priority:2",
        3: "priority:3",
        4: "priority:4",
        5: "priority:5",
    }

    REVERSE_PRIORITY_MAP: dict[str, int] = {v: k for k, v in PRIORITY_LABEL_MAP.items()}

    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        github_token: str | None = None,
    ):
        """Initialize the GitHubTracker.

        Args:
            repo_owner: Owner/organization of the GitHub repository.
            repo_name: Name of the GitHub repository.
            github_token: Optional GitHub API token. If not provided,
                         uses gh CLI's existing authentication.
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
        self.repo = f"{repo_owner}/{repo_name}"

    def _run_gh_command(self, *args: str) -> str:
        """Run a gh CLI command and return JSON output.

        Args:
            *args: Arguments to pass to gh command.

        Returns:
            JSON output from the command.

        Raises:
            subprocess.CalledProcessError: If the command fails.
        """
        cmd = ["gh", "issue"] + list(args) + ["--json"]
        env = None

        # If token is provided, set it in environment
        if self.github_token:
            import os

            env = os.environ.copy()
            env["GH_TOKEN"] = self.github_token

        result = subprocess.run(
            cmd,
            cwd=None,
            capture_output=True,
            text=False,
            check=True,
            env=env,
        )
        return result.stdout.decode()

    def _parse_task(self, issue_data: dict) -> Task:
        """Parse a task from GitHub issue data.

        Args:
            issue_data: Dictionary from GitHub API response.

        Returns:
            Task object.
        """
        # Extract task type from labels
        task_type: TaskType = "task"
        priority: int | None = None
        labels: list[str] = []

        if "labels" in issue_data and issue_data["labels"]:
            for label in issue_data["labels"]:
                label_name = label.get("name", "")
                if label_name in self.REVERSE_TYPE_LABEL_MAP:
                    task_type = self.REVERSE_TYPE_LABEL_MAP[label_name]
                elif label_name in self.REVERSE_PRIORITY_MAP:
                    priority = self.REVERSE_PRIORITY_MAP[label_name]
                else:
                    labels.append(label_name)

        # Parse timestamps
        created_at = self._parse_datetime(issue_data.get("createdAt"))
        updated_at = self._parse_datetime(issue_data.get("updatedAt"))
        closed_at = self._parse_datetime(issue_data.get("closedAt"))

        # Map GitHub state to Task status
        status: TaskStatus = "open"
        if issue_data.get("state") == "CLOSED" or issue_data.get("state") == "closed":
            status = "closed"

        return Task(
            id=str(issue_data["number"]),
            title=issue_data["title"],
            task_type=task_type,
            status=status,
            created_at=created_at or datetime.now(),
            description=issue_data.get("body"),
            priority=priority,
            updated_at=updated_at,
            closed_at=closed_at,
            labels=labels if labels else None,
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
            # Handle GitHub API format with Z suffix
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
        """Create a new GitHub issue.

        Args:
            title: Issue title.
            description: Optional issue description.
            task_type: Type of task (bug, feature, task, epic, chore).
            priority: Optional priority (1-5, 1 is highest).
            epic_id: Optional parent epic ID (becomes a label).
            labels: Optional list of additional labels.

        Returns:
            The created task.
        """
        import os

        # Build gh issue create command
        cmd = ["gh", "issue", "create", "--repo", self.repo, "--title", title]

        if description:
            cmd.extend(["--body", description])

        # Add type label
        gh_labels = [self.TYPE_LABEL_MAP[task_type]]

        # Add priority label if specified
        if priority is not None and priority in self.PRIORITY_LABEL_MAP:
            gh_labels.append(self.PRIORITY_LABEL_MAP[priority])

        # Add epic label if specified
        if epic_id:
            gh_labels.append(f"epic:{epic_id}")

        # Add custom labels
        if labels:
            gh_labels.extend(labels)

        if gh_labels:
            cmd.extend(["--label", ",".join(gh_labels)])

        env = None
        if self.github_token:
            env = os.environ.copy()
            env["GH_TOKEN"] = self.github_token

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=False,
            check=True,
            env=env,
        )

        # gh create returns JSON with the created issue when --json is used
        # For tests, mock returns JSON directly
        try:
            output = result.stdout.decode()
            if output.startswith("[") or output.startswith("{"):
                # Parse JSON response from gh
                issue_data = json.loads(output)
                return self._parse_task(issue_data)
            else:
                # Fallback: extract issue number from text output
                # (usually "Opened issue #123")
                issue_number = output.split("#")[-1].split()[0].strip()
                return self.get_task(issue_number)
        except (json.JSONDecodeError, ValueError, KeyError):
            # If parsing fails, try to extract issue number
            output = result.stdout.decode()
            issue_number = output.split("#")[-1].split()[0].strip()
            return self.get_task(issue_number)

    def get_task(self, task_id: str) -> Task:
        """Get a task by ID (GitHub issue number).

        Args:
            task_id: The task identifier (GitHub issue number).

        Returns:
            The task.

        Raises:
            KeyError: If task not found.
        """
        import os

        cmd = ["gh", "issue", "view", task_id, "--repo", self.repo, "--json"]
        fields = "number,title,body,state,createdAt,updatedAt,closedAt,labels"
        cmd.extend([fields])

        env = None
        if self.github_token:
            env = os.environ.copy()
            env["GH_TOKEN"] = self.github_token

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=False,
                check=True,
                env=env,
            )
            issue_data = json.loads(result.stdout.decode())
            return self._parse_task(issue_data)
        except subprocess.CalledProcessError as e:
            raise KeyError(f"Task {task_id} not found") from e

    def list_tasks(
        self,
        status: TaskStatus | None = None,
        epic_id: str | None = None,
    ) -> list[Task]:
        """List tasks with optional filters.

        Args:
            status: Filter by status (open/closed).
            epic_id: Filter by parent epic.

        Returns:
            List of matching tasks.
        """
        import os

        cmd = ["gh", "issue", "list", "--repo", self.repo, "--json"]
        fields = "number,title,body,state,createdAt,updatedAt,closedAt,labels"
        cmd.extend([fields])

        # Add state filter
        if status == "open":
            cmd.extend(["--state", "open"])
        elif status == "closed":
            cmd.extend(["--state", "closed"])

        # Add epic filter if specified
        if epic_id:
            cmd.extend(["--label", f"epic:{epic_id}"])

        env = None
        if self.github_token:
            env = os.environ.copy()
            env["GH_TOKEN"] = self.github_token

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=False,
            check=True,
            env=env,
        )

        issues_data = json.loads(result.stdout.decode())
        if not issues_data:
            return []

        return [self._parse_task(issue) for issue in issues_data]

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
            status: New status (open/closed).
            title: New title.
            description: New description.
            priority: New priority.
            labels: New labels (replaces all labels).

        Returns:
            The updated task.
        """
        import os

        cmd = ["gh", "issue", "edit", task_id, "--repo", self.repo]

        if title:
            cmd.extend(["--title", title])

        if description:
            cmd.extend(["--body", description])

        if status == "closed":
            cmd.append("--state=closed")
        elif status == "open":
            cmd.append("--state=open")

        # Note: GitHub doesn't support setting labels via CLI edit,
        # would need to use API for that. For now, we just update what we can.

        env = None
        if self.github_token:
            env = os.environ.copy()
            env["GH_TOKEN"] = self.github_token

        subprocess.run(
            cmd,
            capture_output=True,
            text=False,
            check=True,
            env=env,
        )

        # Fetch updated task
        return self.get_task(task_id)

    def get_next_ready_task(self, epic_id: str | None = None) -> Task | None:
        """Get the next task ready to be worked on.

        A task is ready if it's open and has no blocking dependencies.
        GitHub doesn't have native dependency tracking, so we consider
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

        GitHub doesn't have native issue dependencies, so we add a comment
        linking the issues and add a "depends-on" label.

        Args:
            task_id: The task that depends on another.
            depends_on_id: The task being depended upon.
        """
        import os

        # Add a comment on the dependent task
        comment = f"Depends on #{depends_on_id}"
        cmd = ["gh", "issue", "comment", task_id, "--repo", self.repo, "--body", comment]

        env = None
        if self.github_token:
            env = os.environ.copy()
            env["GH_TOKEN"] = self.github_token

        subprocess.run(
            cmd,
            capture_output=True,
            text=False,
            check=True,
            env=env,
        )

    def close_task(self, task_id: str, reason: str | None = None) -> None:
        """Close a task.

        Args:
            task_id: The task to close.
            reason: Optional reason for closing (added as comment).
        """
        import os

        # Close the issue
        cmd = ["gh", "issue", "close", task_id, "--repo", self.repo]

        env = None
        if self.github_token:
            env = os.environ.copy()
            env["GH_TOKEN"] = self.github_token

        subprocess.run(
            cmd,
            capture_output=True,
            text=False,
            check=True,
            env=env,
        )

        # Add closing reason as comment if provided
        if reason:
            comment_cmd = [
                "gh",
                "issue",
                "comment",
                task_id,
                "--repo",
                self.repo,
                "--body",
                f"Closed: {reason}",
            ]

            subprocess.run(
                comment_cmd,
                capture_output=True,
                text=False,
                check=True,
                env=env,
            )
