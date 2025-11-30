"""Repository pattern for database operations."""

from sqlite_utils import Database

from jiro.db.models import Session


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
