"""Structlog configuration for jiro with JSONL and Rich output."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
from rich.console import Console
from rich.logging import RichHandler

from jiro.core.paths import get_logs_dir

# Context variable storage for session and task IDs
_context_vars: dict[str, Any] = {}

# Silent mode flag - when True, suppress console output (still logs to file)
_silent_mode: bool = False


def set_silent_mode(silent: bool) -> None:
    """Enable or disable silent mode (suppress console log output).

    Args:
        silent: If True, suppress console output. Logs still go to file.
    """
    global _silent_mode
    _silent_mode = silent


def is_silent_mode() -> bool:
    """Check if silent mode is enabled.

    Returns:
        True if silent mode is enabled.
    """
    return _silent_mode


def get_context_var(key: str) -> Any:
    """Get a context variable.

    Args:
        key: The context variable key.

    Returns:
        The value of the context variable, or None if not set.
    """
    return _context_vars.get(key)


def set_context_var(key: str, value: Any) -> None:
    """Set a context variable.

    Args:
        key: The context variable key.
        value: The value to set.
    """
    _context_vars[key] = value


def _add_context_vars(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add context variables to log entries.

    Args:
        logger: The structlog logger.
        method_name: The name of the method being called.
        event_dict: The event dictionary.

    Returns:
        The updated event dictionary with context variables.
    """
    # Add all context variables to the event
    for key, value in _context_vars.items():
        if key not in event_dict:
            event_dict[key] = value
    return event_dict


class JSONLRenderer:
    """Custom renderer for JSONL output."""

    def __init__(self, log_file: Path) -> None:
        """Initialize the JSONL renderer.

        Args:
            log_file: Path to the log file.
        """
        self.log_file = log_file

    def __call__(
        self,
        logger: Any,
        method_name: str,
        event_dict: dict[str, Any],
    ) -> str:
        """Render the log entry as JSONL.

        Args:
            logger: The structlog logger.
            method_name: The name of the method being called.
            event_dict: The event dictionary.

        Returns:
            The JSON string.
        """
        # Ensure parent directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Add timestamp if not already present
        if "timestamp" not in event_dict:
            event_dict["timestamp"] = datetime.now().isoformat()

        # Write to file
        with open(self.log_file, "a") as f:
            json.dump(event_dict, f)
            f.write("\n")

        # Return empty string in silent mode, otherwise JSON for console output
        if _silent_mode:
            return ""
        return json.dumps(event_dict)


def configure_logging(
    verbosity: int = logging.INFO,
    project_name: str | None = None,
) -> Any:
    """Configure structlog with JSONL and Rich console output.

    Args:
        verbosity: The log level (logging.INFO, logging.DEBUG, logging.CRITICAL).
        project_name: The project name for log file location.

    Returns:
        A configured structlog logger.

    Raises:
        ValueError: If project_name is not provided.
    """
    if project_name is None:
        project_name = "jiro"

    # Get logs directory
    logs_dir = get_logs_dir(
        project_root=Path.cwd(),
        stealth=True,
        project_name=project_name,
    )
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Create log file path with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{today}.jsonl"

    # Configure standard logging
    # Only add RichHandler for console output when in verbose mode (DEBUG level)
    # Otherwise, use NullHandler to suppress external library logs from STDOUT
    if verbosity <= logging.DEBUG:
        handlers: list[logging.Handler] = [
            RichHandler(
                console=Console(force_terminal=True, stderr=True),
                rich_tracebacks=True,
            ),
        ]
    else:
        handlers = [logging.NullHandler()]

    logging.basicConfig(
        level=verbosity,
        handlers=handlers,
        force=True,  # Override any existing configuration
    )

    # Configure structlog
    structlog.configure(
        processors=[
            # Add context variables
            _add_context_vars,
            # Convert log levels
            structlog.processors.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Render JSONL
            JSONLRenderer(log_file),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )

    # Get and return the logger
    return structlog.get_logger()
