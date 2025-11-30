# ADR-004: Strongly-Typed Commits with Two-Layer Validation

## Status

Accepted

## Context

Jiro enforces strict commit discipline to ensure every commit is reviewable, has a clear purpose, and follows the project's conventions. The spec defines multiple commit types (TDD Red, TDD Green, Documentation, Lint Fix, etc.), each with specific rules about what files can be changed and what the commit message must contain.

We need a mechanism to:

1. Ensure commits conform to their claimed type at creation time
1. Validate commits after the fact to catch semantic violations
1. Embed verification evidence (test results, lint output) in commits

## Decision

Implement a two-layer commit discipline system:

### Layer 1: Creation-Time Enforcement (Python Script)

A Python script creates "strongly typed" commits that are guaranteed to conform to type rules:

```python
def create_docs_commit(message: str, task_id: str, reason: str, ...) -> str:
    """Create a documentation-only commit. Raises if rules violated."""
    staged_files = get_staged_files()

    # Enforce: only docs files allowed
    for file in staged_files:
        if not is_docs_file(file):
            raise CommitRuleViolation(f"Non-docs file staged: {file}")

    # Render commit message from Jinja2 template
    commit_msg = render_template("docs.txt.j2", ...)

    # Create the commit
    return git_commit(commit_msg)
```

The script **refuses to create** a commit that violates its type's rules.

### Layer 2: Review-Time Validation (Python + LLM)

After commits are created, the review stage validates them:

**Deterministic checks (Python):**

- Files changed match claimed commit type
- Commit message follows template format
- Task reference is valid
- Verification command was run and results included

**LLM judgment checks:**

- Changes semantically match commit description
- No scope creep (changes beyond what was claimed)
- For refactoring: behavior is preserved

### Commit Message Template

Commit messages use Jinja2 templates with these variables:

| Variable | Description |
|----------|-------------|
| `message` | Imperative description |
| `task_id` | Task identifier |
| `task_title` | Task title |
| `commit_type` | Type (docs, tdd_red, etc.) |
| `reason` | Why this change is being made |
| `verification_command` | Command used to verify |
| `verification_results` | Output of verification |
| `time_taken` | Time spent |
| `tokens_before` / `tokens_after` | Context tracking |

## Consequences

### Positive

- **Impossible to violate at creation**: Script enforces rules before commit exists
- **Evidence embedded**: Verification results are part of the commit record
- **Reviewable**: Any human or agent can validate commits against their claimed type
- **Semantic validation**: LLM catches subtle violations deterministic checks miss
- **Audit trail**: Every commit has a clear type, reason, and verification

### Negative

- **Complexity**: Two layers of validation to implement and maintain
- **Rigidity**: May be frustrating for developers who want to "just commit"
- **LLM cost**: Review validation has LLM cost per commit
- **False positives**: LLM may flag valid commits as violations

### Mitigations

- Start with single commit type (docs) for steel thread
- LLM review only runs if deterministic checks pass
- Human can override review decisions when halted

## Alternatives Considered

1. **Git hooks only**: Pre-commit hooks can enforce rules but can't embed verification results or do semantic analysis
1. **LLM-only validation**: No deterministic layer; more expensive and less reliable
1. **Post-hoc review only**: Allow any commit, review later; violates "fail fast" principle
1. **No enforcement**: Trust agents to follow rules; too risky for disciplined commits
