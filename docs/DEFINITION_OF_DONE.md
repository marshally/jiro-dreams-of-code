# Definition of Done

This document defines what "done" means for tasks in jiro. Every task must meet these criteria before being marked complete.

## Core Principle

**A task is a complete, shippable unit of work.** Testing, documentation, and quality checks are not separate tasks—they are part of every task's completion criteria.

## Checklist

A task is done when:

- \[ \] **Code works** - The feature/fix functions as specified
- \[ \] **Tests pass** - Unit tests cover the new/changed code
- \[ \] **Linting passes** - No lint errors (`ruff check`)
- \[ \] **Types check** - No type errors (`mypy` or equivalent)
- \[ \] **Docs updated** - Docstrings for public APIs, comments for complex logic
- \[ \] **Committed** - Changes are committed with a clear message

## What This Means for Planning

When `jiro plan` decomposes a spec into tasks, it **must not** create separate tasks for:

- Writing tests
- Adding documentation
- Running linting/formatting
- Adding type hints
- Adding logging/observability
- Validation and error handling

### Anti-Patterns

```
Epic: User Authentication
  Task 1: Implement login endpoint
  Task 2: Write tests for login       <- WRONG: Testing is separate
  Task 3: Add documentation           <- WRONG: Docs are separate
  Task 4: Add logging                 <- WRONG: Observability is separate
```

### Correct Pattern

```
Epic: User Authentication
  Task 1: Implement login endpoint    <- Includes tests, docs, logging
  Task 2: Implement logout endpoint   <- Includes tests, docs, logging
  Task 3: Implement password reset    <- Includes tests, docs, logging
```

## Rationale

1. **Atomic commits**: Each task produces a complete, reviewable commit
1. **No orphaned code**: Tests ship with the code they test
1. **Continuous quality**: Quality is built in, not bolted on
1. **Accurate estimation**: Tasks reflect real work, not artificial phases
1. **Simpler dependencies**: No "tests depend on implementation" chains

## Exceptions

Some tasks are inherently about quality improvements to existing code:

- **Refactoring**: Improving structure without changing behavior (still includes updating tests)
- **Bug fixes**: Fixing existing behavior (includes regression tests)
- **Tech debt**: Paying down accumulated shortcuts (includes any needed tests)

Even these tasks include their own tests and documentation updates.

## See Also

- [TECHNICAL_SPEC.md](./TECHNICAL_SPEC.md) - Overall system design
- [STRONGLY_TYPED_COMMITS.md](./STRONGLY_TYPED_COMMITS.md) - Commit conventions
