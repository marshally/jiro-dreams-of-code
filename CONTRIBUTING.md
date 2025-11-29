# Contributing

## Getting Started

```bash
# Clone the repository
git clone https://github.com/marshally/jiro-dreams-of-code.git
cd jiro-dreams-of-code

# Install dependencies and create virtual environment
make setup

# Install pre-commit and pre-push hooks
make hooks
```

## Development Workflow

1. **Create a feature branch** - Never commit directly to `main`
1. **Make small, discrete commits** - See [AGENTS.md](AGENTS.md) for commit philosophy
1. **Push and create a PR** - CI must pass before merge
1. **Update CHANGELOG.md** - Required before merging

## Pre-commit Hooks

Hooks run automatically to ensure code quality.

### On Every Commit

| Hook | Purpose |
|------|---------|
| `no-commit-to-main` | Prevents direct commits to main branch |
| `isolate-beads` | Ensures .beads/ files are committed separately |
| `trailing-whitespace` | Removes trailing whitespace |
| `end-of-file-fixer` | Ensures files end with newline |
| `check-yaml` | Validates YAML syntax |
| `check-toml` | Validates TOML syntax |
| `ruff` | Python linting (no auto-fix) |
| `ruff-format` | Python formatting check (no auto-fix) |
| `mdformat` | Markdown formatting |
| `pytest-unit` | Runs unit tests |

### On Every Push

| Hook | Purpose |
|------|---------|
| `mypy` | Static type checking |
| `pytest-full` | Runs unit + integration tests |

## CI Pipeline

Three jobs run in parallel on every PR:

| Job | Checks |
|-----|--------|
| `lint` | `ruff check`, `ruff format --check` |
| `typecheck` | `mypy src/` |
| `test` | `pytest` with coverage upload to Codecov |

## Makefile Targets

```bash
make setup     # Create venv and install dependencies
make hooks     # Install pre-commit and pre-push hooks
make lint      # Run ruff linter
make format    # Run ruff formatter
make typecheck # Run mypy
make test      # Run pytest
```

## Troubleshooting

### Pre-commit hooks fail with "No such file or directory"

Ensure your virtual environment is set up:

```bash
make setup
```

### "Cannot commit directly to main branch"

Create a feature branch first:

```bash
git checkout -b my-feature
```

### ".beads/ files must be committed separately"

Commit your code changes first, then commit .beads/ changes in a separate commit:

```bash
git add src/
git commit -m "Add feature"

git add .beads/
git commit -m "beads: update issue status"
```
