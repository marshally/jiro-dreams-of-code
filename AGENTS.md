# Agent Instructions

Instructions for AI agents working on this repository.

## Commit Philosophy

All work must be committed in **small, discrete, orthogonal increments**. Each commit should:

- **Be self-contained** - The commit works on its own without depending on subsequent commits
- **Deliver a sliver of value** - Even small, it should represent a complete, meaningful change
- **Be orthogonal** - Changes should not overlap or intertwine with unrelated changes
- **Touch minimal scope** - Prefer several small commits over one large commit

### Why Small Commits Matter

Small commits enable flexible git workflows:

- **Clean merges** - Less conflict surface area when merging branches
- **Easy rebases** - Smaller changes rebase cleanly onto updated branches
- **Cherry-picking** - Individual features or fixes can be moved between branches
- **Bisect-friendly** - Easier to identify which commit introduced a bug
- **Reviewable** - Each commit tells a clear story

### Examples

**Good**: Three separate commits

1. "Add User model with validation"
1. "Add user creation endpoint"
1. "Add user creation tests"

**Bad**: One large commit

1. "Add user feature with model, endpoint, and tests"

## Pull Request Protocol

Before creating a pull request, you MUST:

1. **Update CHANGELOG.md** - Add an entry under `[Unreleased]` describing your changes

   - Use the appropriate section: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, or `Security`
   - Write clear, user-facing descriptions of what changed
   - Reference issue IDs where applicable

1. **Follow conventional commits** - Use descriptive commit messages

1. **Ensure tests pass** - Run `pytest` before submitting

## Changelog Format

```markdown
## [Unreleased]

### Added
- New feature description

### Changed
- Description of change to existing functionality

### Fixed
- Bug fix description (fixes #123)
```

## Architecture Decision Records

When making a significant architectural decision, record it as an ADR in `docs/architecture/`.

ADRs should be:

- **Brief** - One page or less
- **Focused on WHY** - Explain the reasoning, not just the what
- **Honest about tradeoffs** - Document both positive and negative consequences

Use this template:

```markdown
# ADR-NNN: Title

## Status
Accepted | Superseded | Deprecated

## Context
What problem are we solving? What constraints exist?

## Decision
What did we decide to do?

## Consequences
### Positive
- Benefits of this decision

### Negative
- Tradeoffs we're accepting
```

## Issue Tracking

This project uses [Beads](https://github.com/beads-project/beads) for issue tracking. Use `bd` commands to manage work items rather than markdown TODOs.
