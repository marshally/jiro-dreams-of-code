# ADR-005: Beads Integration via bd CLI

## Status

Accepted

## Context

Jiro needs an issue tracker to manage tasks generated from specs. The spec defines an `IssueTracker` protocol/facade that abstracts the underlying implementation, with Beads as the default for the steel thread.

We have three options for integrating with Beads:

1. Import Beads as a Python library and use internal APIs
1. Shell out to the `bd` CLI
1. Use Beads MCP server via MCP protocol

## Decision

Shell out to the `bd` CLI for all issue tracker operations.

```python
class BeadsTracker:
    def __init__(self, beads_root: Path):
        self.beads_root = beads_root

    def create_task(self, title: str, ...) -> Task:
        result = subprocess.run(
            ["bd", "create", "--title", title, ...],
            cwd=self.beads_root,
            capture_output=True,
            text=True
        )
        return self._parse_task(result.stdout)

    def list_tasks(self, status: str | None = None) -> list[Task]:
        cmd = ["bd", "list", "--json"]
        if status:
            cmd.extend(["--status", status])
        result = subprocess.run(cmd, ...)
        return self._parse_tasks(result.stdout)
```

Each jiro-managed project gets its own isolated Beads database:

- Normal mode: `.jiro-dreams-of-code/.beads/`
- Stealth mode: `~/.jiro-dreams-of-code/$PROJECT/.beads/`

## Consequences

### Positive

- **Decoupling**: Jiro doesn't depend on Beads internals; only the CLI contract
- **Stability**: CLI is the public API; less likely to break than internal APIs
- **Debuggability**: Can manually run `bd` commands to inspect/fix state
- **Swappability**: Easy to implement other trackers (GitHub Issues, Jira) with same pattern
- **No version coupling**: Jiro works with any Beads version that has compatible CLI

### Negative

- **Subprocess overhead**: Each operation spawns a process; slower than library calls
- **Parsing overhead**: Must parse JSON/text output; library would return objects directly
- **Error handling**: Must parse stderr for error messages
- **Feature lag**: Can't use Beads features not exposed via CLI

### Mitigations

- Use `--json` output for reliable parsing
- Cache frequently-accessed data where appropriate
- Batch operations where possible (future optimization)

## Alternatives Considered

1. **Import as library**: Tighter coupling; internal APIs may change; harder to swap implementations
1. **MCP server**: More complex setup; overkill for local issue tracking; adds MCP as dependency
1. **Reimplement minimal subset**: More control but duplicates effort; loses Beads ecosystem benefits
1. **Direct SQLite access**: Bypasses Beads entirely; breaks if schema changes; not portable to other trackers
