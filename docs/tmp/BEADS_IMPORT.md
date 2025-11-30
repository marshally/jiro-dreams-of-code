## config-schema-dataclass Create config dataclass with defaults

| Use TDD to create the config dataclass in `src/jiro/config/schema.py`. The dataclass should include all configuration fields with sensible defaults: - models (planning, execution, review) - commands (test, lint, lint_fix) - conventions (test_file_pattern) - preflight settings

**Reason**: Foundation for configuration system

### Priority

0

### Type

feature

### Labels

tdd,config,foundation

### Design

**Relevant Files**:

- src/jiro/config/schema.py

### Acceptance Criteria

- \[ \] Config dataclass exists with all fields from DDL.md and SESSION_LIFECYCLE.md
- \[ \] Defaults work when no values provided
- \[ \] Type hints for all fields
- \[ \] Tests pass

______________________________________________________________________

## config-loader Create config loader for project scope

| Use TDD to create `src/jiro/config/loader.py` that loads config from `~/.jiro-dreams-of-code/$PROJECT/config.yaml`. Should return the Config dataclass populated from YAML with defaults for missing values.

**Reason**: Load configuration from YAML files

### Priority

1

### Type

feature

### Labels

tdd,config,foundation

### Design

**Relevant Files**:

- src/jiro/config/loader.py
- src/jiro/config/schema.py

### Acceptance Criteria

- \[ \] Loads config from project scope directory
- \[ \] Returns Config dataclass with YAML values
- \[ \] Uses defaults when config file missing
- \[ \] Uses defaults for missing keys in config
- \[ \] Tests pass

______________________________________________________________________

## paths-resolution Create path resolution for normal and stealth modes

| Use TDD to create `src/jiro/core/paths.py` with path resolution logic. Normal mode: `.jiro-dreams-of-code/` in project root Stealth mode: `~/.jiro-dreams-of-code/$PROJECT/` Should provide functions for: - get_jiro_dir(stealth: bool) -> Path - get_database_path(stealth: bool) -> Path - get_config_path(stealth: bool) -> Path - get_specs_dir(stealth: bool) -> Path - get_logs_dir(stealth: bool) -> Path

**Reason**: Support dual storage modes

### Priority

0

### Type

feature

### Labels

tdd,core,foundation

### Design

**Relevant Files**:

- src/jiro/core/paths.py

### Acceptance Criteria

- \[ \] Path resolution works for normal mode
- \[ \] Path resolution works for stealth mode
- \[ \] All directory types supported (db, config, specs, logs)
- \[ \] Tests pass

______________________________________________________________________

## project-name-from-git Create project name derivation from git remote

| Use TDD to create `src/jiro/core/project.py` with function to derive project name from git remote URL. Handle various URL formats: - git@github.com:user/repo.git -> repo - https://github.com/user/repo.git -> repo - https://github.com/user/repo -> repo Should also handle edge cases (no remote, multiple remotes).

**Reason**: Derive unique project identifier

### Priority

0

### Type

feature

### Labels

tdd,core,foundation

### Design

**Relevant Files**:

- src/jiro/core/project.py

### Acceptance Criteria

- \[ \] Derives name from SSH git URLs
- \[ \] Derives name from HTTPS git URLs
- \[ \] Handles missing .git suffix
- \[ \] Returns sensible default when no remote
- \[ \] Tests pass

______________________________________________________________________

## database-wrapper Create sqlite-utils database wrapper

| Use TDD to create `src/jiro/db/database.py` with: - get_database(db_path: Path) -> Database - ensure_schema(db: Database) -> None Following the pattern in DDL.md. Must enable foreign keys with PRAGMA.

**Reason**: Centralized database access with foreign keys

### Priority

0

### Type

feature

### Labels

tdd,db,foundation

### Design

**Relevant Files**:

- src/jiro/db/database.py

### Acceptance Criteria

- \[ \] Database connection with foreign keys enabled
- \[ \] Schema creation using sqlite-utils API
- \[ \] All four tables created (sessions, prompts, task_executions, commits)
- \[ \] Indexes created for common queries
- \[ \] Tests pass

______________________________________________________________________

## session-dataclass Create Session dataclass with from_row/to_row

| Use TDD to create the Session dataclass in `src/jiro/db/models.py` following the specification in DDL.md. Include from_row() and to_row() methods for database serialization.

**Reason**: Type-safe session model

### Priority

0

### Type

feature

### Labels

tdd,db,models

### Design

**Relevant Files**:

- src/jiro/db/models.py

### Acceptance Criteria

- \[ \] Session dataclass with all fields from DDL.md
- \[ \] from_row() classmethod for deserialization
- \[ \] to_row() method for serialization
- \[ \] Proper datetime handling
- \[ \] Tests pass

______________________________________________________________________

## prompt-dataclass Create Prompt dataclass with from_row/to_row

| Use TDD to create the Prompt dataclass in `src/jiro/db/models.py` following the specification in DDL.md. Include from_row() and to_row() methods for database serialization.

**Reason**: Type-safe prompt model

### Priority

0

### Type

feature

### Labels

tdd,db,models

### Design

**Relevant Files**:

- src/jiro/db/models.py

### Acceptance Criteria

- \[ \] Prompt dataclass with all fields from DDL.md
- \[ \] from_row() classmethod for deserialization
- \[ \] to_row() method for serialization
- \[ \] Proper datetime handling
- \[ \] Tests pass

______________________________________________________________________

## task-execution-dataclass Create TaskExecution dataclass with from_row/to_row

| Use TDD to create the TaskExecution dataclass in `src/jiro/db/models.py` following the specification in DDL.md. Include from_row() and to_row() methods for database serialization.

**Reason**: Type-safe task execution model

### Priority

0

### Type

feature

### Labels

tdd,db,models

### Design

**Relevant Files**:

- src/jiro/db/models.py

### Acceptance Criteria

- \[ \] TaskExecution dataclass with all fields from DDL.md
- \[ \] from_row() classmethod for deserialization
- \[ \] to_row() method for serialization
- \[ \] Proper datetime handling
- \[ \] Tests pass

______________________________________________________________________

## commit-dataclass Create Commit dataclass with from_row/to_row

| Use TDD to create the Commit dataclass in `src/jiro/db/models.py` following the specification in DDL.md. Include from_row() and to_row() methods for database serialization.

**Reason**: Type-safe commit model

### Priority

0

### Type

feature

### Labels

tdd,db,models

### Design

**Relevant Files**:

- src/jiro/db/models.py

### Acceptance Criteria

- \[ \] Commit dataclass with all fields from DDL.md
- \[ \] from_row() classmethod for deserialization
- \[ \] to_row() method for serialization
- \[ \] Proper datetime handling
- \[ \] Tests pass

______________________________________________________________________

## session-repository Create SessionRepository for CRUD operations

| Use TDD to create SessionRepository in `src/jiro/db/repository.py` with: - create(session: Session) -> Session - get(id: str) -> Session | None - get_active() -> list\[Session\] - update(session: Session) -> Session - get_by_status(status: str) -> list\[Session\]

**Reason**: Encapsulate session database operations

### Priority

1

### Type

feature

### Labels

tdd,db,repository

### Design

**Relevant Files**:

- src/jiro/db/repository.py

### Acceptance Criteria

- \[ \] CRUD operations work correctly
- \[ \] Uses Session dataclass
- \[ \] get_active returns running sessions
- \[ \] Tests pass

______________________________________________________________________

## prompt-repository Create PromptRepository for CRUD operations

| Use TDD to create PromptRepository in `src/jiro/db/repository.py` with: - create(prompt: Prompt) -> Prompt - get(id: str) -> Prompt | None - get_by_session(session_id: str) -> list\[Prompt\] - get_by_task(task_id: str) -> list\[Prompt\] - get_total_tokens(session_id: str) -> int

**Reason**: Encapsulate prompt database operations

### Priority

1

### Type

feature

### Labels

tdd,db,repository

### Design

**Relevant Files**:

- src/jiro/db/repository.py

### Acceptance Criteria

- \[ \] CRUD operations work correctly
- \[ \] Uses Prompt dataclass
- \[ \] Token aggregation query works
- \[ \] Tests pass

______________________________________________________________________

## task-execution-repository Create TaskExecutionRepository for CRUD operations

| Use TDD to create TaskExecutionRepository in `src/jiro/db/repository.py` with: - create(execution: TaskExecution) -> TaskExecution - get(id: str) -> TaskExecution | None - get_by_session(session_id: str) -> list\[TaskExecution\] - get_by_task(task_id: str) -> list\[TaskExecution\] - update(execution: TaskExecution) -> TaskExecution

**Reason**: Encapsulate task execution database operations

### Priority

1

### Type

feature

### Labels

tdd,db,repository

### Design

**Relevant Files**:

- src/jiro/db/repository.py

### Acceptance Criteria

- \[ \] CRUD operations work correctly
- \[ \] Uses TaskExecution dataclass
- \[ \] Filtering by session/task works
- \[ \] Tests pass

______________________________________________________________________

## commit-repository Create CommitRepository for CRUD operations

| Use TDD to create CommitRepository in `src/jiro/db/repository.py` with: - create(commit: Commit) -> Commit - get(id: str) -> Commit | None - get_by_session(session_id: str) -> list\[Commit\] - get_by_task(task_id: str) -> list\[Commit\] - get_by_type(session_id: str, commit_type: str) -> list\[Commit\]

**Reason**: Encapsulate commit database operations

### Priority

1

### Type

feature

### Labels

tdd,db,repository

### Design

**Relevant Files**:

- src/jiro/db/repository.py

### Acceptance Criteria

- \[ \] CRUD operations work correctly
- \[ \] Uses Commit dataclass
- \[ \] Filtering by type works
- \[ \] Tests pass

______________________________________________________________________

## structlog-config Configure structlog for jiro

| Use TDD to create `src/jiro/core/logging.py` with structlog configuration: - JSONL output to `~/.jiro-dreams-of-code/$PROJECT/logs/YYYY-MM-DD.jsonl` - Rich console output for human readability - Context binding (session_id, task_id flow through) - Verbosity levels: default=INFO, -v=DEBUG, --quiet=CRITICAL

**Reason**: Structured logging with JSONL and Rich output

### Priority

1

### Type

feature

### Labels

tdd,logging,foundation

### Design

**Relevant Files**:

- src/jiro/core/logging.py

### Acceptance Criteria

- \[ \] JSONL logs written to correct location
- \[ \] Rich console output formatted
- \[ \] Context binding works (session_id, task_id)
- \[ \] Verbosity flags work correctly
- \[ \] Tests pass

______________________________________________________________________

## cli-logging-integration Update CLI to initialize logging with verbosity

| Update `src/jiro/cli/main.py` to initialize structlog on startup. Add global options for verbosity (-v, -vv, --quiet). Use the refactoring skill to add logging initialization to the main callback.

**Reason**: Wire logging into CLI entry point

### Priority

1

### Type

chore

### Labels

refactoring,cli,logging

### Design

**Relevant Files**:

- src/jiro/cli/main.py

### Acceptance Criteria

- \[ \] Logging initialized on CLI startup
- \[ \] -v flag sets DEBUG level
- \[ \] -vv flag sets TRACE/DEBUG level
- \[ \] --quiet flag sets CRITICAL level
- \[ \] Tests pass

______________________________________________________________________

## tracker-protocol Create IssueTracker protocol interface

| Use TDD to create `src/jiro/trackers/interface.py` with the Protocol: - create_task(title, description, task_type, ...) -> Task - get_task(task_id) -> Task - list_tasks(status, epic_id) -> list\[Task\] - update_task(task_id, status, \*\*kwargs) -> Task - get_next_ready_task(epic_id) -> Task | None - add_dependency(task_id, depends_on_id) -> None - close_task(task_id, reason) -> None Also create the Task dataclass.

**Reason**: Abstract interface for issue trackers

### Priority

0

### Type

feature

### Labels

tdd,tracker,foundation

### Design

**Relevant Files**:

- src/jiro/trackers/interface.py

### Acceptance Criteria

- \[ \] Protocol defined with all methods
- \[ \] Task dataclass with required fields
- \[ \] Type hints for all parameters
- \[ \] Tests pass

______________________________________________________________________

## beads-tracker-impl Implement BeadsTracker via bd CLI

| Use TDD to create `src/jiro/trackers/beads.py` implementing IssueTracker by shelling out to `bd` CLI commands. Handle JSON output parsing. Initialize beads database in correct location based on mode.

**Reason**: Integrate with beads issue tracker

### Priority

1

### Type

feature

### Labels

tdd,tracker,beads

### Design

**Relevant Files**:

- src/jiro/trackers/beads.py

### Acceptance Criteria

- \[ \] All IssueTracker methods implemented
- \[ \] Uses `bd` CLI with --json flag
- \[ \] Parses JSON output into Task objects
- \[ \] Error handling for bd command failures
- \[ \] Initializes beads in correct location (normal vs stealth)
- \[ \] Tests pass (mocking subprocess calls)

______________________________________________________________________

## agent-config Create AgentConfig dataclass

| Use TDD to create AgentConfig dataclass in `src/jiro/agents/base.py`: - model: str - system_prompt: str - allowed_tools: list\[str\] - permission_mode: str = "acceptEdits" - max_turns: int = 10

**Reason**: Configuration for agent execution

### Priority

0

### Type

feature

### Labels

tdd,agents,foundation

### Design

**Relevant Files**:

- src/jiro/agents/base.py

### Acceptance Criteria

- \[ \] AgentConfig dataclass with all fields
- \[ \] Sensible defaults
- \[ \] Tests pass

______________________________________________________________________

## agent-result Create AgentResult dataclass

| Use TDD to create AgentResult dataclass in `src/jiro/agents/base.py`: - success: bool - output: str - tokens_before: int - tokens_after: int - error: str | None

**Reason**: Capture agent execution results

### Priority

0

### Type

feature

### Labels

tdd,agents,foundation

### Design

**Relevant Files**:

- src/jiro/agents/base.py

### Acceptance Criteria

- \[ \] AgentResult dataclass with all fields
- \[ \] Tests pass

______________________________________________________________________

## agent-client Create AgentClient wrapper for Claude Agent SDK

| Use TDD to create AgentClient in `src/jiro/agents/client.py`: - async execute(prompt: str, config: AgentConfig) -> AgentResult - Track context usage (tokens before/after) - Store results in prompts table - Proper error handling and logging

**Reason**: Wrap Claude Agent SDK with context tracking

### Priority

2

### Type

feature

### Labels

tdd,agents,foundation

### Design

**Relevant Files**:

- src/jiro/agents/client.py

### Acceptance Criteria

- \[ \] Wraps Claude Agent SDK
- \[ \] Context tracking captured
- \[ \] Results stored in prompts table
- \[ \] Proper error handling
- \[ \] Tests pass (mocking SDK)

______________________________________________________________________

## docs-commit-template Create docs commit template

| Use TDD to create `src/jiro/assets/templates/commit/docs.txt.j2`: - :memo: emoji prefix - Task reference and type - Reason for change - Verification command and results - Time taken and context tokens

**Reason**: Jinja2 template for documentation commits

### Priority

0

### Type

feature

### Labels

tdd,commits,templates

### Design

**Relevant Files**:

- src/jiro/assets/templates/commit/docs.txt.j2

### Acceptance Criteria

- \[ \] Template renders correctly
- \[ \] All required fields included
- \[ \] Jinja2 syntax valid
- \[ \] Tests pass

______________________________________________________________________

## commit-enforcement-docs Create commit enforcement for docs type

| Use TDD to create `src/jiro/core/commit.py` with create_docs_commit(): - Validate only .md files, docstrings, or comment changes - Raise error if non-docs files are staged - Render commit message from template - Create git commit - Record commit in database

**Reason**: Enforce documentation-only commits

### Priority

1

### Type

feature

### Labels

tdd,commits,enforcement

### Design

**Relevant Files**:

- src/jiro/core/commit.py

### Acceptance Criteria

- \[ \] Validates staged files are docs-only
- \[ \] Raises error for code changes
- \[ \] Renders template correctly
- \[ \] Creates git commit
- \[ \] Records in database
- \[ \] Tests pass

______________________________________________________________________

## planning-agent-prompt Create planning agent system prompt

| Create `src/jiro/assets/prompts/planning_agent.md` with instructions for: - Receiving task from issue tracker - Analyzing codebase context - Producing step-by-step execution plan - Identifying specific files, line numbers, patterns - Setting up verification commands

**Reason**: System prompt for task planning

### Priority

0

### Type

feature

### Labels

tdd,agents,prompts

### Design

**Relevant Files**:

- src/jiro/assets/prompts/planning_agent.md

### Acceptance Criteria

- \[ \] Clear instructions for planning
- \[ \] Output format specified (YAML)
- \[ \] Examples included
- \[ \] Tests pass (template loads)

______________________________________________________________________

## planning-agent-impl Create planning agent implementation

| Use TDD to create `src/jiro/agents/planning.py`: - PlanningAgent class using AgentClient - plan(task: Task) -> ExecutionPlan method - ExecutionPlan dataclass with steps, verification - Context tracking throughout

**Reason**: Agent that produces execution plans

### Priority

2

### Type

feature

### Labels

tdd,agents,planning

### Design

**Relevant Files**:

- src/jiro/agents/planning.py

### Acceptance Criteria

- \[ \] Planning agent produces structured plan
- \[ \] Plan includes specific files and actions
- \[ \] Plan includes verification command
- \[ \] Context usage tracked
- \[ \] Tests pass

______________________________________________________________________

## execution-agent-prompt Create execution agent system prompt

| Create `src/jiro/assets/prompts/execution_agent.md` with instructions for: - Receiving detailed plan from planning agent - Executing each step mechanically - Creating strongly-typed commits after logical units - Reporting results - NOT making autonomous decisions

**Reason**: System prompt for task execution

### Priority

0

### Type

feature

### Labels

tdd,agents,prompts

### Design

**Relevant Files**:

- src/jiro/assets/prompts/execution_agent.md

### Acceptance Criteria

- \[ \] Clear instructions for execution
- \[ \] Commit creation explained
- \[ \] Tools available documented
- \[ \] Examples included
- \[ \] Tests pass (template loads)

______________________________________________________________________

## execution-agent-impl Create execution agent implementation

| Use TDD to create `src/jiro/agents/execution.py`: - ExecutionAgent class using AgentClient - execute(plan: ExecutionPlan) -> ExecutionResult method - Creates docs commits via strongly-typed commit system - Stops on any error - Context tracking throughout

**Reason**: Agent that executes plans mechanically

### Priority

2

### Type

feature

### Labels

tdd,agents,execution

### Design

**Relevant Files**:

- src/jiro/agents/execution.py

### Acceptance Criteria

- \[ \] Execution agent follows plan step by step
- \[ \] Creates docs commits via commit system
- \[ \] Stops on any error
- \[ \] Context usage tracked
- \[ \] Tests pass

______________________________________________________________________

## review-agent-prompt Create review agent system prompt

| Create `src/jiro/assets/prompts/review_agent.md` with instructions for: - Verifying commits match claimed type - Checking for scope creep - Validating documentation-only changes - Flagging concerns

**Reason**: System prompt for commit review

### Priority

0

### Type

feature

### Labels

tdd,agents,prompts

### Design

**Relevant Files**:

- src/jiro/assets/prompts/review_agent.md

### Acceptance Criteria

- \[ \] Clear instructions for review
- \[ \] Validation criteria explained
- \[ \] Output format specified
- \[ \] Examples included
- \[ \] Tests pass (template loads)

______________________________________________________________________

## review-deterministic Create deterministic commit review checks

| Use TDD to create `src/jiro/core/review.py` with deterministic checks: - verify_commit_files(sha: str, commit_type: str) -> bool - verify_commit_message(sha: str) -> bool - verify_task_reference(sha: str, task_id: str) -> bool These run before LLM review to catch obvious violations.

**Reason**: Python validation before LLM review

### Priority

0

### Type

feature

### Labels

tdd,review,deterministic

### Design

**Relevant Files**:

- src/jiro/core/review.py

### Acceptance Criteria

- \[ \] File type validation for docs commits
- \[ \] Message template validation
- \[ \] Task reference validation
- \[ \] Clear error messages
- \[ \] Tests pass

______________________________________________________________________

## review-agent-impl Create review agent implementation

| Use TDD to create `src/jiro/agents/review.py`: - ReviewAgent class using AgentClient - review(commit_sha: str, task: Task) -> ReviewResult method - Runs deterministic checks first - Runs LLM review if deterministic passes - Returns HALT if any violation

**Reason**: Agent that validates commits

### Priority

2

### Type

feature

### Labels

tdd,agents,review

### Design

**Relevant Files**:

- src/jiro/agents/review.py

### Acceptance Criteria

- \[ \] Deterministic checks run first
- \[ \] LLM review validates semantic correctness
- \[ \] HALT on any violation
- \[ \] Review results logged
- \[ \] Tests pass

______________________________________________________________________

## session-preflight Create session preflight checks

| Use TDD to create session preflight in `src/jiro/core/session.py`: - check_git_clean() -> bool - check_correct_branch(config) -> bool - check_up_to_date() -> bool - check_tests_pass(config) -> bool - check_lint_pass(config) -> bool - run_preflight(config) -> PreflightResult

**Reason**: Validate environment before execution

### Priority

1

### Type

feature

### Labels

tdd,session,preflight

### Design

**Relevant Files**:

- src/jiro/core/session.py

### Acceptance Criteria

- \[ \] All checks implemented
- \[ \] Clear error messages on failure
- \[ \] Skip optimization for recent pass
- \[ \] Results logged
- \[ \] Tests pass

______________________________________________________________________

## session-postflight Create session postflight checks

| Use TDD to add session postflight to `src/jiro/core/session.py`: - run_full_tests(config) -> bool - run_full_lint(config) -> bool - push_to_origin() -> bool - run_postflight(config) -> PostflightResult

**Reason**: Validate environment after execution

### Priority

1

### Type

feature

### Labels

tdd,session,postflight

### Design

**Relevant Files**:

- src/jiro/core/session.py

### Acceptance Criteria

- \[ \] Full test suite runs
- \[ \] Full lint runs
- \[ \] Push to origin works
- \[ \] Results logged
- \[ \] Tests pass

______________________________________________________________________

## task-preflight Create task preflight checks

| Use TDD to create task preflight in `src/jiro/core/executor.py`: - run_relevant_tests(task, config) -> bool - run_relevant_lint(task, config) -> bool - enhance_task_with_planning(task) -> EnhancedTask - run_task_preflight(task, config) -> PreflightResult

**Reason**: Prepare context before task execution

### Priority

1

### Type

feature

### Labels

tdd,task,preflight

### Design

**Relevant Files**:

- src/jiro/core/executor.py

### Acceptance Criteria

- \[ \] Relevant tests identified and run
- \[ \] Relevant files linted
- \[ \] Planning agent called
- \[ \] Results logged
- \[ \] Tests pass

______________________________________________________________________

## task-postflight Create task postflight checks

| Use TDD to add task postflight to `src/jiro/core/executor.py`: - review_commits(task, commits) -> ReviewResult - run_relevant_tests_post(task, config) -> bool - run_relevant_lint_post(task, config) -> bool - record_results(task, result) -> None - close_task_in_tracker(task) -> None - run_task_postflight(task, commits, config) -> PostflightResult

**Reason**: Validate work after task execution

### Priority

2

### Type

feature

### Labels

tdd,task,postflight

### Design

**Relevant Files**:

- src/jiro/core/executor.py

### Acceptance Criteria

- \[ \] Review agent validates commits
- \[ \] Relevant tests run
- \[ \] Relevant files linted
- \[ \] Results recorded
- \[ \] Task closed in tracker
- \[ \] Tests pass

______________________________________________________________________

## session-orchestration Create session lifecycle orchestration

| Use TDD to create session orchestration in `src/jiro/core/session.py`: - SessionOrchestrator class - run(epic_id: str | None) -> SessionResult - Coordinates: preflight -> task loop -> postflight - Creates and updates database records - HALT on any failure

**Reason**: Coordinate full execution flow

### Priority

2

### Type

feature

### Labels

tdd,session,orchestration

### Design

**Relevant Files**:

- src/jiro/core/session.py

### Acceptance Criteria

- \[ \] Session created and tracked in database
- \[ \] Preflight checks run and logged
- \[ \] Tasks executed in dependency order
- \[ \] Postflight checks run
- \[ \] HALT on failure with proper error message
- \[ \] Session status updated throughout
- \[ \] Tests pass

______________________________________________________________________

## spec-schema-template Create spec schema template

| Create `src/jiro/assets/templates/spec_schema.md` with the spec format: - Feature title - Overview (1-2 paragraphs) - Requirements (bullet list) - Acceptance Criteria (checkbox list) - Out of Scope (bullet list) - Technical Notes

**Reason**: Define specification document format

### Priority

0

### Type

feature

### Labels

tdd,dreaming,templates

### Design

**Relevant Files**:

- src/jiro/assets/templates/spec_schema.md

### Acceptance Criteria

- \[ \] Schema fully defined
- \[ \] Examples included
- \[ \] Tests pass (template loads)

______________________________________________________________________

## dreaming-agent-prompt Create dreaming agent system prompt

| Create `src/jiro/assets/prompts/dreaming_agent.md` with instructions for: - Generating structured specifications - Following the spec schema - Asking clarifying questions - Focusing on requirements and acceptance criteria

**Reason**: System prompt for spec generation

### Priority

1

### Type

feature

### Labels

tdd,agents,prompts

### Design

**Relevant Files**:

- src/jiro/assets/prompts/dreaming_agent.md

### Acceptance Criteria

- \[ \] Clear instructions for spec generation
- \[ \] Schema reference included
- \[ \] Clarifying question guidance
- \[ \] Examples included
- \[ \] Tests pass (template loads)

______________________________________________________________________

## dreaming-agent-impl Create dreaming agent implementation

| Use TDD to create `src/jiro/agents/dreaming.py`: - DreamingAgent class using AgentClient - dream(prompt: str) -> Spec method - refine(spec: Spec, feedback: str) -> Spec method - Spec dataclass matching schema

**Reason**: Agent that generates specifications

### Priority

1

### Type

feature

### Labels

tdd,agents,dreaming

### Design

**Relevant Files**:

- src/jiro/agents/dreaming.py

### Acceptance Criteria

- \[ \] Dreaming agent generates spec from prompt
- \[ \] Spec follows defined schema
- \[ \] Refinement method works
- \[ \] Context usage tracked
- \[ \] Tests pass

______________________________________________________________________

## spec-parser Create spec parser

| Use TDD to create spec parser in `src/jiro/core/planner.py`: - parse_spec(path: Path) -> Spec - Extract all sections from markdown - Validate against schema

**Reason**: Parse spec documents for planning

### Priority

1

### Type

feature

### Labels

tdd,planner,parsing

### Design

**Relevant Files**:

- src/jiro/core/planner.py

### Acceptance Criteria

- \[ \] Parses spec markdown correctly
- \[ \] Extracts all sections
- \[ \] Validates required sections present
- \[ \] Returns Spec dataclass
- \[ \] Tests pass

______________________________________________________________________

## spec-planning-agent Create spec planning agent for task decomposition

| Use TDD to create spec planning in `src/jiro/core/planner.py`: - SpecPlanner class - plan(spec: Spec) -> PlanResult - Generates epics (parallel workstreams) - Generates tasks within epics - Analyzes and sets dependencies - Uses LLM for intelligent decomposition

**Reason**: Generate epics and tasks from specs

### Priority

1

### Type

feature

### Labels

tdd,planner,decomposition

### Design

**Relevant Files**:

- src/jiro/core/planner.py

### Acceptance Criteria

- \[ \] Spec parsed correctly
- \[ \] Epics generated for parallel work
- \[ \] Tasks generated with descriptions
- \[ \] Dependencies analyzed
- \[ \] Tests pass

______________________________________________________________________

## create-tasks-from-plan Create tasks from plan in issue tracker

| Use TDD to add task creation to `src/jiro/core/planner.py`: - create_tasks(plan: PlanResult, tracker: IssueTracker) -> list\[Task\] - Creates epics first - Creates tasks with dependencies - Returns created tasks

**Reason**: Create beads tasks from plan

### Priority

1

### Type

feature

### Labels

tdd,planner,tracker

### Design

**Relevant Files**:

- src/jiro/core/planner.py

### Acceptance Criteria

- \[ \] Epics created in tracker
- \[ \] Tasks created with dependencies
- \[ \] All tasks linked correctly
- \[ \] Summary available
- \[ \] Tests pass

______________________________________________________________________

## init-command-impl Implement init command core logic

| Use TDD to implement init command in `src/jiro/cli/init.py`: - Verify inside git repository - Derive project name from git remote - Create directory structure (normal or stealth) - Initialize beads database via `bd init` - Create default config file Extract from main.py stub.

**Reason**: Initialize jiro in a project

### Priority

2

### Type

feature

### Labels

tdd,cli,init

### Design

**Relevant Files**:

- src/jiro/cli/init.py
- src/jiro/cli/main.py

### Acceptance Criteria

- \[ \] Fails gracefully if not in git repo
- \[ \] Creates correct directory structure
- \[ \] Beads database initialized
- \[ \] Config file created with defaults
- \[ \] Tests pass

______________________________________________________________________

## init-interactive-mode Implement init command interactive mode

| Use TDD to add interactive mode to init command: - Prompt for test command - Prompt for lint command - Save to config file

**Reason**: Prompt for test/lint commands

### Priority

1

### Type

feature

### Labels

tdd,cli,init

### Design

**Relevant Files**:

- src/jiro/cli/init.py

### Acceptance Criteria

- \[ \] Prompts for test command
- \[ \] Prompts for lint command
- \[ \] Validates commands work
- \[ \] Saves to config
- \[ \] Tests pass

______________________________________________________________________

## init-cli-wire Wire init command to CLI

| Use the refactoring skill to update main.py to import and use the init command implementation from init.py module.

**Reason**: Connect init module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,init

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/init.py

### Acceptance Criteria

- \[ \] Init command works from CLI
- \[ \] All options functional
- \[ \] Tests pass

______________________________________________________________________

## doctor-checks-impl Implement doctor command checks

| Use TDD to implement doctor checks in `src/jiro/cli/doctor.py`: - check_python_version() -> CheckResult - check_claude_sdk() -> CheckResult - check_api_key() -> CheckResult - check_git() -> CheckResult - check_test_command(config) -> CheckResult - check_lint_command(config) -> CheckResult - check_beads() -> CheckResult - check_config() -> CheckResult - check_directories() -> CheckResult

**Reason**: Health checks for jiro installation

### Priority

1

### Type

feature

### Labels

tdd,cli,doctor

### Design

**Relevant Files**:

- src/jiro/cli/doctor.py

### Acceptance Criteria

- \[ \] All 9 checks implemented
- \[ \] Clear status reporting
- \[ \] Exit code reflects health
- \[ \] Tests pass

______________________________________________________________________

## doctor-fix-impl Implement doctor command --fix option

| Use TDD to add --fix support to doctor: - Fix missing directories - Fix missing config with defaults - Report what was fixed

**Reason**: Auto-remediation for fixable issues

### Priority

1

### Type

feature

### Labels

tdd,cli,doctor

### Design

**Relevant Files**:

- src/jiro/cli/doctor.py

### Acceptance Criteria

- \[ \] Creates missing directories
- \[ \] Creates missing config
- \[ \] Reports fixes applied
- \[ \] Tests pass

______________________________________________________________________

## doctor-cli-wire Wire doctor command to CLI

| Use the refactoring skill to update main.py to import and use the doctor command implementation from doctor.py module.

**Reason**: Connect doctor module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,doctor

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/doctor.py

### Acceptance Criteria

- \[ \] Doctor command works from CLI
- \[ \] --fix option functional
- \[ \] Tests pass

______________________________________________________________________

## dream-command-impl Implement dream command

| Use TDD to implement dream command in `src/jiro/cli/dream.py`: - Initialize dreaming agent - Generate initial spec from prompt - Display spec with Rich formatting - Enter chat refinement loop - Save final spec to specs directory

**Reason**: Generate specs from prompts

### Priority

1

### Type

feature

### Labels

tdd,cli,dream

### Design

**Relevant Files**:

- src/jiro/cli/dream.py

### Acceptance Criteria

- \[ \] Spec generated and displayed
- \[ \] Chat refinement works
- \[ \] Exit commands work (done, exit, /quit, Ctrl+D)
- \[ \] Spec saved to correct location
- \[ \] --model override works
- \[ \] Tests pass

______________________________________________________________________

## dream-cli-wire Wire dream command to CLI

| Use the refactoring skill to update main.py to import and use the dream command implementation from dream.py module.

**Reason**: Connect dream module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,dream

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/dream.py

### Acceptance Criteria

- \[ \] Dream command works from CLI
- \[ \] --model option functional
- \[ \] Tests pass

______________________________________________________________________

## plan-command-impl Implement plan command

| Use TDD to implement plan command in `src/jiro/cli/plan.py`: - Load spec file - Run spec planning agent - Display summary (epics, tasks, dependencies) - Prompt: `Proceed? [yes/chat/edit/quit]` - On yes: create tasks in beads

**Reason**: Generate tasks from specs

### Priority

1

### Type

feature

### Labels

tdd,cli,plan

### Design

**Relevant Files**:

- src/jiro/cli/plan.py

### Acceptance Criteria

- \[ \] Spec loaded from file
- \[ \] Planning produces epics and tasks
- \[ \] Summary displayed with Rich
- \[ \] Confirmation prompt works
- \[ \] Tasks created in beads on yes
- \[ \] Tests pass

______________________________________________________________________

## plan-cli-wire Wire plan command to CLI

| Use the refactoring skill to update main.py to import and use the plan command implementation from plan.py module.

**Reason**: Connect plan module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,plan

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/plan.py

### Acceptance Criteria

- \[ \] Plan command works from CLI
- \[ \] --spec option functional
- \[ \] Tests pass

______________________________________________________________________

## tasks-list-impl Implement tasks list command

| Use TDD to implement tasks list in `src/jiro/cli/tasks.py`: - List all tasks grouped by epic/status - Filter by status and epic - Rich formatting - --json output

**Reason**: List tasks with filtering

### Priority

1

### Type

feature

### Labels

tdd,cli,tasks

### Design

**Relevant Files**:

- src/jiro/cli/tasks.py

### Acceptance Criteria

- \[ \] Lists tasks with Rich formatting
- \[ \] Filtering by status works
- \[ \] Filtering by epic works
- \[ \] --json output works
- \[ \] Tests pass

______________________________________________________________________

## tasks-show-impl Implement tasks show command

| Use TDD to add tasks show to `src/jiro/cli/tasks.py`: - Show full task detail - Include dependencies - Include execution history - --json output

**Reason**: Show task details

### Priority

1

### Type

feature

### Labels

tdd,cli,tasks

### Design

**Relevant Files**:

- src/jiro/cli/tasks.py

### Acceptance Criteria

- \[ \] Shows full task detail
- \[ \] Includes dependencies
- \[ \] Includes history
- \[ \] --json output works
- \[ \] Tests pass

______________________________________________________________________

## tasks-next-impl Implement tasks next command

| Use TDD to add tasks next to `src/jiro/cli/tasks.py`: - Find task with no blockers - Filter by epic if specified - --json output

**Reason**: Show next ready task

### Priority

1

### Type

feature

### Labels

tdd,cli,tasks

### Design

**Relevant Files**:

- src/jiro/cli/tasks.py

### Acceptance Criteria

- \[ \] Finds next ready task
- \[ \] Epic filter works
- \[ \] --json output works
- \[ \] Tests pass

______________________________________________________________________

## tasks-cli-wire Wire tasks commands to CLI

| Use the refactoring skill to update main.py to import and use the tasks command implementations from tasks.py module.

**Reason**: Connect tasks module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,tasks

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/tasks.py

### Acceptance Criteria

- \[ \] All tasks subcommands work from CLI
- \[ \] Tests pass

______________________________________________________________________

## execute-command-impl Implement execute command

| Use TDD to implement execute command in `src/jiro/cli/execute.py`: - Create session using SessionOrchestrator - Run session with optional epic filter - Display progress with Rich - Handle HALT with clear message

**Reason**: Run task execution session

### Priority

1

### Type

feature

### Labels

tdd,cli,execute

### Design

**Relevant Files**:

- src/jiro/cli/execute.py

### Acceptance Criteria

- \[ \] Session created and tracked
- \[ \] Preflight checks run
- \[ \] Tasks executed in order
- \[ \] Postflight checks run
- \[ \] HALT on failure with clear message
- \[ \] --epic filter works
- \[ \] Tests pass

______________________________________________________________________

## execute-cli-wire Wire execute command to CLI

| Use the refactoring skill to update main.py to import and use the execute command implementation from execute.py module.

**Reason**: Connect execute module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,execute

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/execute.py

### Acceptance Criteria

- \[ \] Execute command works from CLI
- \[ \] --epic option functional
- \[ \] Tests pass

______________________________________________________________________

## status-command-impl Implement status command

| Use TDD to implement status command in `src/jiro/cli/status.py`: - Query active sessions from database - Display current status, task, progress - Rich formatting - --json output

**Reason**: Show active session status

### Priority

1

### Type

feature

### Labels

tdd,cli,status

### Design

**Relevant Files**:

- src/jiro/cli/status.py

### Acceptance Criteria

- \[ \] Active sessions displayed
- \[ \] Current task shown
- \[ \] Progress indicated
- \[ \] --json output works
- \[ \] Tests pass

______________________________________________________________________

## status-cli-wire Wire status command to CLI

| Use the refactoring skill to update main.py to import and use the status command implementation from status.py module.

**Reason**: Connect status module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,status

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/status.py

### Acceptance Criteria

- \[ \] Status command works from CLI
- \[ \] Tests pass

______________________________________________________________________

## config-list-impl Implement config list command

| Use TDD to implement config list in `src/jiro/cli/config.py`: - Show all config values - Show source (default, project) - Rich formatting - --json output

**Reason**: List configuration values

### Priority

1

### Type

feature

### Labels

tdd,cli,config

### Design

**Relevant Files**:

- src/jiro/cli/config.py

### Acceptance Criteria

- \[ \] Lists all config values
- \[ \] Shows value sources
- \[ \] Rich formatting
- \[ \] --json output works
- \[ \] Tests pass

______________________________________________________________________

## config-get-impl Implement config get command

| Use TDD to add config get to `src/jiro/cli/config.py`: - Get value by key (dot notation) - Show value and source - --json output

**Reason**: Get specific config value

### Priority

1

### Type

feature

### Labels

tdd,cli,config

### Design

**Relevant Files**:

- src/jiro/cli/config.py

### Acceptance Criteria

- \[ \] Gets value by key
- \[ \] Shows source
- \[ \] --json output works
- \[ \] Tests pass

______________________________________________________________________

## config-set-impl Implement config set command

| Use TDD to add config set to `src/jiro/cli/config.py`: - Set value by key - Write to project config - Validate key exists in schema

**Reason**: Set config value

### Priority

1

### Type

feature

### Labels

tdd,cli,config

### Design

**Relevant Files**:

- src/jiro/cli/config.py

### Acceptance Criteria

- \[ \] Sets value by key
- \[ \] Writes to project config
- \[ \] Validates key
- \[ \] Tests pass

______________________________________________________________________

## config-cli-wire Wire config commands to CLI

| Use the refactoring skill to update main.py to import and use the config command implementations from config.py module.

**Reason**: Connect config module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,config

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/config.py

### Acceptance Criteria

- \[ \] All config subcommands work from CLI
- \[ \] Tests pass

______________________________________________________________________

## mode-command-impl Implement mode command

| Use TDD to implement mode command in `src/jiro/cli/mode.py`: - No argument: show current mode - stealth/local: switch mode - Migrate data between modes - Confirmation prompt before migration

**Reason**: View and switch modes

### Priority

1

### Type

feature

### Labels

tdd,cli,mode

### Design

**Relevant Files**:

- src/jiro/cli/mode.py

### Acceptance Criteria

- \[ \] Current mode displayed
- \[ \] Mode switch migrates data
- \[ \] Confirmation prompt works
- \[ \] Tests pass

______________________________________________________________________

## mode-cli-wire Wire mode command to CLI

| Use the refactoring skill to update main.py to import and use the mode command implementation from mode.py module.

**Reason**: Connect mode module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,mode

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/mode.py

### Acceptance Criteria

- \[ \] Mode command works from CLI
- \[ \] Tests pass

______________________________________________________________________

## logs-command-impl Implement logs command

| Use TDD to implement logs command in `src/jiro/cli/logs.py`: - Display logs from JSONL files - Rich formatting - --follow for live tail - --tail N for last N lines

**Reason**: View structured logs

### Priority

1

### Type

feature

### Labels

tdd,cli,logs

### Design

**Relevant Files**:

- src/jiro/cli/logs.py

### Acceptance Criteria

- \[ \] Logs displayed with Rich formatting
- \[ \] --follow streams new entries
- \[ \] --tail shows last N lines
- \[ \] Tests pass

______________________________________________________________________

## logs-cli-wire Wire logs command to CLI

| Use the refactoring skill to update main.py to import and use the logs command implementation from logs.py module.

**Reason**: Connect logs module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,logs

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/logs.py

### Acceptance Criteria

- \[ \] Logs command works from CLI
- \[ \] Tests pass

______________________________________________________________________

## web-app-fastapi Create FastAPI web application

| Use TDD to create `src/jiro/web/app.py`: - FastAPI application - Static file serving - HTMX template rendering

**Reason**: Read-only web dashboard

### Priority

0

### Type

feature

### Labels

tdd,web,fastapi

### Design

**Relevant Files**:

- src/jiro/web/app.py

### Acceptance Criteria

- \[ \] FastAPI app configured
- \[ \] Static files served
- \[ \] Template rendering works
- \[ \] Tests pass

______________________________________________________________________

## web-task-list Create task list dashboard view

| Use TDD to create task list route in `src/jiro/web/routes/`: - GET /tasks - List all tasks - Grouped by epic/status - HTMX template

**Reason**: Display tasks in web UI

### Priority

1

### Type

feature

### Labels

tdd,web,views

### Design

**Relevant Files**:

- src/jiro/web/routes/tasks.py
- src/jiro/web/templates/tasks.html

### Acceptance Criteria

- \[ \] Task list endpoint works
- \[ \] Tasks grouped correctly
- \[ \] HTMX template renders
- \[ \] Tests pass

______________________________________________________________________

## web-session-status Create session status dashboard view

| Use TDD to create session status route in `src/jiro/web/routes/`: - GET /status - Active sessions - Current task, progress - HTMX template

**Reason**: Display session status in web UI

### Priority

1

### Type

feature

### Labels

tdd,web,views

### Design

**Relevant Files**:

- src/jiro/web/routes/status.py
- src/jiro/web/templates/status.html

### Acceptance Criteria

- \[ \] Session status endpoint works
- \[ \] Active sessions shown
- \[ \] HTMX template renders
- \[ \] Tests pass

______________________________________________________________________

## web-log-viewer Create log viewer dashboard view

| Use TDD to create log viewer route in `src/jiro/web/routes/`: - GET /logs - Recent logs - HTMX template with auto-refresh

**Reason**: Display logs in web UI

### Priority

1

### Type

feature

### Labels

tdd,web,views

### Design

**Relevant Files**:

- src/jiro/web/routes/logs.py
- src/jiro/web/templates/logs.html

### Acceptance Criteria

- \[ \] Log viewer endpoint works
- \[ \] Logs displayed correctly
- \[ \] HTMX auto-refresh works
- \[ \] Tests pass

______________________________________________________________________

## web-command-impl Implement web command

| Use TDD to implement web command in `src/jiro/cli/web.py`: - Start FastAPI server - --port option - --daemon for background

**Reason**: Start web dashboard server

### Priority

2

### Type

feature

### Labels

tdd,cli,web

### Design

**Relevant Files**:

- src/jiro/cli/web.py

### Acceptance Criteria

- \[ \] Server starts on configured port
- \[ \] --daemon runs in background
- \[ \] Tests pass

______________________________________________________________________

## web-cli-wire Wire web command to CLI

| Use the refactoring skill to update main.py to import and use the web command implementation from web.py module.

**Reason**: Connect web module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,web

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/web.py

### Acceptance Criteria

- \[ \] Web command works from CLI
- \[ \] Tests pass

______________________________________________________________________

## asset-loader-complete Complete asset loader implementation

| Use TDD to complete `src/jiro/assets/loader.py`: - load_prompt(name: str) -> str - load_template(name: str) -> Template - list_assets() -> list\[AssetInfo\] - get_asset_path(name: str) -> Path

**Reason**: Load assets from package

### Priority

0

### Type

feature

### Labels

tdd,assets,loader

### Design

**Relevant Files**:

- src/jiro/assets/loader.py

### Acceptance Criteria

- \[ \] Loads prompts from package
- \[ \] Loads templates from package
- \[ \] Lists all available assets
- \[ \] Returns correct paths
- \[ \] Tests pass

______________________________________________________________________

## assets-list-impl Implement assets list command

| Use TDD to implement assets list in `src/jiro/cli/assets.py`: - List all bundled assets - Show asset type (prompt, template) - Rich formatting

**Reason**: List available assets

### Priority

1

### Type

feature

### Labels

tdd,cli,assets

### Design

**Relevant Files**:

- src/jiro/cli/assets.py

### Acceptance Criteria

- \[ \] Lists all assets
- \[ \] Shows asset types
- \[ \] Rich formatting
- \[ \] Tests pass

______________________________________________________________________

## assets-which-impl Implement assets which command

| Use TDD to add assets which to `src/jiro/cli/assets.py`: - Show package location for asset - (Steel thread: always package, no overrides)

**Reason**: Show asset location

### Priority

1

### Type

feature

### Labels

tdd,cli,assets

### Design

**Relevant Files**:

- src/jiro/cli/assets.py

### Acceptance Criteria

- \[ \] Shows package location
- \[ \] Tests pass

______________________________________________________________________

## assets-customize-impl Implement assets customize command stub

| Use TDD to add assets customize to `src/jiro/cli/assets.py`: - Show message that overrides are deferred - List what the package default contains

**Reason**: Explain deferred feature

### Priority

1

### Type

feature

### Labels

tdd,cli,assets

### Design

**Relevant Files**:

- src/jiro/cli/assets.py

### Acceptance Criteria

- \[ \] Explains feature is deferred
- \[ \] Shows package default content
- \[ \] Tests pass

______________________________________________________________________

## assets-cli-wire Wire assets commands to CLI

| Use the refactoring skill to update main.py to import and use the assets command implementations from assets.py module.

**Reason**: Connect assets module to main CLI

### Priority

1

### Type

chore

### Labels

refactoring,cli,assets

### Design

**Relevant Files**:

- src/jiro/cli/main.py
- src/jiro/cli/assets.py

### Acceptance Criteria

- \[ \] All assets subcommands work from CLI
- \[ \] Tests pass

______________________________________________________________________

## unit-tests-config Create unit tests for config module

| Create comprehensive unit tests for config module: - Test schema defaults - Test loader with missing file - Test loader with partial config - Test loader with full config

**Reason**: Test configuration loading

### Priority

1

### Type

feature

### Labels

tdd,testing,unit

### Design

**Relevant Files**:

- tests/unit/test_config.py

### Acceptance Criteria

- \[ \] All config scenarios tested
- \[ \] Mocks used appropriately
- \[ \] > 90% coverage for config module
- \[ \] Tests pass

______________________________________________________________________

## unit-tests-paths Create unit tests for paths module

| Create comprehensive unit tests for paths module: - Test normal mode paths - Test stealth mode paths - Test all path types

**Reason**: Test path resolution

### Priority

1

### Type

feature

### Labels

tdd,testing,unit

### Design

**Relevant Files**:

- tests/unit/test_paths.py

### Acceptance Criteria

- \[ \] All path scenarios tested
- \[ \] > 90% coverage for paths module
- \[ \] Tests pass

______________________________________________________________________

## unit-tests-database Create unit tests for database module

| Create comprehensive unit tests for database module: - Test database creation - Test schema creation - Test all dataclass models - Test all repositories

**Reason**: Test database operations

### Priority

1

### Type

feature

### Labels

tdd,testing,unit

### Design

**Relevant Files**:

- tests/unit/test_database.py

### Acceptance Criteria

- \[ \] All database scenarios tested
- \[ \] In-memory SQLite used
- \[ \] > 90% coverage for db module
- \[ \] Tests pass

______________________________________________________________________

## unit-tests-commit Create unit tests for commit module

| Create comprehensive unit tests for commit module: - Test docs commit validation - Test template rendering - Test git operations (mocked)

**Reason**: Test commit enforcement

### Priority

1

### Type

feature

### Labels

tdd,testing,unit

### Design

**Relevant Files**:

- tests/unit/test_commit.py

### Acceptance Criteria

- \[ \] All commit scenarios tested
- \[ \] Git operations mocked
- \[ \] > 90% coverage for commit module
- \[ \] Tests pass

______________________________________________________________________

## unit-tests-tracker Create unit tests for tracker module

| Create comprehensive unit tests for tracker module: - Test BeadsTracker with mocked subprocess - Test all interface methods - Test error handling

**Reason**: Test issue tracker facade

### Priority

1

### Type

feature

### Labels

tdd,testing,unit

### Design

**Relevant Files**:

- tests/unit/test_tracker.py

### Acceptance Criteria

- \[ \] All tracker scenarios tested
- \[ \] Subprocess calls mocked
- \[ \] > 90% coverage for tracker module
- \[ \] Tests pass

______________________________________________________________________

## unit-tests-agents Create unit tests for agents

| Create comprehensive unit tests for agents: - Test AgentClient with mocked SDK - Test PlanningAgent - Test ExecutionAgent - Test ReviewAgent - Test DreamingAgent

**Reason**: Test agent implementations

### Priority

1

### Type

feature

### Labels

tdd,testing,unit

### Design

**Relevant Files**:

- tests/unit/agents/test_base.py
- tests/unit/agents/test_planning.py
- tests/unit/agents/test_execution.py
- tests/unit/agents/test_review.py
- tests/unit/agents/test_dreaming.py

### Acceptance Criteria

- \[ \] All agent scenarios tested
- \[ \] SDK calls mocked
- \[ \] > 90% coverage for agents module
- \[ \] Tests pass

______________________________________________________________________

## unit-tests-cli Create unit tests for CLI commands

| Create comprehensive unit tests for all CLI commands: - Test command execution with typer.testing - Test output formatting - Test error handling

**Reason**: Test CLI command implementations

### Priority

1

### Type

feature

### Labels

tdd,testing,unit

### Design

**Relevant Files**:

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

### Acceptance Criteria

- \[ \] All CLI commands tested
- \[ \] Dependencies mocked
- \[ \] > 80% coverage for CLI module
- \[ \] Tests pass

______________________________________________________________________

## integration-test-dream Create integration test for dream flow

| Create integration test with VCR for dream flow: - Test spec generation - Test chat refinement - Test spec saving Record real API interactions.

**Reason**: Test full dream workflow

### Priority

1

### Type

feature

### Labels

tdd,testing,integration

### Design

**Relevant Files**:

- tests/integration/test_dream_flow.py
- tests/integration/cassettes/dream\_\*.yaml

### Acceptance Criteria

- \[ \] Full dream flow tested
- \[ \] VCR cassette recorded
- \[ \] No API calls on replay
- \[ \] Tests pass

______________________________________________________________________

## integration-test-plan Create integration test for plan flow

| Create integration test with VCR for plan flow: - Test spec parsing - Test task decomposition - Test task creation in beads Record real API interactions.

**Reason**: Test full plan workflow

### Priority

1

### Type

feature

### Labels

tdd,testing,integration

### Design

**Relevant Files**:

- tests/integration/test_plan_flow.py
- tests/integration/cassettes/plan\_\*.yaml

### Acceptance Criteria

- \[ \] Full plan flow tested
- \[ \] VCR cassette recorded
- \[ \] No API calls on replay
- \[ \] Tests pass

______________________________________________________________________

## integration-test-execute Create integration test for execute flow

| Create integration test with VCR for execute flow: - Test session creation - Test task execution - Test commit creation - Test review validation Record real API interactions (with docs-only task).

**Reason**: Test full execute workflow

### Priority

1

### Type

feature

### Labels

tdd,testing,integration

### Design

**Relevant Files**:

- tests/integration/test_execute_flow.py
- tests/integration/cassettes/execute\_\*.yaml

### Acceptance Criteria

- \[ \] Full execute flow tested
- \[ \] VCR cassette recorded
- \[ \] No API calls on replay
- \[ \] Tests pass

______________________________________________________________________

## e2e-test-init Create E2E test for init command

| Create E2E test for init command: - Create temp git repo - Run jiro init - Verify directory structure - Verify config file - Verify beads initialized

**Reason**: Test init command end-to-end

### Priority

1

### Type

feature

### Labels

tdd,testing,e2e

### Design

**Relevant Files**:

- tests/e2e/test_init_command.py

### Acceptance Criteria

- \[ \] Init tested in subprocess
- \[ \] File system verified
- \[ \] Temp directories cleaned up
- \[ \] Tests pass

______________________________________________________________________

## e2e-test-full-workflow Create E2E test for full workflow

| Create E2E test for full workflow: - jiro init - jiro dream (with recorded cassette) - jiro plan (with recorded cassette) - jiro execute (with recorded cassette) Verify database state and file changes.

**Reason**: Test complete jiro workflow

### Priority

1

### Type

feature

### Labels

tdd,testing,e2e

### Design

**Relevant Files**:

- tests/e2e/test_full_workflow.py

### Acceptance Criteria

- \[ \] Full workflow tested
- \[ \] Database state verified
- \[ \] File changes verified
- \[ \] Tests pass

______________________________________________________________________
