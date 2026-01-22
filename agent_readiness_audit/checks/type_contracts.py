"""Type contracts checks for v2 agent readiness."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_exists,
    glob_files,
    read_file_safe,
)


def _count_typed_functions(file_path: Path) -> tuple[int, int]:
    """Count total and typed functions in a Python file using AST.

    A function is considered typed if it has any type annotation
    on parameters or return type.

    Args:
        file_path: Path to Python file.

    Returns:
        Tuple of (total_functions, typed_functions).
    """
    content = read_file_safe(file_path)
    if not content:
        return 0, 0

    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        return 0, 0

    total = 0
    typed = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total += 1
            has_type = False

            # Check return annotation
            if node.returns is not None:
                has_type = True

            # Check parameter annotations
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                if arg.annotation is not None:
                    has_type = True
                    break

            if node.args.vararg and node.args.vararg.annotation:
                has_type = True
            if node.args.kwarg and node.args.kwarg.annotation:
                has_type = True

            if has_type:
                typed += 1

    return total, typed


@check(
    name="python_type_hint_coverage",
    category="static_guardrails",
    description="Check type hint coverage across Python source files",
    pillar="type_contracts",
    gate_level=4,
)
def check_python_type_hint_coverage(repo_path: Path) -> CheckResult:
    """Check type hint coverage in Python files.

    Scans all .py files (excluding tests/, migrations/, vendor/)
    and calculates the percentage of functions with type annotations.

    Pass threshold: >= 70% for Level 4.
    """
    # Find all Python files, excluding certain directories
    exclude_patterns = [
        "tests/",
        "test/",
        "migrations/",
        "vendor/",
        "__pycache__/",
        ".venv/",
        "venv/",
        ".tox/",
        "node_modules/",
        "site-packages/",
    ]
    py_files = glob_files(repo_path, "**/*.py")

    # Filter out excluded directories
    filtered_files = []
    for f in py_files:
        rel_path = str(f.relative_to(repo_path))
        if not any(excl in rel_path for excl in exclude_patterns):
            filtered_files.append(f)

    if not filtered_files:
        # No Python files found - check if this is a Python project
        if not file_exists(repo_path, "pyproject.toml", "setup.py", "requirements.txt"):
            return CheckResult(
                passed=True,
                evidence="Not a Python project; type hint check not applicable.",
            )
        return CheckResult(
            passed=False,
            evidence="No Python source files found outside test directories.",
            suggestion="Add Python source files with type hints.",
        )

    total_functions = 0
    typed_functions = 0
    files_without_types: list[tuple[str, int, int]] = []

    for py_file in filtered_files:
        total, typed = _count_typed_functions(py_file)
        total_functions += total
        typed_functions += typed
        if total > 0 and typed < total:
            rel_path = str(py_file.relative_to(repo_path))
            files_without_types.append((rel_path, typed, total))

    if total_functions == 0:
        return CheckResult(
            passed=True,
            evidence="No functions found in source files.",
        )

    coverage = (typed_functions / total_functions) * 100

    # Sort by most functions needing types
    files_without_types.sort(key=lambda x: x[2] - x[1], reverse=True)
    top_missing = files_without_types[:5]

    evidence_parts = [
        f"Type hint coverage: {coverage:.1f}%",
        f"({typed_functions}/{total_functions} functions typed)",
    ]

    if top_missing:
        evidence_parts.append(
            "Files needing types: " + ", ".join(f[0] for f in top_missing)
        )

    evidence = " ".join(evidence_parts)

    if coverage >= 70:
        return CheckResult(
            passed=True,
            evidence=evidence,
        )
    elif coverage >= 40:
        return CheckResult(
            passed=False,
            partial=True,
            evidence=evidence,
            suggestion="Add type hints to reach 70% coverage. Focus on public APIs first.",
        )
    else:
        return CheckResult(
            passed=False,
            evidence=evidence,
            suggestion="Add type hints to top modules. Current coverage is below 40%.",
        )


@check(
    name="mypy_strictness",
    category="static_guardrails",
    description="Check if mypy is configured with strict mode",
    pillar="type_contracts",
    gate_level=4,
)
def check_mypy_strictness(repo_path: Path) -> CheckResult:
    """Check if mypy is configured with strict settings.

    Pass if:
    - mypy.ini or pyproject.toml contains strict = true
    - OR disallow_untyped_defs = true
    """
    # Check pyproject.toml
    pyproject = file_exists(repo_path, "pyproject.toml")
    if pyproject:
        content = read_file_safe(pyproject)
        if content and "[tool.mypy]" in content:
            # Use regex to handle variable whitespace (strict = true, strict=true, etc.)
            if re.search(r"strict\s*=\s*true", content, re.IGNORECASE):
                return CheckResult(
                    passed=True,
                    evidence=f"mypy strict mode enabled in {pyproject.name}",
                )
            if re.search(r"disallow_untyped_defs\s*=\s*true", content, re.IGNORECASE):
                return CheckResult(
                    passed=True,
                    evidence=f"mypy disallow_untyped_defs enabled in {pyproject.name}",
                )
            # mypy configured but not strict
            return CheckResult(
                passed=False,
                partial=True,
                evidence=f"mypy configured in {pyproject.name} but not strict",
                suggestion="Add 'strict = true' to [tool.mypy] in pyproject.toml",
            )

    # Check mypy.ini
    mypy_ini = file_exists(repo_path, "mypy.ini")
    if mypy_ini:
        content = read_file_safe(mypy_ini)
        if content:
            # Use regex to handle variable whitespace
            if re.search(r"strict\s*=\s*True", content, re.IGNORECASE):
                return CheckResult(
                    passed=True,
                    evidence="mypy strict mode enabled in mypy.ini",
                )
            if re.search(r"disallow_untyped_defs\s*=\s*True", content, re.IGNORECASE):
                return CheckResult(
                    passed=True,
                    evidence="mypy disallow_untyped_defs enabled in mypy.ini",
                )
            return CheckResult(
                passed=False,
                partial=True,
                evidence="mypy.ini exists but strict mode not enabled",
                suggestion="Add 'strict = True' to mypy.ini",
            )

    # Check setup.cfg
    setup_cfg = file_exists(repo_path, "setup.cfg")
    if setup_cfg:
        content = read_file_safe(setup_cfg)
        if content and "[mypy]" in content:
            # Use regex to handle variable whitespace
            if re.search(r"strict\s*=\s*True", content, re.IGNORECASE):
                return CheckResult(
                    passed=True,
                    evidence="mypy strict mode enabled in setup.cfg",
                )
            return CheckResult(
                passed=False,
                partial=True,
                evidence="mypy configured in setup.cfg but not strict",
                suggestion="Add 'strict = True' to [mypy] in setup.cfg",
            )

    # No mypy configuration found
    # Check if this is a Python project
    if not file_exists(repo_path, "pyproject.toml", "setup.py", "requirements.txt"):
        return CheckResult(
            passed=True,
            evidence="Not a Python project; mypy check not applicable.",
        )

    return CheckResult(
        passed=False,
        evidence="No mypy configuration found",
        suggestion="Add [tool.mypy] with 'strict = true' to pyproject.toml",
    )
