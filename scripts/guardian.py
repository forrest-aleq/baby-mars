#!/usr/bin/env python3
"""Guardian: Automated architect for MARS-Lite.

Enforces 13 architectural rules via pre-commit hooks.
See function docstrings for individual rule documentation.
"""

from __future__ import annotations

import ast
import re
import sys
from collections.abc import Iterable
from pathlib import Path

# Configuration
MAX_FILE_LINES = 500
MAX_FUNC_LINES = 50
MAX_INLINE_STRING = 50
TARGET_ROOT = Path("src/mars_lite")

# Custom file size limits (path suffix -> limit).
# Only guardian.py is exempt - it's self-referential and must stay cohesive.
# All other files MUST be under 500 lines with no exceptions.
CUSTOM_FILE_LIMITS: dict[str, int] = {
    "scripts/guardian.py": 700,
}

# Files allowed to use typing.Any (interact with Neo4j records)
ANY_TYPING_ALLOWED: tuple[str, ...] = (
    "brain/write/belief/",  # Neo4j record types in belief module
    "brain/fetch/",  # Neo4j record types
    "brain/connection.py",  # Neo4j driver types
    "loop/objects.py",  # Neo4j record types in objects column
    "loop/turn_zero.py",  # Neo4j record types in turn 0 handling
    "connectors/llm/",  # LLM responses are dynamic JSON
)

# Pure math/logic modules where sync functions ARE allowed (no I/O)
# These modules contain only CPU-bound operations (math, string parsing, regex)
# See CLAUDE.md: "Logic/Math should be `def`, Database/Network should be `async def`"
SYNC_ALLOWED_IN_ASYNC_ZONES: tuple[str, ...] = (
    "brain/write/belief/math.py",  # Pure EMA calculations
    "brain/write/belief/types.py",  # TypedDicts and enums
)

# Paths
ASYNC_ONLY_DIRS = ("mars_lite/loop", "mars_lite/brain")
CONNECTORS_DIR = "mars_lite/connectors"
REDIS_ALLOWED_DIRS = ("mars_lite/connectors", "mars_lite/working_memory")
PORTED_REQUIRED_ROOT = "src/mars_lite"

# Banned patterns
PROD_BANNED_TOKENS = ("mock", "dummy", "fake", "placeholder")
BLOCKED_NETWORK_LIBS = {"httpx", "aiohttp", "requests", "urllib3"}
BLOCKING_CALLS = {
    "time.sleep",
    "subprocess.run",
    "subprocess.call",
    "subprocess.check_output",
    "os.system",
}
FINANCIAL_CYPHER_VARS = ("$amount", "$balance", "$price", "$total", "$cost")
BAN_NEW_CODE_TOKENS = ("todo", "tbd", "fixme", "unimplemented")

# Regex patterns
SYNC_WITH_PATTERN = re.compile(r"\bwith\s+(?!open\()")
ASYNC_WITH_PATTERN = re.compile(r"\basync\s+with\b")
SESSION_CALL_PATTERN = re.compile(r"\.session\s*\(")
CYPHER_PATTERN = re.compile(r"\b(MATCH|CREATE|MERGE)\s+\(", re.IGNORECASE)
ORG_ID_PATTERN = re.compile(r"org_id\s*[:=]", re.IGNORECASE)


def iter_py_files(root: Path) -> Iterable[Path]:
    """Iterate over all Python files in a directory."""
    if not root.exists():
        return []
    return (p for p in root.rglob("*.py") if p.is_file())


def is_async_only_zone(path: Path) -> bool:
    """Check if path is in an async-only zone (loop/ or brain/)."""
    return any(seg in str(path) for seg in ASYNC_ONLY_DIRS)


def is_connector(path: Path) -> bool:
    """Check if path is in connectors directory."""
    return CONNECTORS_DIR in str(path)


def in_tests(path: Path) -> bool:
    """Check if path is in tests directory."""
    return "tests" in path.parts


def in_scripts(path: Path) -> bool:
    """Check if path is in scripts directory."""
    return "scripts/" in str(path)


def is_redis_allowed_zone(path: Path) -> bool:
    """Check if Redis imports are permitted in this path."""
    return any(seg in str(path) for seg in REDIS_ALLOWED_DIRS)


def _get_file_limit(path: Path) -> int:
    """Get the line limit for a file (custom or default)."""
    path_str = str(path)
    for pattern, limit in CUSTOM_FILE_LIMITS.items():
        if path_str.endswith(pattern):
            return limit
    return MAX_FILE_LINES


def check_file_size(path: Path, lines: list[str]) -> list[str]:
    """RULE 1: File size (500 lines max, or custom limit)."""
    limit = _get_file_limit(path)
    if len(lines) > limit:
        return [
            f"{path}: File has {len(lines)} lines (max {limit}). "
            "Split into smaller modules."
        ]
    return []


def check_ported_from(path: Path, content: str) -> list[str]:
    """Enforce provenance marker for mars_lite files."""
    if not str(path).startswith(PORTED_REQUIRED_ROOT):
        return []
    if in_tests(path):
        return []
    if path.name == "__init__.py":
        return []
    marker = "PORTED_FROM:"
    if marker not in content:
        return [
            f"{path}: Missing provenance marker '{marker}'. "
            "Add a comment like '# PORTED_FROM: src/old/path.py:function'."
        ]
    return []


def _is_any_typing_allowed(path: Path) -> bool:
    """Check if typing.Any is allowed for this file."""
    path_str = str(path)
    return any(pattern in path_str for pattern in ANY_TYPING_ALLOWED)


def check_lazy_typing(path: Path, content: str) -> list[str]:
    """RULE 7: Ban lazy typing (Any, type: ignore)."""
    violations: list[str] = []
    if "# type: ignore" in content:
        violations.append(f"{path}: Contains '# type: ignore'. Fix the types properly.")
    has_any_import = "from typing import Any" in content or "import Any" in content
    if has_any_import and not _is_any_typing_allowed(path):
        violations.append(
            f"{path}: Imports 'Any'. Use explicit types or Pydantic models."
        )
    return violations


def check_mocks_in_production(path: Path, content: str) -> list[str]:
    """RULE 8: Ban mocks/placeholders in production."""
    if in_tests(path):
        return []
    lowered = content.lower()
    for token in PROD_BANNED_TOKENS:
        if token in lowered:
            return [
                f"{path}: Contains '{token}' in production code. "
                "Move test data to tests/."
            ]
    return []


def check_print_in_production(path: Path, content: str) -> list[str]:
    """RULE 9: Ban print() in production (use logger)."""
    if in_tests(path) or in_scripts(path):
        return []
    if "print(" in content:
        return [f"{path}: Contains print(). Use logging.getLogger() instead."]
    return []


def check_new_code_tokens(path: Path, content: str) -> list[str]:
    """Ban TODO/TBD/FIXME/UNIMPLEMENTED in production code."""
    if in_tests(path):
        return []
    lowered = content.lower()
    for token in BAN_NEW_CODE_TOKENS:
        if token in lowered:
            return [
                f"{path}: Contains '{token.upper()}' marker. "
                "Finish implementation or remove placeholder."
            ]
    return []


def check_sync_redis(path: Path, content: str) -> list[str]:
    """RULE 6: Ban sync Redis imports."""
    violations: list[str] = []
    has_async = "redis.asyncio" in content
    has_sync = "import redis" in content or "from redis import" in content

    # Disallow any Redis imports outside allowed zones
    if not is_redis_allowed_zone(path) and (has_async or has_sync):
        return [
            f"{path}: Redis import not allowed here. Only connectors/ and working_memory/ may use Redis."
        ]

    if has_sync:
        violations.append(
            f"{path}: Imports sync Redis. Use 'from redis.asyncio import Redis'."
        )

    return violations


def check_network_imports(path: Path, tree: ast.AST) -> list[str]:
    """RULE 10: Ban network imports outside connectors."""
    if is_connector(path):
        return []
    violations: list[str] = []
    for node in ast.walk(tree):
        result = _get_import_lib(node)
        if result is not None:
            lib, lineno = result
            if lib in BLOCKED_NETWORK_LIBS:
                violations.append(
                    f"{path}:{lineno}: Imports '{lib}' outside "
                    "connectors/. Network calls must go through connectors."
                )
    return violations


def _get_import_lib(node: ast.AST) -> tuple[str, int] | None:
    """Extract library name and line number from import node."""
    if isinstance(node, ast.Import):
        for alias in node.names:
            return (alias.name.split(".")[0], node.lineno)
    if isinstance(node, ast.ImportFrom) and node.module:
        return (node.module.split(".")[0], node.lineno)
    return None


def check_file(path: Path) -> list[str]:
    """Run all checks on a single file."""
    violations: list[str] = []

    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = path.read_text(encoding="utf-8", errors="replace")

    lines = content.splitlines()

    # Text-based rules
    violations.extend(check_file_size(path, lines))
    violations.extend(check_ported_from(path, content))
    violations.extend(check_lazy_typing(path, content))
    violations.extend(check_mocks_in_production(path, content))
    violations.extend(check_print_in_production(path, content))
    violations.extend(check_new_code_tokens(path, content))
    violations.extend(check_sync_redis(path, content))

    # Parse AST for deeper checks
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return violations

    violations.extend(check_network_imports(path, tree))

    # Function-level checks
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            violations.extend(check_function(path, node, content))

    # Prompt sovereignty in async zones
    if is_async_only_zone(path):
        violations.extend(check_long_strings(path, tree))

    # Cypher query checks
    violations.extend(check_cypher_queries(path, content))

    return violations


def check_function_size(
    path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef
) -> list[str]:
    """RULE 2: Function size (50 lines max)."""
    start_line = node.lineno
    end_line = getattr(node, "end_lineno", start_line)
    func_len = end_line - start_line + 1
    if func_len > MAX_FUNC_LINES:
        return [
            f"{path}:{start_line}: Function '{node.name}' is {func_len} lines "
            f"(max {MAX_FUNC_LINES}). Extract helper functions."
        ]
    return []


def _is_sync_allowed_module(path: Path) -> bool:
    """Check if sync functions are allowed in this module (pure math/logic)."""
    path_str = str(path)
    return any(pattern in path_str for pattern in SYNC_ALLOWED_IN_ASYNC_ZONES)


def check_async_only_zone(
    path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef
) -> list[str]:
    """RULE 3: Async-only in loop/brain (except pure math modules)."""
    if not is_async_only_zone(path) or isinstance(node, ast.AsyncFunctionDef):
        return []
    if node.name.startswith("__"):
        return []

    # Allow sync functions in pure math/logic modules
    if _is_sync_allowed_module(path):
        return []

    allowed = {"staticmethod", "classmethod", "property"}
    decorator_names = {_get_decorator_name(d) for d in node.decorator_list}
    if allowed & decorator_names:
        return []

    return [
        f"{path}:{node.lineno}: Sync function '{node.name}' in "
        "async-only zone. Use 'async def'."
    ]


def _get_decorator_name(dec: ast.expr) -> str:
    """Extract decorator name from AST node."""
    if isinstance(dec, ast.Name):
        return dec.id
    if isinstance(dec, ast.Attribute):
        return dec.attr
    return ""


def _has_check_true(call: ast.Call) -> bool:
    """Detect check=True in a call keyword list."""
    for kw in call.keywords:
        if (
            kw.arg == "check"
            and isinstance(kw.value, ast.Constant)
            and kw.value.value is True
        ):
            return True
    return False


def check_sync_with_async_cm(
    path: Path, node: ast.AsyncFunctionDef, content: str
) -> list[str]:
    """RULE 4: Ban sync `with` on async context managers."""
    start_line = node.lineno
    end_line = getattr(node, "end_lineno", start_line)
    func_lines = content.splitlines()[start_line - 1 : end_line]
    func_text = "\n".join(func_lines)

    has_session = SESSION_CALL_PATTERN.search(func_text)
    has_sync_with = SYNC_WITH_PATTERN.search(func_text)
    has_async_with = ASYNC_WITH_PATTERN.search(func_text)

    if has_session and has_sync_with and not has_async_with:
        return [
            f"{path}:{start_line}: Function '{node.name}' uses "
            "'with .session()'. Must use 'async with'."
        ]
    return []


def check_blocking_calls(path: Path, node: ast.AsyncFunctionDef) -> list[str]:
    """RULE 5: Ban blocking calls in async functions."""
    violations: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            call_name = get_call_name(child)
            if call_name in BLOCKING_CALLS:
                violations.append(
                    f"{path}:{child.lineno}: Blocking call '{call_name}' "
                    f"in async function '{node.name}'. Use async equivalent."
                )
            if call_name == "subprocess.run" and not _has_check_true(child):
                violations.append(
                    f"{path}:{child.lineno}: subprocess.run without check=True. "
                    "Set check=True or use async equivalent."
                )
    return violations


def check_function(
    path: Path,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    content: str,
) -> list[str]:
    """Check a single function for violations (RULES 2-5)."""
    violations: list[str] = []

    violations.extend(check_function_size(path, node))
    violations.extend(check_async_only_zone(path, node))

    if isinstance(node, ast.AsyncFunctionDef):
        violations.extend(check_sync_with_async_cm(path, node, content))
        violations.extend(check_blocking_calls(path, node))
    else:
        # Synchronous function: still enforce subprocess.run check=True safety.
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_name = get_call_name(child)
                if call_name == "subprocess.run" and not _has_check_true(child):
                    violations.append(
                        f"{path}:{child.lineno}: subprocess.run without check=True. "
                        "Set check=True or use a safer helper."
                    )

    return violations


def get_call_name(node: ast.Call) -> str:
    """Extract the full name of a function call (e.g., 'time.sleep')."""
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parts: list[str] = []
        current: ast.expr = node.func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def check_long_strings(path: Path, tree: ast.AST) -> list[str]:
    """RULE 13: Prompt sovereignty (no long strings in loop/brain)."""
    violations: list[str] = []
    prompt_keywords = ("you are", "assistant", "system", "user")
    docstring_ids = _collect_docstring_constants(tree)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if len(node.value) <= MAX_INLINE_STRING:
            continue
        # Skip docstrings (module, class, function)
        if id(node) in docstring_ids:
            continue
        if any(kw in node.value.lower() for kw in prompt_keywords):
            violations.append(
                f"{path}:{node.lineno}: Long prompt string detected. "
                "Move to prompts module."
            )
    return violations


def check_cypher_queries(path: Path, content: str) -> list[str]:
    """RULES 11, 12: Cypher query checks."""
    if not CYPHER_PATTERN.search(content):
        return []

    violations: list[str] = []
    violations.extend(_check_org_id_in_cypher(path, content))
    violations.extend(_check_financial_vars_in_cypher(path, content))
    return violations


def _check_org_id_in_cypher(path: Path, content: str) -> list[str]:
    """RULE 11: Enforce org_id in Cypher queries."""
    # Only match actual Cypher queries, not method calls like .create()
    # Real Cypher: MATCH (n:Label) - uppercase keyword followed by space and (
    cypher_query_start = re.compile(r"\b(MATCH|CREATE|MERGE)\s+\(", re.IGNORECASE)
    # Skip method calls like .create( or messages.create(
    method_call_pattern = re.compile(r"\.\s*(create|merge|match)\s*\(", re.IGNORECASE)
    # Skip "ON CREATE SET" and "ON MATCH SET" clauses (part of MERGE)
    on_clause = re.compile(r"\bON\s+(CREATE|MATCH)\b", re.IGNORECASE)
    # Skip relationship patterns
    relationship_pattern = re.compile(
        r"\b(MERGE|CREATE)\s*\([a-z0-9_]*\)\s*-\[", re.IGNORECASE
    )
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        if not cypher_query_start.search(line):
            continue
        # Skip method calls on objects (SDK calls like .create())
        if method_call_pattern.search(line):
            continue
        if "INDEX" in line.upper() or "CONSTRAINT" in line.upper():
            continue
        if on_clause.search(line):
            continue
        if relationship_pattern.search(line):
            continue

        context_end = min(len(lines), i + 5)
        context = "\n".join(lines[i - 1 : context_end])

        if not ORG_ID_PATTERN.search(context):
            return [
                f"{path}:{i}: Cypher query may be missing org_id. "
                "All queries must scope by org_id for multi-tenancy."
            ]
    return []


def _check_financial_vars_in_cypher(path: Path, content: str) -> list[str]:
    """RULE 12: Ban financial fields in Cypher."""
    for var in FINANCIAL_CYPHER_VARS:
        if var in content:
            return [
                f"{path}: Financial variable '{var}' in Cypher query. "
                "Financial data belongs in Stargate, not Neo4j."
            ]
    return []


def _collect_docstring_constants(tree: ast.AST) -> set[int]:
    """Collect ids of Constant nodes that are docstrings."""
    doc_ids: set[int] = set()

    def record_doc(node: ast.AST) -> None:
        body = getattr(node, "body", [])
        if not body:
            return
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            doc_ids.add(id(first.value))

    class DocVisitor(ast.NodeVisitor):
        def visit_Module(self, node: ast.Module) -> None:
            record_doc(node)
            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            record_doc(node)
            self.generic_visit(node)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            record_doc(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            record_doc(node)
            self.generic_visit(node)

    DocVisitor().visit(tree)
    return doc_ids


def main() -> int:
    """Run guardian checks on all target files."""
    all_files = list(iter_py_files(TARGET_ROOT))

    if not all_files:
        print("guardian: No files found in target directory. Skipping.")
        return 0

    all_violations: list[str] = []
    for path in all_files:
        violations = check_file(path)
        all_violations.extend(violations)

    if all_violations:
        print("=" * 60)
        print("GUARDIAN VIOLATIONS - These must be fixed before merge")
        print("=" * 60)
        for v in sorted(set(all_violations)):
            print(f"  {v}")
        print("=" * 60)
        print(f"Total: {len(all_violations)} violation(s)")
        return 1

    print("guardian: All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
