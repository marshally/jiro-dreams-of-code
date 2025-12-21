# CLI Style Guide

This document defines the user experience patterns for the jiro CLI.

## Output Philosophy

**Quiet by default, verbose on request.** Users should see clean, actionable output—not log spam.

## Verbosity Levels

| Flag | Level | What's shown |
|------|-------|--------------|
| (none) | Normal | Progress messages, results, errors |
| `-v` | Verbose | Above + debug logs |
| `-q` | Quiet | Errors only |

### Implementation

```python
# In main.py callback
set_silent_mode(verbose == 0)  # Suppress logs unless -v passed
configure_logging(verbosity=log_level)
```

## Progress Indicators

Use Rich console for user-facing output:

```python
from rich.console import Console

console = Console()

# Status messages
console.print("[cyan]Parsing specification...[/cyan]")
console.print("[cyan]Running planning agent...[/cyan]")

# Success
console.print("[green]✓[/green] Created config file")

# Already exists / no action needed
console.print("[dim]·[/dim] .gitignore already configured")

# Warning (non-fatal)
console.print("[yellow]![/yellow] Beads not initialized")

# Error
console.print("[red]Error: No spec files found.[/red]")
console.print("[dim]Run 'jiro dream' to create a specification first.[/dim]")
```

## Command Patterns

### Auto-Discovery

When a required input has an obvious default, use it:

```bash
# If only one spec exists, use it
jiro plan                    # Uses most recent spec
jiro plan --spec foo.md      # Explicit override
```

### Fix Mode

Commands with `--fix` should:

1. Run checks silently
1. Show fix messages for what was fixed
1. Re-run checks and show final state

```
❯ jiro doctor --fix
Attempting to fix issues...
✓ Updated .gitignore

        Health Check Results
┏━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━┓
│ Check    │ Status │ Details │
├──────────┼────────┼─────────┤
│ gitignore│ PASS   │         │
└──────────┴────────┴─────────┘
```

### Confirmation Prompts

For destructive or significant actions, require confirmation:

```python
proceed = typer.confirm("Proceed with creating tasks?", default=False)
if not proceed:
    console.print("[yellow]Cancelled.[/yellow]")
    return
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (check failed, operation failed, etc.) |

```python
if not doctor_result.passed:
    raise typer.Exit(code=1)
```

## Error Messages

### Structure

```
Error: <What went wrong>
<How to fix it>
```

### Examples

```python
# Good: actionable
console.print("[red]Error: No spec files found.[/red]")
console.print("[dim]Run 'jiro dream' to create a specification first.[/dim]")

# Good: shows the actual error
console.print(f"[yellow]Warning: Could not initialize beads: {stderr.strip()}[/yellow]")

# Bad: vague
console.print("[red]Error: Operation failed[/red]")
```

## Tables

Use Rich tables for structured data:

```python
from rich.table import Table

table = Table(title="Health Check Results")
table.add_column("Check", style="cyan")
table.add_column("Status", style="magenta")
table.add_column("Details", style="yellow")

for name, result in checks.items():
    status = "[green]PASS[/green]" if result.passed else "[red]FAIL[/red]"
    table.add_row(name, status, result.error or "")

console.print(table)
```

## Interactive Modes

For multi-step interactions (like `jiro dream` refinement):

```
Enter refinement chat.
Enter to submit. Shift+Enter for a newline.
Commands: 'done' / 'exit' / '/quit' / Ctrl+D to save and exit

─────────────────────────────────────────────────
Refinement>
```

- Show available commands upfront
- Use a clear prompt indicator
- Support multiple exit methods

## See Also

- [DEFINITION_OF_DONE.md](./DEFINITION_OF_DONE.md) - Task completion criteria
- [TECHNICAL_SPEC.md](./TECHNICAL_SPEC.md) - Overall system design
