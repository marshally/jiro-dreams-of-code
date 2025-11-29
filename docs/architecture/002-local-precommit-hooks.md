# ADR-002: External vs Local Pre-commit Hooks

## Status

Accepted (partial migration to local hooks)

## Context

Pre-commit supports two types of hook sources:

**External hooks** (from repos):

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.8.4
  hooks:
    - id: ruff
```

**Local hooks** (using project tools):

```yaml
- repo: local
  hooks:
    - id: ruff
      entry: uv run ruff check
      language: system
```

External hooks create isolated virtual environments for each hook repository. This adds ~30-60 seconds to first run and uses disk space for duplicate tool installations.

## Decision

Use a hybrid approach:

1. **Local hooks** for tools already in our dev dependencies (pytest)
1. **External hooks** for tools with complex dependencies or additional plugins (ruff, mypy, mdformat)

Current local hooks:

- `pytest-unit` - uses `uv run pytest`
- `pytest-full` - uses `uv run pytest`
- `no-commit-to-main` - custom bash script
- `isolate-beads` - custom bash script

Current external hooks:

- `ruff` / `ruff-format` - from ruff-pre-commit
- `mypy` - from mirrors-mypy
- `mdformat` - from mdformat repo

## Consequences

### Positive

- **Isolation**: External hooks can't conflict with project dependencies
- **Consistency**: External hooks use pinned versions independent of project
- **Simpler config**: No need to specify `types`, `language`, etc.

### Negative

- **Slower first run**: Each external repo creates its own venv
- **Disk usage**: Duplicate installations of tools
- **Version drift**: External hook versions may differ from project versions

## Future Consideration

If pre-commit performance becomes a bottleneck, migrate more hooks to local:

```yaml
- repo: local
  hooks:
    - id: ruff
      name: ruff
      entry: uv run ruff check --no-fix
      language: system
      types: [python]

    - id: ruff-format
      name: ruff-format
      entry: uv run ruff format --check --diff
      language: system
      types: [python]
```

This would eliminate the isolated venv overhead but requires maintaining hook configuration manually.
