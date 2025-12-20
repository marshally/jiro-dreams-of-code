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
        hook_failures = []
        lines = output.split("\n")

        current_hook = None
        for line in lines:
            # Detect hook names
            if line.endswith("...Passed"):
                continue
            if line.endswith("...Failed"):
                hook_name = line.replace("...Failed", "").strip()
                hook_failures.append(hook_name[:40])
            elif line.endswith("...Skipped"):
                continue
            elif "hook id:" in line.lower():
                # pre-commit hook format
                if match := re.search(r"hook id: (\S+)", line):
                    current_hook = match.group(1)
            elif current_hook and line.strip() and not line.startswith("-"):
                # Capture first error line for current hook
                if len(hook_failures) == 0 or hook_failures[-1] != current_hook:
                    hook_failures.append(f"{current_hook}: {line.strip()[:50]}")
                current_hook = None

        # Dedupe and limit
        hook_failures = list(dict.fromkeys(hook_failures))[:5]

        return {
            "success": False,
            "sha": None,
            "files_changed": len(staged_files),
            "error": "Commit failed",
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
