"""Main scanning logic for Agent Readiness Audit."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    get_all_checks,
    run_check,
)
from agent_readiness_audit.models import (
    PILLAR_INFO,
    AuditConfig,
    CategoryScore,
    Pillar,
    PillarScore,
    RepoResult,
    ScanSummary,
    calculate_maturity_level,
    get_level_for_score,
    get_maturity_info,
)

# Category order for consistent output (v1 compatibility)
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

# Category descriptions (v1 compatibility)
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

# Category to pillar mapping (v1 -> v2)
CATEGORY_TO_PILLAR: dict[str, list[str]] = {
    "discoverability": [Pillar.DISTRIBUTION_DX.value],
    "deterministic_setup": [Pillar.ENVIRONMENT_DETERMINISM.value],
    "build_and_run": [Pillar.FAST_GUARDRAILS.value, Pillar.DISTRIBUTION_DX.value],
    "test_feedback_loop": [
        Pillar.VERIFICATION_TRUST.value,
        Pillar.VERIFICATION_SPEED.value,
    ],
    "static_guardrails": [Pillar.FAST_GUARDRAILS.value, Pillar.TYPE_CONTRACTS.value],
    "observability": [Pillar.STRUCTURED_LOGGING_COST.value],
    "ci_enforcement": [Pillar.VERIFICATION_TRUST.value],
    "security_and_governance": [Pillar.SECRET_HYGIENE.value],
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

    # Initialize category scores (v1 compatibility)
    for category in CATEGORY_ORDER:
        cat_config = config.categories.get(category)
        if cat_config and not cat_config.enabled:
            continue

        result.category_scores[category] = CategoryScore(
            name=category,
            description=CATEGORY_DESCRIPTIONS.get(category, ""),
            max_points=cat_config.max_points if cat_config else 2.0,
        )

    # Initialize pillar scores (v2)
    for pillar in Pillar:
        if pillar.value in config.ignore.pillars:
            continue
        info = PILLAR_INFO.get(pillar, {})
        result.pillar_scores[pillar.value] = PillarScore(
            pillar=pillar.value,
            name=info.get("name", pillar.value),
            description=info.get("description", ""),
        )

    # Run all checks
    all_checks = get_all_checks()
    for check_name, check_def in all_checks.items():
        # Check if check is ignored
        if check_name in config.ignore.checks:
            continue

        # Check if check is enabled
        check_config = config.checks.get(check_name)
        if check_config and not check_config.enabled:
            continue

        # Check if category is enabled
        cat_config = config.categories.get(check_def.category)
        if cat_config and not cat_config.enabled:
            continue

        # Check if pillar is ignored
        if check_def.pillar and check_def.pillar in config.ignore.pillars:
            continue

        # Run the check
        check_result = run_check(check_def, repo_path)

        # Apply weight override if configured
        if check_config:
            check_result.weight = check_config.weight

        # Store in all_checks dict for gate calculation
        result.all_checks[check_name] = check_result

        # Add to category (v1 compatibility)
        if check_def.category in result.category_scores:
            result.category_scores[check_def.category].checks.append(check_result)
            result.category_scores[check_def.category].total_checks += 1
            if check_result.passed:
                result.category_scores[check_def.category].passed_checks += 1
                result.passed_checks.append(check_result)
            else:
                result.failed_checks.append(check_result)

        # Add to pillar (v2)
        pillar_key = check_def.pillar or _get_pillar_for_category(check_def.category)
        if pillar_key and pillar_key in result.pillar_scores:
            result.pillar_scores[pillar_key].checks.append(check_name)
            result.pillar_scores[pillar_key].total_checks += 1
            if check_result.passed:
                result.pillar_scores[pillar_key].passed_checks += 1

    # Calculate category scores (v1 compatibility)
    for _category, cat_score in result.category_scores.items():
        if cat_score.total_checks > 0:
            # Score is proportional to passed checks (including partial)
            total_score = sum(c.score for c in cat_score.checks)
            pass_ratio = total_score / cat_score.total_checks
            cat_score.score = pass_ratio * cat_score.max_points

    # Calculate pillar scores (v2)
    for _pillar, pillar_score in result.pillar_scores.items():
        if pillar_score.total_checks > 0:
            pass_ratio = pillar_score.passed_checks / pillar_score.total_checks
            pillar_score.score = pass_ratio * pillar_score.max_score

    # Calculate total score (from categories for v1 compatibility)
    result.score_total = sum(cs.score for cs in result.category_scores.values())
    result.max_score = sum(cs.max_points for cs in result.category_scores.values())

    # Determine v1 level
    result.level = get_level_for_score(result.score_total)

    # Determine v2 maturity level and gates
    maturity_level, gates = calculate_maturity_level(
        result.score_total, result.all_checks
    )
    result.maturity_level = maturity_level.value
    result.maturity_info = get_maturity_info(maturity_level)
    result.gates = gates

    # Generate fix-first recommendations
    result.fix_first = generate_fix_first(result)

    return result


def _get_pillar_for_category(category: str) -> str | None:
    """Get the primary pillar for a v1 category.

    Args:
        category: V1 category name.

    Returns:
        Primary pillar name, or None if not mapped.
    """
    pillars = CATEGORY_TO_PILLAR.get(category, [])
    return pillars[0] if pillars else None


def generate_fix_first(result: RepoResult) -> list[str]:
    """Generate fix-first recommendations based on failed checks.

    Prioritizes:
    1. Gate check failures for the next maturity level
    2. Category failures in priority order

    Args:
        result: Repository audit result.

    Returns:
        List of prioritized fix recommendations.
    """
    recommendations: list[str] = []
    seen_suggestions: set[str] = set()

    # First, prioritize gate failures for the next maturity level
    current_level = result.maturity_level
    next_level = current_level + 1

    if next_level <= 5 and next_level in result.gates:
        gate_status = result.gates[next_level]
        if not gate_status.passed:
            for check_name in gate_status.blocking_checks:
                check_result = result.all_checks.get(check_name)
                if (
                    check_result
                    and check_result.suggestion
                    and check_result.suggestion not in seen_suggestions
                ):
                    recommendations.append(check_result.suggestion)
                    seen_suggestions.add(check_result.suggestion)

    # Then, add category-based recommendations
    for category, _fix_name in FIX_FIRST_PRIORITIES:
        if category in result.category_scores:
            cat_score = result.category_scores[category]
            # If category has failures, add recommendation
            if cat_score.passed_checks < cat_score.total_checks:
                # Get specific suggestions from failed checks
                for check in cat_score.checks:
                    if (
                        not check.passed
                        and check.suggestion
                        and check.suggestion not in seen_suggestions
                    ):
                        recommendations.append(check.suggestion)
                        seen_suggestions.add(check.suggestion)

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
