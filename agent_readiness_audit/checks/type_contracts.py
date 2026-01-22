"""Type contracts checks - type hint coverage and strictness configuration."""

from __future__ import annotations

import ast
from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    check_dependency_present,
    file_contains,
    file_exists,
    glob_files,
    read_toml_section,
)

# Directories to exclude from type hint scanning
EXCLUDED_DIRS = {
    "tests",
    "test",
    "__tests__",
    "migrations",
    "vendor",
    "third_party",
    "node_modules",
    ".venv",
    "venv",
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".tox",
    ".nox",
}


def _count_type_hints_in_file(file_path: Path) -> tuple[int, int]:
    """Count functions with/without type hints in a Python file.

    Args:
        file_path: Path to Python file.

    Returns:
        Tuple of (total_functions, annotated_functions).
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
    except (SyntaxError, ValueError):
        return 0, 0

    total_funcs = 0
    annotated_funcs = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip private/dunder methods except __init__
            if node.name.startswith("_") and node.name != "__init__":
                continue

            total_funcs += 1

            # Check for any annotation (return or args)
            has_annotation = False

            # Check return annotation
            if node.returns is not None:
                has_annotation = True

            # Check argument annotations
            if not has_annotation:
                for arg in (
                    node.args.args + node.args.posonlyargs + node.args.kwonlyargs
                ):
                    if arg.annotation is not None:
                        has_annotation = True
                        break

            if has_annotation:
                annotated_funcs += 1

    return total_funcs, annotated_funcs


def _should_exclude_path(path: Path) -> bool:
    """Check if path should be excluded from scanning."""
    return any(part in EXCLUDED_DIRS for part in path.parts)


@check(
    name="python_type_hint_coverage",
    category="static_guardrails",
    description="Check type hint coverage percentage in Python code",
    pillar="type_contracts",
    weight=1.5,
    gate_for=[4, 5],
)
def check_python_type_hint_coverage(repo_path: Path) -> CheckResult:
    """Check type hint coverage in Python files.

    Level 4 requires ≥70% coverage.
    Level 5 requires ≥85% coverage.
    """
    # Find all Python files, excluding test/vendor directories
    py_files = glob_files(repo_path, "**/*.py", limit=500)
    py_files = [
        f for f in py_files if not _should_exclude_path(f.relative_to(repo_path))
    ]

    if not py_files:
        # No Python files - check if this is a Python project
        pyproject = repo_path / "pyproject.toml"
        if not pyproject.exists():
            return CheckResult(
                passed=True,
                evidence="No Python files found (non-Python project)",
                confidence="MEDIUM",
            )
        return CheckResult(
            passed=False,
            evidence="Python project detected but no .py files found in source directories",
            suggestion="Add Python source files with type hints.",
        )

    total_functions = 0
    annotated_functions = 0
    files_missing_hints: list[tuple[Path, int, int]] = []

    for py_file in py_files:
        total, annotated = _count_type_hints_in_file(py_file)
        total_functions += total
        annotated_functions += annotated

        # Track files with low coverage
        if total > 0 and annotated < total:
            files_missing_hints.append(
                (py_file.relative_to(repo_path), total - annotated, total)
            )

    if total_functions == 0:
        return CheckResult(
            passed=True,
            evidence="No public functions found to check",
            confidence="MEDIUM",
        )

    coverage_pct = (annotated_functions / total_functions) * 100

    # Sort by most missing hints
    files_missing_hints.sort(key=lambda x: x[1], reverse=True)
    top_missing = files_missing_hints[:5]
    missing_summary = ", ".join(f"{f[0]}({f[1]}/{f[2]})" for f in top_missing)

    evidence = (
        f"Type hint coverage: {coverage_pct:.1f}% "
        f"({annotated_functions}/{total_functions} functions). "
        f"Files needing hints: {missing_summary or 'none'}"
    )

    if coverage_pct >= 85:
        return CheckResult(
            passed=True,
            evidence=evidence,
        )
    elif coverage_pct >= 70:
        return CheckResult(
            passed=True,
            partial=True,
            evidence=evidence + " (L4 threshold met, L5 requires ≥85%)",
            suggestion="Add type hints to reach 85% coverage for Level 5.",
        )
    else:
        return CheckResult(
            passed=False,
            evidence=evidence,
            suggestion=f"Add type hints to public functions. Target: ≥70% for Level 4, ≥85% for Level 5. Current: {coverage_pct:.1f}%.",
        )


@check(
    name="mypy_strictness",
    category="static_guardrails",
    description="Check if mypy is configured with strict settings",
    pillar="type_contracts",
    weight=1.0,
)
def check_mypy_strictness(repo_path: Path) -> CheckResult:
    """Check if mypy has strict configuration."""
    # Check pyproject.toml for mypy config
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        mypy_section = read_toml_section(pyproject, "tool.mypy")
        if mypy_section:
            strict = mypy_section.get("strict", False)
            disallow_untyped = mypy_section.get("disallow_untyped_defs", False)

            if strict is True:
                return CheckResult(
                    passed=True,
                    evidence="mypy configured with strict=true in pyproject.toml",
                )
            if disallow_untyped is True:
                return CheckResult(
                    passed=True,
                    evidence="mypy configured with disallow_untyped_defs=true in pyproject.toml",
                )
            return CheckResult(
                passed=False,
                partial=True,
                evidence="mypy configured but strict mode not enabled",
                suggestion="Enable strict=true or disallow_untyped_defs=true in [tool.mypy].",
            )

    # Check mypy.ini
    mypy_ini = file_exists(repo_path, "mypy.ini", ".mypy.ini")
    if mypy_ini:
        if file_contains(mypy_ini, "strict = true", "strict=true", "strict=True"):
            return CheckResult(
                passed=True,
                evidence=f"mypy configured with strict mode in {mypy_ini.name}",
            )
        if file_contains(
            mypy_ini,
            "disallow_untyped_defs = true",
            "disallow_untyped_defs=true",
            "disallow_untyped_defs=True",
        ):
            return CheckResult(
                passed=True,
                evidence=f"mypy configured with disallow_untyped_defs in {mypy_ini.name}",
            )
        return CheckResult(
            passed=False,
            partial=True,
            evidence=f"mypy configured via {mypy_ini.name} but strict mode not detected",
            suggestion="Enable strict=true or disallow_untyped_defs=true in mypy config.",
        )

    # Check setup.cfg
    setup_cfg = repo_path / "setup.cfg"
    if setup_cfg.exists() and file_contains(setup_cfg, "[mypy]"):
        if file_contains(setup_cfg, "strict = true", "strict=true"):
            return CheckResult(
                passed=True,
                evidence="mypy configured with strict mode in setup.cfg",
            )
        if file_contains(
            setup_cfg, "disallow_untyped_defs = true", "disallow_untyped_defs=true"
        ):
            return CheckResult(
                passed=True,
                evidence="mypy configured with disallow_untyped_defs in setup.cfg",
            )

    # Check if mypy is even configured
    has_mypy = check_dependency_present(repo_path, "mypy")
    if has_mypy:
        return CheckResult(
            passed=False,
            partial=True,
            evidence="mypy in dependencies but no strict configuration found",
            suggestion="Add [tool.mypy] to pyproject.toml with strict=true.",
        )

    return CheckResult(
        passed=False,
        evidence="No mypy configuration found",
        suggestion="Add mypy with strict=true to enforce type checking.",
    )
