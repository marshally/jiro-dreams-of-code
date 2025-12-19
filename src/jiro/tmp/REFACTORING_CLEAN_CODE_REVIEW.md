# Clean Code Review: src/jiro

## Summary

The jiro codebase demonstrates solid architectural patterns with good use of protocols, dataclasses, and separation of concerns. However, there are significant Clean Code violations in function size, code duplication, and error handling patterns that reduce maintainability and testability. The most pressing issues are excessive function lengths in orchestration code and pervasive code duplication in preflight/postflight checks.

______________________________________________________________________

## Critical Issues (Must Fix)

### 1. Excessive Code Duplication in Preflight/Postflight Checks

**Location:** `core/session.py:226-500` (`run_preflight`, `run_postflight`)

**Problem:** The `run_preflight` and `run_postflight` functions contain nearly identical patterns repeated 5+ times each. Each check follows the same structure:

```python
try:
    result = check_function(config)
    checks["name"] = CheckResult(
        name="name",
        passed=result,
        error=None if result else "Error message",
    )
    if not result:
        errors.append("name: Error message")
except Exception as e:
    checks["name"] = CheckResult(
        name="name",
        passed=False,
        error=str(e),
    )
    errors.append(f"name: {str(e)}")
```

**Clean Code Principle:** DRY (Don't Repeat Yourself) - "Every piece of knowledge must have a single, unambiguous, authoritative representation within a system."

**Recommendation:** Extract a `run_check` helper function:

```python
def run_check(
    name: str,
    check_fn: Callable[[], bool],
    error_message: str,
    checks: dict[str, CheckResult],
    errors: list[str],
) -> None:
    """Run a single check and record the result."""
    try:
        passed = check_fn()
        checks[name] = CheckResult(
            name=name, passed=passed, error=None if passed else error_message
        )
        if not passed:
            errors.append(f"{name}: {error_message}")
    except Exception as e:
        checks[name] = CheckResult(name=name, passed=False, error=str(e))
        errors.append(f"{name}: {str(e)}")
```

### 2. Duplicate Test/Lint Runner Functions

**Location:** `core/executor.py:101-234` and `core/executor.py:352-485`

**Problem:** `run_relevant_tests` and `run_relevant_tests_post` are nearly identical functions (80% code duplication). Same for `run_relevant_lint` and `run_relevant_lint_post`.

**Clean Code Principle:** DRY - Functions should have one, and only one, reason to exist.

**Recommendation:** Consolidate into single functions with optional `phase` parameter for logging differentiation:

```python
def run_relevant_tests(
    task: Task, config: Config, phase: Literal["preflight", "postflight"] = "preflight"
) -> bool:
    """Run relevant tests for a task in either preflight or postflight phase."""
```

### 3. Functions Too Long - SessionOrchestrator.run()

**Location:** `core/session.py:546-704` (158 lines)

**Problem:** The `run` method is too long and handles multiple responsibilities: session creation, preflight, task execution, postflight, error handling, and status updates.

**Clean Code Principle:** "The first rule of functions is that they should be small. The second rule is that they should be smaller than that."

**Recommendation:** Extract each phase into separate private methods:

```python
def run(self, epic_id: str | None = None) -> SessionResult:
    session = self._create_session(epic_id)
    try:
        if not self._run_preflight_phase(session):
            return self._fail_session(session, "Preflight failed")

        tasks_result = self._execute_tasks_phase(session, epic_id)
        if tasks_result.halted:
            return tasks_result

        if not self._run_postflight_phase(session):
            return self._fail_session(session, "Postflight failed")

        return self._complete_session(session, tasks_result)
    except Exception as e:
        return self._handle_unexpected_error(session, e)
```

### 4. Functions Too Long - execute_task()

**Location:** `core/session.py:760-891` (131 lines)

**Problem:** The `execute_task` method in SessionOrchestrator is too long and has multiple levels of nested try-except blocks.

**Clean Code Principle:** Functions should do one thing. "If a function does only those steps that are one level below the stated name of the function, then the function is doing one thing."

**Recommendation:** Extract into smaller, focused methods:

- `_create_task_execution_record()`
- `_initialize_agents()`
- `_run_task_with_executor()`
- `_handle_postflight_result()`

______________________________________________________________________

## Important Issues (Should Fix)

### 5. Bare Exception Catching Throughout

**Location:** Multiple files: `session.py`, `executor.py`, `beads.py`, `client.py`

**Problem:** Many functions catch bare `Exception` which can mask programming errors and make debugging difficult:

```python
except Exception:
    return False
```

**Clean Code Principle:** "Catch specific exceptions, not just Exception."

**Recommendation:** Catch specific exceptions where possible:

```python
except subprocess.CalledProcessError:
    return False
except FileNotFoundError:
    logger.warning("File not found", path=path)
    return False
```

### 6. Module-Level Function get_tracker() Creates Hidden Dependency

**Location:** `core/executor.py:24-38`

**Problem:** The `get_tracker()` function creates a hidden dependency by importing and instantiating BeadsTracker inline. This violates dependency injection principles and makes testing difficult.

**Clean Code Principle:** "Avoid hidden dependencies. Make dependencies explicit."

**Recommendation:** Inject the tracker as a parameter or use a factory pattern:

```python
class TaskExecutor:
    def __init__(
        self,
        config: Config,
        planning_agent: PlanningAgent,
        review_agent: ReviewAgent,
        tracker: IssueTracker,  # Inject explicitly
    ):
```

### 7. Type Annotation Using Any

**Location:** `core/session.py:747-758`

**Problem:** `get_tasks` returns `list[Any]` and `execute_task` accepts `task: Any`, losing type safety:

```python
def get_tasks(self, epic_id: str | None = None) -> list[Any]:
def execute_task(self, task: Any, session_id: str) -> None:
```

**Clean Code Principle:** Strong typing improves code clarity and catches errors at compile time.

**Recommendation:** Use proper type hints:

```python
from jiro.trackers.interface import Task

def get_tasks(self, epic_id: str | None = None) -> list[Task]:
def execute_task(self, task: Task, session_id: str) -> None:
```

### 8. Redundant Boolean Return

**Location:** `core/session.py:127`

**Problem:** Unnecessary explicit boolean conversion:

```python
return bool(current_branch == target_branch)
```

**Clean Code Principle:** "The best code is no code at all." Avoid unnecessary operations.

**Recommendation:** Simply return the comparison result:

```python
return current_branch == target_branch
```

### 9. Similar Result Dataclasses Should Share Base Class

**Location:** `core/session.py:48-76` (PreflightResult, PostflightResult) and `core/executor.py:249-277`

**Problem:** There are two pairs of nearly identical PreflightResult/PostflightResult dataclasses (one in session.py, one in executor.py) with similar fields.

**Clean Code Principle:** "If you find yourself making the same changes in several places, you have duplication."

**Recommendation:** Create a shared base class or consolidate:

```python
@dataclass
class CheckPhaseResult:
    """Base result for preflight/postflight phases."""

    passed: bool
    checks: dict[str, CheckResult] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
```

### 10. Hardcoded Magic Values

**Location:** Multiple locations

**Problem:** Hardcoded values like timeouts, paths, and defaults:

- `core/executor.py:135, 203, 386, 454`: `timeout=60`
- `core/executor.py:55`: `tests_dir = Path("tests/unit")`
- `core/executor.py:85`: `src_dir = Path("src/jiro")`

**Clean Code Principle:** "Replace magic numbers with named constants."

**Recommendation:** Extract to configuration or module constants:

```python
DEFAULT_COMMAND_TIMEOUT = 60  # seconds
DEFAULT_TEST_DIR = Path("tests/unit")
DEFAULT_SOURCE_DIR = Path("src/jiro")
```

______________________________________________________________________

## Minor Issues (Consider Fixing)

### 11. Inconsistent Exception Variable Naming

**Location:** Throughout codebase

**Problem:** Exception variables alternate between `e`, `error`, and unnamed:

```python
except Exception as e:
except Exception:
```

**Recommendation:** Standardize on `e` or `exc` consistently.

### 12. Long Import Lists

**Location:** `core/session.py:774-782`

**Problem:** Imports inside method bodies reduce readability and may indicate the method is doing too much:

```python
def execute_task(self, task: Any, session_id: str) -> None:
    import asyncio
    import uuid
    from datetime import datetime
    from jiro.agents.client import AgentClient

    ...
```

**Clean Code Principle:** "Imports should be at the top of the file."

**Recommendation:** Move imports to module level or restructure to avoid circular imports.

### 13. Unused Logger Variable

**Location:** `core/executor.py:21`

**Problem:** Module-level logger is defined but some functions get their own logger:

```python
logger = structlog.get_logger()
# Later in run_preflight:
logger = structlog.get_logger()
```

**Recommendation:** Use the module-level logger consistently.

### 14. Inconsistent Method Organization in Classes

**Location:** `core/session.py` - SessionOrchestrator class

**Problem:** Public methods, private methods, and helper methods are interleaved without clear organization.

**Clean Code Principle:** "Organize code top to bottom in dependency order."

**Recommendation:** Order methods: public → helpers used by public → private implementation details.

### 15. Comments Stating the Obvious

**Location:** Various locations

**Problem:** Some comments merely restate what the code does:

```python
# Step 1: Create session record
session_id = str(uuid.uuid4().hex)
```

**Clean Code Principle:** "Don't use a comment when you can use a function or a variable."

**Recommendation:** Remove redundant comments or make code self-documenting.

______________________________________________________________________

## Strengths

1. **Good Use of Protocols:** The `IssueTracker` protocol in `trackers/interface.py` enables clean abstractions and pluggable backends.

1. **Comprehensive Docstrings:** Most functions have well-written docstrings with Args, Returns, and Raises sections.

1. **Structured Logging:** Consistent use of structlog with contextual information throughout.

1. **Dataclass Usage:** Effective use of dataclasses for DTOs like Task, CheckResult, AgentResult.

1. **Type Annotations:** Generally good type annotations throughout the codebase.

1. **Separation of Concerns:** Clear separation between CLI, core, agents, and trackers modules.

1. **TDD Sequence Enforcement:** The TddSequenceTracker shows thoughtful design for enforcing TDD discipline.

1. **Error Handling Strategy:** Consistent pattern of logging errors with context before raising/returning.

______________________________________________________________________

## Overall Assessment

**Code Quality Score:** Fair

**Maintainability:** Fair - Good architecture but hampered by duplication and long functions

**Readability:** Good - Clear naming and comprehensive documentation

______________________________________________________________________

## Priority Recommendations

1. **Extract repetitive check patterns** in session.py preflight/postflight (reduces ~200 lines of duplication)

1. **Consolidate duplicate test/lint runners** in executor.py (reduces ~300 lines of duplication)

1. **Split long orchestration methods** into smaller, focused functions (improves testability)

1. **Inject IssueTracker dependency** instead of hidden instantiation (improves testability)

1. **Extract magic values to constants/config** (improves maintainability)

______________________________________________________________________

## Refactoring Scope

### Files Requiring Changes:

- `core/session.py` - Major refactoring (preflight/postflight extraction, method splitting)
- `core/executor.py` - Major refactoring (consolidate duplicates, inject dependencies)
- `trackers/beads.py` - Minor (specific exception handling)
- `agents/client.py` - Minor (specific exception handling)
- `cli/execute.py` - No changes needed

### Estimated Impact:

- **Lines reduced:** ~400-500 through deduplication
- **New abstractions:** 2-3 helper functions/classes
- **Test coverage improvement:** Easier to test smaller functions
