# ADR-008: Convention-Based Step Type Discovery

## Status

Accepted

## Context

The strongly typed commit system (ADR-004) defines 11 step types, each requiring four classes:

- Command (spawns subagent to do work)
- Result (dataclass capturing what happened)
- Verification (validates the work)
- Commit (creates the git commit)

With 11 step types × 4 classes = 44 classes, we need a way to:

1. Organize these classes in a discoverable structure
1. Dynamically load the right classes at runtime
1. Make it easy to add new step types

## Decision

Use a convention-based discovery system where the step type identifier directly maps to the module path and class names.

### Convention

**Underscore = directory separator.** The step type string maps to the module path by replacing underscores with dots.

| Step Type | Module Path | Directory |
|-----------|-------------|-----------|
| `tdd_red` | `jiro.steps.tdd.red` | `src/jiro/steps/tdd/red/` |
| `tdd_green` | `jiro.steps.tdd.green` | `src/jiro/steps/tdd/green/` |
| `lint_fix` | `jiro.steps.lint.fix` | `src/jiro/steps/lint/fix/` |
| `documentation` | `jiro.steps.documentation` | `src/jiro/steps/documentation/` |

**Class naming:** PascalCase(step_type) + suffix

| Step Type | Command | Verification | Commit |
|-----------|---------|--------------|--------|
| `tdd_red` | `TddRedCommand` | `TddRedVerify` | `TddRedCommit` |
| `lint_fix` | `LintFixCommand` | `LintFixVerify` | `LintFixCommit` |

**File naming:** `{step_type}_{suffix}.py`

| Step Type | Command File | Verification File |
|-----------|--------------|-------------------|
| `tdd_red` | `tdd_red_command.py` | `tdd_red_verify.py` |

### Discovery Implementation

```python
def get_module_path(step_type: str) -> str:
    """Convert step type to module path."""
    return f"jiro.steps.{step_type.replace('_', '.')}"


def to_pascal_case(step_type: str) -> str:
    """Convert step_type to PascalCase."""
    return "".join(word.capitalize() for word in step_type.split("_"))


def discover_command(step_type: StepType) -> Command:
    module_path = get_module_path(step_type.value)
    class_name = f"{to_pascal_case(step_type.value)}Command"
    module = importlib.import_module(f"{module_path}.{step_type.value}_command")
    return getattr(module, class_name)()
```

### Directory Structure

```
src/jiro/steps/
├── tdd/
│   ├── red/
│   │   ├── tdd_red_command.py
│   │   ├── tdd_red_result.py
│   │   ├── tdd_red_verify.py
│   │   ├── tdd_red_commit.py
│   │   └── commit_message.md.j2
│   ├── green/
│   └── refactor/
├── bug/
│   ├── red/
│   └── green/
├── lint/
│   └── fix/
├── test/
│   └── only/
├── documentation/
├── refactoring/
├── config/
└── performance/
```

## Consequences

### Positive

- **Zero configuration**: No registry to maintain; adding a step type just means creating the directory and files
- **Predictable**: Given a step type, you know exactly where to find its code
- **Grep-friendly**: `git grep TddRedCommand` finds the right file
- **IDE-friendly**: Standard Python imports work; autocomplete works
- **Grouping**: Related steps (tdd_red, tdd_green, tdd_refactor) are siblings in the directory tree

### Negative

- **Rigid naming**: Must follow exact conventions; typos cause import errors
- **Some awkward mappings**: `lint_fix` becomes `lint/fix/` which reads oddly
- **No explicit registry**: Can't enumerate all step types without filesystem inspection

### Mitigations

- Unit tests verify all 11 step types are discoverable
- StepType enum is the canonical list of valid step types
- Clear error messages when discovery fails (e.g., "Cannot find TddRedCommand in jiro.steps.tdd.red")

## Alternatives Considered

### 1. Explicit Registry

```python
COMMANDS = {
    StepType.TDD_RED: TddRedCommand,
    StepType.TDD_GREEN: TddGreenCommand,
    # ... 9 more
}
```

**Rejected because:** Requires manual maintenance; easy to forget to register new step types; duplicates information already present in directory structure.

### 2. Flat Directory Structure

All step types at same level: `jiro.steps.tdd_red`, `jiro.steps.lint_fix`

**Rejected because:** Loses grouping of related steps (TDD phases, bug fix phases); 11 directories at same level is harder to navigate than hierarchical structure.

### 3. Single File Per Step Type

All four classes in one file: `jiro/steps/tdd_red.py`

**Rejected because:** Files become large; harder to test individual classes; less clear separation of concerns.

### 4. Dot Separator in Identifiers

Use `tdd.red` instead of `tdd_red` as the identifier.

**Rejected because:** Dots are problematic in database columns, URLs, and shell commands; underscores are safer in more contexts.
