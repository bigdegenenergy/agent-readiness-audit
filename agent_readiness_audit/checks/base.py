"""Base infrastructure for check implementations."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

from agent_readiness_audit.models import PILLAR_TO_CATEGORY, CheckStatus
from agent_readiness_audit.models import CheckResult as ModelCheckResult

# Configure logger for audit warnings
_logger = logging.getLogger("agent_readiness_audit")
if not _logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(logging.WARNING)

# Registry of all checks
_CHECK_REGISTRY: dict[str, CheckDefinition] = {}


@dataclass
class CheckResult:
    """Result returned by individual check functions."""

    passed: bool
    evidence: str = ""
    suggestion: str = ""
    partial: bool = False  # v2: for partial compliance

    def to_model(
        self,
        name: str,
        category: str,
        weight: float = 1.0,
        pillar: str = "",
        gate_level: int | None = None,
    ) -> ModelCheckResult:
        """Convert to model CheckResult."""
        if self.partial:
            status = CheckStatus.PARTIAL
        elif self.passed:
            status = CheckStatus.PASSED
        else:
            status = CheckStatus.FAILED

        return ModelCheckResult(
            name=name,
            category=category,
            status=status,
            evidence=self.evidence,
            suggestion=self.suggestion,
            weight=weight,
            pillar=pillar,
            gate_level=gate_level,
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
    pillar: str = ""  # v2: which pillar this check belongs to
    gate_level: int | None = None  # v2: if set, this is a gate for that level


CheckFunc: TypeAlias = Callable[[Path], CheckResult]


def check(
    name: str,
    category: str,
    description: str,
    weight: float = 1.0,
    pillar: str = "",
    gate_level: int | None = None,
) -> Callable[[CheckFunc], CheckFunc]:
    """Decorator to register a check function.

    Args:
        name: Unique identifier for the check.
        category: Category this check belongs to (v1 compatibility).
        description: Human-readable description of what the check verifies.
        weight: Weight multiplier for scoring (default 1.0).
        pillar: v2 pillar this check belongs to. If not provided,
                derived from category mapping.
        gate_level: If set, this check is a gate for that maturity level.

    Returns:
        Decorator function.
    """
    # Derive category from pillar if pillar provided but no category
    effective_category = category
    effective_pillar = pillar

    # If pillar not provided, try to infer from category
    if not effective_pillar and effective_category:
        # Reverse lookup - not ideal but maintains compatibility
        effective_pillar = effective_category

    # If pillar provided, ensure category is set for v1 compatibility
    if effective_pillar and not effective_category:
        effective_category = PILLAR_TO_CATEGORY.get(effective_pillar, effective_pillar)

    def decorator(func: CheckFunc) -> CheckFunc:
        _CHECK_REGISTRY[name] = CheckDefinition(
            name=name,
            category=effective_category,
            description=description,
            func=func,
            weight=weight,
            pillar=effective_pillar,
            gate_level=gate_level,
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
        level: Maturity level (3, 4, or 5).

    Returns:
        List of check definitions that are gates for that level.
    """
    return [c for c in _CHECK_REGISTRY.values() if c.gate_level == level]


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
            pillar=check_def.pillar,
            gate_level=check_def.gate_level,
        )
    except Exception as e:
        return ModelCheckResult(
            name=check_def.name,
            category=check_def.category,
            status=CheckStatus.UNKNOWN,
            evidence=f"Check failed with error: {e}",
            suggestion="Investigate the error and ensure the repository is accessible.",
            weight=check_def.weight,
            pillar=check_def.pillar,
            gate_level=check_def.gate_level,
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


def glob_files(repo_path: Path, pattern: str) -> list[Path]:
    """Find files matching a glob pattern.

    Args:
        repo_path: Path to repository root.
        pattern: Glob pattern to match.

    Returns:
        List of matching file paths.
    """
    return list(repo_path.glob(pattern))


def read_file_safe(file_path: Path, max_size: int = 1_000_000) -> str | None:
    """Safely read a file with size limit.

    Args:
        file_path: Path to file to read.
        max_size: Maximum file size in bytes to read.

    Returns:
        File contents or None if file doesn't exist, is too large, or unreadable.

    Note:
        Permission errors and other read failures are logged as warnings to stderr.
    """
    try:
        if not file_path.exists():
            return None
        if file_path.stat().st_size > max_size:
            _logger.debug("Skipping large file (>%d bytes): %s", max_size, file_path)
            return None
        return file_path.read_text(encoding="utf-8", errors="ignore")
    except PermissionError:
        _logger.warning("Permission denied reading file: %s", file_path)
        return None
    except OSError as e:
        _logger.warning("Cannot read file %s: %s", file_path, e)
        return None
    except Exception as e:
        _logger.warning("Unexpected error reading file %s: %s", file_path, e)
        return None
