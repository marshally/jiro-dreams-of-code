# ADR-007: Use sqlite-utils Instead of ORM

## Status

Accepted

## Context

Jiro needs a database layer for storing sessions, prompts, commits, and task executions. Options include:

1. **Full ORM** (SQLAlchemy): Feature-rich but heavy
1. **Raw SQL**: Maximum control but verbose
1. **sqlite-utils**: Lightweight Python API for SQLite

Our schema is simple: 4 tables with basic foreign keys, no complex relationships or queries.

## Decision

Use `sqlite-utils` for database operations.

```python
from sqlite_utils import Database

db = Database("jiro.db")

# Create table
db["sessions"].create(
    {
        "id": str,
        "epic_id": str,
        "branch_name": str,
        "status": str,
        "started_at": str,
        "ended_at": str,
    },
    pk="id",
    if_not_exists=True,
)

# Insert
db["sessions"].insert(
    {
        "id": "sess-123",
        "branch_name": "feature/auth",
        "status": "running",
        "started_at": datetime.now().isoformat(),
    }
)

# Query
session = db["sessions"].get("sess-123")
running = list(db["sessions"].rows_where("status = ?", ["running"]))

# Update
db["sessions"].update("sess-123", {"status": "completed"})
```

Combine with dataclasses for type safety:

```python
@dataclass
class Session:
    id: str
    branch_name: str
    status: str
    started_at: datetime
    epic_id: str | None = None
    ended_at: datetime | None = None

    @classmethod
    def from_row(cls, row: dict) -> "Session":
        return cls(**row)

    def to_row(self) -> dict:
        return asdict(self)
```

## Consequences

### Positive

- **Lightweight**: Single dependency, no ORM complexity
- **Pythonic API**: Dict-based, intuitive for simple operations
- **CLI included**: `sqlite-utils` CLI for debugging and inspection
- **Flexible**: Can drop to raw SQL when needed
- **Good fit for SQLite**: Purpose-built for SQLite, not a generic ORM

### Negative

- **SQLite only**: Can't switch to PostgreSQL without rewrite (acceptable for jiro)
- **No migrations framework**: Must handle schema changes manually
- **Less type safety**: Dict-based API; we add types via dataclasses
- **No relationship handling**: Must manage foreign keys manually

### Mitigations

- Use dataclasses for type safety at application layer
- Simple migration approach: numbered SQL files run in order
- Foreign key constraints enforced at database level

## Alternatives Considered

1. **SQLAlchemy**: Too heavy for 4 simple tables; adds complexity we don't need
1. **Raw sqlite3**: More verbose; sqlite-utils provides nicer API for same operations
1. **Peewee**: Lighter than SQLAlchemy but still ORM overhead
1. **TinyDB**: JSON-based, not relational; poor fit for our schema
