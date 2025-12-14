# ADR-009: Results as Pure Data

## Status

Accepted

## Context

The strongly typed commit system (ADR-004) passes data between three stages:

1. **Command** - Executes work via subagent, produces a Result
1. **Verification** - Validates the Result, produces a VerificationResult
1. **Commit** - Consumes both to create a git commit

We need to decide how to structure these Result objects:

- Should they have behavior (methods that do things)?
- Should they validate themselves?
- What serialization formats do we need?

## Decision

**Results are pure data containers** - they hold data and can serialize themselves, but contain no business logic.

### Structure

```python
@dataclass
class Result:
    """Base result - pure data with serialization."""

    changed_files: list[Path]

    # Serialization methods (data transformation only)
    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), default=str)

    def as_toon(self) -> str:
        """TOON format for LLM token efficiency."""
        ...

    def as_html(self) -> str:
        """HTML rendering for web UI."""
        ...

    def __str__(self) -> str:
        """Human-readable plain text."""
        ...
```

### What Results Can Do

- **Hold data** - Store values returned from subagents
- **Serialize** - Transform to JSON, TOON, HTML, plain text
- **Format strings** - `__str__`, `__repr__` for display

### What Results Cannot Do

- **Validate themselves** - Validation belongs in Verification classes
- **Execute actions** - No subprocess calls, file I/O, network requests
- **Modify state** - Immutable after creation (dataclass frozen=False for practical reasons, but treated as immutable)
- **Contain business logic** - No if/else decisions about what to do next

### Serialization Formats

| Format | Use Case |
|--------|----------|
| `as_dict()` | Python interop, database storage |
| `as_json()` | API responses, logging |
| `as_toon()` | LLM prompts (40% fewer tokens than JSON) |
| `as_html()` | Web UI rendering |
| `__str__()` | Console output, debugging |

## Consequences

### Positive

- **Testable** - Pure data is trivial to construct and assert against
- **Serializable** - No hidden state; what you see is what you get
- **Debuggable** - Print a Result and see everything
- **Type-safe** - Pydantic/dataclass validation catches errors early
- **Portable** - Can be stored in DB, sent over network, logged

### Negative

- **Verbose** - Each step type needs its own Result dataclass
- **No encapsulation** - Validation logic lives elsewhere (in Verification)
- **Multiple files** - Result, Verification, Command are separate (but this is also a positive for separation of concerns)

### Mitigations

- Base `Result` class provides common serialization methods
- Clear naming convention: `TddRedResult`, `TddGreenResult`, etc.
- Colocate Result with its Command in the same directory

## Alternatives Considered

### 1. Active Record Pattern

Results validate and save themselves:

```python
class TddRedResult:
    def validate(self) -> bool:
        """Check if result is valid."""
        ...

    def save(self, db: Database) -> None:
        """Persist to database."""
        ...
```

**Rejected because:** Mixes concerns; harder to test; creates coupling between data and infrastructure.

### 2. No Base Class

Each Result is independent with no shared structure:

```python
@dataclass
class TddRedResult:
    test_file: Path
    # ... no as_json(), no as_toon()
```

**Rejected because:** Duplicates serialization logic; inconsistent interfaces; harder to write generic code.

### 3. Dict/TypedDict Instead of Dataclass

Use dictionaries for maximum flexibility:

```python
TddRedResult = TypedDict('TddRedResult', {'test_file': Path, ...})
```

**Rejected because:** Loses IDE autocomplete; no default serialization; easier to have typos in key names.

### 4. Protocol-Based Interface

Define a Protocol that Results must implement:

```python
class ResultProtocol(Protocol):
    def as_json(self) -> str: ...
    def as_toon(self) -> str: ...
```

**Rejected because:** Adds indirection without benefit; inheritance from base dataclass is simpler and achieves the same goal.
