# ADR-001: Use --frozen flag for uv sync in CI

## Status

Accepted

## Context

When running `uv sync` in GitHub Actions CI, we encountered intermittent failures:

```
error: Failed to spawn: `ruff`
  Caused by: No such file or directory (os error 2)
```

This occurred because `uv sync` without `--frozen` may attempt to update the lockfile or resolve dependencies differently than expected, leading to race conditions or missing binaries in the virtual environment.

## Decision

Use `uv sync --frozen` in all CI workflows.

```yaml
- name: Install dependencies
  run: uv sync --frozen --extra dev --extra test
```

## Consequences

### Positive

- **Reproducible builds**: CI uses exact versions from `uv.lock`
- **Faster installs**: No dependency resolution needed
- **Reliable**: Eliminates "Failed to spawn" errors
- **Explicit failures**: If `uv.lock` is outdated, CI fails clearly

### Negative

- **Must keep uv.lock updated**: Developers must run `uv sync` locally and commit the lockfile when dependencies change
- **CI won't catch lockfile drift**: If someone forgets to update `uv.lock`, CI still passes with stale deps

## Alternatives Considered

1. **Use `uv tool run`**: Runs tools without project venv, but uses uv's tool cache instead of project's pinned versions
1. **Explicitly create venv first**: `uv venv && uv sync` - more verbose, still has resolution overhead
1. **No lockfile**: Let CI resolve fresh each time - slower and non-reproducible
