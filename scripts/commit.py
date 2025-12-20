#!/usr/bin/env python3
"""Run git commit and output condensed structured results.

Usage:
    scripts/commit.py "commit message"
    scripts/commit.py -m "commit message"

Examples:
    scripts/commit.py "fix: resolve bug in parser"
    scripts/commit.py -m "feat: add new feature"
"""

import json
import re
import subprocess
import sys
from pathlib import Path


def run_git(*args: str) -> subprocess.CompletedProcess:
    """Run a git command."""
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )


def get_staged_files() -> list[str]:
    """Get list of staged files."""
    result = run_git("diff", "--cached", "--name-only")
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.strip().split("\n") if f]


def parse_hook_failures(output: str) -> list[dict]:
    """Parse pre-commit hook failures into structured errors.

    Returns list of:
        {"hook": "ruff", "file": "src/foo.py", "line": 10, "error": "E501 ..."}
    """
    failures = []
    lines = output.split("\n")

    current_hook = None
    in_hook_output = False

    for line in lines:
        # Skip empty lines and progress dots
        stripped = line.strip()
        if not stripped or re.match(r"^[\.\s]+$", stripped):
            continue

        # Detect hook failure: "ruff.....Failed" or "ruff...Failed"
        if "Failed" in line and "..." in line:
            # Extract hook name (everything before the dots)
            hook_match = re.match(r"^([a-zA-Z0-9_-]+)\.+", stripped)
            if hook_match:
                current_hook = hook_match.group(1)
                in_hook_output = True
            continue

        # Detect hook passed/skipped - reset state
        if "Passed" in line or "Skipped" in line:
            current_hook = None
            in_hook_output = False
            continue

        # Skip hook metadata lines
        if stripped.startswith("- hook id:") or stripped.startswith("- exit code:"):
            continue

        # Parse actual error lines when in a failed hook's output
        if current_hook and in_hook_output:
            # Pattern: file:line:col: error OR file:line: error
            # Examples:
            #   src/foo.py:10:5: E501 Line too long
            #   src/foo.py:10: error: Type mismatch
            #   +++ src/foo.py (for diff-based hooks)

            # Skip diff headers
            if stripped.startswith("+++") or stripped.startswith("---"):
                continue

            # Try to parse file:line:col: message
            match = re.match(r"^([^:]+):(\d+):(\d+):\s*(.+)$", stripped)
            if match:
                failures.append(
                    {
                        "hook": current_hook,
                        "file": match.group(1),
                        "line": int(match.group(2)),
                        "col": int(match.group(3)),
                        "error": match.group(4)[:80],  # Truncate long messages
                    }
                )
                continue

            # Try to parse file:line: message (no column)
            match = re.match(r"^([^:]+):(\d+):\s*(.+)$", stripped)
            if match:
                failures.append(
                    {
                        "hook": current_hook,
                        "file": match.group(1),
                        "line": int(match.group(2)),
                        "error": match.group(3)[:80],
                    }
                )
                continue

    # Limit to first 10 errors
    return failures[:10]


def run_commit(message: str) -> dict:
    """Run git commit and return structured results."""
    # Get staged files before commit
    staged_files = get_staged_files()

    if not staged_files:
        return {
            "success": False,
            "error": "No staged files",
            "sha": None,
            "files_changed": 0,
            "hook_failures": [],
        }

    # Run commit
    result = run_git("commit", "-m", message)
    output = result.stdout + result.stderr

    # Parse result
    if result.returncode == 0:
        # Extract SHA from output like "[branch abc1234] message"
        sha = None
        if match := re.search(r"\[[\w\-/]+ ([a-f0-9]+)\]", output):
            sha = match.group(1)

        # Count files
        files_match = re.search(r"(\d+) files? changed", output)
        files_changed = int(files_match.group(1)) if files_match else len(staged_files)

        return {
            "success": True,
            "sha": sha,
            "files_changed": files_changed,
            "hook_failures": [],
        }
    else:
        # Parse hook failures
        hook_failures = parse_hook_failures(output)

        # If no structured errors found, try to get hook names at least
        if not hook_failures:
            for line in output.split("\n"):
                if "Failed" in line and "..." in line:
                    hook_match = re.match(r"^([a-zA-Z0-9_-]+)\.+", line.strip())
                    if hook_match:
                        hook_failures.append({"hook": hook_match.group(1), "error": "check output"})

        return {
            "success": False,
            "sha": None,
            "files_changed": len(staged_files),
            "error": "hook_failed",
            "hook_failures": hook_failures,
        }


def main() -> int:
    # Parse args
    args = sys.argv[1:]

    if not args:
        print(json.dumps({"success": False, "error": "No commit message provided"}))
        return 1

    # Handle -m flag
    if args[0] == "-m":
        if len(args) < 2:
            print(json.dumps({"success": False, "error": "No commit message after -m"}))
            return 1
        message = args[1]
    else:
        message = args[0]

    result = run_commit(message)

    # Output as compact JSON
    print(json.dumps(result))

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
