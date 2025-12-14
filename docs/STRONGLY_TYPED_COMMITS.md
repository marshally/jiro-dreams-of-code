# Strongly Typed Commits

> Design document for jiro's commit discipline system.

## Related Documents

- [Session Lifecycle](SESSION_LIFECYCLE.md) - How commits fit into task/session execution
- [Technical Spec](TECHNICAL_SPEC.md) - Overall jiro architecture
- [DDL](DDL.md) - Database schema reference

______________________________________________________________________

## Overview

Jiro enforces commit discipline through a two-layer system:

1. **Layer 1 - Creation**: Python code enforces rules at commit-creation time. The commit is rejected if it violates type-specific rules.
1. **Layer 2 - Review**: Post-commit validation combines deterministic Python checks with LLM judgment calls.

This document describes the architecture for Layer 1: strongly typed commit creation.

______________________________________________________________________

## Architecture

### Execution Flow

Each step in a plan follows this flow:

```
┌─────────────────────────────────────────────────────────────────┐
│                      ExecutionStep                               │
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │ Command  │───▶│ Verification │───▶│    Commit    │          │
│  │          │    │              │    │              │          │
│  │ (spawns  │    │ (validates   │    │ (stores DB,  │          │
│  │ subagent)│    │  the work)   │    │  git commit) │          │
│  └──────────┘    └──────────────┘    └──────────────┘          │
│       │                 │                   │                   │
│       ▼                 ▼                   ▼                   │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │  Result  │    │ Verification │    │   Commit     │          │
│  │(dataclass│    │    Result    │    │   Result     │          │
│  └──────────┘    └──────────────┘    └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Aspect | Decision |
|--------|----------|
| Commit invocation | Direct function call from orchestrator (not MCP tool, not Bash) |
| Commit boundaries | Automatic after each step; one commit type per step |
| Class discovery | Convention-based from directory structure |
| Results | Pydantic dataclasses with multi-format serialization |
| Verification failure | Raise exception → HALT (human intervention required) |
| Abstractions | YAGNI - rule of 3 before extracting shared code |

______________________________________________________________________

## Core Type Definitions

### StepType Enum

```python
from enum import StrEnum


class StepType(StrEnum):
    """Step types for strongly typed commits.

    Uses StrEnum so values are directly usable as strings without .value
    """

    TDD_RED = "tdd_red"
    TDD_GREEN = "tdd_green"
    TDD_REFACTOR = "tdd_refactor"
    BUG_RED = "bug_red"
    BUG_GREEN = "bug_green"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    LINT_FIX = "lint_fix"
    CONFIG = "config"
    TEST_ONLY = "test_only"
    PERFORMANCE = "performance"
```

### PlanStep Dataclass

```python
@dataclass
class PlanStep:
    """A single step from the execution plan.

    Kept minimal - additional fields can be added during implementation if needed.
    """

    step_type: StepType
    planning_context: str  # Detailed instructions from planning agent
```

### VerificationError Exception

```python
class VerificationError(Exception):
    """Raised when step verification fails.

    Causes immediate HALT - human intervention required.
    """

    def __init__(
        self,
        step_type: StepType,
        rule_violated: str,
        expected: Any,
        actual: Any,
        details: str,
    ):
        self.step_type = step_type
        self.rule_violated = rule_violated
        self.expected = expected
        self.actual = actual
        self.details = details
        super().__init__(
            f"Verification failed for {step_type}: {rule_violated}\n"
            f"Expected: {expected}\n"
            f"Actual: {actual}\n"
            f"Details: {details}"
        )
```

______________________________________________________________________

## Commit Types

| Type | Emoji | Description |
|------|-------|-------------|
| `tdd_red` | 🔴 | Add failing test, mark as skipped |
| `tdd_green` | 🟢 | Implement code to pass test, unskip test |
| `tdd_refactor` | ♻️ | Refactor implementation, tests still pass |
| `bug_red` | 🐛 | Add failing test proving bug exists, mark as skipped |
| `bug_green` | 🦋 | Fix bug, unskip test |
| `refactoring` | ♻️ | Behavior-neutral refactoring via refactoring MCP |
| `documentation` | 📝 | Only `.md` files or docstring/comment changes |
| `lint_fix` | 🧹 | Single lint error fixed in single file |
| `config` | ⚙️ | Only config files changed |
| `test_only` | 🧪 | Adding tests to existing code (one test per commit) |
| `performance` | 🚀 | Optimization changes, tests must pass |

______________________________________________________________________

## Verification Rules

Each step type has specific verification rules enforced before commit creation.

### TDD Red (`tdd_red`)

- Only test files in `changed_files`
- `git diff --name-only` matches exactly `result.changed_files`
- Test must fail when run (without skip)
- Test is marked with `@pytest.mark.skip(reason="TDD red: awaiting implementation")`

### TDD Green (`tdd_green`)

- Only implementation files in `changed_files`
- No test file changes allowed
- Test must pass when run
- Skip decorator has been removed

### TDD Refactor (`tdd_refactor`)

- Only implementation files changed
- All tests still pass
- No new functionality (verified via refactoring MCP checksum)

### Bug Red (`bug_red`)

- Same rules as `tdd_red`
- Test proves the bug exists

### Bug Green (`bug_green`)

- Same rules as `tdd_green`
- Bug is fixed, test passes

### Refactoring (`refactoring`)

- Uses refactoring MCP for changes
- Verify via checksum/sentinel from refactoring MCP
- Tests must pass
- No test file changes

**Refactoring MCP Integration:**

The refactoring MCP is a Python library that can be called directly (not just as a tool).

```python
# Command calls MCP directly
mcp_result = refactoring_mcp.apply(
    refactoring_type="rename",  # or "extract_method", "inline", etc.
    target="old_name",
    new_name="new_name",
    # ... other parameters depend on refactoring type
)

# mcp_result contains:
# - changed_files: list[Path]
# - refactoring_type: str
# - metadata: dict (type-specific details)
# - checksum: str (proves behavior preservation)

# Verification calls back to MCP
refactoring_mcp.verify_checksum(mcp_result.checksum)  # raises if invalid
```

The checksum is a sentinel value that proves the refactoring was behavior-preserving. The MCP generates it during the refactoring and can verify it afterward.

### Documentation (`documentation`)

- Only `.md` files changed, OR
- Only docstring/comment changes in code files (verified via git diff line parsing)

**Documentation Change Detection Algorithm:**

For `.md` files, validation is trivial - any change is valid.

For Python files, the algorithm classifies each changed line:

```
1. Run `git diff --unified=0` to get only changed lines (no context)

2. For each changed file:
   a. If file is `.md` → always valid documentation change
   b. If file is `.py` → analyze changed lines using algorithm below

3. For Python files, classify each added/removed line:
   - COMMENT: line stripped starts with `#`
   - DOCSTRING: line is inside `"""..."""` or `'''...'''`
   - WHITESPACE: line is empty or whitespace-only
   - CODE: anything else

4. For docstring detection:
   - Track state: inside_docstring = False
   - On line containing `"""` or `'''`:
     - If line has opening and closing quotes → single-line docstring
     - Otherwise toggle inside_docstring state
   - Lines while inside_docstring = True are DOCSTRING

5. Verification:
   - PASSES if ALL changed lines are COMMENT, DOCSTRING, or WHITESPACE
   - FAILS if ANY changed line is CODE
```

**Edge cases to handle:**

- Single-line docstrings: `"""This is a docstring"""`
- Docstrings with quotes inside them
- f-strings containing `#` (these are CODE, not COMMENT)
- Raw strings with `#` inside

### Lint Fix (`lint_fix`)

- Single file changed
- Lint passes on that file
- Commit message format: "lint fix \[error code\] in \[filename\]"

### Config (`config`)

- Only config files changed (`.yaml`, `.toml`, `.json`, `.ini`, etc.)

### Test Only (`test_only`)

- Only test files changed
- One test per commit
- Tests pass

### Performance (`performance`)

- Tests must pass
- (Additional performance verification TBD)

______________________________________________________________________

## Directory Structure

Step-specific code is grouped by step type. Underscore in the step type identifier maps to directory separator.

```
src/jiro/
├── commands/
│   └── base.py                         # Command ABC
├── results/
│   └── base.py                         # Result base dataclass
├── verifications/
│   └── base.py                         # Verification ABC
├── commits/
│   └── base.py                         # Commit ABC
│
└── steps/
    ├── tdd/
    │   ├── red/
    │   │   ├── __init__.py
    │   │   ├── tdd_red_command.py
    │   │   ├── tdd_red_result.py
    │   │   ├── tdd_red_verify.py
    │   │   ├── tdd_red_commit.py
    │   │   ├── prompt.md.j2            # Optional subagent prompt
    │   │   └── commit_message.md.j2    # Commit message template
    │   ├── green/
    │   │   └── ... (same pattern)
    │   └── refactor/
    │       └── ... (same pattern)
    │
    ├── bug/
    │   ├── red/
    │   │   └── ... (same pattern)
    │   └── green/
    │       └── ... (same pattern)
    │
    ├── refactoring/
    │   ├── __init__.py
    │   ├── refactoring_command.py
    │   ├── refactoring_result.py
    │   ├── refactoring_verify.py
    │   ├── refactoring_commit.py
    │   └── commit_message.md.j2
    │
    ├── documentation/
    │   └── ... (same pattern)
    │
    ├── lint/
    │   └── fix/
    │       └── ... (same pattern)
    │
    ├── config/
    │   └── ... (same pattern)
    │
    ├── test/
    │   └── only/
    │       └── ... (same pattern)
    │
    └── performance/
        └── ... (same pattern)
```

### Test Structure

Tests mirror the source structure:

```
tests/unit/
├── commands/
│   └── test_base.py
├── results/
│   └── test_base.py
├── verifications/
│   └── test_base.py
├── commits/
│   └── test_base.py
└── steps/
    ├── tdd/
    │   ├── red/
    │   │   ├── test_tdd_red_command.py
    │   │   ├── test_tdd_red_result.py
    │   │   ├── test_tdd_red_verify.py
    │   │   └── test_tdd_red_commit.py
    │   └── ... (same pattern for green, refactor)
    └── ... (same pattern for all step types)

tests/integration/
└── test_tdd_workflow.py                # Full TDD red→green→refactor flow
```

______________________________________________________________________

## Class Interfaces

### Base Classes

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json


class Command(ABC):
    """Base class for step commands that spawn subagents."""

    tools: list[type]  # Tools available to subagent
    output_schema: type  # Pydantic model for structured output

    @abstractmethod
    def execute(self, *, step: PlanStep, task: Task) -> Result:
        """Execute the command, spawning a subagent to do the work."""
        ...


@dataclass
class Result:
    """Base result dataclass with serialization methods."""

    changed_files: list[Path]  # Files modified by this step

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_json(self) -> str:
        return json.dumps(self.as_dict(), default=str)

    def as_toon(self) -> str:
        """TOON format for LLM token efficiency."""
        ...

    def as_html(self) -> str:
        """HTML rendering."""
        ...

    def __str__(self) -> str:
        """Plain text rendering."""
        ...


class Verification(ABC):
    """Base class for step verification."""

    @abstractmethod
    def verify(self, *, result: Result) -> VerificationResult:
        """Verify the work. Raises exception on failure."""
        ...


@dataclass
class VerificationResult:
    """Result of verification."""

    success: bool
    verification_command: str
    verification_output: str
    verification_time: float


class Commit(ABC):
    """Base class for creating strongly typed commits."""

    @abstractmethod
    def create(
        self,
        *,
        result: Result,
        verification: VerificationResult,
        e2e_time: float,
    ) -> CommitResult:
        """Store metadata in DB, render template, create git commit."""
        ...


@dataclass
class CommitResult:
    """Result of commit creation."""

    sha: str
    message: str
```

### ExecutionStep (Factory Pattern)

```python
class ExecutionStep:
    """Orchestrates Command → Verification → Commit for a step type."""

    def __init__(
        self,
        step_type: StepType,
        session: Session,
        db: Database,
    ):
        self.step_type = step_type
        self.session = session
        self.db = db

    @classmethod
    def for_type(
        cls,
        step_type: StepType,
        **context,
    ) -> "ExecutionStep":
        """Factory method to create ExecutionStep for a step type."""
        return cls(step_type, **context)

    @property
    def command(self) -> Command:
        return discover_command(self.step_type)

    @property
    def verify(self) -> Verification:
        return discover_verification(self.step_type)

    @property
    def commit(self) -> Commit:
        return discover_commit(self.step_type)

    def execute(self, plan_step: PlanStep, task: Task) -> CommitResult:
        """Execute the full step: command → verify → commit."""
        start = time.monotonic()

        # 1. Execute (spawns subagent, does work)
        result = self.command.execute(step=plan_step, task=task)

        # 2. Verify (raises exception on failure → HALT)
        verification = self.verify.verify(result=result)

        # 3. Commit (stores in DB, renders template, git commit)
        commit_result = self.commit.create(
            result=result,
            verification=verification,
            e2e_time=time.monotonic() - start,
        )

        return commit_result
```

### Discovery Convention

The discovery convention maps step type identifiers to module paths and class names.

**Algorithm:**

1. Take step_type string (e.g., `"tdd_red"`, `"documentation"`)
1. Replace underscores with dots: `"tdd_red"` → `"tdd.red"`
1. Build module path: `f"jiro.steps.{converted}"`
1. Build class name: PascalCase(step_type) + suffix

**Complete Mapping:**

| step_type | module_path | Command class |
|-----------|-------------|---------------|
| `tdd_red` | `jiro.steps.tdd.red` | `TddRedCommand` |
| `tdd_green` | `jiro.steps.tdd.green` | `TddGreenCommand` |
| `tdd_refactor` | `jiro.steps.tdd.refactor` | `TddRefactorCommand` |
| `bug_red` | `jiro.steps.bug.red` | `BugRedCommand` |
| `bug_green` | `jiro.steps.bug.green` | `BugGreenCommand` |
| `lint_fix` | `jiro.steps.lint.fix` | `LintFixCommand` |
| `test_only` | `jiro.steps.test.only` | `TestOnlyCommand` |
| `documentation` | `jiro.steps.documentation` | `DocumentationCommand` |
| `refactoring` | `jiro.steps.refactoring` | `RefactoringCommand` |
| `config` | `jiro.steps.config` | `ConfigCommand` |
| `performance` | `jiro.steps.performance` | `PerformanceCommand` |

**Implementation:**

```python
def get_module_path(step_type: str) -> str:
    """Convert step type to module path.

    Underscore always becomes dot (directory separator).

    Examples:
        tdd_red -> jiro.steps.tdd.red
        lint_fix -> jiro.steps.lint.fix
        documentation -> jiro.steps.documentation
    """
    return f"jiro.steps.{step_type.replace('_', '.')}"


def to_pascal_case(step_type: str) -> str:
    """Convert step_type to PascalCase.

    Examples:
        tdd_red -> TddRed
        lint_fix -> LintFix
        documentation -> Documentation
    """
    return "".join(word.capitalize() for word in step_type.split("_"))


def discover_command(step_type: StepType) -> Command:
    """Discover and instantiate Command class for step type."""
    module_path = get_module_path(step_type.value)
    class_name = f"{to_pascal_case(step_type.value)}Command"

    module = importlib.import_module(f"{module_path}.{step_type.value}_command")
    command_cls = getattr(module, class_name)
    return command_cls()


def discover_verification(step_type: StepType) -> Verification:
    """Discover and instantiate Verification class for step type."""
    module_path = get_module_path(step_type.value)
    class_name = f"{to_pascal_case(step_type.value)}Verify"

    module = importlib.import_module(f"{module_path}.{step_type.value}_verify")
    verify_cls = getattr(module, class_name)
    return verify_cls()


def discover_commit(step_type: StepType) -> Commit:
    """Discover and instantiate Commit class for step type."""
    module_path = get_module_path(step_type.value)
    class_name = f"{to_pascal_case(step_type.value)}Commit"

    module = importlib.import_module(f"{module_path}.{step_type.value}_commit")
    commit_cls = getattr(module, class_name)
    return commit_cls()
```

______________________________________________________________________

## Result Dataclasses

Each step type has a specific Result dataclass.

### Example: TddRedResult

```python
@dataclass
class TddRedResult(Result):
    """Result from TDD red step."""

    # From base
    changed_files: list[Path]

    # Step-specific
    test_file: Path
    test_name: str  # e.g., "test_login_validates_email"
    test_specifier: str  # e.g., "tests/test_auth.py::test_login_validates_email"
    test_output: str  # Output showing test failure

    # Subagent metrics
    subagent_type: str
    subagent_prompt: str
    tokens_in: int
    tokens_out: int
    subagent_time: float
```

### Example: TddGreenResult

```python
@dataclass
class TddGreenResult(Result):
    """Result from TDD green step."""

    changed_files: list[Path]

    # Step-specific
    test_specifier: str  # The test that now passes
    test_output: str  # Output showing test passing
    implementation_files: list[Path]

    # Subagent metrics
    subagent_type: str
    subagent_prompt: str
    tokens_in: int
    tokens_out: int
    subagent_time: float
```

______________________________________________________________________

## Database Schema

Extend the `commits` table with JSON metadata:

```sql
CREATE TABLE commits (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    session_id TEXT REFERENCES sessions(id),
    sha TEXT,                   -- NULL until git commit succeeds
    commit_type TEXT NOT NULL,
    status TEXT NOT NULL,       -- 'pending' or 'committed'
    metadata JSON NOT NULL,     -- Flexible type-specific data
    message TEXT NOT NULL,      -- Rendered commit message (immutable)
    created_at TIMESTAMP NOT NULL
);
```

The `metadata` column stores all Result and VerificationResult data as JSON, enabling:

- Flexible schema per commit type
- No migrations when adding new fields
- Full audit trail of what happened

### Transaction Handling

The `status` column handles the DB/git transaction boundary:

1. **Write to DB** with `status='pending'`, `sha=NULL`
1. **Attempt git commit**
1. **On success:** Update to `status='committed'`, set `sha`
1. **On failure:** Record remains with `status='pending'` for debugging

Orphaned `pending` records indicate failed git operations and can be cleaned up or investigated.

______________________________________________________________________

## Commit Message Templates

Templates are Jinja2 files that live with the step type, but can be overridden via project assets.

### Resolution Order

1. `~/.jiro-dreams-of-code/$PROJECT/assets/templates/commit/tdd_red.md.j2` (project override)
1. `src/jiro/steps/tdd/red/commit_message.md.j2` (package default)

### Example: TDD Red Template

```jinja2
🔴 Add failing test for {{ test_name }}

Task: {{ task_id }} - {{ task_title }}
Type: tdd_red
Test: {{ test_specifier }}

Verification: {{ verification_command }}
{{ verification_output | indent(2) }}
Verification time: {{ verification_time | format_duration }}

Subagent: {{ subagent_type }}
Tokens: {{ tokens_in }} → {{ tokens_out }}
Subagent time: {{ subagent_time | format_duration }}
E2E time: {{ e2e_time | format_duration }}
```

### Template Variables

**Shared (all commit types):**

- `task_id`, `task_title`
- `commit_type`
- `e2e_time`
- `subagent_type`, `subagent_prompt`, `tokens_in`, `tokens_out`, `subagent_time`
- `verification_command`, `verification_output`, `verification_time`

**Type-specific (examples):**

- TDD Red: `test_name`, `test_file`, `test_specifier`, `test_output`
- TDD Green: `test_specifier`, `implementation_files`
- Lint Fix: `error_code`, `filename`

______________________________________________________________________

## Subagent Integration

Commands spawn subagents using the Claude Agent SDK with:

1. Defined tools per command type
1. Pydantic schema for structured output
1. Rendered prompt template

**Implementation Note:** When implementing Command classes that spawn subagents, use the `agent-sdk-builder` skill for guidance on Claude Agent SDK patterns, particularly for structured output handling.

### Example: TddRedCommand

```python
class TddRedCommand(Command):
    tools = [Read, Write, Bash]  # Bash for running tests
    output_schema = TddRedResult

    def execute(self, *, step: PlanStep, task: Task) -> TddRedResult:
        # Load and render prompt template
        prompt = self.render_prompt(step=step, task=task)

        # Spawn subagent with structured output
        result = self.run_subagent(
            prompt=prompt,
            tools=self.tools,
            output_schema=self.output_schema,
        )

        return result  # Already typed as TddRedResult
```

### Subagent Responsibilities (TDD Red)

1. Create the failing test
1. Run the test to verify it fails
1. If test doesn't fail, rework until it fails correctly
1. Mark test as skipped: `@pytest.mark.skip(reason="TDD red: awaiting implementation")`
1. Return structured result with test specifier and changed files

______________________________________________________________________

## Error Handling

**On verification failure:** Raise `VerificationError` exception (see Core Type Definitions).

This causes immediate HALT - the executor stops, records the failure, and exits with code 5. Human intervention is required to diagnose and fix the issue.

Future enhancement: Automatic retry with feedback for certain failure types.

______________________________________________________________________

## Logging

Logging uses moderate detail with dual output formats:

**Detail Level:** Log each phase with timing

- Step start/end
- Command start/end with subagent metrics
- Verification start/end with result
- Commit start/end with SHA

**Output Formats:**

- **Console:** Human-readable, pretty-printed
- **File:** Structured JSON for aggregation and analysis

**Example log entries:**

```
# Console (human-readable)
[12:34:56] Starting step: tdd_red
[12:34:57] Command: spawning subagent (haiku)
[12:35:12] Command: complete (15.2s, 1,234 tokens in, 567 out)
[12:35:12] Verification: checking changed files
[12:35:13] Verification: passed (0.8s)
[12:35:13] Commit: creating with message "🔴 Add failing test for login validation"
[12:35:14] Commit: success (sha: abc1234)
[12:35:14] Step complete: tdd_red (18.1s total)

# File (JSON)
{"timestamp": "2025-01-15T12:35:14Z", "event": "step_complete", "step_type": "tdd_red", "duration_s": 18.1, "sha": "abc1234", ...}
```

______________________________________________________________________

## Git Operations

The Commit class handles all git operations:

1. **Stage files:** `git add` only the files in `result.changed_files`
1. **Verify staging:** Assert `git diff --cached --name-only` matches `result.changed_files`
1. **Create commit:** `git commit` with rendered message
1. **Return SHA:** Extract and return the commit SHA

### Verification Pre-check

Before staging, verification confirms:

- `git diff --name-only` (unstaged changes) matches exactly `result.changed_files`
- No unexpected files were modified by the subagent

______________________________________________________________________

## Task Definition vs Result

**Task definition** (from issue tracker) provides intent and constraints:

- May be specific: "Implement login validation for `jiro.auth.login` module"
- May be open-ended: "Add input validation to the auth system"

**Result** (from subagent) captures what actually happened:

- Always specific: exact files, test names, line counts
- Subagent has authority to make tactical decisions (filenames, test names)

The planning agent provides the "what" and "why"; the execution subagent determines the "how" and reports back.

______________________________________________________________________

## Implementation Order

Suggested order for implementing step types:

1. **Base classes** - Command, Result, Verification, Commit ABCs
1. **ExecutionStep** - Factory and orchestration
1. **Discovery** - Convention-based class loading
1. **TDD Red** - Establishes the full pattern
1. **TDD Green** - Completes TDD pair
1. **TDD Refactor** - Requires refactoring MCP integration
1. **Documentation** - Simple, validates the pattern
1. **Remaining types** - lint_fix, config, test_only, performance, bug_red, bug_green, refactoring
