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
    # Build command with short traceback for parsing failures
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "--tb=line",  # One-line tracebacks for failure info
        "-q",  # Quiet mode
        *args,
    ]

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

    # Extract failed test details
    # --tb=line format: "/path/to/test.py:42: AssertionError: message"
    failed_tests = []
    if failed > 0 or errors > 0:
        for line in lines:
            stripped = line.strip()

            # Skip pytest internals and warnings
            if "site-packages" in stripped or "Warning:" in stripped:
                continue

            # Match pytest's line traceback format
            # e.g., "/full/path/test_foo.py:42: AssertionError"
            match = re.match(
                r"^(.+?):(\d+):\s*(Assert\w+|ValueError|TypeError|KeyError|RuntimeError|Exception):\s*(.*)$",
                stripped,
            )
            if match:
                file_path = match.group(1)
                # Shorten path - keep just tests/... or src/...
                if "tests/" in file_path:
                    file_path = "tests/" + file_path.split("tests/")[-1]
                elif "src/" in file_path:
                    file_path = "src/" + file_path.split("src/")[-1]
                else:
                    # For other paths, just use basename
                    file_path = Path(file_path).name

                failed_tests.append(
                    {
                        "file": file_path,
                        "line": int(match.group(2)),
                        "error": match.group(3),
                        "msg": match.group(4)[:60] if match.group(4) else "",
                    }
                )

    # Limit to first 10
    failed_tests = failed_tests[:10]

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
        "failures": failed_tests,
    }


def main() -> int:
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    result = run_pytest(args)

    # Output as compact JSON
    print(json.dumps(result))

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
