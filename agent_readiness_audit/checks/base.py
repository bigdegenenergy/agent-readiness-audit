"""Base infrastructure for check implementations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, TypeAlias

from agent_readiness_audit.models import CheckResult as ModelCheckResult
from agent_readiness_audit.models import CheckStatus

# Registry of all checks
_CHECK_REGISTRY: dict[str, "CheckDefinition"] = {}


@dataclass
class CheckResult:
    """Result returned by individual check functions."""

    passed: bool
    evidence: str = ""
    suggestion: str = ""

    def to_model(self, name: str, category: str, weight: float = 1.0) -> ModelCheckResult:
        """Convert to model CheckResult."""
        return ModelCheckResult(
            name=name,
            category=category,
            status=CheckStatus.PASSED if self.passed else CheckStatus.FAILED,
            evidence=self.evidence,
            suggestion=self.suggestion,
            weight=weight,
        )


@dataclass
class CheckDefinition:
    """Definition of a check including metadata."""

    name: str
    category: str
    description: str
    func: Callable[[Path], CheckResult]
    weight: float = 1.0
    enabled: bool = True


CheckFunc: TypeAlias = Callable[[Path], CheckResult]


def check(
    name: str,
    category: str,
    description: str,
    weight: float = 1.0,
) -> Callable[[CheckFunc], CheckFunc]:
    """Decorator to register a check function.

    Args:
        name: Unique identifier for the check.
        category: Category this check belongs to.
        description: Human-readable description of what the check verifies.
        weight: Weight multiplier for scoring (default 1.0).

    Returns:
        Decorator function.
    """

    def decorator(func: CheckFunc) -> CheckFunc:
        _CHECK_REGISTRY[name] = CheckDefinition(
            name=name,
            category=category,
            description=description,
            func=func,
            weight=weight,
        )
        return func

    return decorator


def get_all_checks() -> dict[str, CheckDefinition]:
    """Get all registered checks.

    Returns:
        Dictionary mapping check names to their definitions.
    """
    return _CHECK_REGISTRY.copy()


def get_checks_by_category(category: str) -> list[CheckDefinition]:
    """Get all checks for a specific category.

    Args:
        category: Category name to filter by.

    Returns:
        List of check definitions for the category.
    """
    return [c for c in _CHECK_REGISTRY.values() if c.category == category]


def run_check(check_def: CheckDefinition, repo_path: Path) -> ModelCheckResult:
    """Run a single check and return the result.

    Args:
        check_def: Check definition to execute.
        repo_path: Path to repository to check.

    Returns:
        Check result as model object.
    """
    try:
        result = check_def.func(repo_path)
        return result.to_model(
            name=check_def.name,
            category=check_def.category,
            weight=check_def.weight,
        )
    except Exception as e:
        return ModelCheckResult(
            name=check_def.name,
            category=check_def.category,
            status=CheckStatus.UNKNOWN,
            evidence=f"Check failed with error: {e}",
            suggestion="Investigate the error and ensure the repository is accessible.",
            weight=check_def.weight,
        )


# Utility functions for checks


def file_exists(repo_path: Path, *filenames: str) -> Path | None:
    """Check if any of the given files exist in the repo.

    Args:
        repo_path: Path to repository root.
        *filenames: File names or paths to check.

    Returns:
        Path to first found file, or None if none found.
    """
    for filename in filenames:
        path = repo_path / filename
        if path.exists():
            return path
    return None


def dir_exists(repo_path: Path, *dirnames: str) -> Path | None:
    """Check if any of the given directories exist in the repo.

    Args:
        repo_path: Path to repository root.
        *dirnames: Directory names or paths to check.

    Returns:
        Path to first found directory, or None if none found.
    """
    for dirname in dirnames:
        path = repo_path / dirname
        if path.is_dir():
            return path
    return None


def file_contains(file_path: Path, *patterns: str, case_sensitive: bool = False) -> str | None:
    """Check if file contains any of the given patterns.

    Args:
        file_path: Path to file to search.
        *patterns: Patterns to search for.
        case_sensitive: Whether search should be case-sensitive.

    Returns:
        First matching pattern found, or None if none found.
    """
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if not case_sensitive:
            content = content.lower()

        for pattern in patterns:
            search_pattern = pattern if case_sensitive else pattern.lower()
            if search_pattern in content:
                return pattern
        return None
    except Exception:
        return None


def glob_files(repo_path: Path, pattern: str) -> list[Path]:
    """Find files matching a glob pattern.

    Args:
        repo_path: Path to repository root.
        pattern: Glob pattern to match.

    Returns:
        List of matching file paths.
    """
    return list(repo_path.glob(pattern))
