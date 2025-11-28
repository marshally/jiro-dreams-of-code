# jiro-dreams-of-code Technical Specification

> "I'll continue to climb, trying to reach the top, but no one knows where the top is." — Jiro Ono

A disciplined AI agent orchestration system that builds software using the shokunin philosophy: mastery through small, deliberate, repeated steps.

## Table of Contents

1. [Overview](#overview)
2. [Philosophy](#philosophy)
3. [Architecture](#architecture)
4. [CLI Style Guide](#cli-style-guide)
5. [CLI Commands](#cli-commands)
6. [Core Workflow](#core-workflow)
7. [Agent System](#agent-system)
8. [Commit Discipline](#commit-discipline)
9. [Preflight & Postflight Checks](#preflight--postflight-checks)
10. [Configuration System](#configuration-system)
11. [Data Storage](#data-storage)
12. [Web UI](#web-ui)
13. [Issue Tracker Facade](#issue-tracker-facade)
14. [Context Tracking](#context-tracking)
15. [Error Handling & Human Escalation](#error-handling--human-escalation)
16. [Directory Structure](#directory-structure)
17. [Project Setup](#project-setup)
18. [Steel Thread Scope](#steel-thread-scope)
19. [Definition of Done](#definition-of-done)
20. [Design Principle: Python Over LLM](#design-principle-python-over-llm)
21. [Customizable Assets](#customizable-assets)
22. [Future Enhancements](#future-enhancements)

---

## Overview

jiro-dreams-of-code is a CLI and web-based tool that:

1. Takes a natural language prompt and generates a detailed specification
2. Breaks specifications into granular, dependency-aware tasks
3. Spawns AI agents to execute tasks with strict discipline
4. Enforces commit hygiene through validation rules
5. Tracks context usage and metrics for every prompt

### Key Principles

- **Extremely granular commits**: One lint fix = one commit. One refactoring = one commit.
- **Strict TDD**: Red-green-refactor with separate commits for each phase
- **Agent review**: Every commit is validated against discipline rules
- **Context awareness**: Track token usage to optimize agent efficiency
- **Parallelizable work**: Epics are independent workstreams that can run concurrently
- **Python over LLM**: Anything that can be done deterministically with Python code should be—conserves context and ensures precision
- **Customizable assets**: All scripts and prompts are bundled in the package but overridable per-project or per-user

---

## Philosophy

Named after Jiro Ono, the 93-year-old sushi master from "Jiro Dreams of Sushi," this project embodies:

- **Shokunin** (職人): The artisan spirit—dedication to mastering one craft through continuous refinement
- **Kaizen**: Continuous small improvements
- **Discipline over speed**: Correctness and reviewability trump velocity

Every commit should be reviewable by another agent or human. The granularity enables:
- Automated validation of discipline adherence
- Easy rollback of specific changes
- Clear audit trail of decision-making

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI (Typer)                             │
├─────────────────────────────────────────────────────────────────┤
│                      Web UI (FastAPI + HTMX)                    │
├─────────────────────────────────────────────────────────────────┤
│                         Core Services                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  Dream   │ │   Plan   │ │ Execute  │ │     Session      │   │
│  │ Service  │ │ Service  │ │ Service  │ │    Manager       │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                         Agent Layer                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Planning │ │Execution │ │  Review  │ │      Spec        │   │
│  │  Agent   │ │  Agent   │ │  Agent   │ │   Refinement     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                      Infrastructure                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │  Issue   │ │  Config  │ │ Metrics  │ │       Git        │   │
│  │ Tracker  │ │  System  │ │    DB    │ │    Operations    │   │
│  │ (Beads)  │ │          │ │ (SQLite) │ │                  │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| CLI Framework | Typer |
| Web Framework | FastAPI + HTMX |
| Agent SDK | Claude Agent SDK |
| Database | SQLite |
| Issue Tracking | Beads (default), facade for others |
| Package Manager | uv |
| Testing | pytest, pytest-asyncio, pytest-cov, pytest-httpx, VCR |
| Linting | Ruff |
| Type Checking | mypy |

---

## CLI Style Guide

### Command Naming Convention

jiro follows the **verb-noun** pattern used by git, docker, and kubectl:

```
jiro <verb> [noun] [options]
```

| Pattern | Example | Description |
|---------|---------|-------------|
| `jiro <verb>` | `jiro init`, `jiro execute` | Single action |
| `jiro <noun> <verb>` | `jiro tasks list`, `jiro config set` | Resource + action |
| `jiro <noun> <verb> <target>` | `jiro tasks show TASK_ID` | Resource + action + target |

### Naming Rules

1. **Lowercase only**: All commands and subcommands are lowercase
2. **Short and memorable**: Prefer `tasks` over `task-management`
3. **Verbs are imperative**: `list`, `show`, `create`, not `listing`, `showing`
4. **Nouns are plural for collections**: `tasks`, `assets`, `logs`
5. **No abbreviations unless standard**: `config` (standard), not `cfg`

### Standard Verbs

| Verb | Meaning | Example |
|------|---------|---------|
| `list` | Show all items | `jiro tasks list` |
| `show` | Show single item detail | `jiro tasks show TASK_ID` |
| `create` | Create new item | (future: `jiro tasks create`) |
| `update` | Modify existing item | (future: `jiro tasks update`) |
| `delete` | Remove item | (future: `jiro tasks delete`) |

### Output Formats

Every command that produces output **must** support three formats:

```bash
jiro tasks list              # Human-readable (default)
jiro tasks list --json       # JSON for machine parsing
jiro tasks list --toon       # TOON for LLM token efficiency
```

#### Human-Readable (Default)

Rich formatted output with colors, tables, and progress indicators:

```
Tasks (3 total)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ JIRO-1  Add user login          completed
● JIRO-2  Implement OAuth         in_progress
○ JIRO-3  Add session handling    pending
```

#### JSON (`--json`)

Standard JSON for scripting and machine consumption:

```json
{
  "tasks": [
    {"id": "JIRO-1", "title": "Add user login", "status": "completed"},
    {"id": "JIRO-2", "title": "Implement OAuth", "status": "in_progress"},
    {"id": "JIRO-3", "title": "Add session handling", "status": "pending"}
  ]
}
```

#### TOON (`--toon`)

[Token-Oriented Object Notation](https://github.com/toon-format/toon) for LLM inputs—~40% fewer tokens than JSON:

```
tasks[3]{id,title,status}:
 JIRO-1,Add user login,completed
 JIRO-2,Implement OAuth,in_progress
 JIRO-3,Add session handling,pending
```

### Option Naming

1. **Long form required**: Every option must have `--long-form`
2. **Short form optional**: Common options may have `-s` short form
3. **Boolean flags**: Use `--flag/--no-flag` pattern for toggles
4. **Consistent across commands**: Same option = same name everywhere

| Option | Short | Description |
|--------|-------|-------------|
| `--json` | | JSON output format |
| `--toon` | | TOON output format |
| `--verbose` | `-v` | Increase verbosity (stackable: `-vv`) |
| `--quiet` | `-q` | Suppress non-error output |
| `--help` | `-h` | Show help |
| `--version` | | Show version |
| `--epic` | `-e` | Filter by epic |
| `--status` | `-s` | Filter by status |

### Help Text Standards

Every command must have:

1. **One-line description**: Shown in parent command's help
2. **Detailed description**: Shown in `--help` for the command
3. **Examples**: At least one usage example
4. **Option documentation**: Every option explained

```bash
$ jiro tasks --help

Usage: jiro tasks [OPTIONS] COMMAND [ARGS]...

  Manage and view tasks in the issue tracker.

Commands:
  list   List all tasks with optional filters
  show   Show detailed information about a task
  next   Show the next task to be executed

Examples:
  jiro tasks list
  jiro tasks list --status pending --epic JIRO-42
  jiro tasks show JIRO-15
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid usage / bad arguments |
| 3 | Configuration error |
| 4 | Resource not found |
| 5 | Operation halted (human intervention needed) |

---

## CLI Commands

### Project Setup

```bash
jiro init [--stealth] [--interactive]
```
- Creates project configuration and beads database
- `--stealth`: Store all files in `~/.jiro-dreams-of-code/$PROJECT_NAME/` instead of project root
- `--interactive`: Prompt for test command, lint command, etc.
- **Requires**: Must be run inside a git repository

```bash
jiro doctor [--fix]
```
- Verify installation and configuration health
- `--fix`: Attempt auto-remediation of fixable issues
- Validates that an Anthropic API key is available from either the environment or the system keyring (warns if both are configured)

### Anthropic Credentials

Commands that integrate with Anthropic require a key sourced from one of two locations:

1. The `ANTHROPIC_API_KEY` environment variable
2. The OS keyring entry that `jiro` manages

`jiro doctor` inspects both sources, issuing a warning if duplicates are detected so users can consolidate on a single source of truth. If neither source is available, any command that depends on Anthropic exits immediately with a clear error before performing additional work.

### Spec & Planning

```bash
jiro dream "prompt"
```
- Generate a specification from natural language
- Opens interactive chat refinement mode
- Saves spec to `.jiro-dreams-of-code/specs/` (or stealth equivalent)

```bash
jiro plan --spec "auth-system.md" ["optional refinement prompt"]
```
- Parse spec and generate epics + tasks
- Analyze dependencies between tasks
- Output summary with clickable spec file path
- Prompt: `Proceed? [yes/chat/edit/quit]`
- Accepts either the bare spec filename (resolved in `.jiro-dreams-of-code/specs/` or its stealth equivalent) or an explicit path if you store specs elsewhere

### Task Management

```bash
jiro tasks list
```
- Show summary of all tasks (grouped by epic, status)

```bash
jiro tasks show TASK_ID
```
- Show full detail of a specific task

```bash
jiro tasks next
```
- Show full detail of the next task to be executed

### Execution

```bash
jiro execute [--epic EPIC_ID]
```
- Run session preflight checks
- Iteratively execute tasks
- Run session postflight checks
- `--epic`: Limit execution to a specific epic

```bash
jiro status
```
- Show status of all active sessions for this project

### Configuration

```bash
jiro config [--global|--project|--local] [key] [value]
jiro config --list [--global|--project|--local]
```
- Get/set configuration values (git-style interface)
- `--global`: `~/.jiro-dreams-of-code/config.yaml`
- `--project`: `~/.jiro-dreams-of-code/$PROJECT_NAME/config.yaml`
- `--local`: `./.jiro-dreams-of-code.yaml`

```bash
jiro mode [stealth|local]
```
- View or switch between stealth and local modes
- Migrates all data when switching

### Observability

```bash
jiro logs
```
- View logs (with filtering options)

```bash
jiro web [--daemon]
```
- Start web UI on localhost:8888
- `--daemon`: Run in background

### Asset Management

```bash
jiro assets list
```
- List all assets and their source locations

```bash
jiro assets which <asset-path>
```
- Show where a specific asset is loaded from

```bash
jiro assets customize <asset-path> [--local|--project|--global]
```
- Copy package default to specified location for customization

---

## Core Workflow

### 1. Dream Phase

```
User: jiro dream "build a user authentication system with OAuth"

Agent generates spec with defined schema:
┌─────────────────────────────────────────┐
│ # Feature: User Authentication          │
│                                         │
│ ## Overview                             │
│ <high-level description>                │
│                                         │
│ ## Requirements                         │
│ - <requirement 1>                       │
│ - <requirement 2>                       │
│                                         │
│ ## Acceptance Criteria                  │
│ - [ ] <criterion 1>                     │
│ - [ ] <criterion 2>                     │
│                                         │
│ ## Out of Scope                         │
│ - <explicitly excluded items>           │
│                                         │
│ ## Technical Notes                      │
│ <implementation hints>                  │
└─────────────────────────────────────────┘

Interactive refinement via chat (terminal or web UI)
```

### 2. Plan Phase

```
User: jiro plan --spec "auth-system.md"

Agent analyzes spec and produces:
- Multiple epics (parallelizable workstreams)
- Tasks within each epic (with dependencies)
- Task metadata:
  - Type (feature-tdd, refactor, docs, bugfix, config, test-only, performance)
  - Estimated complexity
  - Affected files (if known)
  - Acceptance criteria

Output:
┌─────────────────────────────────────────┐
│ Planning complete.                      │
│                                         │
│ Spec: .jiro-dreams-of-code/specs/auth-system.md│
│                                         │
│ This will create:                       │
│ - 3 epics (2 parallel, 1 dependent)     │
│ - 14 tasks total                        │
│                                         │
│ Epic 1: OAuth Integration (5 tasks)     │
│ Epic 2: Session Management (5 tasks)    │
│ Epic 3: User Profile (4 tasks)          │
│   └── depends on Epic 1, Epic 2         │
│                                         │
│ Proceed? [yes/chat/edit/quit]           │
└─────────────────────────────────────────┘
```

### 3. Execute Phase

```
User: jiro execute --epic JIRO-42

Session Preflight:
  ✓ Git repo is clean
  ✓ On base branch (main)
  ✓ Branch up to date with origin
  ✓ All tests pass
  ✓ All linters pass

For each task:
  Task Preflight:
    ✓ Relevant tests pass
    ✓ Relevant files linted
    → Planning subagent enhances task spec (files, line numbers)

  Execution:
    → Agent executes with TDD discipline
    → Granular commits created

  Task Postflight:
    → Review agent validates commits
    ✓ Relevant tests pass
    ✓ Relevant files linted
    → Results recorded to database

Session Postflight:
  ✓ All tests pass
  ✓ All linters pass
  → Branch pushed to origin
```

---

## Agent System

### Agent Types

| Agent | Model (Default) | Capabilities | Purpose |
|-------|-----------------|--------------|---------|
| Dreaming | claude-sonnet-4-5-20250929 | Read, WebSearch | Generate specs from prompts |
| Planning | claude-sonnet-4-5-20250929 | Read, WebSearch | Break specs into tasks, analyze dependencies |
| Execution | claude-haiku | Read, Write, Bash (constrained), Git | Execute tasks with TDD discipline |
| Review | claude-sonnet-4-5-20250929 | Read | Validate commits against discipline rules |

### Execution Agent Permissions

**Allowed:**
- File read/write/edit
- Bash: test commands, lint commands
- Git: commit, checkout, merge, rebase, push
- GitHub CLI: `gh pr create`, `gh pr view`

**Not Allowed:**
- Web search (planning agent handles research)
- Arbitrary bash commands

### Planning Subagent (Task Preflight)

Before each task executes, a planning subagent:
- Reviews the task specification
- Identifies specific files, line numbers, byte ranges
- Updates task with detailed execution hints
- Has read-only access + web search

### Model Configuration

```yaml
models:
  dreaming: claude-sonnet-4-5-20250929
  planning: claude-sonnet-4-5-20250929
  execution: claude-haiku
  review: claude-sonnet-4-5-20250929
```

Configurable per-project and overridable per-invocation:
```bash
jiro dream --model claude-opus-4 "complex architectural decision"
```

---

## Commit Discipline

### Commit Types

| Type | Emoji | Rules |
|------|-------|-------|
| TDD Red | 🔴 | Only test files modified; test must FAIL |
| TDD Green | 🟢 | Only code files modified; test must PASS; minimal code |
| TDD Refactor | ♻️ | Code files only; tests must still PASS; no new functionality |
| Refactoring | ♻️ | Behavior-neutral; uses refactoring MCP; never changes tests |
| Documentation | 📝 | Only .md files, docstrings, or comments |
| Lint Fix | 🧹 | Single lint error fixed per commit |
| Bug Fix | 🐛 | Follows red-green pattern |
| Config | ⚙️ | Configuration changes; warning if mixed with code |
| Test Only | 🧪 | Adding tests to existing code |
| Performance | ⚡ | Optimization changes |

### Commit Message Format

```
:emoji: Imperative description of what the commit does

Task: JIRO-42 - Implement user login endpoint
Reason: Add authentication capability for API consumers
Tests: pytest tests/test_auth.py -k "test_login" → 3 passed (0.8s)
Time: 2m 34s
Context: 12,450 tokens (8,200 → 20,650)
```

For TDD Red commits (showing failure):
```
🔴 Add failing test for user login validation

Task: JIRO-42 - Implement user login endpoint
Reason: Establish expected behavior before implementation
Tests: pytest tests/test_auth.py -k "test_login_validates_email"
  ✗ test_login_validates_email: AssertionError: expected ValidationError
  (1 failed, 0.2s)
Time: 1m 12s
Context: 8,200 tokens (0 → 8,200)
```

### Validation Rules (Hardcoded - The Jiro Discipline)

| Commit Type | Validation |
|-------------|------------|
| Refactoring | Must use behavior-neutral refactorings; include refactoring MCP command + results; never change tests; tests must pass |
| TDD Red | Only test files changed; test command must show failure |
| TDD Green | Only code files changed; test command must show success |
| TDD Refactor | No test changes; tests must pass; no new functionality |
| Lint Fix | Single lint error + single fix per commit |
| Docs (md) | Always isolated; never mixed with code commits |
| Docstrings | Updated with associated code change |
| Config | Ideally isolated; warning (not halt) if mixed with code/tests |

**On validation failure**: HALT and page human for help.

---

## Preflight & Postflight Checks

### Session Preflight

Runs once at the start of `jiro execute`:

| Check | Action |
|-------|--------|
| Git repo is clean | Assert no changed/staged files |
| Correct base branch | Assert on configured base branch (default: main) |
| Branch up to date | Fetch and verify latest from origin |
| All tests pass | Run full test suite; fix failures |
| All linters pass | Run linters on all files; fix errors |

**Skip optimization**: If session preflight passed within configured time (default: 60 minutes), expensive checks (full tests, full lint) are skipped.

```yaml
preflight:
  skip_if_recent_minutes: 60
```

### Session Postflight

Runs once at the end of `jiro execute`:

| Check | Action |
|-------|--------|
| All tests pass | Run full test suite |
| All linters pass | Run linters on all files |
| Push to origin | Push branch to remote |

### Task Preflight

Runs before each task:

| Check | Action |
|-------|--------|
| Relevant tests pass | Run tests matching convention |
| Relevant files linted | Lint files likely to be modified |
| Enhance task spec | Planning subagent adds file paths, line numbers, byte ranges |

### Task Postflight

Runs after each task:

| Check | Action |
|-------|--------|
| Review commits | Validate all commits against discipline rules |
| Relevant tests pass | Run tests for modified files |
| Relevant files linted | Lint all modified files |
| Record results | Save to database |

**On review failure**: HALT and page human.

### Determining "Relevant" Tests

Steel thread uses convention-based matching:

```yaml
conventions:
  test_file_pattern: "test_{name}.py"  # or "{name}_test.py"
```

Fallback: If no matching tests found, run all tests.

### Determining "Relevant" Files for Linting

All files modified during the current task.

---

## Configuration System

### Precedence (highest to lowest)

1. CLI flags
2. Local config (`./.jiro-dreams-of-code.yaml`)
3. Project config (`~/.jiro-dreams-of-code/$PROJECT_NAME/config.yaml`)
4. Global config (`~/.jiro-dreams-of-code/config.yaml`)

**Conflict handling**: If keys conflict between local and project config, warn the user. Local takes precedence.

### Configuration Schema

```yaml
project:
  name: my-project                    # default: derived from git remote
  base_branch: main

commands:
  test: "pytest"
  lint: "ruff check"
  lint_fix: "ruff check --fix"

conventions:
  test_file_pattern: "test_{name}.py"

preflight:
  skip_if_recent_minutes: 60

models:
  dreaming: claude-sonnet-4-5-20250929
  planning: claude-sonnet-4-5-20250929
  execution: claude-haiku
  review: claude-sonnet-4-5-20250929

limits:
  max_context_percent: 85             # of model's context window

web:
  port: 8888

commit:
  style: default                      # or path to custom template
```

### CLI Config Interface

```bash
# Set values at different scopes
jiro config --global commands.test "pytest"
jiro config --project commands.test "npm test"
jiro config --local commands.test "make test"

# Get values (shows effective value + source scope)
jiro config commands.test

# List all
jiro config --list
jiro config --list --global
```

---

## Data Storage

### Database: jiro.db (SQLite)

Location:
- Normal mode: `.jiro-dreams-of-code/jiro.db`
- Stealth mode: `~/.jiro-dreams-of-code/$PROJECT_NAME/jiro.db`

#### Schema

```sql
-- Sessions
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    epic_id TEXT,
    branch_name TEXT NOT NULL,
    status TEXT NOT NULL,  -- running, completed, failed, halted
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    preflight_passed_at TIMESTAMP
);

-- Prompts (context tracking)
CREATE TABLE prompts (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    task_id TEXT,
    prompt_text TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_before INTEGER NOT NULL,
    tokens_after INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- Task executions
CREATE TABLE task_executions (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    session_id TEXT REFERENCES sessions(id),
    phase TEXT NOT NULL,  -- preflight, executing, postflight
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    status TEXT NOT NULL,  -- running, success, failed, halted
    halt_reason TEXT
);

-- Commits
CREATE TABLE commits (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    session_id TEXT REFERENCES sessions(id),
    sha TEXT NOT NULL,
    commit_type TEXT NOT NULL,
    message TEXT NOT NULL,
    test_command TEXT,
    test_output_summary TEXT,
    time_taken_seconds INTEGER,
    created_at TIMESTAMP NOT NULL
);
```

### Issue Tracker: Beads

Location:
- Normal mode: `.jiro-dreams-of-code/.beads/`
- Stealth mode: `~/.jiro-dreams-of-code/$PROJECT_NAME/.beads/`

---

## Web UI

### Technology

- **Backend**: FastAPI
- **Frontend**: HTMX (minimal JavaScript)
- **Port**: 8888 (configurable)
- **Auth**: None (localhost only, single user)

### Views

1. **Spec Refinement**
   - Left panel: Rendered spec markdown
   - Right panel: Chat interface for refinement
   - Shows diffs after each change

2. **Task List**
   - Grouped by epic
   - Status indicators
   - Click to view detail

3. **Execution Status**
   - Live view of running sessions
   - Current task, phase, context usage
   - Log streaming

4. **Metrics/History**
   - Prompt history with context usage
   - Commit history
   - Session history

5. **Logs**
   - Live tail during execution
   - Historical browse with filtering

### Starting the UI

```bash
jiro web              # foreground
jiro web --daemon     # background
```

---

## Issue Tracker Facade

### Interface

```python
from typing import Protocol

class IssueTracker(Protocol):
    def create_task(
        self,
        title: str,
        description: str,
        task_type: str,
        priority: int = 2,
        labels: list[str] | None = None,
        deps: list[str] | None = None,
    ) -> Task: ...

    def get_task(self, task_id: str) -> Task: ...

    def list_tasks(
        self,
        status: str | None = None,
        epic_id: str | None = None,
    ) -> list[Task]: ...

    def update_task(
        self,
        task_id: str,
        status: str | None = None,
        **kwargs,
    ) -> Task: ...

    def get_next_ready_task(self, epic_id: str | None = None) -> Task | None: ...

    def add_dependency(
        self,
        task_id: str,
        depends_on_id: str,
    ) -> None: ...

    def close_task(self, task_id: str, reason: str = "Completed") -> None: ...
```

### Implementations

**Steel thread**: Beads (default)

**Future**: GitHub Issues, Jira, Linear

---

## Context Tracking

Every prompt sent to an agent is recorded:

| Field | Description |
|-------|-------------|
| prompt_text | Full prompt content |
| model | Model used (e.g., claude-haiku) |
| tokens_before | Context tokens before this prompt |
| tokens_after | Context tokens after response |
| task_id | Associated task |
| session_id | Associated session |

### Stuck/Loop Detection

If context usage exceeds threshold, halt and page human:

```yaml
limits:
  max_context_percent: 85  # of model's context window
```

Default: 85% of one Haiku context window.

Configurable per task type for complex operations.

---

## Error Handling & Human Escalation

### Halt Conditions

| Condition | Action |
|-----------|--------|
| Commit fails validation | HALT, page human |
| Merge conflict unresolved after N attempts | HALT, page human |
| Agent stuck/looping (context limit exceeded) | HALT, page human |
| Task cannot be completed | Mark as blocked, continue to next |

### Notification (Steel Thread)

Terminal output with clear message. Session pauses until human intervenes.

### Recovery

After human fixes the issue:
```bash
jiro execute  # resumes from where it left off
```

### Future Notification Channels

- Web UI flash alerts
- Slack webhook
- Email
- SMS

---

## Directory Structure

### Normal Mode

```
$PROJECT_ROOT/
└── .jiro-dreams-of-code/
    ├── config.yaml           # local config
    ├── jiro.db               # metrics, prompts, sessions
    ├── specs/                # generated specifications
    │   └── auth-system.md
    ├── .beads/               # issue tracker database
    ├── worktrees/            # git worktrees for parallel execution
    │   └── epic-JIRO-42/
    └── logs/
        └── 2025-11-27.jsonl
```

### Stealth Mode

```
~/.jiro-dreams-of-code/
├── config.yaml               # global config
└── $PROJECT_NAME/
    ├── config.yaml           # project-scoped config
    ├── jiro.db               # metrics, prompts, sessions
    ├── specs/                # generated specifications
    │   └── auth-system.md
    ├── .beads/               # issue tracker database
    ├── worktrees/            # git worktrees for parallel execution
    │   └── epic-JIRO-42/
    └── logs/
        └── 2025-11-27.jsonl
```

### Project Name Derivation

Default: Derived from git remote URL (e.g., `github.com/user/repo` → `user-repo`)

Override: `jiro init --name custom-name`

---

## Project Setup

### Package Structure

```
jiro-dreams-of-code/
├── pyproject.toml
├── src/
│   └── jiro/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py           # Typer app entry point
│       │   ├── init.py
│       │   ├── dream.py
│       │   ├── plan.py
│       │   ├── tasks.py
│       │   ├── execute.py
│       │   ├── config.py
│       │   ├── doctor.py
│       │   ├── mode.py
│       │   ├── status.py
│       │   ├── logs.py
│       │   └── web.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── spec.py           # Spec generation and parsing
│       │   ├── planner.py        # Task decomposition
│       │   ├── executor.py       # Task execution orchestration
│       │   ├── session.py        # Session management
│       │   ├── commit.py         # Commit formatting and validation
│       │   └── checks.py         # Preflight/postflight checks
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py           # Base agent class
│       │   ├── dreaming.py       # Spec generation agent
│       │   ├── planning.py       # Task planning agent
│       │   ├── execution.py      # Task execution agent
│       │   └── review.py         # Commit review agent
│       ├── trackers/
│       │   ├── __init__.py
│       │   ├── interface.py      # IssueTracker protocol
│       │   └── beads.py          # Beads implementation
│       ├── web/
│       │   ├── __init__.py
│       │   ├── app.py            # FastAPI app
│       │   ├── routes/
│       │   └── templates/        # HTMX templates
│       ├── db/
│       │   ├── __init__.py
│       │   ├── connection.py
│       │   ├── models.py
│       │   └── migrations/
│       ├── config/
│       │   ├── __init__.py
│       │   ├── schema.py         # Config schema/validation
│       │   └── loader.py         # Config loading/merging
│       └── assets/               # Package default assets
│           ├── __init__.py
│           ├── loader.py         # Asset resolution logic
│           ├── prompts/
│           │   ├── dreaming_agent.md
│           │   ├── planning_agent.md
│           │   ├── execution_agent.md
│           │   └── review_agent.md
│           └── templates/
│               ├── commit/
│               │   ├── default.txt
│               │   ├── tdd_red.txt
│               │   ├── tdd_green.txt
│               │   └── refactor.txt
│               └── spec_schema.md
├── tests/
│   ├── conftest.py
│   ├── factories.py
│   ├── unit/
│   │   ├── conftest.py
│   │   ├── cli/
│   │   ├── core/
│   │   ├── agents/
│   │   ├── trackers/
│   │   └── db/
│   ├── integration/
│   │   ├── conftest.py
│   │   ├── cassettes/
│   │   ├── test_dream_flow.py
│   │   ├── test_plan_flow.py
│   │   └── test_execute_flow.py
│   └── e2e/
│       ├── conftest.py
│       ├── test_init_command.py
│       ├── test_full_workflow.py
│       └── test_doctor.py
└── docs/
    └── TECHNICAL_SPEC.md
```

### Dependencies

```toml
[project]
name = "jiro-dreams-of-code"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.9",
    "fastapi>=0.109",
    "uvicorn>=0.27",
    "jinja2>=3.1",
    "httpx>=0.26",
    "claude-agent-sdk>=0.1",
    "pyyaml>=6.0",
    "rich>=13.0",
]

[project.optional-dependencies]
test = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "pytest-mock>=3.12",
    "pytest-httpx>=0.30",
    "pytest-timeout>=2.2",
    "pytest-recording>=0.13",  # VCR
]
dev = [
    "ruff>=0.2",
    "mypy>=1.8",
    "pre-commit>=3.6",
]

[project.scripts]
jiro = "jiro.cli.main:app"
```

### Git Hooks

**Pre-commit** (relevant files):
- Run tests for changed files
- Lint changed files

**Pre-push** (all files):
- Run full test suite
- Lint all files

---

## Steel Thread Scope

The minimum viable release includes:

### CLI Commands
- [x] `jiro init [--stealth] [--interactive]`
- [x] `jiro doctor [--fix]`
- [x] `jiro dream "prompt"` (with chat refinement)
- [x] `jiro plan --spec "filename" ["prompt"]`
- [x] `jiro tasks list`
- [x] `jiro tasks show TASK_ID`
- [x] `jiro tasks next`
- [x] `jiro execute [--epic EPIC_ID]`
- [x] `jiro status`
- [x] `jiro config [--global|--project|--local] [key] [value]`
- [x] `jiro mode [stealth|local]`
- [x] `jiro logs`
- [x] `jiro web [--daemon]`
- [x] `jiro assets list`
- [x] `jiro assets which <asset-path>`
- [x] `jiro assets customize <asset-path>`

### Core Features
- [x] Spec generation with defined schema
- [x] Chat-based spec refinement (terminal)
- [x] Task decomposition with dependency analysis
- [x] Sequential task execution (parallel deferred)
- [x] Session preflight/postflight checks
- [x] Task preflight/postflight checks
- [x] Commit discipline validation (hardcoded rules)
- [x] Context tracking for all prompts
- [x] Issue tracker facade with Beads implementation
- [x] Config system with three-level precedence
- [x] SQLite database for metrics/sessions
- [x] Structured logging with verbosity levels
- [x] Web UI with spec refinement, task list, execution status
- [x] Asset system with package defaults and user overrides

### Deferred to Future
- [ ] Parallel execution with git worktrees
- [ ] GitHub Issues, Jira, Linear integrations
- [ ] Slack/email/SMS notifications
- [ ] Static analysis for relevant test detection
- [ ] System keychain for API key storage
- [ ] Custom commit templates

---

## Definition of Done

Every feature must include:

1. **Code written** - Implementation complete
2. **Has tests** - Unit and/or integration tests with appropriate coverage
3. **Has observability** - Logging at appropriate levels
4. **Docs updated** - User-facing documentation current
5. **Hooked to CLI and Web UI** - If applicable
6. **Doctor updated** - If applicable, health checks added

Coverage requirement: 70-80%

---

## Design Principle: Python Over LLM

### Rationale

LLM context is expensive and non-deterministic. Whenever behavior can be implemented with deterministic Python code, it **must** be.

**Use Python for:**
- Git operations (commit, checkout, branch, push)
- File system operations (read, write, list)
- Running tests and linters (subprocess calls)
- Parsing and validating commit messages
- Config file loading and merging
- Database operations
- Determining relevant tests (convention-based matching)
- Commit message formatting from templates
- Preflight/postflight check orchestration
- Diffing and displaying changes

**Use LLM for:**
- Generating specs from natural language
- Breaking specs into tasks
- Writing code and tests
- Refining specs through conversation
- Making judgment calls (e.g., "is this a behavior-neutral refactoring?")
- Reviewing commits for conceptual violations

### Benefits

1. **Context conservation**: Python operations consume zero tokens
2. **Precision**: Deterministic behavior, no hallucination risk
3. **Speed**: Python executes instantly vs. LLM round-trips
4. **Testability**: Python logic can be unit tested thoroughly
5. **Cost**: Fewer tokens = lower API costs

---

## Customizable Assets

### Overview

All scripts and prompts are bundled in the Python package but can be overridden at project or user level.

### Asset Types

| Type | Description | Example |
|------|-------------|---------|
| **Prompts** | System prompts for each agent type | `dreaming_agent.md`, `review_agent.md` |
| **Templates** | Commit message templates, spec schema | `commit_template.txt`, `spec_schema.md` |
| **Scripts** | Shell/Python scripts for common operations | `run_tests.sh`, `lint_files.py` |

### Resolution Order (highest to lowest)

1. **Local** (`.jiro-dreams-of-code/assets/`)
2. **Project** (`~/.jiro-dreams-of-code/$PROJECT_NAME/assets/`)
3. **Global** (`~/.jiro-dreams-of-code/assets/`)
4. **Package defaults** (bundled in `jiro` package)

### Directory Structure

```
# Package defaults (bundled)
src/jiro/assets/
├── prompts/
│   ├── dreaming_agent.md
│   ├── planning_agent.md
│   ├── execution_agent.md
│   └── review_agent.md
├── templates/
│   ├── commit/
│   │   ├── default.txt
│   │   ├── tdd_red.txt
│   │   ├── tdd_green.txt
│   │   └── refactor.txt
│   └── spec_schema.md
└── scripts/
    └── (reserved for future use)

# User overrides (any level)
.jiro-dreams-of-code/assets/
├── prompts/
│   └── execution_agent.md    # Override just this one
└── templates/
    └── commit/
        └── default.txt       # Custom commit format
```

### Usage

```python
from jiro.assets import load_asset

# Loads with resolution order: local → project → global → package
prompt = load_asset("prompts/execution_agent.md")
template = load_asset("templates/commit/tdd_red.txt")
```

### CLI for Asset Management

```bash
# List all assets and their sources
jiro assets list

# Show where a specific asset is loaded from
jiro assets which prompts/execution_agent.md

# Copy package default to local for customization
jiro assets customize prompts/execution_agent.md --local

# Copy to global (user-wide)
jiro assets customize prompts/execution_agent.md --global
```

---

## Future Enhancements

### Near-term
- Parallel execution with git worktrees
- Static analysis for relevant test detection
- Additional issue tracker integrations

### Medium-term
- Custom commit templates
- Authentication helpers: `jiro auth login/logout/status` for credential management (post steel thread)
- System keychain integration
- Slack/email/SMS notifications
- Agent memory/learning from past tasks

### Long-term
- Multi-provider support (OpenAI, local models via LiteLLM)
- Team collaboration features
- Analytics dashboard
- IDE integrations

---

## Appendix A: Spec Document Schema

```markdown
# Feature: <title>

## Overview
<1-2 paragraph high-level description>

## Requirements
- <requirement 1>
- <requirement 2>
- ...

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>
- ...

## Out of Scope
- <explicitly excluded item 1>
- <explicitly excluded item 2>
- ...

## Technical Notes
<optional implementation hints, constraints, or considerations>
```

---

## Appendix B: Chat Refinement Commands

During chat refinement (in `jiro dream` or `Proceed? [yes/chat/edit/quit]`):

- Type messages to refine the spec
- Agent shows diffs after each change
- Exit with: `done`, `exit`, `/quit`, or Ctrl+D

---

## Appendix C: Doctor Checks

```
jiro doctor

✓ Python version (3.12+)
✓ Claude Agent SDK installed
✓ Anthropic API key configured (ANTHROPIC_API_KEY)
✓ Git available
✓ Test command works: pytest
✓ Lint command works: ruff check
✓ Beads database accessible
✓ Config files valid YAML
✓ Worktree directory writable
✓ Web port available (8888)
```

With `--fix`: Attempts to create missing directories, initialize missing databases, etc.
