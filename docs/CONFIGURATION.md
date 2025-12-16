# Configuration System

Jiro uses a multi-level configuration system that allows you to set defaults globally, customize them per project, and override them locally without committing configuration to version control.

## Overview

The configuration system supports three levels of precedence:

1. **Local config** (highest priority) - `.jiro-dreams-of-code.yaml` in your project root
1. **Project config** - `~/.jiro-dreams-of-code/$PROJECT_NAME/config.yaml`
1. **Global config** - `~/.jiro-dreams-of-code/config.yaml`
1. **Defaults** (lowest priority) - Built-in defaults in the application

Configuration values are merged hierarchically, meaning you only need to specify values you want to override at each level.

## Configuration File Locations

### Global Config

**Location**: `~/.jiro-dreams-of-code/config.yaml`

The global configuration applies to all jiro projects on your machine. Use this for settings that should be consistent across all projects.

Example:

```yaml
models:
  planning: claude-opus-4-20250514
  execution: claude-3-5-haiku-20241022
  review: claude-sonnet-4-20250514
commands:
  test: pytest
  lint: ruff check
  lint_fix: ruff check --fix
conventions:
  test_file_pattern: test_{name}.py
preflight:
  skip_if_recent_minutes: 60
```

### Project Config

**Location**: `~/.jiro-dreams-of-code/$PROJECT_NAME/config.yaml`

Project-specific configuration stored outside your repository. Useful for team-specific settings that shouldn't vary per developer or working context.

Example (for a project named `my-service`):

```yaml
# ~/.jiro-dreams-of-code/my-service/config.yaml
models:
  execution: claude-3-5-sonnet-20241022
commands:
  test: npm test
  lint: eslint .
```

### Local Config

**Location**: `.jiro-dreams-of-code.yaml` in your project root

Local configuration in your project directory. This is typically **not committed to version control** as it may contain personal preferences or sensitive values.

Example:

```yaml
models:
  planning: claude-opus-4-20250514
commands:
  lint: ruff check --exclude migrations
```

## Precedence Order

When jiro loads configuration, it applies values in this order (later entries override earlier ones):

1. **Defaults** - Built-in defaults
1. **Global** - `~/.jiro-dreams-of-code/config.yaml`
1. **Project** - `~/.jiro-dreams-of-code/$PROJECT_NAME/config.yaml`
1. **Local** - `./.jiro-dreams-of-code.yaml`

For nested configuration sections, values are merged at the section level. You don't need to repeat values from lower-precedence configs.

### Example Precedence

**Global config** (`~/.jiro-dreams-of-code/config.yaml`):

```yaml
models:
  planning: claude-opus-4-20250514
  execution: claude-3-5-haiku-20241022
commands:
  test: pytest
```

**Project config** (`~/.jiro-dreams-of-code/my-service/config.yaml`):

```yaml
models:
  execution: claude-3-5-sonnet-20241022
```

**Local config** (`.jiro-dreams-of-code.yaml`):

```yaml
commands:
  test: npm test
```

**Effective configuration**:

```yaml
models:
  planning: claude-opus-4-20250514          # from global
  execution: claude-3-5-sonnet-20241022     # from project (overrides global)
commands:
  test: npm test                            # from local (overrides global)
```

## Merge Behavior

Configuration merging is **deep and hierarchical**. Each level merges its values into the result from lower-precedence levels:

- Primitive values (strings, numbers) are replaced entirely
- Nested objects (dictionaries) are merged recursively
- Missing values at higher precedence levels don't erase lower-level values

### Example: Nested Merge

**Global** defines two models:

```yaml
models:
  planning: claude-opus-4-20250514
  execution: claude-3-5-haiku-20241022
```

**Local** only overrides execution:

```yaml
models:
  execution: claude-opus-4-20250514
```

**Result**: Both `planning` and `execution` values are present, with `execution` from local overriding global.

## Configuration Sections

### `models` - AI Model Selection

Controls which Claude models are used for different tasks.

| Setting | Purpose | Default |
|---------|---------|---------|
| `models.planning` | Model for generating specifications and task plans | `claude-opus-4-20250514` |
| `models.execution` | Model for agent task execution | `claude-3-5-haiku-20241022` |
| `models.review` | Model for code review and quality checks | `claude-sonnet-4-20250514` |

### `commands` - Tool Integration

Commands executed during various phases of task execution.

| Setting | Purpose | Default |
|---------|---------|---------|
| `commands.test` | Test runner command | `pytest` |
| `commands.lint` | Linting command (read-only) | `ruff check` |
| `commands.lint_fix` | Linting command with fixes | `ruff check --fix` |

### `conventions` - Project Conventions

Naming patterns and conventions for your project.

| Setting | Purpose | Default |
|---------|---------|---------|
| `conventions.test_file_pattern` | Pattern for test file discovery (e.g., `test_{name}.py`) | `test_{name}.py` |

### `preflight` - Optimization Settings

Settings for session preflight and optimization.

| Setting | Purpose | Default |
|---------|---------|---------|
| `preflight.skip_if_recent_minutes` | Skip expensive checks if preflight passed within N minutes | `60` |

## Common Configuration Scenarios

### Scenario 1: Different Models Per Project

**Use Case**: You want to use fast execution model globally, but a specific project needs better quality.

**Global config** (`~/.jiro-dreams-of-code/config.yaml`):

```yaml
models:
  execution: claude-3-5-haiku-20241022  # Fast, economical
```

**Project config** (`~/.jiro-dreams-of-code/my-critical-service/config.yaml`):

```yaml
models:
  execution: claude-opus-4-20250514  # Better quality for critical work
```

### Scenario 2: Team Standards with Personal Overrides

**Use Case**: Your team standardizes on certain commands, but you want different settings locally.

**Project config** (`~/.jiro-dreams-of-code/web-team/config.yaml`):

```yaml
commands:
  test: npm test
  lint: eslint src/
  lint_fix: eslint src/ --fix
```

**Local config** (`.jiro-dreams-of-code.yaml`):

```yaml
commands:
  # Exclude certain paths during personal development
  lint: eslint src/ --ignore-path .eslintignore.local
```

### Scenario 3: Conditional Behavior Based on Environment

**Use Case**: Different execution model for CI/CD vs local development.

**Global config** (`~/.jiro-dreams-of-code/config.yaml`):

```yaml
models:
  execution: claude-3-5-sonnet-20241022
```

**Local config** (`.jiro-dreams-of-code.yaml` - development machine):

```yaml
models:
  execution: claude-3-5-haiku-20241022  # Faster iteration locally
```

### Scenario 4: Project-Specific Test Framework

**Use Case**: Your organization uses different testing frameworks across projects.

**Global config** (`~/.jiro-dreams-of-code/config.yaml`):

```yaml
commands:
  test: pytest
```

**Project config** (for Rust project):

```yaml
commands:
  test: cargo test
  lint: cargo clippy
  lint_fix: cargo clippy --fix
```

## Working with Configuration

### List Configuration

View all configuration values and their sources:

```bash
# Show effective configuration with sources
jiro config list

# Show as JSON
jiro config list --json

# Show only global config
jiro config list --global

# Show only project config
jiro config list --project

# Show only local config (current directory)
jiro config list --local
```

Example output:

```
Configuration
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Setting                 ┃ Value                      ┃ Source ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ models.planning         │ claude-opus-4-20250514     │ global │
│ models.execution        │ claude-3-5-sonnet-20241022 │ local  │
│ models.review           │ claude-sonnet-4-20250514   │ default│
│ commands.test           │ npm test                   │ project│
│ commands.lint           │ ruff check                 │ global │
│ commands.lint_fix       │ ruff check --fix           │ global │
│ conventions.test_file   │ test_{name}.py             │ default│
│ preflight.skip_minutes  │ 60                         │ global │
└─────────────────────────┴────────────────────────────┴────────┘
```

### Get Specific Value

Retrieve a single configuration value:

```bash
# Get value with source
jiro config get models.execution

# Get as JSON
jiro config get models.execution --json
```

Output:

```
Key: models.execution
Value: claude-3-5-sonnet-20241022
Source: local
```

### Set Configuration Values

Save configuration at a specific level:

```bash
# Set globally (affects all projects)
jiro config set models.planning claude-opus-4-20250514 --global

# Set at project scope (specific project)
jiro config set commands.test "npm test" --project

# Set locally (current project, not committed)
jiro config set commands.lint "eslint src/" --local

# Default: saves to project config
jiro config set models.execution claude-3-5-haiku-20241022
```

### Understanding Source Output

The `list` and `get` commands show where each value comes from:

| Source | Meaning |
|--------|---------|
| `default` | Built-in application default |
| `global` | From `~/.jiro-dreams-of-code/config.yaml` |
| `project` | From `~/.jiro-dreams-of-code/$PROJECT_NAME/config.yaml` |
| `local` | From `.jiro-dreams-of-code.yaml` in current directory |

## Configuration Best Practices

### Global Configuration

Use for settings that apply to **all your projects**:

- Preferred execution model across all work
- Standard test and lint commands that most projects use
- Default conventions for your development style

Example:

```yaml
# ~/.jiro-dreams-of-code/config.yaml
models:
  execution: claude-3-5-haiku-20241022

commands:
  test: pytest
  lint: ruff check
```

### Project Configuration

Use for **team standards** that are project-specific:

- Commands specific to the project's tech stack
- Models preferred for that specific project
- Project conventions that differ from global

Example:

```yaml
# ~/.jiro-dreams-of-code/web-team/config.yaml
commands:
  test: npm test
  lint: eslint src/
  lint_fix: eslint src/ --fix
```

### Local Configuration

Use for **personal preferences** that shouldn't be shared:

- Temporary overrides for experimentation
- Personal optimizations (faster execution model for iteration)
- Sensitive configuration (if any)

Example:

```yaml
# .jiro-dreams-of-code.yaml (not committed)
models:
  execution: claude-3-5-haiku-20241022  # Fast iteration locally
```

### Version Control

By default, `.jiro-dreams-of-code.yaml` should **not be committed**. Add it to `.gitignore`:

```bash
# .gitignore
.jiro-dreams-of-code.yaml
```

This ensures personal configuration doesn't affect team members' setups.

## Environment Variables

Configuration can also be provided via environment variables, with the highest precedence:

- `ANTHROPIC_API_KEY` - Anthropic API key (checked before keyring)

The configuration system prioritizes in this order:

1. Environment variables (highest)
1. Local config (`.jiro-dreams-of-code.yaml`)
1. Project config (`~/.jiro-dreams-of-code/$PROJECT_NAME/config.yaml`)
1. Global config (`~/.jiro-dreams-of-code/config.yaml`)
1. Built-in defaults (lowest)

## Troubleshooting Configuration

### Check What's Being Used

When debugging configuration issues, use `jiro config list` to see the effective configuration and sources:

```bash
jiro config list
```

### Verify File Permissions

Ensure config files are readable:

```bash
# Check global config
cat ~/.jiro-dreams-of-code/config.yaml

# Check project config
cat ~/.jiro-dreams-of-code/$PROJECT_NAME/config.yaml

# Check local config
cat .jiro-dreams-of-code.yaml
```

### Reset to Defaults

To reset a value to its default, simply remove it from all config files:

```bash
# Find where a value is set
jiro config get models.execution

# Remove it from the config file shown in "Source:"
# Then verify it reverted to default
jiro config get models.execution
```

### Common Issues

**Problem**: Changes to config aren't taking effect

- Verify the config file exists with `cat`
- Check the precedence with `jiro config list` to see which level is active
- Ensure YAML syntax is valid (watch for indentation)

**Problem**: Can't find where a config value is set

- Use `jiro config get KEY` to see the source
- Check that file directly with `cat`
- Remember: local overrides project, project overrides global

**Problem**: Different team members have different configurations

- Use `jiro config list` to see each person's effective config
- Ensure project-level config is set correctly in `~/.jiro-dreams-of-code/$PROJECT_NAME/config.yaml`
- Check that `.jiro-dreams-of-code.yaml` is in `.gitignore`
