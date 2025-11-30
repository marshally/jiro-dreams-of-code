# Project Instructions for Claude

## Pre-commit Hooks

**CRITICAL**: NEVER skip or bypass pre-commit hooks.

### Rules

1. **NEVER** use `SKIP=<hook-name>` to bypass any hook
1. **NEVER** use `--no-verify` with git commit
1. **NEVER** disable hooks temporarily "just this once"

The hooks exist to protect code quality. If a hook fails:

- **Fix the underlying issue** - don't bypass the hook
- If a hook modifies files (formatting, linting), re-add the files and retry
- If you don't understand why a hook failed, investigate before proceeding

### Why This Matters

Hooks enforce:

- Code formatting consistency
- Linting rules
- Test passing
- Commit isolation rules
- Security checks

Bypassing them creates technical debt and can introduce bugs or security issues.

______________________________________________________________________

## Beads Commit Isolation

**CRITICAL**: `.beads/` files must ALWAYS be committed separately from all other files.

### Rules

1. **NEVER** add `.beads/` files to the same commit as code, tests, docs, or any other files
1. **ALWAYS** commit in this order:
   - First: Commit your code/test changes (without .beads files)
   - Second: Commit .beads changes separately

### Correct Workflow

```bash
# Step 1: Stage and commit code changes only
git add src/path/to/file.py tests/path/to/test.py
git commit -m "feat: implement feature X"

# Step 2: Stage and commit beads changes separately
git add .beads/
git commit -m "chore(beads): update task status"
```

### What NOT to Do

```bash
# WRONG - Never mix beads with other files:
git add src/file.py .beads/issues.jsonl
git commit -m "feat: implement feature"
```

### Why This Matters

- Beads tracks issue state in git
- Mixing beads commits with code commits pollutes git history
- Makes it impossible to cleanly revert code changes
- The pre-commit hook exists specifically to enforce this separation

### If Pre-commit Hook Fails

If you see "ERROR - .beads/ files must be committed separately":

1. Run `git reset HEAD .beads/` to unstage beads files
1. Commit your code changes
1. Then `git add .beads/ && git commit -m "chore(beads): ..."`
