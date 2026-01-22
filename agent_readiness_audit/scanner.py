"""Main scanning logic for Agent Readiness Audit."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import get_all_checks, get_checks_by_category, run_check
from agent_readiness_audit.models import (
    AuditConfig,
    CategoryScore,
    CheckResult,
    RepoResult,
    ScanSummary,
    get_level_for_score,
)

# Category order for consistent output
CATEGORY_ORDER = [
    "discoverability",
    "deterministic_setup",
    "build_and_run",
    "test_feedback_loop",
    "static_guardrails",
    "observability",
    "ci_enforcement",
    "security_and_governance",
]

# Category descriptions
CATEGORY_DESCRIPTIONS = {
    "discoverability": "Repo orientation: README presence and basic onboarding clarity",
    "deterministic_setup": "Reproducible dependency setup and pinning",
    "build_and_run": "Standard commands exist for build/test/lint/format",
    "test_feedback_loop": "Tests exist and are runnable with reasonable defaults",
    "static_guardrails": "Linters/formatters/types reduce ambiguity for agents",
    "observability": "Logging/metrics help agents validate behavior changes",
    "ci_enforcement": "CI exists and validates changes",
    "security_and_governance": "Baseline hygiene around secrets and contribution policy",
}

# Fix-first priority mapping
FIX_FIRST_PRIORITIES = [
    ("discoverability", "add_or_improve_readme_setup_and_test"),
    ("deterministic_setup", "add_lockfile_or_pin_deps"),
    ("build_and_run", "add_makefile_or_task_runner_targets"),
    ("test_feedback_loop", "add_basic_test_harness"),
    ("static_guardrails", "add_lint_and_format"),
    ("ci_enforcement", "add_ci_workflow"),
    ("security_and_governance", "add_contributing_and_security_docs"),
]


def is_git_repo(path: Path) -> bool:
    """Check if a path is a git repository.

    Args:
        path: Path to check.

    Returns:
        True if path contains a .git directory.
    """
    return (path / ".git").is_dir()


def find_repos(
    root: Path,
    depth: int = 2,
    include_pattern: str | None = None,
    exclude_pattern: str | None = None,
) -> list[Path]:
    """Find git repositories under a root directory.

    Args:
        root: Root directory to search.
        depth: Maximum depth to search.
        include_pattern: Glob pattern to include.
        exclude_pattern: Glob pattern to exclude.

    Returns:
        List of paths to git repositories.
    """
    import fnmatch

    repos: list[Path] = []

    def search(path: Path, current_depth: int) -> None:
        if current_depth > depth:
            return

        if is_git_repo(path):
            # Check include/exclude patterns
            name = path.name
            if include_pattern and not fnmatch.fnmatch(name, include_pattern):
                return
            if exclude_pattern and fnmatch.fnmatch(name, exclude_pattern):
                return
            repos.append(path)
            return  # Don't search inside git repos

        if path.is_dir():
            try:
                for child in path.iterdir():
                    if child.is_dir() and not child.name.startswith("."):
                        search(child, current_depth + 1)
            except PermissionError:
                pass

    search(root, 0)
    return sorted(repos)


def scan_repo(repo_path: Path, config: AuditConfig) -> RepoResult:
    """Scan a single repository and return results.

    Args:
        repo_path: Path to repository to scan.
        config: Audit configuration.

    Returns:
        Audit result for the repository.
    """
    repo_path = repo_path.resolve()
    result = RepoResult(
        repo_path=str(repo_path),
        repo_name=repo_path.name,
    )

    # Initialize category scores
    for category in CATEGORY_ORDER:
        cat_config = config.categories.get(category)
        if cat_config and not cat_config.enabled:
            continue

        result.category_scores[category] = CategoryScore(
            name=category,
            description=CATEGORY_DESCRIPTIONS.get(category, ""),
            max_points=cat_config.max_points if cat_config else 2.0,
        )

    # Run all checks
    all_checks = get_all_checks()
    for check_name, check_def in all_checks.items():
        # Check if check is enabled
        check_config = config.checks.get(check_name)
        if check_config and not check_config.enabled:
            continue

        # Check if category is enabled
        cat_config = config.categories.get(check_def.category)
        if cat_config and not cat_config.enabled:
            continue

        # Run the check
        check_result = run_check(check_def, repo_path)

        # Apply weight override if configured
        if check_config:
            check_result.weight = check_config.weight

        # Add to category
        if check_def.category in result.category_scores:
            result.category_scores[check_def.category].checks.append(check_result)
            result.category_scores[check_def.category].total_checks += 1
            if check_result.passed:
                result.category_scores[check_def.category].passed_checks += 1
                result.passed_checks.append(check_result)
            else:
                result.failed_checks.append(check_result)

    # Calculate category scores
    for category, cat_score in result.category_scores.items():
        if cat_score.total_checks > 0:
            # Score is proportional to passed checks
            pass_ratio = cat_score.passed_checks / cat_score.total_checks
            cat_score.score = pass_ratio * cat_score.max_points

    # Calculate total score
    result.score_total = sum(cs.score for cs in result.category_scores.values())
    result.max_score = sum(cs.max_points for cs in result.category_scores.values())

    # Determine level
    result.level = get_level_for_score(result.score_total)

    # Generate fix-first recommendations
    result.fix_first = generate_fix_first(result)

    return result


def generate_fix_first(result: RepoResult) -> list[str]:
    """Generate fix-first recommendations based on failed checks.

    Args:
        result: Repository audit result.

    Returns:
        List of prioritized fix recommendations.
    """
    recommendations: list[str] = []

    for category, fix_name in FIX_FIRST_PRIORITIES:
        if category in result.category_scores:
            cat_score = result.category_scores[category]
            # If category has failures, add recommendation
            if cat_score.passed_checks < cat_score.total_checks:
                # Get specific suggestions from failed checks
                for check in cat_score.checks:
                    if not check.passed and check.suggestion:
                        if check.suggestion not in recommendations:
                            recommendations.append(check.suggestion)

    return recommendations[:7]  # Limit to top 7 recommendations


def scan_repos(
    paths: list[Path],
    config: AuditConfig,
) -> ScanSummary:
    """Scan multiple repositories and return summary.

    Args:
        paths: List of repository paths to scan.
        config: Audit configuration.

    Returns:
        Summary of all scan results.
    """
    summary = ScanSummary(
        config_used=str(config),
    )

    for path in paths:
        result = scan_repo(path, config)
        summary.repos.append(result)

    summary.calculate_summary()
    return summary
