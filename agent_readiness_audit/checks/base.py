"""Base infrastructure for check implementations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias

from agent_readiness_audit.models import CheckResult as ModelCheckResult
from agent_readiness_audit.models import CheckStatus

# Registry of all checks
_CHECK_REGISTRY: dict[str, CheckDefinition] = {}


@dataclass
class CheckResult:
    """Result returned by individual check functions."""

    passed: bool
    evidence: str = ""
    suggestion: str = ""
    partial: bool = False  # True for PARTIAL status (between PASSED and FAILED)
    confidence: str = "HIGH"  # HIGH, MEDIUM, LOW for heuristic checks

    def to_model(
        self,
        name: str,
        category: str,
        pillar: str = "",
        weight: float = 1.0,
        gate_for: list[int] | None = None,
    ) -> ModelCheckResult:
        """Convert to model CheckResult."""
        if self.passed:
            status = CheckStatus.PASSED
        elif self.partial:
            status = CheckStatus.PARTIAL
        else:
            status = CheckStatus.FAILED

        return ModelCheckResult(
            name=name,
            category=category,
            pillar=pillar,
            status=status,
            evidence=self.evidence,
            suggestion=self.suggestion,
            weight=weight,
            gate_for=gate_for or [],
            confidence=self.confidence,
        )


@dataclass
class CheckDefinition:
    """Definition of a check including metadata."""

    name: str
    category: str
    description: str
    func: Callable[[Path], CheckResult]
    pillar: str = ""  # V2 pillar assignment
    weight: float = 1.0
    enabled: bool = True
    gate_for: list[int] = field(
        default_factory=list
    )  # Maturity levels this is a gate for


CheckFunc: TypeAlias = Callable[[Path], CheckResult]


def check(
    name: str,
    category: str,
    description: str,
    pillar: str = "",
    weight: float = 1.0,
    gate_for: list[int] | None = None,
) -> Callable[[CheckFunc], CheckFunc]:
    """Decorator to register a check function.

    Args:
        name: Unique identifier for the check.
        category: Category this check belongs to (v1 compatibility).
        description: Human-readable description of what the check verifies.
        pillar: V2 pillar this check belongs to.
        weight: Weight multiplier for scoring (default 1.0).
        gate_for: List of maturity levels this check is a gate for.

    Returns:
        Decorator function.
    """

    def decorator(func: CheckFunc) -> CheckFunc:
        _CHECK_REGISTRY[name] = CheckDefinition(
            name=name,
            category=category,
            description=description,
            func=func,
            pillar=pillar,
            weight=weight,
            gate_for=gate_for or [],
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


def get_checks_by_pillar(pillar: str) -> list[CheckDefinition]:
    """Get all checks for a specific pillar.

    Args:
        pillar: Pillar name to filter by.

    Returns:
        List of check definitions for the pillar.
    """
    return [c for c in _CHECK_REGISTRY.values() if c.pillar == pillar]


def get_gate_checks(level: int) -> list[CheckDefinition]:
    """Get all gate checks for a specific maturity level.

    Args:
        level: Maturity level (1-5).

    Returns:
        List of check definitions that are gates for the level.
    """
    return [c for c in _CHECK_REGISTRY.values() if level in c.gate_for]


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
            pillar=check_def.pillar,
            weight=check_def.weight,
            gate_for=check_def.gate_for,
        )
    except Exception as e:
        return ModelCheckResult(
            name=check_def.name,
            category=check_def.category,
            pillar=check_def.pillar,
            status=CheckStatus.UNKNOWN,
            evidence=f"Check failed with error: {e}",
            suggestion="Investigate the error and ensure the repository is accessible.",
            weight=check_def.weight,
            gate_for=check_def.gate_for,
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


def file_contains(
    file_path: Path, *patterns: str, case_sensitive: bool = False
) -> str | None:
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


def file_contains_any(
    repo_path: Path,
    filenames: list[str],
    patterns: list[str],
    case_sensitive: bool = False,
) -> tuple[Path | None, str | None]:
    """Check if any file contains any of the given patterns.

    Args:
        repo_path: Path to repository root.
        filenames: File names to search in.
        patterns: Patterns to search for.
        case_sensitive: Whether search should be case-sensitive.

    Returns:
        Tuple of (file path, matched pattern) or (None, None) if not found.
    """
    for filename in filenames:
        file_path = repo_path / filename
        if file_path.exists():
            matched = file_contains(file_path, *patterns, case_sensitive=case_sensitive)
            if matched:
                return file_path, matched
    return None, None


def glob_files(repo_path: Path, pattern: str, limit: int = 50) -> list[Path]:
    """Find files matching a glob pattern.

    Args:
        repo_path: Path to repository root.
        pattern: Glob pattern to match.
        limit: Maximum number of files to return.

    Returns:
        List of matching file paths.
    """
    return list(repo_path.glob(pattern))[:limit]


def read_toml_section(file_path: Path, section: str) -> dict | None:
    """Read a section from a TOML file.

    Args:
        file_path: Path to TOML file.
        section: Section name (e.g., "tool.ruff").

    Returns:
        Section contents as dict, or None if not found.
    """
    try:
        import tomllib

        content = file_path.read_text(encoding="utf-8")
        data = tomllib.loads(content)

        # Navigate to section
        parts = section.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current if isinstance(current, dict) else None
    except Exception:
        return None


def check_dependency_present(repo_path: Path, *package_names: str) -> str | None:
    """Check if any of the given packages are in dependencies.

    Args:
        repo_path: Path to repository root.
        *package_names: Package names to search for.

    Returns:
        First found package name, or None if none found.
    """
    # Check pyproject.toml
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore").lower()
        for pkg in package_names:
            if pkg.lower() in content:
                return pkg

    # Check requirements.txt
    requirements = repo_path / "requirements.txt"
    if requirements.exists():
        content = requirements.read_text(encoding="utf-8", errors="ignore").lower()
        for pkg in package_names:
            if pkg.lower() in content:
                return pkg

    # Check package.json
    package_json = repo_path / "package.json"
    if package_json.exists():
        content = package_json.read_text(encoding="utf-8", errors="ignore").lower()
        for pkg in package_names:
            if pkg.lower() in content:
                return pkg

    # Check Cargo.toml
    cargo_toml = repo_path / "Cargo.toml"
    if cargo_toml.exists():
        content = cargo_toml.read_text(encoding="utf-8", errors="ignore").lower()
        for pkg in package_names:
            if pkg.lower() in content:
                return pkg

    return None
