# jiro-dreams-of-code

> "I'll continue to climb, trying to reach the top, but no one knows where the top is." — Jiro Ono

A disciplined AI agent orchestration system that builds software using the shokunin philosophy: mastery through small, deliberate, repeated steps.

## Philosophy

Named after Jiro Ono, the 93-year-old sushi master from "Jiro Dreams of Sushi," this project embodies:

- **Shokunin** (職人): The artisan spirit—dedication to mastering one craft through continuous refinement
- **Kaizen**: Continuous small improvements
- **Discipline over speed**: Correctness and reviewability trump velocity

## Features

- Generate detailed specifications from natural language prompts
- Break specifications into granular, dependency-aware tasks
- Execute tasks with AI agents using strict TDD discipline
- Enforce commit hygiene through automated validation
- Track context usage and metrics for every operation
- Web UI for real-time monitoring and refinement

## Installation

```bash
# Using uv (recommended)
uv pip install jiro-dreams-of-code

# Using pip
pip install jiro-dreams-of-code
```

## Quick Start

```bash
# Initialize jiro in your project
jiro init

# Verify installation
jiro doctor

# Generate a spec from a prompt
jiro dream "build a user authentication system"

# Plan the implementation
jiro plan --spec specs/auth-system.md

# Execute the tasks
jiro execute

# Monitor progress
jiro status
jiro web
```

## Documentation

See [TECHNICAL_SPEC.md](docs/TECHNICAL_SPEC.md) for complete documentation.

## Requirements

- Python 3.12+
- Git
- Anthropic API key (for Claude)

## Development

```bash
# Clone the repository
git clone https://github.com/marshally/jiro-dreams-of-code.git
cd jiro-dreams-of-code

# Install with dev dependencies
uv pip install -e ".[dev,test]"

# Set up pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy src/jiro
```

## License

MIT
