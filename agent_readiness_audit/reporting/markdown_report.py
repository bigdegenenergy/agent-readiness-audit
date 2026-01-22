"""Markdown report generation for Agent Readiness Audit."""

from __future__ import annotations

from agent_readiness_audit.models import RepoResult, ScanSummary


def render_markdown_report(summary: ScanSummary) -> str:
    """Render scan summary as Markdown.

    Args:
        summary: Scan summary to render.

    Returns:
        Markdown string representation.
    """
    lines: list[str] = []

    # Header
    lines.append("# Agent Readiness Audit Report")
    lines.append("")
    lines.append(f"**Generated:** {summary.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Repositories Scanned:** {summary.total_repos}")
    lines.append(f"**Average Score:** {summary.average_score:.1f}/16")
    lines.append("")

    # Level distribution
    if summary.level_distribution:
        lines.append("## Level Distribution")
        lines.append("")
        lines.append("| Level | Count |")
        lines.append("|-------|-------|")
        for level, count in sorted(summary.level_distribution.items()):
            lines.append(f"| {level} | {count} |")
        lines.append("")

    # Summary table
    lines.append("## Repository Summary")
    lines.append("")
    lines.append("| Repository | Score | Level | Top Issues |")
    lines.append("|------------|-------|-------|------------|")

    for repo in summary.repos:
        top_issues = ", ".join(repo.fix_first[:2]) if repo.fix_first else "None"
        if len(top_issues) > 50:
            top_issues = top_issues[:47] + "..."
        lines.append(
            f"| {repo.repo_name} | {repo.score_total:.1f}/16 | {repo.level.value} | {top_issues} |"
        )
    lines.append("")

    # Detailed results per repo
    lines.append("## Detailed Results")
    lines.append("")

    for repo in summary.repos:
        lines.append(render_repo_markdown(repo))
        lines.append("")

    return "\n".join(lines)


def render_repo_markdown(result: RepoResult) -> str:
    """Render single repo result as Markdown.

    Args:
        result: Repository result to render.

    Returns:
        Markdown string representation.
    """
    lines: list[str] = []

    # Header
    lines.append(f"### {result.repo_name}")
    lines.append("")
    lines.append(f"**Path:** `{result.repo_path}`")
    lines.append(
        f"**Score:** {result.score_total:.1f}/{result.max_score:.0f} ({result.percentage:.0f}%)"
    )
    lines.append(f"**Level:** {result.level.value}")
    lines.append("")

    # Category breakdown
    lines.append("#### Category Scores")
    lines.append("")
    lines.append("| Category | Score | Status |")
    lines.append("|----------|-------|--------|")

    for cat_name, cat_score in result.category_scores.items():
        status = "✅" if cat_score.score >= cat_score.max_points * 0.5 else "⚠️"
        if cat_score.score == 0:
            status = "❌"
        lines.append(
            f"| {cat_name.replace('_', ' ').title()} | {cat_score.score:.1f}/{cat_score.max_points:.0f} | {status} |"
        )
    lines.append("")

    # Failed checks
    if result.failed_checks:
        lines.append("#### Failed Checks")
        lines.append("")
        for check in result.failed_checks[:10]:  # Limit to 10
            lines.append(f"- **{check.name}**: {check.evidence}")
            if check.suggestion:
                lines.append(f"  - *Suggestion:* {check.suggestion}")
        lines.append("")

    # Fix-first recommendations
    if result.fix_first:
        lines.append("#### Fix-First Recommendations")
        lines.append("")
        for i, rec in enumerate(result.fix_first[:5], 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

    return "\n".join(lines)
