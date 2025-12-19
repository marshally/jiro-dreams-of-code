"""Repository pattern for database operations."""

from sqlite_utils import Database

from jiro.db.models import Commit, DreamSession, ExecutionPlan, Prompt, Session, TaskExecution


class SessionRepository:
    """Repository for Session CRUD operations."""

    def __init__(self, db: Database) -> None:
        """Initialize repository with database connection.

        Args:
            db: sqlite-utils Database instance.
        """
        self.db = db

    def create(self, session: Session) -> Session:
        """Create a new session in the database.

        Args:
            session: Session instance to create.

        Returns:
            The created Session instance.
        """
        row = session.to_row()
        self.db["sessions"].insert(row)
        return session

    def get(self, session_id: str) -> Session | None:
        """Retrieve a session by ID.

        Args:
            session_id: ID of the session to retrieve.

        Returns:
            Session instance if found, None otherwise.
        """
        rows = list(self.db["sessions"].rows_where("id = ?", [session_id]))
        if not rows:
            return None
        return Session.from_row(rows[0])

    def get_active(self) -> list[Session]:
        """Retrieve all active (running) sessions.

        Returns:
            List of Session instances with status='running'.
        """
        rows = list(self.db["sessions"].rows_where("status = ?", ["running"]))
        return [Session.from_row(row) for row in rows]

    def update(self, session: Session) -> Session:
        """Update an existing session in the database.

        Args:
            session: Session instance with updated values.

        Returns:
            The updated Session instance.
        """
        row = session.to_row()
        self.db["sessions"].update(session.id, row)
        return session

    def get_by_status(self, status: str) -> list[Session]:
        """Retrieve all sessions with a specific status.

        Args:
            status: Session status to filter by.

        Returns:
            List of Session instances matching the status.
        """
        rows = list(self.db["sessions"].rows_where("status = ?", [status]))
        return [Session.from_row(row) for row in rows]


class PromptRepository:
    """Repository for Prompt CRUD operations."""

    def __init__(self, db: Database) -> None:
        """Initialize repository with database connection.

        Args:
            db: sqlite-utils Database instance.
        """
        self.db = db

    def create(self, prompt: Prompt) -> Prompt:
        """Create a new prompt in the database.

        Args:
            prompt: Prompt instance to create.

        Returns:
            The created Prompt instance.
        """
        row = prompt.to_row()
        self.db["prompts"].insert(row)
        return prompt

    def get(self, prompt_id: str) -> Prompt | None:
        """Retrieve a prompt by ID.

        Args:
            prompt_id: ID of the prompt to retrieve.

        Returns:
            Prompt instance if found, None otherwise.
        """
        rows = list(self.db["prompts"].rows_where("id = ?", [prompt_id]))
        if not rows:
            return None
        return Prompt.from_row(rows[0])

    def get_by_session(self, session_id: str) -> list[Prompt]:
        """Retrieve all prompts for a specific session.

        Args:
            session_id: Session ID to filter by.

        Returns:
            List of Prompt instances for the session.
        """
        rows = list(self.db["prompts"].rows_where("session_id = ?", [session_id]))
        return [Prompt.from_row(row) for row in rows]

    def get_by_task(self, task_id: str) -> list[Prompt]:
        """Retrieve all prompts for a specific task.

        Args:
            task_id: Task ID to filter by.

        Returns:
            List of Prompt instances for the task.
        """
        rows = list(self.db["prompts"].rows_where("task_id = ?", [task_id]))
        return [Prompt.from_row(row) for row in rows]

    def get_total_tokens(self, session_id: str) -> int:
        """Get total tokens_after for a session.

        Args:
            session_id: Session ID to aggregate tokens for.

        Returns:
            Sum of tokens_after for all prompts in the session.
        """
        result = self.db.execute(
            "SELECT COALESCE(SUM(tokens_after), 0) as total FROM prompts WHERE session_id = ?",
            [session_id],
        ).fetchone()
        return result[0] if result else 0


class TaskExecutionRepository:
    """Repository for TaskExecution CRUD operations."""

    def __init__(self, db: Database) -> None:
        """Initialize repository with database connection.

        Args:
            db: sqlite-utils Database instance.
        """
        self.db = db

    def create(self, execution: TaskExecution) -> TaskExecution:
        """Create a new task execution in the database.

        Args:
            execution: TaskExecution instance to create.

        Returns:
            The created TaskExecution instance.
        """
        row = execution.to_row()
        self.db["task_executions"].insert(row)
        return execution

    def get(self, execution_id: str) -> TaskExecution | None:
        """Retrieve a task execution by ID.

        Args:
            execution_id: ID of the task execution to retrieve.

        Returns:
            TaskExecution instance if found, None otherwise.
        """
        rows = list(self.db["task_executions"].rows_where("id = ?", [execution_id]))
        if not rows:
            return None
        return TaskExecution.from_row(rows[0])

    def get_by_session(self, session_id: str) -> list[TaskExecution]:
        """Retrieve all task executions for a specific session.

        Args:
            session_id: Session ID to filter by.

        Returns:
            List of TaskExecution instances for the session.
        """
        rows = list(self.db["task_executions"].rows_where("session_id = ?", [session_id]))
        return [TaskExecution.from_row(row) for row in rows]

    def get_by_task(self, task_id: str) -> list[TaskExecution]:
        """Retrieve all task executions for a specific task.

        Args:
            task_id: Task ID to filter by.

        Returns:
            List of TaskExecution instances for the task.
        """
        rows = list(self.db["task_executions"].rows_where("task_id = ?", [task_id]))
        return [TaskExecution.from_row(row) for row in rows]

    def update(self, execution: TaskExecution) -> TaskExecution:
        """Update an existing task execution in the database.

        Args:
            execution: TaskExecution instance with updated values.

        Returns:
            The updated TaskExecution instance.
        """
        row = execution.to_row()
        self.db["task_executions"].update(execution.id, row)
        return execution


class CommitRepository:
    """Repository for Commit CRUD operations."""

    def __init__(self, db: Database) -> None:
        """Initialize repository with database connection.

        Args:
            db: sqlite-utils Database instance.
        """
        self.db = db

    def create(self, commit: Commit) -> Commit:
        """Create a new commit in the database.

        Args:
            commit: Commit instance to create.

        Returns:
            The created Commit instance.
        """
        row = commit.to_row()
        self.db["commits"].insert(row)
        return commit

    def get(self, commit_id: str) -> Commit | None:
        """Retrieve a commit by ID.

        Args:
            commit_id: ID of the commit to retrieve.

        Returns:
            Commit instance if found, None otherwise.
        """
        rows = list(self.db["commits"].rows_where("id = ?", [commit_id]))
        if not rows:
            return None
        return Commit.from_row(rows[0])

    def get_by_session(self, session_id: str) -> list[Commit]:
        """Retrieve all commits for a specific session.

        Args:
            session_id: Session ID to filter by.

        Returns:
            List of Commit instances for the session.
        """
        rows = list(self.db["commits"].rows_where("session_id = ?", [session_id]))
        return [Commit.from_row(row) for row in rows]

    def get_by_task(self, task_id: str) -> list[Commit]:
        """Retrieve all commits for a specific task.

        Args:
            task_id: Task ID to filter by.

        Returns:
            List of Commit instances for the task.
        """
        rows = list(self.db["commits"].rows_where("task_id = ?", [task_id]))
        return [Commit.from_row(row) for row in rows]

    def get_by_type(self, session_id: str, commit_type: str) -> list[Commit]:
        """Retrieve commits for a session filtered by commit type.

        Args:
            session_id: Session ID to filter by.
            commit_type: Commit type to filter by.

        Returns:
            List of Commit instances matching both filters.
        """
        rows = list(
            self.db["commits"].rows_where(
                "session_id = ? AND commit_type = ?",
                [session_id, commit_type],
            )
        )
        return [Commit.from_row(row) for row in rows]


class ExecutionPlanRepository:
    """Repository for ExecutionPlan CRUD operations."""

    def __init__(self, db: Database) -> None:
        """Initialize repository with database connection.

        Args:
            db: sqlite-utils Database instance.
        """
        self.db = db

    def create(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Create a new execution plan in the database.

        Args:
            plan: ExecutionPlan instance to create.

        Returns:
            The created ExecutionPlan instance.
        """
        row = plan.to_row()
        self.db["execution_plans"].insert(row)
        return plan

    def get(self, plan_id: str) -> ExecutionPlan | None:
        """Retrieve an execution plan by ID.

        Args:
            plan_id: ID of the execution plan to retrieve.

        Returns:
            ExecutionPlan instance if found, None otherwise.
        """
        rows = list(self.db["execution_plans"].rows_where("id = ?", [plan_id]))
        if not rows:
            return None
        return ExecutionPlan.from_row(rows[0])

    def get_by_session(self, session_id: str) -> list[ExecutionPlan]:
        """Retrieve all execution plans for a specific session.

        Args:
            session_id: Session ID to filter by.

        Returns:
            List of ExecutionPlan instances for the session.
        """
        rows = list(self.db["execution_plans"].rows_where("session_id = ?", [session_id]))
        return [ExecutionPlan.from_row(row) for row in rows]

    def get_by_task(self, task_id: str) -> list[ExecutionPlan]:
        """Retrieve all execution plans for a specific task.

        Args:
            task_id: Task ID to filter by.

        Returns:
            List of ExecutionPlan instances for the task.
        """
        rows = list(self.db["execution_plans"].rows_where("task_id = ?", [task_id]))
        return [ExecutionPlan.from_row(row) for row in rows]


class DreamSessionRepository:
    """Repository for DreamSession CRUD operations.

    Manages dream/interview sessions for crash recovery in jiro dream.
    """

    def __init__(self, db: Database) -> None:
        """Initialize repository with database connection.

        Args:
            db: sqlite-utils Database instance.
        """
        self.db = db

    def create(self, session: DreamSession) -> DreamSession:
        """Create a new dream session in the database.

        Args:
            session: DreamSession instance to create.

        Returns:
            The created DreamSession instance.
        """
        row = session.to_row()
        self.db["dream_sessions"].insert(row)
        return session

    def get(self, session_id: str) -> DreamSession | None:
        """Retrieve a dream session by ID.

        Args:
            session_id: ID of the dream session to retrieve.

        Returns:
            DreamSession instance if found, None otherwise.
        """
        rows = list(self.db["dream_sessions"].rows_where("id = ?", [session_id]))
        if not rows:
            return None
        return DreamSession.from_row(rows[0])

    def get_incomplete(self) -> list[DreamSession]:
        """Retrieve all incomplete dream sessions.

        Returns sessions that are not 'completed' or 'abandoned',
        ordered by most recently updated first.

        Returns:
            List of DreamSession instances that can be resumed.
        """
        rows = list(
            self.db["dream_sessions"].rows_where(
                "status NOT IN (?, ?)",
                ["completed", "abandoned"],
                order_by="-updated_at",
            )
        )
        return [DreamSession.from_row(row) for row in rows]

    def update(self, session: DreamSession) -> DreamSession:
        """Update an existing dream session in the database.

        Args:
            session: DreamSession instance with updated values.

        Returns:
            The updated DreamSession instance.
        """
        row = session.to_row()
        self.db["dream_sessions"].update(session.id, row)
        return session

    def delete(self, session_id: str) -> None:
        """Delete a dream session from the database.

        Args:
            session_id: ID of the dream session to delete.
        """
        self.db["dream_sessions"].delete_where("id = ?", [session_id])
