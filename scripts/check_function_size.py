#!/usr/bin/env python3
"""Pre-commit hook: Check that functions don't exceed 50 lines."""

import ast
import sys
from pathlib import Path

MAX_LINES = 50


def count_function_lines(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Count lines in a function, excluding docstrings and blank lines."""
    if not node.body:
        return 0

    start_line = node.lineno
    end_line = node.end_lineno or start_line

    return end_line - start_line + 1


def check_file(filepath: str) -> list[str]:
    """Check all functions in a file for size violations."""
    path = Path(filepath)
    if not path.exists() or path.suffix != ".py":
        return []

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return []  # Let other tools handle syntax errors

    violations = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            line_count = count_function_lines(node)
            if line_count > MAX_LINES:
                violations.append(
                    f"  {filepath}:{node.lineno} "
                    f"'{node.name}()' has {line_count} lines (max {MAX_LINES})"
                )

    return violations


def main() -> int:
    """Check all provided files."""
    if len(sys.argv) < 2:
        return 0

    all_violations = []
    for filepath in sys.argv[1:]:
        violations = check_file(filepath)
        all_violations.extend(violations)

    if all_violations:
        print(f"Functions exceeding {MAX_LINES} lines:")
        for v in all_violations:
            print(v)
        print("\nExtract helper functions to reduce size.")
        print("See CLAUDE.md for guidance on decomposition.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
