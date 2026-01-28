"""Main scanning logic for Agent Readiness Audit."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    get_all_checks,
    run_check,
)
from agent_readiness_audit.models import (
    CATEGORY_TO_DOMAIN,
    DOMAIN_DESCRIPTIONS,
    DOMAIN_WEIGHTS,
    GATE_CHECKS,
    PILLAR_TO_DOMAIN,
    AuditConfig,
    CategoryScore,
    DomainScore,
    GateStatus,
    PillarScore,
    RepoResult,
    ScanSummary,
    calculate_domain_score,
    calculate_maturity_with_gates,
    calculate_overall_score,
    get_grade_description,
    get_grade_for_score,
    get_level_for_score,
    get_maturity_for_score,
    get_maturity_name,
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

# v2: Pillar order for consistent output
PILLAR_ORDER = [
    "environment_determinism",
    "fast_guardrails",
    "type_contracts",
    "verification_trust",
    "verification_speed",
    "documentation_structure",
    "inline_documentation",
    "contribution_contract",
    "agentic_security",
    "secret_hygiene",
    "telemetry_tracing",
    "structured_logging_cost",
    "eval_frameworks",
    "golden_datasets",
    "distribution_dx",
]

# v3: Domain order for consistent output (per ARA specification)
DOMAIN_ORDER = [
    "structure",  # Structure & Discoverability (15%)
    "interfaces",  # Interfaces & Contracts (20%)
    "determinism",  # Determinism & Side Effects (20%)
    "security",  # Security & Blast Radius (20%)
    "testing",  # Testing & Validation (15%)
    "ergonomics",  # Agent Ergonomics (10%)
]

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

    # Initialize pillar scores (v2)
    for pillar in PILLAR_ORDER:
        result.pillar_scores[pillar] = PillarScore(
            name=pillar,
            max_points=2.0,  # All pillars have max 2 points for now
        )

    # Initialize domain scores (v3)
    for domain in DOMAIN_ORDER:
        domain_config = config.domains.get(domain)
        if domain_config and not domain_config.enabled:
            continue

        result.domain_scores[domain] = DomainScore(
            name=domain,
            description=DOMAIN_DESCRIPTIONS.get(domain, ""),
            weight=DOMAIN_WEIGHTS.get(domain, 0.0),
        )

    # Track check results by name for gate evaluation
    check_results: dict[str, bool] = {}

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

        # Track result for gate evaluation
        check_results[check_name] = check_result.passed

        # Add to category
        if check_def.category in result.category_scores:
            result.category_scores[check_def.category].checks.append(check_result)
            result.category_scores[check_def.category].total_checks += 1
            if check_result.passed:
                result.category_scores[check_def.category].passed_checks += 1
                result.passed_checks.append(check_result)
            else:
                result.failed_checks.append(check_result)

        # Add to pillar (v2)
        pillar_name = check_def.pillar or check_def.category
        if pillar_name in result.pillar_scores:
            result.pillar_scores[pillar_name].checks.append(check_name)
            result.pillar_scores[pillar_name].total_checks += 1
            if check_result.passed:
                result.pillar_scores[pillar_name].passed_checks += 1

        # Add to domain (v3) - use check's domain or fallback to mapping
        domain_name = check_def.domain
        if not domain_name and pillar_name and pillar_name in PILLAR_TO_DOMAIN:
            domain_name = PILLAR_TO_DOMAIN[pillar_name]
        elif not domain_name and check_def.category in CATEGORY_TO_DOMAIN:
            domain_name = CATEGORY_TO_DOMAIN[check_def.category]

        if domain_name and domain_name in result.domain_scores:
            result.domain_scores[domain_name].checks.append(check_result)
            result.domain_scores[domain_name].total_checks += 1
            if check_result.passed:
                result.domain_scores[domain_name].passed_checks += 1
                if check_result.evidence:
                    result.domain_scores[domain_name].evidence.append(
                        check_result.evidence
                    )
            else:
                if check_result.suggestion:
                    result.domain_scores[domain_name].red_flags.append(
                        check_result.suggestion
                    )

    # Calculate category scores
    for _category, cat_score in result.category_scores.items():
        if cat_score.total_checks > 0:
            # Score is proportional to passed checks
            pass_ratio = cat_score.passed_checks / cat_score.total_checks
            cat_score.score = pass_ratio * cat_score.max_points

    # Calculate pillar scores (v2)
    for _pillar, pillar_score in result.pillar_scores.items():
        if pillar_score.total_checks > 0:
            pass_ratio = pillar_score.passed_checks / pillar_score.total_checks
            pillar_score.score = pass_ratio * pillar_score.max_points

    # Calculate total score
    result.score_total = sum(cs.score for cs in result.category_scores.values())
    result.max_score = sum(cs.max_points for cs in result.category_scores.values())

    # Determine v1 level (for backward compatibility)
    result.level = get_level_for_score(result.score_total)

    # Calculate gate status (v2)
    result.gates = calculate_gates(check_results)

    # Determine v2 maturity level
    score_based_level = get_maturity_for_score(result.score_total)
    result.maturity_level = calculate_maturity_with_gates(
        score_based_level, result.gates
    )
    result.maturity_name = get_maturity_name(result.maturity_level)

    # Calculate domain scores (v3)
    for _domain_name, domain_score in result.domain_scores.items():
        domain_score.score = calculate_domain_score(
            domain_score.passed_checks, domain_score.total_checks
        )

    # Calculate overall weighted score (v3)
    result.overall_score = calculate_overall_score(result.domain_scores)

    # Determine grade (v3)
    result.grade = get_grade_for_score(result.overall_score)
    result.grade_description = get_grade_description(result.grade)

    # Generate fix-first recommendations
    result.fix_first = generate_fix_first(result)

    # Generate remediation items (v3) - ordered by domain weight (highest first)
    result.remediation_items = generate_remediation(result)

    return result


def calculate_gates(check_results: dict[str, bool]) -> dict[str, GateStatus]:
    """Calculate gate status for each maturity level.

    Args:
        check_results: Dictionary mapping check names to pass/fail status.

    Returns:
        Dictionary mapping level keys to GateStatus objects.
    """
    gates: dict[str, GateStatus] = {}

    for level, required_checks in GATE_CHECKS.items():
        gate_key = f"level_{level}"
        failed_checks = [
            check_name
            for check_name in required_checks
            if not check_results.get(check_name, False)
        ]

        gates[gate_key] = GateStatus(
            level=level,
            passed=len(failed_checks) == 0,
            required_checks=required_checks,
            failed_checks=failed_checks,
        )

    return gates


def generate_fix_first(result: RepoResult) -> list[str]:
    """Generate fix-first recommendations based on failed checks.

    Priority order:
    1. Gate failures for next level (highest leverage)
    2. Category failures by priority order

    Args:
        result: Repository audit result.

    Returns:
        List of prioritized fix recommendations.
    """
    recommendations: list[str] = []

    # First, prioritize gate failures for next level
    next_level = result.maturity_level + 1
    if next_level <= 5:
        gate_key = f"level_{next_level}"
        if gate_key in result.gates and not result.gates[gate_key].passed:
            # Add suggestions for failed gate checks
            for check in result.failed_checks:
                if (
                    check.name in result.gates[gate_key].failed_checks
                    and check.suggestion
                    and check.suggestion not in recommendations
                ):
                    recommendations.append(check.suggestion)

    # Then add remaining category-based recommendations
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
                        and check.suggestion not in recommendations
                    ):
                        recommendations.append(check.suggestion)

    return recommendations[:7]  # Limit to top 7 recommendations


def generate_remediation(result: RepoResult) -> list[str]:
    """Generate remediation items ordered by domain weight (v3).

    Higher-weighted domains are prioritized because fixing them
    has more impact on the overall score.

    Args:
        result: Repository audit result.

    Returns:
        Ordered list of remediation items.
    """
    remediation: list[str] = []

    # Sort domains by weight (highest first)
    sorted_domains = sorted(
        result.domain_scores.items(),
        key=lambda x: x[1].weight,
        reverse=True,
    )

    for _domain_name, domain_score in sorted_domains:
        # Skip domains with perfect scores
        if domain_score.score >= 100:
            continue

        # Add red flags (failed check suggestions) for this domain
        for red_flag in domain_score.red_flags:
            if red_flag not in remediation:
                remediation.append(red_flag)

    return remediation


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
