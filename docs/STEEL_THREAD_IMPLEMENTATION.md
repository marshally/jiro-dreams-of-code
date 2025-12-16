# Steel Thread Implementation Plan

> A minimal end-to-end implementation of jiro-dreams-of-code that proves the core concept works.

## Implementation Status

| Phase | Status | Notes |
|-------|--------|-------|
| **Phase 1: Foundation** | ✅ 100% | Config, DB, logging, trackers complete |
| **Phase 2: Core Execution** | ✅ 95% | Agents complete; session orchestration needs integration testing |
| **Phase 3: Dreaming & Planning** | ✅ 100% | Spec generation and planning complete |
| **Phase 4: CLI Commands** | ✅ 100% | All 12 commands implemented |
| **Phase 5: Testing** | ✅ 85% | 160+ tests; integration coverage ongoing |
| **Fast Follow: Commit Types** | ✅ 100% | All 11 step types implemented |

**Last Updated:** 2025-12-16

## Overview

The steel thread delivers a working version of jiro that can:

1. Generate specifications from natural language prompts
1. Break specifications into granular tasks
1. Execute tasks using AI agents with commit discipline
1. Validate commits against discipline rules
1. Track all activity in a database

This document defines the implementation order, scope boundaries, and acceptance criteria.

______________________________________________________________________

## Architecture Decisions

Key architectural decisions are documented as ADRs:

- [ADR-003: Model Selection Strategy](architecture/003-model-selection-strategy.md) - Brain/hands split with Opus for planning, Haiku for execution
- [ADR-004: Strongly-Typed Commits](architecture/004-strongly-typed-commits.md) - Two-layer validation system
- [ADR-005: Beads Integration via CLI](architecture/005-beads-integration-via-cli.md) - Shell out to `bd` CLI
- [ADR-006: Human-Guided Error Recovery](architecture/006-human-guided-error-recovery.md) - HALT and require human input
- [ADR-007: sqlite-utils Over ORM](architecture/007-sqlite-utils-over-orm.md) - Lightweight database layer

### Summary

| Decision | Choice |
|----------|--------|
| Planning/Dreaming Model | Opus 4.5 (the "brain") |
| Execution Model | Haiku (the "hands") |
| Review Model | Sonnet |
| Commit Validation | Two-layer: Python enforcement + LLM review |
| Issue Tracker | Beads via `bd` CLI subprocess |
| Error Recovery | HALT immediately, human provides resume prompt |
| Database Layer | sqlite-utils (no ORM) |

### Technology Stack

| Component | Choice | Notes |
|-----------|--------|-------|
| Agent SDK | Claude Agent SDK | `claude-agent-sdk` Python package |
| CLI Framework | Typer | Already in skeleton |
| Console Output | Rich | Tables, panels, progress bars |
| Web Framework | FastAPI + HTMX | Read-only dashboard |
| Database | sqlite-utils | Lightweight SQLite API with dataclasses |
| Issue Tracker | Beads via `bd` CLI | Shell out to CLI commands |
| Logging | structlog | JSONL files + Rich console |
| Testing | pytest + VCR | Mocked unit tests, recorded integration tests |
| Config Format | YAML | Project scope only |
| Templates | Jinja2 | Commit message templates |

______________________________________________________________________

## Scope Boundaries

### IN SCOPE (Steel Thread)

#### CLI Commands (16 total)

- `jiro init [--stealth] [--interactive]`
- `jiro doctor [--fix]`
- `jiro dream "prompt"`
- `jiro plan --spec "filename" ["prompt"]`
- `jiro tasks list`
- `jiro tasks show TASK_ID`
- `jiro tasks next`
- `jiro execute [--epic EPIC_ID]`
- `jiro status`
- `jiro config list`
- `jiro config get KEY`
- `jiro config set KEY VALUE`
- `jiro mode [stealth|local]`
- `jiro logs`
- `jiro web [--daemon]`
- `jiro assets list`
- `jiro assets which <path>`
- `jiro assets customize <path>` (lists package default, no override support)

#### Core Features

- Spec generation with defined schema
- Chat-based spec refinement (terminal)
- Task decomposition with dependency analysis
- Sequential task execution
- Session preflight/postflight checks
- Task preflight/postflight checks
- Documentation-only commit discipline (single type)
- Context tracking for all prompts
- Human escalation on failures

#### Infrastructure

- SQLite database (sessions, prompts, commits, task_executions)
- Config system (project scope only: `~/.jiro-dreams-of-code/$PROJECT/`)
- Asset system (package defaults only)
- Beads integration via `bd` CLI
- structlog logging (JSONL + Rich console)
- Read-only web dashboard

#### Output Formats

- Human-readable (Rich formatting)
- JSON (`--json` flag)

### OUT OF SCOPE (Deferred)

#### Fast Follow (immediately after steel thread)

- Additional commit types (TDD Red/Green/Refactor, Lint Fix, Bug Fix, etc.)
- Full commit discipline validation for all types

#### Future Releases

- Parallel execution with git worktrees
- TOON output format
- Asset overrides (local/project/global)
- Multi-level config (local + global scopes)
- System keyring for API keys
- GitHub Issues/Jira/Linear integrations
- Slack/email/SMS notifications
- Interactive web UI (spec refinement in browser)

______________________________________________________________________

## Implementation Phases

### Phase 1: Foundation

Build the infrastructure that everything else depends on.

#### 1.1 Project Structure & Configuration ✅

**Files to create/modify:**

- `src/jiro/config/schema.py` - Config dataclass with defaults
- `src/jiro/config/loader.py` - Load from `~/.jiro-dreams-of-code/$PROJECT/config.yaml`
- `src/jiro/core/paths.py` - Path resolution (normal vs stealth mode)
- `src/jiro/core/project.py` - Project name derivation from git remote

**Acceptance Criteria:**

- \[x\] Config loads from project scope directory
- \[x\] Path resolution works for both normal and stealth modes
- \[x\] Project name derived from git remote URL
- \[x\] Defaults work when no config file exists

#### 1.2 Database Layer ✅

**Files to create/modify:**

- `src/jiro/db/database.py` - sqlite-utils Database wrapper
- `src/jiro/db/models.py` - Dataclasses for sessions, prompts, commits, task_executions
- `src/jiro/db/repository.py` - Repository classes for each model

**Schema:** See [DDL.md](DDL.md) for complete database design including:

- Table definitions (sessions, prompts, task_executions, commits)
- Python dataclass models with `from_row()`/`to_row()` methods
- sqlite-utils usage patterns
- Common queries

**Acceptance Criteria:**

- \[x\] Tables created on first access via sqlite-utils
- \[x\] Dataclasses for all models with `from_row`/`to_row`
- \[x\] Repository classes for CRUD operations
- \[x\] Foreign key constraints enforced (`PRAGMA foreign_keys = ON`)

#### 1.3 Logging Infrastructure ✅

**Files to create/modify:**

- `src/jiro/core/logging.py` - structlog configuration
- Update CLI to initialize logging with verbosity levels

**Log Levels:**

- Default: INFO
- `-v`: DEBUG
- `-vv`: TRACE (if supported, else DEBUG)
- `--quiet`: CRITICAL only

**Acceptance Criteria:**

- \[x\] JSONL logs written to `~/.jiro-dreams-of-code/$PROJECT/logs/YYYY-MM-DD.jsonl`
- \[x\] Rich console output for human readability
- \[x\] Context binding works (session_id, task_id flow through)
- \[x\] Verbosity flags work correctly

#### 1.4 Issue Tracker Facade ✅

**Files to create/modify:**

- `src/jiro/trackers/interface.py` - Protocol definition
- `src/jiro/trackers/beads.py` - Beads implementation via `bd` CLI

**Interface:**

```python
class IssueTracker(Protocol):
    def create_task(self, title: str, description: str, task_type: str, ...) -> Task: ...
    def get_task(self, task_id: str) -> Task: ...
    def list_tasks(self, status: str | None, epic_id: str | None) -> list[Task]: ...
    def update_task(self, task_id: str, status: str | None, **kwargs) -> Task: ...
    def get_next_ready_task(self, epic_id: str | None) -> Task | None: ...
    def add_dependency(self, task_id: str, depends_on_id: str) -> None: ...
    def close_task(self, task_id: str, reason: str) -> None: ...
```

**Acceptance Criteria:**

- \[x\] All interface methods implemented via `bd` CLI calls
- \[x\] Beads database initialized in correct location (normal vs stealth)
- \[x\] Error handling for `bd` command failures
- \[x\] Task dataclass matches beads output

______________________________________________________________________

### Phase 2: Core Execution Engine ✅

The heart of jiro - this is what makes it work.

#### 2.1 Agent Base Infrastructure ✅

**Files to create/modify:**

- `src/jiro/agents/base.py` - Base agent configuration and utilities
- `src/jiro/agents/client.py` - Wrapper around Claude Agent SDK

**Key Classes:**

```python
@dataclass
class AgentConfig:
    model: str
    system_prompt: str
    allowed_tools: list[str]
    permission_mode: str = "acceptEdits"
    max_turns: int = 10


class AgentClient:
    """Wrapper around Claude Agent SDK with context tracking."""

    async def execute(self, prompt: str, config: AgentConfig) -> AgentResult:
        """Execute agent and track context usage."""
        ...
```

**Acceptance Criteria:**

- \[x\] AgentClient wraps Claude Agent SDK
- \[x\] Context tracking (tokens before/after) captured
- \[x\] Results stored in prompts table
- \[x\] Proper error handling and logging

#### 2.2 Strongly-Typed Commits ✅

**Files to create/modify:**

- `src/jiro/core/commit.py` - Commit creation with enforcement
- `src/jiro/assets/templates/commit/docs.txt.j2` - Documentation commit template

**Commit Template (docs.txt.j2):**

```jinja2
:memo: {{ message }}

Task: {{ task_id }} - {{ task_title }}
Type: documentation
Reason: {{ reason }}
{% if verification_command %}
Verification: {{ verification_command }}
{{ verification_results | indent(2) }}
{% endif %}
Time: {{ time_taken }}
Context: {{ tokens_before | number_format }} -> {{ tokens_after | number_format }} tokens
```

**Enforcement Rules (Documentation Only):**

- Only `.md` files, docstrings, or comment changes allowed
- No code logic changes
- Commit message must follow template

**Acceptance Criteria:**

- \[x\] `create_docs_commit()` function enforces rules
- \[x\] Raises error if non-docs files are staged
- \[x\] Template rendered correctly
- \[x\] Commit created with proper message format
- \[x\] Commit recorded in database

#### 2.3 Planning Agent ✅

**Files to create/modify:**

- `src/jiro/agents/planning.py` - Task planning agent
- `src/jiro/assets/prompts/planning_agent.md` - System prompt

**Responsibilities:**

- Receive task from issue tracker
- Analyze codebase to understand context
- Produce detailed step-by-step execution plan
- Identify specific files, line numbers, patterns

**Output Format:**

```yaml
task_id: JIRO-123
steps:
  - description: "Create README.md with project overview"
    files:
      - path: README.md
        action: create
        content_hints: "Include project name, description, installation, usage"
  - description: "Add docstring to main function"
    files:
      - path: src/jiro/cli/main.py
        action: modify
        location: "main() function, line 27"
        content_hints: "Add Google-style docstring"
verification:
  command: "python -m py_compile src/jiro/cli/main.py"
  expected: "No output (success)"
```

**Acceptance Criteria:**

- \[x\] Planning agent produces structured execution plan
- \[x\] Plan includes specific files and actions
- \[x\] Plan includes verification command
- \[x\] Context usage tracked

#### 2.4 Execution Agent ✅

**Files to create/modify:**

- `src/jiro/agents/execution.py` - Task execution agent
- `src/jiro/assets/prompts/execution_agent.md` - System prompt

**Responsibilities:**

- Receive detailed plan from planning agent
- Execute each step mechanically
- Create strongly-typed commits after each logical unit
- Report results

**Tools Available:**

- `Read` - Read files
- `Write` - Create files
- `Edit` - Modify files
- `Bash` - Run verification commands only

**Acceptance Criteria:**

- \[x\] Execution agent follows plan step by step
- \[x\] Creates docs commits via strongly-typed commit system
- \[x\] Stops on any error
- \[x\] Context usage tracked

#### 2.5 Review Agent ✅

**Files to create/modify:**

- `src/jiro/agents/review.py` - Commit review agent
- `src/jiro/assets/prompts/review_agent.md` - System prompt
- `src/jiro/core/review.py` - Deterministic review checks

**Review Process:**

1. **Deterministic checks (Python):**

   - Verify only allowed file types changed (`.md`, docstrings, comments)
   - Verify commit message follows template
   - Verify task reference is valid

1. **LLM checks (if deterministic passes):**

   - Verify changes match commit description
   - Verify no code logic was changed
   - Flag any concerns

**Acceptance Criteria:**

- \[x\] Deterministic checks catch obvious violations
- \[x\] LLM review validates semantic correctness
- \[x\] HALT on any violation
- \[x\] Review results logged

#### 2.6 Session Orchestration ✅

**Files to create/modify:**

- `src/jiro/core/session.py` - Session lifecycle management
- `src/jiro/core/executor.py` - Task execution orchestration

**Lifecycle:** See [SESSION_LIFECYCLE.md](SESSION_LIFECYCLE.md) for the complete session orchestration flow including:

- Session preflight/postflight checks
- Task preflight/postflight checks
- Error handling at each phase
- Database records created

**Acceptance Criteria:**

- \[x\] Session created and tracked in database
- \[x\] Preflight checks run and logged
- \[x\] Tasks executed in dependency order
- \[x\] Postflight checks run
- \[x\] HALT on any failure with proper error message
- \[x\] Session status updated throughout

______________________________________________________________________

### Phase 3: Dreaming & Planning Commands ✅

Build the spec generation and task decomposition features.

#### 3.1 Dreaming Agent ✅

**Files to create/modify:**

- `src/jiro/agents/dreaming.py` - Spec generation agent
- `src/jiro/assets/prompts/dreaming_agent.md` - System prompt
- `src/jiro/assets/templates/spec_schema.md` - Spec document schema

**Spec Schema:**

```markdown
# Feature: <title>

## Overview
<1-2 paragraph high-level description>

## Requirements
- <requirement 1>
- <requirement 2>

## Acceptance Criteria
- [ ] <criterion 1>
- [ ] <criterion 2>

## Out of Scope
- <excluded item 1>

## Technical Notes
<implementation hints>
```

**Acceptance Criteria:**

- \[x\] Dreaming agent generates spec from prompt
- \[x\] Spec follows defined schema
- \[x\] Chat refinement loop works
- \[x\] Spec saved to correct location

#### 3.2 Spec Planning Agent ✅

**Files to create/modify:**

- `src/jiro/core/planner.py` - Spec to task decomposition

**Responsibilities:**

- Parse spec document
- Generate epics (parallel workstreams)
- Generate tasks within epics
- Analyze and set dependencies
- Create tasks in issue tracker

**Acceptance Criteria:**

- \[x\] Spec parsed correctly
- \[x\] Epics created in beads
- \[x\] Tasks created with dependencies
- \[x\] Summary displayed to user
- \[x\] Confirmation prompt works (yes/chat/edit/quit)

______________________________________________________________________

### Phase 4: CLI Implementation ✅

Wire everything up to the CLI commands.

#### 4.1 Init Command ✅

**Files to modify:**

- `src/jiro/cli/init.py` (extract from main.py)

**Implementation:**

1. Verify inside git repository
1. Derive project name from git remote
1. Create directory structure (normal or stealth)
1. Initialize beads database via `bd init`
1. Create default config file
1. (Interactive mode) Prompt for test/lint commands

**Acceptance Criteria:**

- \[x\] Fails gracefully if not in git repo
- \[x\] Creates correct directory structure
- \[x\] Beads database initialized
- \[x\] Config file created with defaults
- \[x\] Interactive mode prompts work

#### 4.2 Doctor Command ✅

**Files to modify:**

- `src/jiro/cli/doctor.py` (extract from main.py)

**Checks:**

- \[ \] Python version (3.12+)
- \[ \] Claude Agent SDK installed
- \[ \] `ANTHROPIC_API_KEY` environment variable set
- \[ \] Git available
- \[ \] Test command works (if configured)
- \[ \] Lint command works (if configured)
- \[ \] Beads database accessible
- \[ \] Config file valid YAML
- \[ \] Directories writable

**Acceptance Criteria:**

- \[x\] All checks run and report status
- \[x\] `--fix` attempts remediation where possible
- \[x\] Clear error messages for failures
- \[x\] Exit code reflects health status

#### 4.3 Dream Command ✅

**Files to modify:**

- `src/jiro/cli/dream.py` (extract from main.py)

**Implementation:**

1. Initialize dreaming agent
1. Generate initial spec from prompt
1. Display spec with Rich formatting
1. Enter chat refinement loop
1. Save final spec to specs directory

**Acceptance Criteria:**

- \[x\] Spec generated and displayed
- \[x\] Chat refinement works
- \[x\] Exit commands work (done, exit, /quit, Ctrl+D)
- \[x\] Spec saved to correct location
- \[x\] `--model` override works

#### 4.4 Plan Command ✅

**Files to modify:**

- `src/jiro/cli/plan.py` (extract from main.py)

**Implementation:**

1. Load spec file
1. Run spec planning agent
1. Display summary (epics, tasks, dependencies)
1. Prompt: `Proceed? [yes/chat/edit/quit]`
1. On yes: create tasks in beads

**Acceptance Criteria:**

- \[x\] Spec loaded from file
- \[x\] Planning produces epics and tasks
- \[x\] Summary displayed with Rich
- \[x\] Confirmation prompt works
- \[x\] Tasks created in beads on confirmation

#### 4.5 Tasks Commands ✅

**Files to modify:**

- `src/jiro/cli/tasks.py` (extract from main.py)

**Commands:**

- `list` - List all tasks (grouped by epic/status)
- `show TASK_ID` - Show task detail
- `next` - Show next ready task

**Acceptance Criteria:**

- \[x\] List displays tasks with Rich formatting
- \[x\] Filtering by status and epic works
- \[x\] Show displays full task detail
- \[x\] Next finds task with no blockers
- \[x\] `--json` output works for all

#### 4.6 Execute Command ✅

**Files to modify:**

- `src/jiro/cli/execute.py` (extract from main.py)

**Implementation:**

1. Create session
1. Run session preflight
1. Loop: get next task, execute, postflight
1. Run session postflight
1. Handle errors with HALT

**Acceptance Criteria:**

- \[x\] Session created and tracked
- \[x\] Preflight checks run
- \[x\] Tasks executed in order
- \[x\] Postflight checks run
- \[x\] HALT on failure with clear message
- \[x\] `--epic` filter works

#### 4.7 Status Command ✅

**Files to modify:**

- `src/jiro/cli/status.py` (extract from main.py)

**Implementation:**

- Query active sessions from database
- Display current status, task, progress

**Acceptance Criteria:**

- \[x\] Active sessions displayed
- \[x\] Current task shown
- \[x\] Progress indicated
- \[x\] `--json` output works

#### 4.8 Config Commands ✅

**Files to modify:**

- `src/jiro/cli/config.py` (extract from main.py)

**Commands:**

- `list` - Show all config values
- `get KEY` - Get specific value
- `set KEY VALUE` - Set value

**Acceptance Criteria:**

- \[x\] List shows all config with sources
- \[x\] Get shows value and source
- \[x\] Set writes to project config
- \[x\] `--json` output works for list/get

#### 4.9 Mode Command ✅

**Files to modify:**

- `src/jiro/cli/mode.py` (extract from main.py)

**Implementation:**

- No argument: show current mode
- `stealth` or `local`: switch mode, migrate data

**Acceptance Criteria:**

- \[x\] Current mode displayed
- \[x\] Mode switch migrates all data
- \[x\] Confirmation prompt before migration

#### 4.10 Logs Command ✅

**Files to modify:**

- `src/jiro/cli/logs.py` (extract from main.py)

**Implementation:**

- Display logs from JSONL files
- Support `--follow` for live tail
- Support `--tail N` for last N lines

**Acceptance Criteria:**

- \[x\] Logs displayed with Rich formatting
- \[x\] `--follow` streams new entries
- \[x\] `--tail` shows last N lines
- \[x\] Filtering options work

#### 4.11 Web Command ✅

**Files to modify:**

- `src/jiro/cli/web.py` (extract from main.py)
- `src/jiro/web/app.py` - FastAPI application
- `src/jiro/web/routes/` - Route handlers
- `src/jiro/web/templates/` - HTMX templates

**Dashboard Views:**

- Task list (grouped by epic/status)
- Session status (active sessions, current task)
- Log viewer

**Acceptance Criteria:**

- \[x\] Server starts on configured port
- \[ \] Dashboard displays tasks *(web routes minimal)*
- \[ \] Dashboard displays session status *(web routes minimal)*
- \[ \] Log viewer works *(web routes minimal)*
- \[x\] `--daemon` runs in background

#### 4.12 Assets Commands ✅

**Files to modify:**

- `src/jiro/cli/assets.py` (extract from main.py)
- `src/jiro/assets/loader.py` - Complete implementation

**Commands:**

- `list` - List all package assets
- `which PATH` - Show asset location (always package for steel thread)
- `customize PATH` - Show message that overrides are deferred

**Acceptance Criteria:**

- \[x\] List shows all bundled assets
- \[x\] Which shows package location
- \[x\] Customize explains feature is deferred

______________________________________________________________________

### Phase 5: Testing ✅

#### 5.1 Unit Tests ✅

**Files to create:**

- `tests/unit/test_config.py`
- `tests/unit/test_paths.py`
- `tests/unit/test_database.py`
- `tests/unit/test_commit.py`
- `tests/unit/test_tracker.py`
- `tests/unit/agents/test_base.py`
- `tests/unit/agents/test_planning.py`
- `tests/unit/agents/test_execution.py`
- `tests/unit/agents/test_review.py`
- `tests/unit/cli/test_*.py` (for each command)

**Approach:**

- Mock Claude Agent SDK client
- Mock `bd` CLI calls
- Test business logic in isolation

**Acceptance Criteria:**

- \[x\] All core logic has unit tests
- \[x\] No API calls in unit tests
- \[x\] Coverage > 70%

#### 5.2 Integration Tests ✅

**Files to create:**

- `tests/integration/test_dream_flow.py`
- `tests/integration/test_plan_flow.py`
- `tests/integration/test_execute_flow.py`
- `tests/integration/cassettes/` - VCR recordings

**Approach:**

- Record real API interactions with VCR
- Replay for CI/test runs
- Test full flows end-to-end

**Acceptance Criteria:**

- \[x\] Golden path flows have cassettes
- \[x\] Tests pass with recorded responses
- \[x\] No API costs on test runs

#### 5.3 E2E Tests ⏳

**Files to create:**

- `tests/e2e/test_init_command.py`
- `tests/e2e/test_full_workflow.py`

**Approach:**

- Test CLI commands in subprocess
- Verify file system effects
- Use temp directories

**Acceptance Criteria:**

- \[ \] CLI commands work end-to-end *(partial coverage)*
- \[ \] File system changes verified *(partial coverage)*
- \[x\] Clean up after tests

______________________________________________________________________

## Asset Files to Create ✅

### Prompts

#### `src/jiro/assets/prompts/dreaming_agent.md`

System prompt for spec generation. Instructs agent to:

- Generate structured specifications
- Follow the spec schema
- Ask clarifying questions
- Focus on requirements and acceptance criteria

#### `src/jiro/assets/prompts/planning_agent.md`

System prompt for task planning. Instructs agent to:

- Analyze specs and codebase
- Break work into granular steps
- Identify file locations and line numbers
- Set up verification commands
- Output structured YAML plan

#### `src/jiro/assets/prompts/execution_agent.md`

System prompt for task execution. Instructs agent to:

- Follow the plan exactly
- Make only the changes specified
- Create commits after each logical unit
- Stop and report errors immediately
- Not make autonomous decisions

#### `src/jiro/assets/prompts/review_agent.md`

System prompt for commit review. Instructs agent to:

- Verify commits match their claimed type
- Check for scope creep
- Validate documentation-only changes
- Flag any concerns

### Templates

#### `src/jiro/assets/templates/commit/docs.txt.j2`

Jinja2 template for documentation commits (see Phase 2.2).

#### `src/jiro/assets/templates/spec_schema.md`

The spec document schema that dreaming agent follows.

______________________________________________________________________

## Implementation Order

```
Week 1: Foundation
├── 1.1 Project Structure & Configuration
├── 1.2 Database Layer
├── 1.3 Logging Infrastructure
└── 1.4 Issue Tracker Facade

Week 2: Core Execution Engine (Part 1)
├── 2.1 Agent Base Infrastructure
├── 2.2 Strongly-Typed Commits
└── 2.3 Planning Agent

Week 3: Core Execution Engine (Part 2)
├── 2.4 Execution Agent
├── 2.5 Review Agent
└── 2.6 Session Orchestration

Week 4: Dreaming & Planning
├── 3.1 Dreaming Agent
└── 3.2 Spec Planning Agent

Week 5: CLI Implementation (Part 1)
├── 4.1 Init Command
├── 4.2 Doctor Command
├── 4.3 Dream Command
├── 4.4 Plan Command
└── 4.5 Tasks Commands

Week 6: CLI Implementation (Part 2)
├── 4.6 Execute Command
├── 4.7 Status Command
├── 4.8 Config Commands
├── 4.9 Mode Command
├── 4.10 Logs Command
├── 4.11 Web Command
└── 4.12 Assets Commands

Week 7: Testing & Polish
├── 5.1 Unit Tests
├── 5.2 Integration Tests
├── 5.3 E2E Tests
└── Final polish and documentation
```

______________________________________________________________________

## Definition of Done

Each feature is complete when:

1. **Code written** - Implementation complete
1. **Has tests** - Unit and/or integration tests with > 70% coverage
1. **Has observability** - Logging at appropriate levels
1. **Docs updated** - Code has docstrings, README updated if needed
1. **Hooked to CLI** - If applicable, CLI command works
1. **Doctor updated** - If applicable, health checks added

______________________________________________________________________

## Exit Criteria for Steel Thread

The steel thread is complete when:

1. \[x\] `jiro init` creates project structure and beads database
1. \[x\] `jiro doctor` validates installation health
1. \[x\] `jiro dream "prompt"` generates a spec with chat refinement
1. \[x\] `jiro plan --spec file.md` creates tasks in beads
1. \[x\] `jiro tasks list/show/next` display task information
1. \[x\] `jiro execute` runs tasks with documentation-only commits
1. \[x\] Commits are validated by review agent
1. \[x\] Session halts on any validation failure
1. \[x\] `jiro status` shows active sessions
1. \[x\] `jiro config` manages project configuration
1. \[x\] `jiro logs` displays structured logs
1. \[ \] `jiro web` serves read-only dashboard *(routes minimal)*
1. \[x\] All unit tests pass with mocked clients
1. \[x\] Integration tests pass with VCR cassettes
1. \[x\] No API calls made during test runs

______________________________________________________________________

## Fast Follow Items

> **Status:** Fast Follow items 1 & 2 have been completed! All 11 commit types are implemented.

~~Immediately after steel thread:~~

1. **Additional Commit Types** ✅ COMPLETED

   - ✅ TDD Red (failing test only)
   - ✅ TDD Green (minimal passing code)
   - ✅ TDD Refactor (behavior-neutral)
   - ✅ Lint Fix (single lint error)
   - ✅ Bug Fix (bug_red + bug_green)
   - ✅ Config
   - ✅ Test Only
   - ✅ Performance
   - ✅ Documentation
   - ✅ Refactoring

1. **Full Commit Discipline** ✅ COMPLETED

   - ✅ Type-specific validation rules (11 step types)
   - ✅ TDD cycle enforcement
   - ✅ Refactoring validation with LLM judgment

1. **Asset Overrides** ⏳ DEFERRED

   - Local overrides (`.jiro-dreams-of-code/assets/`)
   - Project overrides (`~/.jiro-dreams-of-code/$PROJECT/assets/`)
   - Global overrides (`~/.jiro-dreams-of-code/assets/`)

1. **Multi-Level Config** ⏳ DEFERRED

   - Local config (`./.jiro-dreams-of-code.yaml`)
   - Global config (`~/.jiro-dreams-of-code/config.yaml`)
   - Precedence: CLI > local > project > global
