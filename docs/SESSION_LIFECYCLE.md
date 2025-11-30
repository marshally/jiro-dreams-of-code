# Session Lifecycle

> How jiro orchestrates task execution with preflight and postflight checks.

## Overview

A **session** is a single invocation of `jiro execute`. It runs tasks sequentially, with validation checks at multiple levels to ensure quality and catch errors early.

## Lifecycle Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SESSION START                                  │
│                     jiro execute [--epic EPIC_ID]                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SESSION PREFLIGHT                                │
├─────────────────────────────────────────────────────────────────────────┤
│  ✓ Git repo is clean (no uncommitted changes)                           │
│  ✓ On correct base branch (default: main)                               │
│  ✓ Branch up to date with origin                                        │
│  ✓ All tests pass                                                       │
│  ✓ All linters pass                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│  On failure: HALT → Human fixes issue → Resume with prompt              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │     For each ready task:      │
                    │   (respecting dependencies)   │
                    └───────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          TASK PREFLIGHT                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  1. Run relevant tests (convention-based matching)                      │
│  2. Lint relevant files (files likely to be modified)                   │
│  3. Planning agent (Opus) enhances task:                                │
│     • Analyzes codebase context                                         │
│     • Identifies specific files, line numbers                           │
│     • Produces detailed step-by-step execution plan                     │
│     • Sets up verification command                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  On failure: HALT → Human intervention required                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         TASK EXECUTION                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  Execution agent (Haiku) mechanically follows the plan:                 │
│                                                                         │
│  For each step in plan:                                                 │
│    1. Execute the step (read/write/edit files)                          │
│    2. Run verification command                                          │
│    3. Create strongly-typed commit                                      │
│       • Commit script enforces type rules                               │
│       • Embeds verification results in message                          │
│       • Records to database                                             │
│                                                                         │
│  Tools available: Read, Write, Edit, Bash (verification only)           │
├─────────────────────────────────────────────────────────────────────────┤
│  On error: HALT → Human intervention required                           │
│  On commit rule violation: Script raises error → HALT                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         TASK POSTFLIGHT                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  1. Review agent (Sonnet) validates commits:                            │
│     • Deterministic checks (Python):                                    │
│       - Files match claimed commit type                                 │
│       - Message follows template                                        │
│       - Task reference valid                                            │
│     • LLM judgment checks:                                              │
│       - Changes match description                                       │
│       - No scope creep                                                  │
│       - Flag concerns                                                   │
│                                                                         │
│  2. Run relevant tests (for modified files)                             │
│  3. Lint modified files                                                 │
│  4. Record results to database                                          │
│  5. Mark task complete in issue tracker                                 │
├─────────────────────────────────────────────────────────────────────────┤
│  On validation failure: HALT → Human must review                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │    More tasks remaining?      │
                    └───────────────────────────────┘
                          │                 │
                         Yes                No
                          │                 │
                          ▼                 ▼
                    [Task Preflight]        │
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        SESSION POSTFLIGHT                                │
├─────────────────────────────────────────────────────────────────────────┤
│  ✓ All tests pass (full suite)                                          │
│  ✓ All linters pass (all files)                                         │
│  ✓ Push branch to origin                                                │
├─────────────────────────────────────────────────────────────────────────┤
│  On failure: HALT → Human fixes issue → Resume with prompt              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          SESSION COMPLETE                                │
│                      Status: completed in database                       │
└─────────────────────────────────────────────────────────────────────────┘
```

______________________________________________________________________

## Phase Details

### Session Preflight

Runs **once** at the start of `jiro execute`. Ensures the repository is in a clean, known state before any work begins.

| Check | Purpose |
|-------|---------|
| Git repo clean | No uncommitted changes that could be lost |
| Correct branch | On configured base branch (default: main) |
| Up to date | Fetched latest from origin |
| Tests pass | Full test suite green |
| Linters pass | All files pass lint |

**Skip optimization**: If session preflight passed within configured time (default: 60 minutes), expensive checks (full tests, full lint) are skipped.

### Task Preflight

Runs **before each task**. Prepares context and ensures relevant code is healthy.

| Step | Agent | Purpose |
|------|-------|---------|
| Relevant tests | Python | Run tests matching convention for files to be modified |
| Relevant lint | Python | Lint files likely to be modified |
| Enhance task | Planning (Opus) | Produce detailed execution plan with file paths, line numbers |

The planning agent's output is a structured YAML plan that the execution agent follows mechanically.

### Task Execution

The execution agent (Haiku) follows the plan step by step. It does not make autonomous decisions.

**Commit creation flow:**

1. Agent makes changes per plan step
1. Agent calls commit creation function with type and metadata
1. Python script validates changes match claimed type
1. Script renders commit message from Jinja2 template
1. Script creates git commit
1. Record stored in database

### Task Postflight

Runs **after each task**. Validates the work and records results.

| Step | Agent | Purpose |
|------|-------|---------|
| Review commits | Review (Sonnet) | Validate commits match their claimed types |
| Relevant tests | Python | Ensure modified code still works |
| Relevant lint | Python | Ensure modified files pass lint |
| Record results | Python | Store in database |
| Close task | Python | Mark complete in issue tracker |

### Session Postflight

Runs **once** at the end of `jiro execute`. Final validation before pushing.

| Check | Purpose |
|-------|---------|
| All tests pass | Full suite, not just relevant tests |
| All linters pass | All files, not just modified |
| Push to origin | Share the work |

______________________________________________________________________

## Error Handling

At any point, if a check fails or an error occurs:

1. **HALT immediately** - Don't continue to next step
1. **Record halt reason** - Store in database with session/task status
1. **Exit with code 5** - Signal operation halted
1. **Wait for human** - Human reviews logs, diagnoses issue

To resume:

```bash
jiro execute --resume "Explanation of what was fixed and how to continue"
```

See [ADR-006: Human-Guided Error Recovery](architecture/006-human-guided-error-recovery.md) for details.

______________________________________________________________________

## Database Records

Throughout the lifecycle, jiro records state to the database:

| Event | Table | Fields Updated |
|-------|-------|----------------|
| Session start | `sessions` | id, branch_name, status=running, started_at |
| Preflight pass | `sessions` | preflight_passed_at |
| Task start | `task_executions` | id, task_id, session_id, phase, status=running |
| Agent prompt | `prompts` | All fields including token counts |
| Commit created | `commits` | All fields including verification results |
| Task complete | `task_executions` | status=success, ended_at |
| Session halt | `sessions` | status=halted, halt_reason |
| Session complete | `sessions` | status=completed, ended_at |

See [DDL.md](DDL.md) for complete schema.

______________________________________________________________________

## Configuration

Relevant configuration options:

```yaml
# In ~/.jiro-dreams-of-code/$PROJECT/config.yaml

commands:
  test: "pytest"              # Test command
  lint: "ruff check"          # Lint command
  lint_fix: "ruff check --fix"

conventions:
  test_file_pattern: "test_{name}.py"  # For relevant test detection

preflight:
  skip_if_recent_minutes: 60  # Skip expensive checks if recent
```
