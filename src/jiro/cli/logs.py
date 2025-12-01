"""Logs subcommand module for viewing JSONL log files."""

import json
import time
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from jiro.core.paths import get_logs_dir

app = typer.Typer()

console = Console()


def tail_follow(log_file: Path, interval: float = 0.5) -> None:
    """Follow a log file for new entries (like tail -f).

    Args:
        log_file: Path to the log file to follow.
        interval: Time in seconds between file checks.
    """
    # Track position in file
    try:
        with open(log_file) as f:
            f.seek(0, 2)  # Seek to end

            while True:
                line = f.readline()
                if line:
                    try:
                        entry = json.loads(line)
                        _display_log_entry(entry)
                    except json.JSONDecodeError:
                        # Skip invalid JSON
                        pass
                else:
                    time.sleep(interval)
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped following logs[/yellow]")


def _get_all_log_entries(logs_dir: Path) -> list[dict]:
    """Read all log entries from JSONL files in chronological order.

    Args:
        logs_dir: Path to the logs directory.

    Returns:
        List of log entries sorted chronologically.
    """
    entries = []

    # Get all JSONL files sorted by name (date)
    if not logs_dir.exists():
        return entries

    log_files = sorted(logs_dir.glob("*.jsonl"))

    for log_file in log_files:
        try:
            with open(log_file) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError:
                        # Skip invalid JSON lines
                        continue
        except OSError:
            # Skip files that can't be read
            continue

    # Sort by timestamp if available
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=False)

    return entries


def _display_log_entry(entry: dict) -> None:
    """Display a single log entry with Rich formatting.

    Args:
        entry: The log entry dictionary.
    """
    timestamp = entry.get("timestamp", "unknown")
    level = entry.get("level", "INFO")
    event = entry.get("event", "")

    # Color code by level
    level_colors = {
        "DEBUG": "dim",
        "INFO": "cyan",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red bold",
    }
    level_color = level_colors.get(level, "white")

    # Format and print
    console.print(f"[{level_color}]{level:8}[/{level_color}] [{timestamp}] {event}")

    # Print additional fields if present
    extra_fields = {k: v for k, v in entry.items() if k not in ("timestamp", "level", "event")}
    for key, value in extra_fields.items():
        console.print(f"  {key}: {value}")


def _display_logs_table(entries: list[dict]) -> None:
    """Display logs in a Rich table format.

    Args:
        entries: List of log entries to display.
    """
    if not entries:
        console.print("[yellow]No logs found[/yellow]")
        return

    # Create a table
    table = Table(title="Logs")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Level", style="magenta")
    table.add_column("Event", style="white")

    for entry in entries:
        timestamp = entry.get("timestamp", "-")
        level = entry.get("level", "-")
        event = entry.get("event", "-")

        # Truncate long events
        if len(str(event)) > 60:
            event = str(event)[:57] + "..."

        table.add_row(timestamp, level, event)

    console.print(table)


@app.callback(invoke_without_command=True)
def logs(
    follow: Annotated[bool, typer.Option("--follow", "-f", help="Follow log output")] = False,
    tail: Annotated[int | None, typer.Option("--tail", "-n", help="Show last N lines")] = None,
) -> None:
    """
    View logs from JSONL files with Rich formatting.

    Displays logs from the jiro logs directory with options for filtering
    and following new entries.

    Examples:
        jiro logs
        jiro logs --tail 50
        jiro logs --follow
        jiro logs -n 10
        jiro logs -f
    """
    try:
        # Get logs directory
        project_root = Path.cwd()
        logs_dir = get_logs_dir(
            project_root=project_root,
            stealth=True,
            project_name=project_root.name,
        )

        # If tail is specified, ignore follow
        # If following (and no tail), watch for new entries in the latest log file
        if follow and tail is None:
            # Get the most recent log file
            log_files = sorted(logs_dir.glob("*.jsonl"), reverse=True)
            if log_files:
                tail_follow(log_files[0])
            else:
                console.print("[yellow]No log files found[/yellow]")
            return

        # Get all log entries
        entries = _get_all_log_entries(logs_dir)

        # Apply tail if specified (default to 50 lines)
        entries = entries[-tail:] if tail is not None else entries[-50:]

        # Display logs in table format
        _display_logs_table(entries)

    except Exception as e:  # noqa: B904
        console.print(f"[red]Error reading logs: {str(e)}[/red]")
        raise typer.Exit(code=1) from e
