# Project Instructions for Claude

## Beads Commit Isolation

**CRITICAL**: `.beads/` files must ALWAYS be committed separately from all other files.

### Rules

1. **NEVER** add `.beads/` files to the same commit as code, tests, docs, or any other files
1. **NEVER** use `SKIP=isolate-beads` or any mechanism to bypass the pre-commit hook
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
# WRONG - Never do this:
git add src/file.py .beads/issues.jsonl
git commit -m "feat: implement feature"

# WRONG - Never bypass the hook:
SKIP=isolate-beads git commit -m "..."
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

Do NOT work around the hook with SKIP or --no-verify.
