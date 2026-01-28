"""Documentation structure checks for v2 agent readiness."""

from __future__ import annotations

import ast
from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    dir_exists,
    glob_files,
    read_file_safe,
)


@check(
    name="diataxis_structure",
    category="discoverability",
    description="Check for Diataxis-style documentation structure",
    pillar="documentation_structure",
)
def check_diataxis_structure(repo_path: Path) -> CheckResult:
    """Check if docs follow Diataxis framework structure.

    Diataxis recommends four types of documentation:
    - Tutorials (learning-oriented)
    - How-to guides (task-oriented)
    - Reference (information-oriented)
    - Explanation (understanding-oriented)

    Pass if docs/ contains 3+ of these categories.
    """
    docs_dir = dir_exists(repo_path, "docs", "doc", "documentation")
    if not docs_dir:
        return CheckResult(
            passed=False,
            evidence="No docs/ directory found",
            suggestion="Create docs/ with Diataxis structure: tutorials/, how-to/, reference/, explanation/",
        )

    # Check for Diataxis-style directories or files
    diataxis_patterns = {
        "tutorials": ["tutorial", "tutorials", "getting-started", "quickstart"],
        "how-to": ["how-to", "howto", "guides", "guide", "recipes"],
        "reference": ["reference", "api", "api-reference", "specification"],
        "explanation": [
            "explanation",
            "concepts",
            "architecture",
            "design",
            "background",
        ],
    }

    found_categories: list[str] = []

    for category, patterns in diataxis_patterns.items():
        for pattern in patterns:
            # Check for directories
            if dir_exists(docs_dir, pattern):
                found_categories.append(category)
                break
            # Check for files
            for ext in [".md", ".rst", ".txt"]:
                if (docs_dir / f"{pattern}{ext}").exists():
                    found_categories.append(category)
                    break
        if category in found_categories:
            continue

    # Also check subdirectories of docs
    if docs_dir.is_dir():
        for subdir in docs_dir.iterdir():
            if subdir.is_dir():
                name = subdir.name.lower()
                for category, patterns in diataxis_patterns.items():
                    if category not in found_categories and any(
                        p in name for p in patterns
                    ):
                        found_categories.append(category)
                        break

    found_categories = list(set(found_categories))

    if len(found_categories) >= 3:
        return CheckResult(
            passed=True,
            evidence=f"Diataxis structure detected: {', '.join(found_categories)}",
        )
    elif len(found_categories) >= 1:
        return CheckResult(
            passed=False,
            partial=True,
            evidence=f"Partial Diataxis structure: {', '.join(found_categories)}",
            suggestion="Add more doc categories: tutorials/, how-to/, reference/, explanation/",
        )
    else:
        return CheckResult(
            passed=False,
            evidence="docs/ exists but lacks Diataxis structure",
            suggestion="Organize docs into: tutorials/, how-to/, reference/, explanation/",
        )


def _count_docstrings(file_path: Path) -> tuple[int, int]:
    """Count total and documented functions/classes in a Python file.

    Args:
        file_path: Path to Python file.

    Returns:
        Tuple of (total_items, documented_items).
    """
    content = read_file_safe(file_path)
    if not content:
        return 0, 0

    try:
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError:
        return 0, 0

    total = 0
    documented = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            total += 1
            # Check for docstring
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                documented += 1

    return total, documented


@check(
    name="docstring_coverage_python",
    category="discoverability",
    description="Check docstring coverage in Python source files",
    pillar="inline_documentation",
)
def check_docstring_coverage_python(repo_path: Path) -> CheckResult:
    """Check docstring coverage in Python files.

    Pass if >= 60% of functions/classes have docstrings.
    Partial if 30-59%.
    """
    # Check if interrogate is configured (preferred)
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = read_file_safe(pyproject)
        if content and "[tool.interrogate]" in content:
            return CheckResult(
                passed=True,
                evidence="interrogate docstring linter configured in pyproject.toml",
            )

    # Manual AST scan
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

    filtered_files = []
    for f in py_files:
        rel_path = str(f.relative_to(repo_path))
        if not any(excl in rel_path for excl in exclude_patterns):
            filtered_files.append(f)

    if not filtered_files:
        return CheckResult(
            passed=True,
            evidence="No Python source files found to check.",
        )

    total_items = 0
    documented_items = 0
    files_without_docs: list[tuple[str, int, int]] = []

    for py_file in filtered_files:
        total, documented = _count_docstrings(py_file)
        total_items += total
        documented_items += documented
        if total > 0 and documented < total:
            rel_path = str(py_file.relative_to(repo_path))
            files_without_docs.append((rel_path, documented, total))

    if total_items == 0:
        return CheckResult(
            passed=True,
            evidence="No functions/classes found in source files.",
        )

    coverage = (documented_items / total_items) * 100

    files_without_docs.sort(key=lambda x: x[2] - x[1], reverse=True)
    top_missing = files_without_docs[:5]

    evidence_parts = [
        f"Docstring coverage: {coverage:.1f}%",
        f"({documented_items}/{total_items} items documented)",
    ]

    if top_missing:
        evidence_parts.append(
            "Files needing docs: " + ", ".join(f[0] for f in top_missing)
        )

    evidence = " ".join(evidence_parts)

    if coverage >= 60:
        return CheckResult(
            passed=True,
            evidence=evidence,
        )
    elif coverage >= 30:
        return CheckResult(
            passed=False,
            partial=True,
            evidence=evidence,
            suggestion="Add docstrings to reach 60% coverage. Focus on public APIs.",
        )
    else:
        return CheckResult(
            passed=False,
            evidence=evidence,
            suggestion="Add docstrings to functions and classes. Coverage is below 30%.",
        )


@check(
    name="contributing_exists",
    category="security_and_governance",
    description="Check for CONTRIBUTING.md",
    pillar="contribution_contract",
)
def check_contributing_exists(repo_path: Path) -> CheckResult:
    """Check if CONTRIBUTING.md exists."""
    contributing = repo_path / "CONTRIBUTING.md"
    if contributing.exists():
        return CheckResult(
            passed=True,
            evidence="CONTRIBUTING.md found",
        )

    # Check alternate locations
    if (repo_path / ".github" / "CONTRIBUTING.md").exists():
        return CheckResult(
            passed=True,
            evidence=".github/CONTRIBUTING.md found",
        )

    if (repo_path / "docs" / "CONTRIBUTING.md").exists():
        return CheckResult(
            passed=True,
            evidence="docs/CONTRIBUTING.md found",
        )

    return CheckResult(
        passed=False,
        evidence="CONTRIBUTING.md not found",
        suggestion="Add CONTRIBUTING.md with development workflow and guidelines.",
    )
