#!/usr/bin/env python3
"""Run pytest and output condensed structured results.

Usage:
    scripts/test.py [pytest args...]

Examples:
    scripts/test.py                          # Run all tests
    scripts/test.py tests/unit/              # Run unit tests only
    scripts/test.py -k "test_dream"          # Run matching tests
    scripts/test.py --no-cov                 # Skip coverage
"""

import json
import re
import subprocess
import sys
from pathlib import Path


def run_pytest(args: list[str]) -> dict:
    """Run pytest and return structured results."""
    # Build command - use JSON report for structured output
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--tb=no",  # No tracebacks in main output
        "-q",  # Quiet mode
        *args,
    ]

    # Check if coverage is disabled
    no_cov = "--no-cov" in args
    if no_cov:
        cmd = [c for c in cmd if c != "--no-cov"]
        cmd.extend(["--no-cov"])

    # Run pytest
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )

    # Parse output
    output = result.stdout + result.stderr
    lines = output.strip().split("\n")

    # Extract summary line (e.g., "1992 passed in 41.42s")
    summary_line = ""
    for line in reversed(lines):
        if "passed" in line or "failed" in line or "error" in line:
            summary_line = line.strip()
            break

    # Parse counts from summary
    passed = failed = errors = skipped = warnings = 0
    duration = ""

    if match := re.search(r"(\d+) passed", summary_line):
        passed = int(match.group(1))
    if match := re.search(r"(\d+) failed", summary_line):
        failed = int(match.group(1))
    if match := re.search(r"(\d+) error", summary_line):
        errors = int(match.group(1))
    if match := re.search(r"(\d+) skipped", summary_line):
        skipped = int(match.group(1))
    if match := re.search(r"(\d+) warning", summary_line):
        warnings = int(match.group(1))
    if match := re.search(r"in ([\d.]+)s", summary_line):
        duration = match.group(1) + "s"

    # Extract failed test names if any
    failed_tests = []
    if failed > 0 or errors > 0:
        for line in lines:
            if line.startswith("FAILED ") or line.startswith("ERROR "):
                # Extract test name
                test_name = line.split(" ")[1].split("::")[1] if "::" in line else line
                failed_tests.append(test_name[:60])  # Truncate long names

    # Extract coverage if present
    coverage = None
    for line in lines:
        if match := re.search(r"TOTAL\s+\d+\s+\d+\s+([\d.]+)%", line):
            coverage = match.group(1) + "%"
            break

    return {
        "success": result.returncode == 0,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "warnings": warnings,
        "duration": duration,
        "coverage": coverage,
        "failed_tests": failed_tests[:5],  # Limit to first 5
    }


def main() -> int:
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    result = run_pytest(args)

    # Output as compact JSON
    print(json.dumps(result))

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
