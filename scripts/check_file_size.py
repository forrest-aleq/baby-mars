#!/usr/bin/env python3
"""Pre-commit hook: Check that Python files don't exceed line limits."""

import sys
from pathlib import Path

MAX_LINES = 500

# Files with custom line limits (path suffix -> limit)
# These files contain cohesive algorithm implementations that would be
# harder to understand if split across multiple files.
CUSTOM_LIMITS: dict[str, int] = {
    "scripts/guardian.py": 700,
    "brain/write/belief_update.py": 900,  # Full EMA + cognitive features
    # Note: loop/activation.py was split into temporal.py, objects.py, turn_zero.py
    "test_loop_activation.py": 600,  # Comprehensive activation tests
}


def get_limit_for_file(filepath: str) -> int:
    """Get the line limit for a file (custom or default)."""
    for pattern, limit in CUSTOM_LIMITS.items():
        if filepath.endswith(pattern):
            return limit
    return MAX_LINES


def check_file(filepath: str) -> bool:
    """Check if file exceeds line limit."""
    path = Path(filepath)
    if not path.exists() or path.suffix != ".py":
        return True

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return True  # Skip files we can't read

    line_count = len(lines)
    limit = get_limit_for_file(filepath)

    if line_count > limit:
        print(f"FAIL {filepath}: {line_count} lines (max {limit})")
        return False

    return True


def main() -> int:
    """Check all provided files."""
    if len(sys.argv) < 2:
        return 0

    failed = False
    for filepath in sys.argv[1:]:
        if not check_file(filepath):
            failed = True

    if failed:
        print(f"\nFiles exceeding {MAX_LINES} lines must be split.")
        print("See CLAUDE.md for guidance on decomposition.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
