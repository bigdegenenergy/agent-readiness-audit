"""Documentation structure checks - Diátaxis structure and docstring coverage."""

from __future__ import annotations

import ast
from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    check_dependency_present,
    dir_exists,
    file_exists,
    glob_files,
)

# Diátaxis documentation structure categories
DIATAXIS_CATEGORIES = {
    "tutorials": ["tutorials", "tutorial", "getting-started", "quickstart"],
    "how-to": ["how-to", "howto", "guides", "guide", "recipes"],
    "reference": ["reference", "api", "api-reference"],
    "explanation": ["explanation", "concepts", "background", "architecture"],
}

# Directories to exclude from docstring scanning
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
}


def _should_exclude_path(path: Path) -> bool:
    """Check if path should be excluded from scanning."""
    return any(part in EXCLUDED_DIRS for part in path.parts)


def _count_docstrings_in_file(file_path: Path) -> tuple[int, int]:
    """Count public functions/classes with/without docstrings.

    Args:
        file_path: Path to Python file.

    Returns:
        Tuple of (total_items, items_with_docstrings).
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
    except (SyntaxError, ValueError):
        return 0, 0

    total = 0
    with_docstring = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Skip private items (except __init__)
            if node.name.startswith("_") and node.name != "__init__":
                continue

            total += 1

            # Check for docstring
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                with_docstring += 1

    return total, with_docstring


@check(
    name="diataxis_structure",
    category="discoverability",
    description="Check if documentation follows Diátaxis structure",
    pillar="documentation_structure",
    weight=1.0,
)
def check_diataxis_structure(repo_path: Path) -> CheckResult:
    """Check if docs follow Diátaxis pattern."""
    docs_dir = dir_exists(repo_path, "docs", "doc", "documentation")

    if not docs_dir:
        # Check if there's a mkdocs.yml or similar
        mkdocs = file_exists(repo_path, "mkdocs.yml", "mkdocs.yaml")
        if mkdocs:
            return CheckResult(
                passed=True,
                partial=True,
                evidence="MkDocs configured but no docs/ directory found",
                suggestion="Create docs/ with Diátaxis structure (tutorials/, how-to/, reference/, explanation/).",
            )

        # Check if there's a sphinx conf.py
        sphinx_conf = file_exists(repo_path, "docs/conf.py", "doc/conf.py")
        if sphinx_conf:
            return CheckResult(
                passed=True,
                partial=True,
                evidence="Sphinx configured",
                suggestion="Organize docs using Diátaxis structure.",
            )

        return CheckResult(
            passed=False,
            evidence="No documentation directory found",
            suggestion="Create docs/ directory with Diátaxis structure (tutorials/, how-to/, reference/, explanation/).",
        )

    # Check for Diátaxis categories
    found_categories: list[str] = []

    # Check subdirectories
    if docs_dir.is_dir():
        subdirs = {d.name.lower() for d in docs_dir.iterdir() if d.is_dir()}

        for category, patterns in DIATAXIS_CATEGORIES.items():
            for pattern in patterns:
                if pattern in subdirs:
                    found_categories.append(category)
                    break

        # Also check for files that match category names
        files = {f.stem.lower() for f in docs_dir.iterdir() if f.is_file()}
        for category, patterns in DIATAXIS_CATEGORIES.items():
            if category not in found_categories:
                for pattern in patterns:
                    if pattern in files or any(pattern in f for f in files):
                        found_categories.append(category)
                        break

    # Also check for index files that might reference these
    index_files = glob_files(docs_dir, "*.md") + glob_files(docs_dir, "*.rst")
    for index_file in index_files[:5]:  # Check first 5 files
        try:
            content = index_file.read_text(encoding="utf-8", errors="ignore").lower()
            for category, patterns in DIATAXIS_CATEGORIES.items():
                if category not in found_categories:
                    for pattern in patterns:
                        if pattern in content:
                            found_categories.append(category)
                            break
        except Exception:
            continue

    found_categories = list(set(found_categories))

    if len(found_categories) >= 3:
        return CheckResult(
            passed=True,
            evidence=f"Diátaxis structure detected: {', '.join(found_categories)}",
        )
    elif len(found_categories) >= 2:
        return CheckResult(
            passed=True,
            partial=True,
            evidence=f"Partial Diátaxis structure: {', '.join(found_categories)}",
            suggestion=f"Add missing categories. Found: {found_categories}. Consider adding: tutorials, how-to, reference, explanation.",
        )
    elif len(found_categories) >= 1:
        return CheckResult(
            passed=False,
            partial=True,
            evidence=f"Minimal documentation structure: {', '.join(found_categories)}",
            suggestion="Expand docs with Diátaxis structure (tutorials/, how-to/, reference/, explanation/).",
        )

    # Has docs but no structure
    doc_files = glob_files(docs_dir, "*.md") + glob_files(docs_dir, "*.rst")
    if doc_files:
        return CheckResult(
            passed=False,
            partial=True,
            evidence=f"Found {len(doc_files)} doc files but no Diátaxis structure",
            suggestion="Organize docs into tutorials/, how-to/, reference/, explanation/.",
        )

    return CheckResult(
        passed=False,
        evidence="Documentation directory exists but is empty or unstructured",
        suggestion="Add documentation with Diátaxis structure.",
    )


@check(
    name="docstring_coverage_python",
    category="discoverability",
    description="Check docstring coverage for public APIs",
    pillar="inline_documentation",
    weight=1.0,
)
def check_docstring_coverage_python(repo_path: Path) -> CheckResult:
    """Check docstring coverage on public functions and classes."""
    # First check if interrogate is configured (preferred)
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        from agent_readiness_audit.checks.base import read_toml_section

        interrogate_section = read_toml_section(pyproject, "tool.interrogate")
        if interrogate_section:
            fail_under = interrogate_section.get("fail-under", 0)
            return CheckResult(
                passed=True,
                evidence=f"Interrogate configured with fail-under={fail_under}%",
            )

    # Check if interrogate is in dependencies
    has_interrogate = check_dependency_present(repo_path, "interrogate")
    if has_interrogate:
        return CheckResult(
            passed=True,
            evidence="Interrogate found in dependencies (docstring coverage enforced)",
        )

    # Fall back to AST-based scanning
    py_files = glob_files(repo_path, "**/*.py", limit=500)
    py_files = [
        f for f in py_files if not _should_exclude_path(f.relative_to(repo_path))
    ]

    if not py_files:
        # Check if this is a Python project
        if not pyproject.exists():
            return CheckResult(
                passed=True,
                evidence="No Python files found (non-Python project)",
                confidence="MEDIUM",
            )
        return CheckResult(
            passed=False,
            evidence="Python project detected but no .py files found",
            suggestion="Add Python source files with docstrings.",
        )

    total_items = 0
    documented_items = 0
    files_missing_docs: list[tuple[Path, int, int]] = []

    for py_file in py_files:
        total, documented = _count_docstrings_in_file(py_file)
        total_items += total
        documented_items += documented

        if total > 0 and documented < total:
            files_missing_docs.append(
                (py_file.relative_to(repo_path), total - documented, total)
            )

    if total_items == 0:
        return CheckResult(
            passed=True,
            evidence="No public functions/classes found to document",
            confidence="MEDIUM",
        )

    coverage_pct = (documented_items / total_items) * 100

    # Sort by most missing docs
    files_missing_docs.sort(key=lambda x: x[1], reverse=True)
    top_missing = files_missing_docs[:5]
    missing_summary = ", ".join(f"{f[0]}({f[1]}/{f[2]})" for f in top_missing)

    evidence = (
        f"Docstring coverage: {coverage_pct:.1f}% "
        f"({documented_items}/{total_items} items). "
        f"Files needing docs: {missing_summary or 'none'}"
    )

    if coverage_pct >= 80:
        return CheckResult(
            passed=True,
            evidence=evidence,
        )
    elif coverage_pct >= 50:
        return CheckResult(
            passed=True,
            partial=True,
            evidence=evidence,
            suggestion="Add docstrings to more public APIs. Target: ≥80% for best agent experience.",
        )
    else:
        return CheckResult(
            passed=False,
            evidence=evidence,
            suggestion=f"Add docstrings to public functions/classes. Current: {coverage_pct:.1f}%. Target: ≥50%.",
        )
