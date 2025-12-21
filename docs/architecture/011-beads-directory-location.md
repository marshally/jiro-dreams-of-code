# ADR-011: Beads Directory Location

## Status

Accepted

## Context

ADR-005 established that Beads integration uses the `bd` CLI and that each project gets its own isolated database. However, the exact directory structure was ambiguous, leading to a bug where `BeadsTracker` looked for `.beads/` in the project root while `jiro init` created it inside `.jiro-dreams-of-code/.beads/`.

## Decision

The Beads database **always** lives inside the jiro directory:

```
# Normal mode
project/
  .jiro-dreams-of-code/
    .beads/           # <- beads database here
    config.yaml
    specs/
    logs/

# Stealth mode
~/.jiro-dreams-of-code/
  $PROJECT_NAME/
    .beads/           # <- beads database here
    config.yaml
    specs/
    logs/
```

This is implemented in `BeadsTracker.__init__`:

```python
jiro_dir = get_jiro_dir(project_root, stealth=stealth, project_name=project_name)
self.beads_dir = jiro_dir / ".beads"  # Always inside jiro_dir
```

## Consequences

### Positive

- **Consistency**: Same structure in both normal and stealth modes
- **Containment**: All jiro state is inside `.jiro-dreams-of-code/`
- **Gitignore simplicity**: One entry (`.jiro-dreams-of-code/`) ignores everything
- **Clean separation**: Project root stays clean; jiro state is isolated

### Negative

- **Nesting**: Beads lives at `.jiro-dreams-of-code/.beads/` (two levels deep)
- **Manual bd usage**: Must `cd .jiro-dreams-of-code` to run `bd` commands directly

### Mitigations

- `jiro` CLI wraps all `bd` operations, so users rarely need direct access
- `jiro doctor` verifies the structure is correct
