# Agent Instructions

Instructions for AI agents working on this repository.

## User Experience Decisions

**CRITICAL**: NEVER make UX decisions without explicit user approval.

This includes but is not limited to:

- Keyboard shortcuts and keybindings
- User-facing messages and prompts
- Interaction patterns (how users input data, navigate, etc.)
- Default behaviors that affect user workflow
- Adding new dependencies that change how users interact with the tool

### What to Do Instead

1. **ASK FIRST** - Before implementing any UX change, ask the user which approach they prefer
1. **Present options** - Give 2-4 concrete choices with tradeoffs
1. **Implement exactly what the user specifies** - Do not substitute your judgment for theirs
1. **If technical constraints prevent the requested approach** - STOP and explain the constraint, then ask how to proceed

### Examples

**Bad**: User says "use Shift+Enter to continue typing" and you implement Meta+Enter instead because of technical limitations.

**Good**: User says "use Shift+Enter to continue typing" and you respond: "Standard terminals can't distinguish Shift+Enter from Enter. Here are alternatives: (1) Meta+Enter, (2) double-Enter to submit, (3) Ctrl+D to submit. Which do you prefer?"

This rule exists because UX decisions directly affect the user's daily workflow. Getting them wrong wastes time and creates frustration.

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

## Design Principles

### YAGNI (You Aren't Gonna Need It)

Prefer simpler solutions until complexity is proven necessary:

- **Rule of 3** - Don't extract abstractions until you've seen the pattern at least 3 times
- **Start flat** - Begin with simple structures; add hierarchy only when needed
- **Defer decisions** - If unsure, choose the simpler option now; refactor later if needed

Examples from this codebase:

- Factory pattern over explicit subclasses for `ExecutionStep`
- Single `VerificationError` exception over a class hierarchy
- Minimal `PlanStep` dataclass (just `step_type` and `planning_context`)

### One-at-a-Time Questioning

When designing complex systems, ask focused questions sequentially:

- **One question per message** - Don't overwhelm with multiple decisions at once
- **Build on answers** - Each question should build on the previous answer
- **Target 95% confidence** - Keep asking until the design is clear enough to implement
- **Present options** - Give 2-4 concrete choices rather than open-ended questions

This approach produces better designs because each decision is made with full context from previous decisions.

### Incremental Documentation

Document as you design, not after:

1. **Design doc first** - Write the design document before creating implementation tasks
1. **Reference the doc** - Implementation tasks should link back to specific sections
1. **ADRs for decisions** - Record significant architectural decisions as ADRs
1. **Update on implementation** - If implementation diverges from design, update the doc

This ensures knowledge is captured while it's fresh and creates a clear trail from requirements to implementation.

## Issue Tracking

This project uses [Beads](https://github.com/beads-project/beads) for issue tracking. Use `bd` commands to manage work items rather than markdown TODOs.

## Beads Commit Isolation

**CRITICAL**: `.beads/` files must ALWAYS be committed separately from code changes.

### Handling the Pre-commit Hook Error

When you see this error:

```
ERROR - .beads/ files must be committed separately from other files.
```

Follow this recovery procedure:

1. **Unstage beads files**: `git restore --staged .beads/`
1. **Commit your code changes first**
1. **Then commit beads changes separately**:
   ```bash
   git add .beads/
   git commit -m "chore(beads): update task status"
   ```

### Proactive Workflow

To avoid the error entirely, always follow this order:

1. After `bd update` or other beads commands, immediately commit beads changes:
   ```bash
   git add .beads/
   git commit -m "chore(beads): claim task [task-id]"
   ```
1. Then do your code work and commit code separately
1. After `bd close`, commit beads changes again:
   ```bash
   git add .beads/
   git commit -m "chore(beads): close task [task-id]"
   ```
