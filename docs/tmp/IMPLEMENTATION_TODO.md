# Steel Thread Implementation Tasks

> Granular tasks extracted from STEEL_THREAD_IMPLEMENTATION.md for subagent execution.

______________________________________________________________________

## Phase 1: Foundation

### 1.1 Project Structure & Configuration

______________________________________________________________________

Title: Create config dataclass with defaults
Type: tdd
Slug: config-schema-dataclass
Reason: Foundation for configuration system
Labels: tdd, config, foundation
Description: |
Use TDD to create the config dataclass in `src/jiro/config/schema.py`.
The dataclass should include all configuration fields with sensible defaults:

- models (planning, execution, review)
- commands (test, lint, lint_fix)
- conventions (test_file_pattern)
- preflight settings
  Relevant files:
- src/jiro/config/schema.py
  Acceptance Criteria:
- \[ \] Config dataclass exists with all fields from DDL.md and SESSION_LIFECYCLE.md
- \[ \] Defaults work when no values provided
- \[ \] Type hints for all fields
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create config loader for project scope
Type: tdd
Slug: config-loader
Reason: Load configuration from YAML files
Labels: tdd, config, foundation
Description: |
Use TDD to create `src/jiro/config/loader.py` that loads config from
`~/.jiro-dreams-of-code/$PROJECT/config.yaml`. Should return the Config
dataclass populated from YAML with defaults for missing values.
Relevant files:

- src/jiro/config/loader.py
- src/jiro/config/schema.py
  Acceptance Criteria:
- \[ \] Loads config from project scope directory
- \[ \] Returns Config dataclass with YAML values
- \[ \] Uses defaults when config file missing
- \[ \] Uses defaults for missing keys in config
- \[ \] Tests pass
  Depends on: \[config-schema-dataclass\]

______________________________________________________________________

______________________________________________________________________

Title: Create path resolution for normal and stealth modes
Type: tdd
Slug: paths-resolution
Reason: Support dual storage modes
Labels: tdd, core, foundation
Description: |
Use TDD to create `src/jiro/core/paths.py` with path resolution logic.
Normal mode: `.jiro-dreams-of-code/` in project root
Stealth mode: `~/.jiro-dreams-of-code/$PROJECT/`
Should provide functions for:

- get_jiro_dir(stealth: bool) -> Path
- get_database_path(stealth: bool) -> Path
- get_config_path(stealth: bool) -> Path
- get_specs_dir(stealth: bool) -> Path
- get_logs_dir(stealth: bool) -> Path
  Relevant files:
- src/jiro/core/paths.py
  Acceptance Criteria:
- \[ \] Path resolution works for normal mode
- \[ \] Path resolution works for stealth mode
- \[ \] All directory types supported (db, config, specs, logs)
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create project name derivation from git remote
Type: tdd
Slug: project-name-from-git
Reason: Derive unique project identifier
Labels: tdd, core, foundation
Description: |
Use TDD to create `src/jiro/core/project.py` with function to derive
project name from git remote URL. Handle various URL formats:

- git@github.com:user/repo.git -> repo
- https://github.com/user/repo.git -> repo
- https://github.com/user/repo -> repo
  Should also handle edge cases (no remote, multiple remotes).
  Relevant files:
- src/jiro/core/project.py
  Acceptance Criteria:
- \[ \] Derives name from SSH git URLs
- \[ \] Derives name from HTTPS git URLs
- \[ \] Handles missing .git suffix
- \[ \] Returns sensible default when no remote
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

### 1.2 Database Layer

______________________________________________________________________

Title: Create sqlite-utils database wrapper
Type: tdd
Slug: database-wrapper
Reason: Centralized database access with foreign keys
Labels: tdd, db, foundation
Description: |
Use TDD to create `src/jiro/db/database.py` with:

- get_database(db_path: Path) -> Database
- ensure_schema(db: Database) -> None
  Following the pattern in DDL.md. Must enable foreign keys with PRAGMA.
  Relevant files:
- src/jiro/db/database.py
  Acceptance Criteria:
- \[ \] Database connection with foreign keys enabled
- \[ \] Schema creation using sqlite-utils API
- \[ \] All four tables created (sessions, prompts, task_executions, commits)
- \[ \] Indexes created for common queries
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create Session dataclass with from_row/to_row
Type: tdd
Slug: session-dataclass
Reason: Type-safe session model
Labels: tdd, db, models
Description: |
Use TDD to create the Session dataclass in `src/jiro/db/models.py`
following the specification in DDL.md. Include from_row() and to_row()
methods for database serialization.
Relevant files:

- src/jiro/db/models.py
  Acceptance Criteria:
- \[ \] Session dataclass with all fields from DDL.md
- \[ \] from_row() classmethod for deserialization
- \[ \] to_row() method for serialization
- \[ \] Proper datetime handling
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create Prompt dataclass with from_row/to_row
Type: tdd
Slug: prompt-dataclass
Reason: Type-safe prompt model
Labels: tdd, db, models
Description: |
Use TDD to create the Prompt dataclass in `src/jiro/db/models.py`
following the specification in DDL.md. Include from_row() and to_row()
methods for database serialization.
Relevant files:

- src/jiro/db/models.py
  Acceptance Criteria:
- \[ \] Prompt dataclass with all fields from DDL.md
- \[ \] from_row() classmethod for deserialization
- \[ \] to_row() method for serialization
- \[ \] Proper datetime handling
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create TaskExecution dataclass with from_row/to_row
Type: tdd
Slug: task-execution-dataclass
Reason: Type-safe task execution model
Labels: tdd, db, models
Description: |
Use TDD to create the TaskExecution dataclass in `src/jiro/db/models.py`
following the specification in DDL.md. Include from_row() and to_row()
methods for database serialization.
Relevant files:

- src/jiro/db/models.py
  Acceptance Criteria:
- \[ \] TaskExecution dataclass with all fields from DDL.md
- \[ \] from_row() classmethod for deserialization
- \[ \] to_row() method for serialization
- \[ \] Proper datetime handling
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create Commit dataclass with from_row/to_row
Type: tdd
Slug: commit-dataclass
Reason: Type-safe commit model
Labels: tdd, db, models
Description: |
Use TDD to create the Commit dataclass in `src/jiro/db/models.py`
following the specification in DDL.md. Include from_row() and to_row()
methods for database serialization.
Relevant files:

- src/jiro/db/models.py
  Acceptance Criteria:
- \[ \] Commit dataclass with all fields from DDL.md
- \[ \] from_row() classmethod for deserialization
- \[ \] to_row() method for serialization
- \[ \] Proper datetime handling
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create SessionRepository for CRUD operations
Type: tdd
Slug: session-repository
Reason: Encapsulate session database operations
Labels: tdd, db, repository
Description: |
Use TDD to create SessionRepository in `src/jiro/db/repository.py` with:

- create(session: Session) -> Session
- get(id: str) -> Session | None
- get_active() -> list\[Session\]
- update(session: Session) -> Session
- get_by_status(status: str) -> list\[Session\]
  Relevant files:
- src/jiro/db/repository.py
  Acceptance Criteria:
- \[ \] CRUD operations work correctly
- \[ \] Uses Session dataclass
- \[ \] get_active returns running sessions
- \[ \] Tests pass
  Depends on: \[database-wrapper, session-dataclass\]

______________________________________________________________________

______________________________________________________________________

Title: Create PromptRepository for CRUD operations
Type: tdd
Slug: prompt-repository
Reason: Encapsulate prompt database operations
Labels: tdd, db, repository
Description: |
Use TDD to create PromptRepository in `src/jiro/db/repository.py` with:

- create(prompt: Prompt) -> Prompt
- get(id: str) -> Prompt | None
- get_by_session(session_id: str) -> list\[Prompt\]
- get_by_task(task_id: str) -> list\[Prompt\]
- get_total_tokens(session_id: str) -> int
  Relevant files:
- src/jiro/db/repository.py
  Acceptance Criteria:
- \[ \] CRUD operations work correctly
- \[ \] Uses Prompt dataclass
- \[ \] Token aggregation query works
- \[ \] Tests pass
  Depends on: \[database-wrapper, prompt-dataclass\]

______________________________________________________________________

______________________________________________________________________

Title: Create TaskExecutionRepository for CRUD operations
Type: tdd
Slug: task-execution-repository
Reason: Encapsulate task execution database operations
Labels: tdd, db, repository
Description: |
Use TDD to create TaskExecutionRepository in `src/jiro/db/repository.py` with:

- create(execution: TaskExecution) -> TaskExecution
- get(id: str) -> TaskExecution | None
- get_by_session(session_id: str) -> list\[TaskExecution\]
- get_by_task(task_id: str) -> list\[TaskExecution\]
- update(execution: TaskExecution) -> TaskExecution
  Relevant files:
- src/jiro/db/repository.py
  Acceptance Criteria:
- \[ \] CRUD operations work correctly
- \[ \] Uses TaskExecution dataclass
- \[ \] Filtering by session/task works
- \[ \] Tests pass
  Depends on: \[database-wrapper, task-execution-dataclass\]

______________________________________________________________________

______________________________________________________________________

Title: Create CommitRepository for CRUD operations
Type: tdd
Slug: commit-repository
Reason: Encapsulate commit database operations
Labels: tdd, db, repository
Description: |
Use TDD to create CommitRepository in `src/jiro/db/repository.py` with:

- create(commit: Commit) -> Commit
- get(id: str) -> Commit | None
- get_by_session(session_id: str) -> list\[Commit\]
- get_by_task(task_id: str) -> list\[Commit\]
- get_by_type(session_id: str, commit_type: str) -> list\[Commit\]
  Relevant files:
- src/jiro/db/repository.py
  Acceptance Criteria:
- \[ \] CRUD operations work correctly
- \[ \] Uses Commit dataclass
- \[ \] Filtering by type works
- \[ \] Tests pass
  Depends on: \[database-wrapper, commit-dataclass\]

______________________________________________________________________

### 1.3 Logging Infrastructure

______________________________________________________________________

Title: Configure structlog for jiro
Type: tdd
Slug: structlog-config
Reason: Structured logging with JSONL and Rich output
Labels: tdd, logging, foundation
Description: |
Use TDD to create `src/jiro/core/logging.py` with structlog configuration:

- JSONL output to `~/.jiro-dreams-of-code/$PROJECT/logs/YYYY-MM-DD.jsonl`
- Rich console output for human readability
- Context binding (session_id, task_id flow through)
- Verbosity levels: default=INFO, -v=DEBUG, --quiet=CRITICAL
  Relevant files:
- src/jiro/core/logging.py
  Acceptance Criteria:
- \[ \] JSONL logs written to correct location
- \[ \] Rich console output formatted
- \[ \] Context binding works (session_id, task_id)
- \[ \] Verbosity flags work correctly
- \[ \] Tests pass
  Depends on: \[paths-resolution\]

______________________________________________________________________

______________________________________________________________________

Title: Update CLI to initialize logging with verbosity
Type: refactoring
Slug: cli-logging-integration
Reason: Wire logging into CLI entry point
Labels: refactoring, cli, logging
Description: |
Update `src/jiro/cli/main.py` to initialize structlog on startup.
Add global options for verbosity (-v, -vv, --quiet).
Use the refactoring skill to add logging initialization to the main callback.
Relevant files:

- src/jiro/cli/main.py
  Acceptance Criteria:
- \[ \] Logging initialized on CLI startup
- \[ \] -v flag sets DEBUG level
- \[ \] -vv flag sets TRACE/DEBUG level
- \[ \] --quiet flag sets CRITICAL level
- \[ \] Tests pass
  Depends on: \[structlog-config\]

______________________________________________________________________

### 1.4 Issue Tracker Facade

______________________________________________________________________

Title: Create IssueTracker protocol interface
Type: tdd
Slug: tracker-protocol
Reason: Abstract interface for issue trackers
Labels: tdd, tracker, foundation
Description: |
Use TDD to create `src/jiro/trackers/interface.py` with the Protocol:

- create_task(title, description, task_type, ...) -> Task
- get_task(task_id) -> Task
- list_tasks(status, epic_id) -> list\[Task\]
- update_task(task_id, status, \*\*kwargs) -> Task
- get_next_ready_task(epic_id) -> Task | None
- add_dependency(task_id, depends_on_id) -> None
- close_task(task_id, reason) -> None
  Also create the Task dataclass.
  Relevant files:
- src/jiro/trackers/interface.py
  Acceptance Criteria:
- \[ \] Protocol defined with all methods
- \[ \] Task dataclass with required fields
- \[ \] Type hints for all parameters
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Implement BeadsTracker via bd CLI
Type: tdd
Slug: beads-tracker-impl
Reason: Integrate with beads issue tracker
Labels: tdd, tracker, beads
Description: |
Use TDD to create `src/jiro/trackers/beads.py` implementing IssueTracker
by shelling out to `bd` CLI commands. Handle JSON output parsing.
Initialize beads database in correct location based on mode.
Relevant files:

- src/jiro/trackers/beads.py
  Acceptance Criteria:
- \[ \] All IssueTracker methods implemented
- \[ \] Uses `bd` CLI with --json flag
- \[ \] Parses JSON output into Task objects
- \[ \] Error handling for bd command failures
- \[ \] Initializes beads in correct location (normal vs stealth)
- \[ \] Tests pass (mocking subprocess calls)
  Depends on: \[tracker-protocol, paths-resolution\]

______________________________________________________________________

______________________________________________________________________

## Phase 2: Core Execution Engine

### 2.1 Agent Base Infrastructure

______________________________________________________________________

Title: Create AgentConfig dataclass
Type: tdd
Slug: agent-config
Reason: Configuration for agent execution
Labels: tdd, agents, foundation
Description: |
Use TDD to create AgentConfig dataclass in `src/jiro/agents/base.py`:

- model: str
- system_prompt: str
- allowed_tools: list\[str\]
- permission_mode: str = "acceptEdits"
- max_turns: int = 10
  Relevant files:
- src/jiro/agents/base.py
  Acceptance Criteria:
- \[ \] AgentConfig dataclass with all fields
- \[ \] Sensible defaults
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create AgentResult dataclass
Type: tdd
Slug: agent-result
Reason: Capture agent execution results
Labels: tdd, agents, foundation
Description: |
Use TDD to create AgentResult dataclass in `src/jiro/agents/base.py`:

- success: bool
- output: str
- tokens_before: int
- tokens_after: int
- error: str | None
  Relevant files:
- src/jiro/agents/base.py
  Acceptance Criteria:
- \[ \] AgentResult dataclass with all fields
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create AgentClient wrapper for Claude Agent SDK
Type: tdd
Slug: agent-client
Reason: Wrap Claude Agent SDK with context tracking
Labels: tdd, agents, foundation
Description: |
Use TDD to create AgentClient in `src/jiro/agents/client.py`:

- async execute(prompt: str, config: AgentConfig) -> AgentResult
- Track context usage (tokens before/after)
- Store results in prompts table
- Proper error handling and logging
  Relevant files:
- src/jiro/agents/client.py
  Acceptance Criteria:
- \[ \] Wraps Claude Agent SDK
- \[ \] Context tracking captured
- \[ \] Results stored in prompts table
- \[ \] Proper error handling
- \[ \] Tests pass (mocking SDK)
  Depends on: \[agent-config, agent-result, prompt-repository, structlog-config\]

______________________________________________________________________

### 2.2 Strongly-Typed Commits

______________________________________________________________________

Title: Create docs commit template
Type: tdd
Slug: docs-commit-template
Reason: Jinja2 template for documentation commits
Labels: tdd, commits, templates
Description: |
Use TDD to create `src/jiro/assets/templates/commit/docs.txt.j2`:

- :memo: emoji prefix
- Task reference and type
- Reason for change
- Verification command and results
- Time taken and context tokens
  Relevant files:
- src/jiro/assets/templates/commit/docs.txt.j2
  Acceptance Criteria:
- \[ \] Template renders correctly
- \[ \] All required fields included
- \[ \] Jinja2 syntax valid
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create commit enforcement for docs type
Type: tdd
Slug: commit-enforcement-docs
Reason: Enforce documentation-only commits
Labels: tdd, commits, enforcement
Description: |
Use TDD to create `src/jiro/core/commit.py` with create_docs_commit():

- Validate only .md files, docstrings, or comment changes
- Raise error if non-docs files are staged
- Render commit message from template
- Create git commit
- Record commit in database
  Relevant files:
- src/jiro/core/commit.py
  Acceptance Criteria:
- \[ \] Validates staged files are docs-only
- \[ \] Raises error for code changes
- \[ \] Renders template correctly
- \[ \] Creates git commit
- \[ \] Records in database
- \[ \] Tests pass
  Depends on: \[docs-commit-template, commit-repository\]

______________________________________________________________________

### 2.3 Planning Agent

______________________________________________________________________

Title: Create planning agent system prompt
Type: tdd
Slug: planning-agent-prompt
Reason: System prompt for task planning
Labels: tdd, agents, prompts
Description: |
Create `src/jiro/assets/prompts/planning_agent.md` with instructions for:

- Receiving task from issue tracker
- Analyzing codebase context
- Producing step-by-step execution plan
- Identifying specific files, line numbers, patterns
- Setting up verification commands
  Relevant files:
- src/jiro/assets/prompts/planning_agent.md
  Acceptance Criteria:
- \[ \] Clear instructions for planning
- \[ \] Output format specified (YAML)
- \[ \] Examples included
- \[ \] Tests pass (template loads)
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create planning agent implementation
Type: tdd
Slug: planning-agent-impl
Reason: Agent that produces execution plans
Labels: tdd, agents, planning
Description: |
Use TDD to create `src/jiro/agents/planning.py`:

- PlanningAgent class using AgentClient
- plan(task: Task) -> ExecutionPlan method
- ExecutionPlan dataclass with steps, verification
- Context tracking throughout
  Relevant files:
- src/jiro/agents/planning.py
  Acceptance Criteria:
- \[ \] Planning agent produces structured plan
- \[ \] Plan includes specific files and actions
- \[ \] Plan includes verification command
- \[ \] Context usage tracked
- \[ \] Tests pass
  Depends on: \[agent-client, planning-agent-prompt, tracker-protocol\]

______________________________________________________________________

### 2.4 Execution Agent

______________________________________________________________________

Title: Create execution agent system prompt
Type: tdd
Slug: execution-agent-prompt
Reason: System prompt for task execution
Labels: tdd, agents, prompts
Description: |
Create `src/jiro/assets/prompts/execution_agent.md` with instructions for:

- Receiving detailed plan from planning agent
- Executing each step mechanically
- Creating strongly-typed commits after logical units
- Reporting results
- NOT making autonomous decisions
  Relevant files:
- src/jiro/assets/prompts/execution_agent.md
  Acceptance Criteria:
- \[ \] Clear instructions for execution
- \[ \] Commit creation explained
- \[ \] Tools available documented
- \[ \] Examples included
- \[ \] Tests pass (template loads)
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create execution agent implementation
Type: tdd
Slug: execution-agent-impl
Reason: Agent that executes plans mechanically
Labels: tdd, agents, execution
Description: |
Use TDD to create `src/jiro/agents/execution.py`:

- ExecutionAgent class using AgentClient
- execute(plan: ExecutionPlan) -> ExecutionResult method
- Creates docs commits via strongly-typed commit system
- Stops on any error
- Context tracking throughout
  Relevant files:
- src/jiro/agents/execution.py
  Acceptance Criteria:
- \[ \] Execution agent follows plan step by step
- \[ \] Creates docs commits via commit system
- \[ \] Stops on any error
- \[ \] Context usage tracked
- \[ \] Tests pass
  Depends on: \[agent-client, execution-agent-prompt, commit-enforcement-docs\]

______________________________________________________________________

### 2.5 Review Agent

______________________________________________________________________

Title: Create review agent system prompt
Type: tdd
Slug: review-agent-prompt
Reason: System prompt for commit review
Labels: tdd, agents, prompts
Description: |
Create `src/jiro/assets/prompts/review_agent.md` with instructions for:

- Verifying commits match claimed type
- Checking for scope creep
- Validating documentation-only changes
- Flagging concerns
  Relevant files:
- src/jiro/assets/prompts/review_agent.md
  Acceptance Criteria:
- \[ \] Clear instructions for review
- \[ \] Validation criteria explained
- \[ \] Output format specified
- \[ \] Examples included
- \[ \] Tests pass (template loads)
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create deterministic commit review checks
Type: tdd
Slug: review-deterministic
Reason: Python validation before LLM review
Labels: tdd, review, deterministic
Description: |
Use TDD to create `src/jiro/core/review.py` with deterministic checks:

- verify_commit_files(sha: str, commit_type: str) -> bool
- verify_commit_message(sha: str) -> bool
- verify_task_reference(sha: str, task_id: str) -> bool
  These run before LLM review to catch obvious violations.
  Relevant files:
- src/jiro/core/review.py
  Acceptance Criteria:
- \[ \] File type validation for docs commits
- \[ \] Message template validation
- \[ \] Task reference validation
- \[ \] Clear error messages
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create review agent implementation
Type: tdd
Slug: review-agent-impl
Reason: Agent that validates commits
Labels: tdd, agents, review
Description: |
Use TDD to create `src/jiro/agents/review.py`:

- ReviewAgent class using AgentClient
- review(commit_sha: str, task: Task) -> ReviewResult method
- Runs deterministic checks first
- Runs LLM review if deterministic passes
- Returns HALT if any violation
  Relevant files:
- src/jiro/agents/review.py
  Acceptance Criteria:
- \[ \] Deterministic checks run first
- \[ \] LLM review validates semantic correctness
- \[ \] HALT on any violation
- \[ \] Review results logged
- \[ \] Tests pass
  Depends on: \[agent-client, review-agent-prompt, review-deterministic\]

______________________________________________________________________

### 2.6 Session Orchestration

______________________________________________________________________

Title: Create session preflight checks
Type: tdd
Slug: session-preflight
Reason: Validate environment before execution
Labels: tdd, session, preflight
Description: |
Use TDD to create session preflight in `src/jiro/core/session.py`:

- check_git_clean() -> bool
- check_correct_branch(config) -> bool
- check_up_to_date() -> bool
- check_tests_pass(config) -> bool
- check_lint_pass(config) -> bool
- run_preflight(config) -> PreflightResult
  Relevant files:
- src/jiro/core/session.py
  Acceptance Criteria:
- \[ \] All checks implemented
- \[ \] Clear error messages on failure
- \[ \] Skip optimization for recent pass
- \[ \] Results logged
- \[ \] Tests pass
  Depends on: \[config-loader, structlog-config\]

______________________________________________________________________

______________________________________________________________________

Title: Create session postflight checks
Type: tdd
Slug: session-postflight
Reason: Validate environment after execution
Labels: tdd, session, postflight
Description: |
Use TDD to add session postflight to `src/jiro/core/session.py`:

- run_full_tests(config) -> bool
- run_full_lint(config) -> bool
- push_to_origin() -> bool
- run_postflight(config) -> PostflightResult
  Relevant files:
- src/jiro/core/session.py
  Acceptance Criteria:
- \[ \] Full test suite runs
- \[ \] Full lint runs
- \[ \] Push to origin works
- \[ \] Results logged
- \[ \] Tests pass
  Depends on: \[session-preflight\]

______________________________________________________________________

______________________________________________________________________

Title: Create task preflight checks
Type: tdd
Slug: task-preflight
Reason: Prepare context before task execution
Labels: tdd, task, preflight
Description: |
Use TDD to create task preflight in `src/jiro/core/executor.py`:

- run_relevant_tests(task, config) -> bool
- run_relevant_lint(task, config) -> bool
- enhance_task_with_planning(task) -> EnhancedTask
- run_task_preflight(task, config) -> PreflightResult
  Relevant files:
- src/jiro/core/executor.py
  Acceptance Criteria:
- \[ \] Relevant tests identified and run
- \[ \] Relevant files linted
- \[ \] Planning agent called
- \[ \] Results logged
- \[ \] Tests pass
  Depends on: \[planning-agent-impl, config-loader\]

______________________________________________________________________

______________________________________________________________________

Title: Create task postflight checks
Type: tdd
Slug: task-postflight
Reason: Validate work after task execution
Labels: tdd, task, postflight
Description: |
Use TDD to add task postflight to `src/jiro/core/executor.py`:

- review_commits(task, commits) -> ReviewResult
- run_relevant_tests_post(task, config) -> bool
- run_relevant_lint_post(task, config) -> bool
- record_results(task, result) -> None
- close_task_in_tracker(task) -> None
- run_task_postflight(task, commits, config) -> PostflightResult
  Relevant files:
- src/jiro/core/executor.py
  Acceptance Criteria:
- \[ \] Review agent validates commits
- \[ \] Relevant tests run
- \[ \] Relevant files linted
- \[ \] Results recorded
- \[ \] Task closed in tracker
- \[ \] Tests pass
  Depends on: \[review-agent-impl, task-preflight, beads-tracker-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Create session lifecycle orchestration
Type: tdd
Slug: session-orchestration
Reason: Coordinate full execution flow
Labels: tdd, session, orchestration
Description: |
Use TDD to create session orchestration in `src/jiro/core/session.py`:

- SessionOrchestrator class
- run(epic_id: str | None) -> SessionResult
- Coordinates: preflight -> task loop -> postflight
- Creates and updates database records
- HALT on any failure
  Relevant files:
- src/jiro/core/session.py
  Acceptance Criteria:
- \[ \] Session created and tracked in database
- \[ \] Preflight checks run and logged
- \[ \] Tasks executed in dependency order
- \[ \] Postflight checks run
- \[ \] HALT on failure with proper error message
- \[ \] Session status updated throughout
- \[ \] Tests pass
  Depends on: \[session-preflight, session-postflight, task-preflight, task-postflight, session-repository, task-execution-repository\]

______________________________________________________________________

______________________________________________________________________

## Phase 3: Dreaming & Planning Commands

### 3.1 Dreaming Agent

______________________________________________________________________

Title: Create spec schema template
Type: tdd
Slug: spec-schema-template
Reason: Define specification document format
Labels: tdd, dreaming, templates
Description: |
Create `src/jiro/assets/templates/spec_schema.md` with the spec format:

- Feature title
- Overview (1-2 paragraphs)
- Requirements (bullet list)
- Acceptance Criteria (checkbox list)
- Out of Scope (bullet list)
- Technical Notes
  Relevant files:
- src/jiro/assets/templates/spec_schema.md
  Acceptance Criteria:
- \[ \] Schema fully defined
- \[ \] Examples included
- \[ \] Tests pass (template loads)
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create dreaming agent system prompt
Type: tdd
Slug: dreaming-agent-prompt
Reason: System prompt for spec generation
Labels: tdd, agents, prompts
Description: |
Create `src/jiro/assets/prompts/dreaming_agent.md` with instructions for:

- Generating structured specifications
- Following the spec schema
- Asking clarifying questions
- Focusing on requirements and acceptance criteria
  Relevant files:
- src/jiro/assets/prompts/dreaming_agent.md
  Acceptance Criteria:
- \[ \] Clear instructions for spec generation
- \[ \] Schema reference included
- \[ \] Clarifying question guidance
- \[ \] Examples included
- \[ \] Tests pass (template loads)
  Depends on: \[spec-schema-template\]

______________________________________________________________________

______________________________________________________________________

Title: Create dreaming agent implementation
Type: tdd
Slug: dreaming-agent-impl
Reason: Agent that generates specifications
Labels: tdd, agents, dreaming
Description: |
Use TDD to create `src/jiro/agents/dreaming.py`:

- DreamingAgent class using AgentClient
- dream(prompt: str) -> Spec method
- refine(spec: Spec, feedback: str) -> Spec method
- Spec dataclass matching schema
  Relevant files:
- src/jiro/agents/dreaming.py
  Acceptance Criteria:
- \[ \] Dreaming agent generates spec from prompt
- \[ \] Spec follows defined schema
- \[ \] Refinement method works
- \[ \] Context usage tracked
- \[ \] Tests pass
  Depends on: \[agent-client, dreaming-agent-prompt\]

______________________________________________________________________

### 3.2 Spec Planning Agent

______________________________________________________________________

Title: Create spec parser
Type: tdd
Slug: spec-parser
Reason: Parse spec documents for planning
Labels: tdd, planner, parsing
Description: |
Use TDD to create spec parser in `src/jiro/core/planner.py`:

- parse_spec(path: Path) -> Spec
- Extract all sections from markdown
- Validate against schema
  Relevant files:
- src/jiro/core/planner.py
  Acceptance Criteria:
- \[ \] Parses spec markdown correctly
- \[ \] Extracts all sections
- \[ \] Validates required sections present
- \[ \] Returns Spec dataclass
- \[ \] Tests pass
  Depends on: \[spec-schema-template\]

______________________________________________________________________

______________________________________________________________________

Title: Create spec planning agent for task decomposition
Type: tdd
Slug: spec-planning-agent
Reason: Generate epics and tasks from specs
Labels: tdd, planner, decomposition
Description: |
Use TDD to create spec planning in `src/jiro/core/planner.py`:

- SpecPlanner class
- plan(spec: Spec) -> PlanResult
- Generates epics (parallel workstreams)
- Generates tasks within epics
- Analyzes and sets dependencies
- Uses LLM for intelligent decomposition
  Relevant files:
- src/jiro/core/planner.py
  Acceptance Criteria:
- \[ \] Spec parsed correctly
- \[ \] Epics generated for parallel work
- \[ \] Tasks generated with descriptions
- \[ \] Dependencies analyzed
- \[ \] Tests pass
  Depends on: \[spec-parser, agent-client\]

______________________________________________________________________

______________________________________________________________________

Title: Create tasks from plan in issue tracker
Type: tdd
Slug: create-tasks-from-plan
Reason: Create beads tasks from plan
Labels: tdd, planner, tracker
Description: |
Use TDD to add task creation to `src/jiro/core/planner.py`:

- create_tasks(plan: PlanResult, tracker: IssueTracker) -> list\[Task\]
- Creates epics first
- Creates tasks with dependencies
- Returns created tasks
  Relevant files:
- src/jiro/core/planner.py
  Acceptance Criteria:
- \[ \] Epics created in tracker
- \[ \] Tasks created with dependencies
- \[ \] All tasks linked correctly
- \[ \] Summary available
- \[ \] Tests pass
  Depends on: \[spec-planning-agent, beads-tracker-impl\]

______________________________________________________________________

______________________________________________________________________

## Phase 4: CLI Implementation

### 4.1 Init Command

______________________________________________________________________

Title: Implement init command core logic
Type: tdd
Slug: init-command-impl
Reason: Initialize jiro in a project
Labels: tdd, cli, init
Description: |
Use TDD to implement init command in `src/jiro/cli/init.py`:

- Verify inside git repository
- Derive project name from git remote
- Create directory structure (normal or stealth)
- Initialize beads database via `bd init`
- Create default config file
  Extract from main.py stub.
  Relevant files:
- src/jiro/cli/init.py
- src/jiro/cli/main.py
  Acceptance Criteria:
- \[ \] Fails gracefully if not in git repo
- \[ \] Creates correct directory structure
- \[ \] Beads database initialized
- \[ \] Config file created with defaults
- \[ \] Tests pass
  Depends on: \[project-name-from-git, paths-resolution, beads-tracker-impl, config-loader\]

______________________________________________________________________

______________________________________________________________________

Title: Implement init command interactive mode
Type: tdd
Slug: init-interactive-mode
Reason: Prompt for test/lint commands
Labels: tdd, cli, init
Description: |
Use TDD to add interactive mode to init command:

- Prompt for test command
- Prompt for lint command
- Save to config file
  Relevant files:
- src/jiro/cli/init.py
  Acceptance Criteria:
- \[ \] Prompts for test command
- \[ \] Prompts for lint command
- \[ \] Validates commands work
- \[ \] Saves to config
- \[ \] Tests pass
  Depends on: \[init-command-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Wire init command to CLI
Type: refactoring
Slug: init-cli-wire
Reason: Connect init module to main CLI
Labels: refactoring, cli, init
Description: |
Use the refactoring skill to update main.py to import and use
the init command implementation from init.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/init.py
  Acceptance Criteria:
- \[ \] Init command works from CLI
- \[ \] All options functional
- \[ \] Tests pass
  Depends on: \[init-interactive-mode\]

______________________________________________________________________

### 4.2 Doctor Command

______________________________________________________________________

Title: Implement doctor command checks
Type: tdd
Slug: doctor-checks-impl
Reason: Health checks for jiro installation
Labels: tdd, cli, doctor
Description: |
Use TDD to implement doctor checks in `src/jiro/cli/doctor.py`:

- check_python_version() -> CheckResult
- check_claude_sdk() -> CheckResult
- check_api_key() -> CheckResult
- check_git() -> CheckResult
- check_test_command(config) -> CheckResult
- check_lint_command(config) -> CheckResult
- check_beads() -> CheckResult
- check_config() -> CheckResult
- check_directories() -> CheckResult
  Relevant files:
- src/jiro/cli/doctor.py
  Acceptance Criteria:
- \[ \] All 9 checks implemented
- \[ \] Clear status reporting
- \[ \] Exit code reflects health
- \[ \] Tests pass
  Depends on: \[config-loader, beads-tracker-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Implement doctor command --fix option
Type: tdd
Slug: doctor-fix-impl
Reason: Auto-remediation for fixable issues
Labels: tdd, cli, doctor
Description: |
Use TDD to add --fix support to doctor:

- Fix missing directories
- Fix missing config with defaults
- Report what was fixed
  Relevant files:
- src/jiro/cli/doctor.py
  Acceptance Criteria:
- \[ \] Creates missing directories
- \[ \] Creates missing config
- \[ \] Reports fixes applied
- \[ \] Tests pass
  Depends on: \[doctor-checks-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Wire doctor command to CLI
Type: refactoring
Slug: doctor-cli-wire
Reason: Connect doctor module to main CLI
Labels: refactoring, cli, doctor
Description: |
Use the refactoring skill to update main.py to import and use
the doctor command implementation from doctor.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/doctor.py
  Acceptance Criteria:
- \[ \] Doctor command works from CLI
- \[ \] --fix option functional
- \[ \] Tests pass
  Depends on: \[doctor-fix-impl\]

______________________________________________________________________

### 4.3 Dream Command

______________________________________________________________________

Title: Implement dream command
Type: tdd
Slug: dream-command-impl
Reason: Generate specs from prompts
Labels: tdd, cli, dream
Description: |
Use TDD to implement dream command in `src/jiro/cli/dream.py`:

- Initialize dreaming agent
- Generate initial spec from prompt
- Display spec with Rich formatting
- Enter chat refinement loop
- Save final spec to specs directory
  Relevant files:
- src/jiro/cli/dream.py
  Acceptance Criteria:
- \[ \] Spec generated and displayed
- \[ \] Chat refinement works
- \[ \] Exit commands work (done, exit, /quit, Ctrl+D)
- \[ \] Spec saved to correct location
- \[ \] --model override works
- \[ \] Tests pass
  Depends on: \[dreaming-agent-impl, paths-resolution\]

______________________________________________________________________

______________________________________________________________________

Title: Wire dream command to CLI
Type: refactoring
Slug: dream-cli-wire
Reason: Connect dream module to main CLI
Labels: refactoring, cli, dream
Description: |
Use the refactoring skill to update main.py to import and use
the dream command implementation from dream.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/dream.py
  Acceptance Criteria:
- \[ \] Dream command works from CLI
- \[ \] --model option functional
- \[ \] Tests pass
  Depends on: \[dream-command-impl\]

______________________________________________________________________

### 4.4 Plan Command

______________________________________________________________________

Title: Implement plan command
Type: tdd
Slug: plan-command-impl
Reason: Generate tasks from specs
Labels: tdd, cli, plan
Description: |
Use TDD to implement plan command in `src/jiro/cli/plan.py`:

- Load spec file
- Run spec planning agent
- Display summary (epics, tasks, dependencies)
- Prompt: `Proceed? [yes/chat/edit/quit]`
- On yes: create tasks in beads
  Relevant files:
- src/jiro/cli/plan.py
  Acceptance Criteria:
- \[ \] Spec loaded from file
- \[ \] Planning produces epics and tasks
- \[ \] Summary displayed with Rich
- \[ \] Confirmation prompt works
- \[ \] Tasks created in beads on yes
- \[ \] Tests pass
  Depends on: \[spec-planning-agent, create-tasks-from-plan\]

______________________________________________________________________

______________________________________________________________________

Title: Wire plan command to CLI
Type: refactoring
Slug: plan-cli-wire
Reason: Connect plan module to main CLI
Labels: refactoring, cli, plan
Description: |
Use the refactoring skill to update main.py to import and use
the plan command implementation from plan.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/plan.py
  Acceptance Criteria:
- \[ \] Plan command works from CLI
- \[ \] --spec option functional
- \[ \] Tests pass
  Depends on: \[plan-command-impl\]

______________________________________________________________________

### 4.5 Tasks Commands

______________________________________________________________________

Title: Implement tasks list command
Type: tdd
Slug: tasks-list-impl
Reason: List tasks with filtering
Labels: tdd, cli, tasks
Description: |
Use TDD to implement tasks list in `src/jiro/cli/tasks.py`:

- List all tasks grouped by epic/status
- Filter by status and epic
- Rich formatting
- --json output
  Relevant files:
- src/jiro/cli/tasks.py
  Acceptance Criteria:
- \[ \] Lists tasks with Rich formatting
- \[ \] Filtering by status works
- \[ \] Filtering by epic works
- \[ \] --json output works
- \[ \] Tests pass
  Depends on: \[beads-tracker-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Implement tasks show command
Type: tdd
Slug: tasks-show-impl
Reason: Show task details
Labels: tdd, cli, tasks
Description: |
Use TDD to add tasks show to `src/jiro/cli/tasks.py`:

- Show full task detail
- Include dependencies
- Include execution history
- --json output
  Relevant files:
- src/jiro/cli/tasks.py
  Acceptance Criteria:
- \[ \] Shows full task detail
- \[ \] Includes dependencies
- \[ \] Includes history
- \[ \] --json output works
- \[ \] Tests pass
  Depends on: \[tasks-list-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Implement tasks next command
Type: tdd
Slug: tasks-next-impl
Reason: Show next ready task
Labels: tdd, cli, tasks
Description: |
Use TDD to add tasks next to `src/jiro/cli/tasks.py`:

- Find task with no blockers
- Filter by epic if specified
- --json output
  Relevant files:
- src/jiro/cli/tasks.py
  Acceptance Criteria:
- \[ \] Finds next ready task
- \[ \] Epic filter works
- \[ \] --json output works
- \[ \] Tests pass
  Depends on: \[tasks-show-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Wire tasks commands to CLI
Type: refactoring
Slug: tasks-cli-wire
Reason: Connect tasks module to main CLI
Labels: refactoring, cli, tasks
Description: |
Use the refactoring skill to update main.py to import and use
the tasks command implementations from tasks.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/tasks.py
  Acceptance Criteria:
- \[ \] All tasks subcommands work from CLI
- \[ \] Tests pass
  Depends on: \[tasks-next-impl\]

______________________________________________________________________

### 4.6 Execute Command

______________________________________________________________________

Title: Implement execute command
Type: tdd
Slug: execute-command-impl
Reason: Run task execution session
Labels: tdd, cli, execute
Description: |
Use TDD to implement execute command in `src/jiro/cli/execute.py`:

- Create session using SessionOrchestrator
- Run session with optional epic filter
- Display progress with Rich
- Handle HALT with clear message
  Relevant files:
- src/jiro/cli/execute.py
  Acceptance Criteria:
- \[ \] Session created and tracked
- \[ \] Preflight checks run
- \[ \] Tasks executed in order
- \[ \] Postflight checks run
- \[ \] HALT on failure with clear message
- \[ \] --epic filter works
- \[ \] Tests pass
  Depends on: \[session-orchestration\]

______________________________________________________________________

______________________________________________________________________

Title: Wire execute command to CLI
Type: refactoring
Slug: execute-cli-wire
Reason: Connect execute module to main CLI
Labels: refactoring, cli, execute
Description: |
Use the refactoring skill to update main.py to import and use
the execute command implementation from execute.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/execute.py
  Acceptance Criteria:
- \[ \] Execute command works from CLI
- \[ \] --epic option functional
- \[ \] Tests pass
  Depends on: \[execute-command-impl\]

______________________________________________________________________

### 4.7 Status Command

______________________________________________________________________

Title: Implement status command
Type: tdd
Slug: status-command-impl
Reason: Show active session status
Labels: tdd, cli, status
Description: |
Use TDD to implement status command in `src/jiro/cli/status.py`:

- Query active sessions from database
- Display current status, task, progress
- Rich formatting
- --json output
  Relevant files:
- src/jiro/cli/status.py
  Acceptance Criteria:
- \[ \] Active sessions displayed
- \[ \] Current task shown
- \[ \] Progress indicated
- \[ \] --json output works
- \[ \] Tests pass
  Depends on: \[session-repository, task-execution-repository\]

______________________________________________________________________

______________________________________________________________________

Title: Wire status command to CLI
Type: refactoring
Slug: status-cli-wire
Reason: Connect status module to main CLI
Labels: refactoring, cli, status
Description: |
Use the refactoring skill to update main.py to import and use
the status command implementation from status.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/status.py
  Acceptance Criteria:
- \[ \] Status command works from CLI
- \[ \] Tests pass
  Depends on: \[status-command-impl\]

______________________________________________________________________

### 4.8 Config Commands

______________________________________________________________________

Title: Implement config list command
Type: tdd
Slug: config-list-impl
Reason: List configuration values
Labels: tdd, cli, config
Description: |
Use TDD to implement config list in `src/jiro/cli/config.py`:

- Show all config values
- Show source (default, project)
- Rich formatting
- --json output
  Relevant files:
- src/jiro/cli/config.py
  Acceptance Criteria:
- \[ \] Lists all config values
- \[ \] Shows value sources
- \[ \] Rich formatting
- \[ \] --json output works
- \[ \] Tests pass
  Depends on: \[config-loader\]

______________________________________________________________________

______________________________________________________________________

Title: Implement config get command
Type: tdd
Slug: config-get-impl
Reason: Get specific config value
Labels: tdd, cli, config
Description: |
Use TDD to add config get to `src/jiro/cli/config.py`:

- Get value by key (dot notation)
- Show value and source
- --json output
  Relevant files:
- src/jiro/cli/config.py
  Acceptance Criteria:
- \[ \] Gets value by key
- \[ \] Shows source
- \[ \] --json output works
- \[ \] Tests pass
  Depends on: \[config-list-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Implement config set command
Type: tdd
Slug: config-set-impl
Reason: Set config value
Labels: tdd, cli, config
Description: |
Use TDD to add config set to `src/jiro/cli/config.py`:

- Set value by key
- Write to project config
- Validate key exists in schema
  Relevant files:
- src/jiro/cli/config.py
  Acceptance Criteria:
- \[ \] Sets value by key
- \[ \] Writes to project config
- \[ \] Validates key
- \[ \] Tests pass
  Depends on: \[config-get-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Wire config commands to CLI
Type: refactoring
Slug: config-cli-wire
Reason: Connect config module to main CLI
Labels: refactoring, cli, config
Description: |
Use the refactoring skill to update main.py to import and use
the config command implementations from config.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/config.py
  Acceptance Criteria:
- \[ \] All config subcommands work from CLI
- \[ \] Tests pass
  Depends on: \[config-set-impl\]

______________________________________________________________________

### 4.9 Mode Command

______________________________________________________________________

Title: Implement mode command
Type: tdd
Slug: mode-command-impl
Reason: View and switch modes
Labels: tdd, cli, mode
Description: |
Use TDD to implement mode command in `src/jiro/cli/mode.py`:

- No argument: show current mode
- stealth/local: switch mode
- Migrate data between modes
- Confirmation prompt before migration
  Relevant files:
- src/jiro/cli/mode.py
  Acceptance Criteria:
- \[ \] Current mode displayed
- \[ \] Mode switch migrates data
- \[ \] Confirmation prompt works
- \[ \] Tests pass
  Depends on: \[paths-resolution, config-loader\]

______________________________________________________________________

______________________________________________________________________

Title: Wire mode command to CLI
Type: refactoring
Slug: mode-cli-wire
Reason: Connect mode module to main CLI
Labels: refactoring, cli, mode
Description: |
Use the refactoring skill to update main.py to import and use
the mode command implementation from mode.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/mode.py
  Acceptance Criteria:
- \[ \] Mode command works from CLI
- \[ \] Tests pass
  Depends on: \[mode-command-impl\]

______________________________________________________________________

### 4.10 Logs Command

______________________________________________________________________

Title: Implement logs command
Type: tdd
Slug: logs-command-impl
Reason: View structured logs
Labels: tdd, cli, logs
Description: |
Use TDD to implement logs command in `src/jiro/cli/logs.py`:

- Display logs from JSONL files
- Rich formatting
- --follow for live tail
- --tail N for last N lines
  Relevant files:
- src/jiro/cli/logs.py
  Acceptance Criteria:
- \[ \] Logs displayed with Rich formatting
- \[ \] --follow streams new entries
- \[ \] --tail shows last N lines
- \[ \] Tests pass
  Depends on: \[paths-resolution, structlog-config\]

______________________________________________________________________

______________________________________________________________________

Title: Wire logs command to CLI
Type: refactoring
Slug: logs-cli-wire
Reason: Connect logs module to main CLI
Labels: refactoring, cli, logs
Description: |
Use the refactoring skill to update main.py to import and use
the logs command implementation from logs.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/logs.py
  Acceptance Criteria:
- \[ \] Logs command works from CLI
- \[ \] Tests pass
  Depends on: \[logs-command-impl\]

______________________________________________________________________

### 4.11 Web Command

______________________________________________________________________

Title: Create FastAPI web application
Type: tdd
Slug: web-app-fastapi
Reason: Read-only web dashboard
Labels: tdd, web, fastapi
Description: |
Use TDD to create `src/jiro/web/app.py`:

- FastAPI application
- Static file serving
- HTMX template rendering
  Relevant files:
- src/jiro/web/app.py
  Acceptance Criteria:
- \[ \] FastAPI app configured
- \[ \] Static files served
- \[ \] Template rendering works
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Create task list dashboard view
Type: tdd
Slug: web-task-list
Reason: Display tasks in web UI
Labels: tdd, web, views
Description: |
Use TDD to create task list route in `src/jiro/web/routes/`:

- GET /tasks - List all tasks
- Grouped by epic/status
- HTMX template
  Relevant files:
- src/jiro/web/routes/tasks.py
- src/jiro/web/templates/tasks.html
  Acceptance Criteria:
- \[ \] Task list endpoint works
- \[ \] Tasks grouped correctly
- \[ \] HTMX template renders
- \[ \] Tests pass
  Depends on: \[web-app-fastapi, beads-tracker-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Create session status dashboard view
Type: tdd
Slug: web-session-status
Reason: Display session status in web UI
Labels: tdd, web, views
Description: |
Use TDD to create session status route in `src/jiro/web/routes/`:

- GET /status - Active sessions
- Current task, progress
- HTMX template
  Relevant files:
- src/jiro/web/routes/status.py
- src/jiro/web/templates/status.html
  Acceptance Criteria:
- \[ \] Session status endpoint works
- \[ \] Active sessions shown
- \[ \] HTMX template renders
- \[ \] Tests pass
  Depends on: \[web-app-fastapi, session-repository\]

______________________________________________________________________

______________________________________________________________________

Title: Create log viewer dashboard view
Type: tdd
Slug: web-log-viewer
Reason: Display logs in web UI
Labels: tdd, web, views
Description: |
Use TDD to create log viewer route in `src/jiro/web/routes/`:

- GET /logs - Recent logs
- HTMX template with auto-refresh
  Relevant files:
- src/jiro/web/routes/logs.py
- src/jiro/web/templates/logs.html
  Acceptance Criteria:
- \[ \] Log viewer endpoint works
- \[ \] Logs displayed correctly
- \[ \] HTMX auto-refresh works
- \[ \] Tests pass
  Depends on: \[web-app-fastapi, paths-resolution\]

______________________________________________________________________

______________________________________________________________________

Title: Implement web command
Type: tdd
Slug: web-command-impl
Reason: Start web dashboard server
Labels: tdd, cli, web
Description: |
Use TDD to implement web command in `src/jiro/cli/web.py`:

- Start FastAPI server
- --port option
- --daemon for background
  Relevant files:
- src/jiro/cli/web.py
  Acceptance Criteria:
- \[ \] Server starts on configured port
- \[ \] --daemon runs in background
- \[ \] Tests pass
  Depends on: \[web-task-list, web-session-status, web-log-viewer\]

______________________________________________________________________

______________________________________________________________________

Title: Wire web command to CLI
Type: refactoring
Slug: web-cli-wire
Reason: Connect web module to main CLI
Labels: refactoring, cli, web
Description: |
Use the refactoring skill to update main.py to import and use
the web command implementation from web.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/web.py
  Acceptance Criteria:
- \[ \] Web command works from CLI
- \[ \] Tests pass
  Depends on: \[web-command-impl\]

______________________________________________________________________

### 4.12 Assets Commands

______________________________________________________________________

Title: Complete asset loader implementation
Type: tdd
Slug: asset-loader-complete
Reason: Load assets from package
Labels: tdd, assets, loader
Description: |
Use TDD to complete `src/jiro/assets/loader.py`:

- load_prompt(name: str) -> str
- load_template(name: str) -> Template
- list_assets() -> list\[AssetInfo\]
- get_asset_path(name: str) -> Path
  Relevant files:
- src/jiro/assets/loader.py
  Acceptance Criteria:
- \[ \] Loads prompts from package
- \[ \] Loads templates from package
- \[ \] Lists all available assets
- \[ \] Returns correct paths
- \[ \] Tests pass
  Depends on: \[\]

______________________________________________________________________

______________________________________________________________________

Title: Implement assets list command
Type: tdd
Slug: assets-list-impl
Reason: List available assets
Labels: tdd, cli, assets
Description: |
Use TDD to implement assets list in `src/jiro/cli/assets.py`:

- List all bundled assets
- Show asset type (prompt, template)
- Rich formatting
  Relevant files:
- src/jiro/cli/assets.py
  Acceptance Criteria:
- \[ \] Lists all assets
- \[ \] Shows asset types
- \[ \] Rich formatting
- \[ \] Tests pass
  Depends on: \[asset-loader-complete\]

______________________________________________________________________

______________________________________________________________________

Title: Implement assets which command
Type: tdd
Slug: assets-which-impl
Reason: Show asset location
Labels: tdd, cli, assets
Description: |
Use TDD to add assets which to `src/jiro/cli/assets.py`:

- Show package location for asset
- (Steel thread: always package, no overrides)
  Relevant files:
- src/jiro/cli/assets.py
  Acceptance Criteria:
- \[ \] Shows package location
- \[ \] Tests pass
  Depends on: \[assets-list-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Implement assets customize command stub
Type: tdd
Slug: assets-customize-impl
Reason: Explain deferred feature
Labels: tdd, cli, assets
Description: |
Use TDD to add assets customize to `src/jiro/cli/assets.py`:

- Show message that overrides are deferred
- List what the package default contains
  Relevant files:
- src/jiro/cli/assets.py
  Acceptance Criteria:
- \[ \] Explains feature is deferred
- \[ \] Shows package default content
- \[ \] Tests pass
  Depends on: \[assets-which-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Wire assets commands to CLI
Type: refactoring
Slug: assets-cli-wire
Reason: Connect assets module to main CLI
Labels: refactoring, cli, assets
Description: |
Use the refactoring skill to update main.py to import and use
the assets command implementations from assets.py module.
Relevant files:

- src/jiro/cli/main.py
- src/jiro/cli/assets.py
  Acceptance Criteria:
- \[ \] All assets subcommands work from CLI
- \[ \] Tests pass
  Depends on: \[assets-customize-impl\]

______________________________________________________________________

______________________________________________________________________

## Phase 5: Testing

### 5.1 Unit Tests

______________________________________________________________________

Title: Create unit tests for config module
Type: tdd
Slug: unit-tests-config
Reason: Test configuration loading
Labels: tdd, testing, unit
Description: |
Create comprehensive unit tests for config module:

- Test schema defaults
- Test loader with missing file
- Test loader with partial config
- Test loader with full config
  Relevant files:
- tests/unit/test_config.py
  Acceptance Criteria:
- \[ \] All config scenarios tested
- \[ \] Mocks used appropriately
- \[ \] > 90% coverage for config module
- \[ \] Tests pass
  Depends on: \[config-loader\]

______________________________________________________________________

______________________________________________________________________

Title: Create unit tests for paths module
Type: tdd
Slug: unit-tests-paths
Reason: Test path resolution
Labels: tdd, testing, unit
Description: |
Create comprehensive unit tests for paths module:

- Test normal mode paths
- Test stealth mode paths
- Test all path types
  Relevant files:
- tests/unit/test_paths.py
  Acceptance Criteria:
- \[ \] All path scenarios tested
- \[ \] > 90% coverage for paths module
- \[ \] Tests pass
  Depends on: \[paths-resolution\]

______________________________________________________________________

______________________________________________________________________

Title: Create unit tests for database module
Type: tdd
Slug: unit-tests-database
Reason: Test database operations
Labels: tdd, testing, unit
Description: |
Create comprehensive unit tests for database module:

- Test database creation
- Test schema creation
- Test all dataclass models
- Test all repositories
  Relevant files:
- tests/unit/test_database.py
  Acceptance Criteria:
- \[ \] All database scenarios tested
- \[ \] In-memory SQLite used
- \[ \] > 90% coverage for db module
- \[ \] Tests pass
  Depends on: \[commit-repository\]

______________________________________________________________________

______________________________________________________________________

Title: Create unit tests for commit module
Type: tdd
Slug: unit-tests-commit
Reason: Test commit enforcement
Labels: tdd, testing, unit
Description: |
Create comprehensive unit tests for commit module:

- Test docs commit validation
- Test template rendering
- Test git operations (mocked)
  Relevant files:
- tests/unit/test_commit.py
  Acceptance Criteria:
- \[ \] All commit scenarios tested
- \[ \] Git operations mocked
- \[ \] > 90% coverage for commit module
- \[ \] Tests pass
  Depends on: \[commit-enforcement-docs\]

______________________________________________________________________

______________________________________________________________________

Title: Create unit tests for tracker module
Type: tdd
Slug: unit-tests-tracker
Reason: Test issue tracker facade
Labels: tdd, testing, unit
Description: |
Create comprehensive unit tests for tracker module:

- Test BeadsTracker with mocked subprocess
- Test all interface methods
- Test error handling
  Relevant files:
- tests/unit/test_tracker.py
  Acceptance Criteria:
- \[ \] All tracker scenarios tested
- \[ \] Subprocess calls mocked
- \[ \] > 90% coverage for tracker module
- \[ \] Tests pass
  Depends on: \[beads-tracker-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Create unit tests for agents
Type: tdd
Slug: unit-tests-agents
Reason: Test agent implementations
Labels: tdd, testing, unit
Description: |
Create comprehensive unit tests for agents:

- Test AgentClient with mocked SDK
- Test PlanningAgent
- Test ExecutionAgent
- Test ReviewAgent
- Test DreamingAgent
  Relevant files:
- tests/unit/agents/test_base.py
- tests/unit/agents/test_planning.py
- tests/unit/agents/test_execution.py
- tests/unit/agents/test_review.py
- tests/unit/agents/test_dreaming.py
  Acceptance Criteria:
- \[ \] All agent scenarios tested
- \[ \] SDK calls mocked
- \[ \] > 90% coverage for agents module
- \[ \] Tests pass
  Depends on: \[dreaming-agent-impl, review-agent-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Create unit tests for CLI commands
Type: tdd
Slug: unit-tests-cli
Reason: Test CLI command implementations
Labels: tdd, testing, unit
Description: |
Create comprehensive unit tests for all CLI commands:

- Test command execution with typer.testing
- Test output formatting
- Test error handling
  Relevant files:
- tests/unit/cli/test_init.py
- tests/unit/cli/test_doctor.py
- tests/unit/cli/test_dream.py
- tests/unit/cli/test_plan.py
- tests/unit/cli/test_tasks.py
- tests/unit/cli/test_execute.py
- tests/unit/cli/test_status.py
- tests/unit/cli/test_config.py
- tests/unit/cli/test_mode.py
- tests/unit/cli/test_logs.py
- tests/unit/cli/test_web.py
- tests/unit/cli/test_assets.py
  Acceptance Criteria:
- \[ \] All CLI commands tested
- \[ \] Dependencies mocked
- \[ \] > 80% coverage for CLI module
- \[ \] Tests pass
  Depends on: \[assets-cli-wire\]

______________________________________________________________________

### 5.2 Integration Tests

______________________________________________________________________

Title: Create integration test for dream flow
Type: tdd
Slug: integration-test-dream
Reason: Test full dream workflow
Labels: tdd, testing, integration
Description: |
Create integration test with VCR for dream flow:

- Test spec generation
- Test chat refinement
- Test spec saving
  Record real API interactions.
  Relevant files:
- tests/integration/test_dream_flow.py
- tests/integration/cassettes/dream\_\*.yaml
  Acceptance Criteria:
- \[ \] Full dream flow tested
- \[ \] VCR cassette recorded
- \[ \] No API calls on replay
- \[ \] Tests pass
  Depends on: \[dream-command-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Create integration test for plan flow
Type: tdd
Slug: integration-test-plan
Reason: Test full plan workflow
Labels: tdd, testing, integration
Description: |
Create integration test with VCR for plan flow:

- Test spec parsing
- Test task decomposition
- Test task creation in beads
  Record real API interactions.
  Relevant files:
- tests/integration/test_plan_flow.py
- tests/integration/cassettes/plan\_\*.yaml
  Acceptance Criteria:
- \[ \] Full plan flow tested
- \[ \] VCR cassette recorded
- \[ \] No API calls on replay
- \[ \] Tests pass
  Depends on: \[plan-command-impl\]

______________________________________________________________________

______________________________________________________________________

Title: Create integration test for execute flow
Type: tdd
Slug: integration-test-execute
Reason: Test full execute workflow
Labels: tdd, testing, integration
Description: |
Create integration test with VCR for execute flow:

- Test session creation
- Test task execution
- Test commit creation
- Test review validation
  Record real API interactions (with docs-only task).
  Relevant files:
- tests/integration/test_execute_flow.py
- tests/integration/cassettes/execute\_\*.yaml
  Acceptance Criteria:
- \[ \] Full execute flow tested
- \[ \] VCR cassette recorded
- \[ \] No API calls on replay
- \[ \] Tests pass
  Depends on: \[execute-command-impl\]

______________________________________________________________________

### 5.3 E2E Tests

______________________________________________________________________

Title: Create E2E test for init command
Type: tdd
Slug: e2e-test-init
Reason: Test init command end-to-end
Labels: tdd, testing, e2e
Description: |
Create E2E test for init command:

- Create temp git repo
- Run jiro init
- Verify directory structure
- Verify config file
- Verify beads initialized
  Relevant files:
- tests/e2e/test_init_command.py
  Acceptance Criteria:
- \[ \] Init tested in subprocess
- \[ \] File system verified
- \[ \] Temp directories cleaned up
- \[ \] Tests pass
  Depends on: \[init-cli-wire\]

______________________________________________________________________

______________________________________________________________________

Title: Create E2E test for full workflow
Type: tdd
Slug: e2e-test-full-workflow
Reason: Test complete jiro workflow
Labels: tdd, testing, e2e
Description: |
Create E2E test for full workflow:

- jiro init
- jiro dream (with recorded cassette)
- jiro plan (with recorded cassette)
- jiro execute (with recorded cassette)
  Verify database state and file changes.
  Relevant files:
- tests/e2e/test_full_workflow.py
  Acceptance Criteria:
- \[ \] Full workflow tested
- \[ \] Database state verified
- \[ \] File changes verified
- \[ \] Tests pass
  Depends on: \[integration-test-execute\]

______________________________________________________________________

______________________________________________________________________

## Summary

Total tasks: 85

### By Phase

- Phase 1 (Foundation): 14 tasks
- Phase 2 (Core Execution): 17 tasks
- Phase 3 (Dreaming & Planning): 6 tasks
- Phase 4 (CLI): 36 tasks
- Phase 5 (Testing): 12 tasks

### By Type

- TDD tasks: 72
- Refactoring tasks: 13
