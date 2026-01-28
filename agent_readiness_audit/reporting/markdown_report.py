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
    lines.append(f"**Average Overall Score:** {summary.average_overall_score:.0f}%")
    lines.append(f"**Average Legacy Score:** {summary.average_score:.1f}/16")
    lines.append("")

    # Grade distribution (v3)
    if summary.grade_distribution:
        lines.append("## Grade Distribution")
        lines.append("")
        lines.append("| Grade | Count |")
        lines.append("|-------|-------|")
        for grade, count in sorted(summary.grade_distribution.items()):
            lines.append(f"| {grade} | {count} |")
        lines.append("")

    # Level distribution (legacy)
    if summary.level_distribution:
        lines.append("## Level Distribution (Legacy)")
        lines.append("")
        lines.append("| Level | Count |")
        lines.append("|-------|-------|")
        for level, count in sorted(summary.level_distribution.items()):
            lines.append(f"| {level} | {count} |")
        lines.append("")

    # Summary table with v3 scores
    lines.append("## Repository Summary")
    lines.append("")
    lines.append("| Repository | Overall | Grade | Legacy | Top Issues |")
    lines.append("|------------|---------|-------|--------|------------|")

    for repo in summary.repos:
        top_issues = ", ".join(repo.fix_first[:2]) if repo.fix_first else "None"
        if len(top_issues) > 40:
            top_issues = top_issues[:37] + "..."
        lines.append(
            f"| {repo.repo_name} | {repo.overall_score:.0f}% | {repo.grade.value} | {repo.score_total:.1f} | {top_issues} |"
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
    lines.append(f"**Overall Score:** {result.overall_score:.0f}%")
    lines.append(f"**Grade:** {result.grade.value}")
    lines.append(f"**Legacy Score:** {result.score_total:.1f}/{result.max_score:.0f}")
    lines.append("")
    if result.grade_description:
        lines.append(f"> {result.grade_description}")
        lines.append("")

    # Domain scores (v3)
    if result.domain_scores:
        lines.append("#### Domain Scores")
        lines.append("")
        lines.append("| Domain | Score | Weight | Weighted | Status |")
        lines.append("|--------|-------|--------|----------|--------|")

        for domain_name, domain_score in result.domain_scores.items():
            status = (
                "✅"
                if domain_score.score >= 75
                else ("⚠️" if domain_score.score >= 60 else "❌")
            )
            lines.append(
                f"| {domain_name.replace('_', ' ').title()} | {domain_score.score:.0f}% | {domain_score.weight * 100:.0f}% | {domain_score.weighted_score:.1f} | {status} |"
            )
        lines.append("")

    # Category breakdown (legacy)
    lines.append("#### Category Scores (Legacy)")
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


def render_remediation_markdown(result: RepoResult) -> str:
    """Render remediation report as Markdown (v3).

    This produces an ordered fix list prioritized by domain weight.

    Args:
        result: Repository result to render.

    Returns:
        Markdown string representation of remediation items.
    """
    lines: list[str] = []

    lines.append("# Remediation Plan")
    lines.append("")
    lines.append(f"**Repository:** {result.repo_name}")
    lines.append(f"**Current Score:** {result.overall_score:.0f}%")
    lines.append(f"**Current Grade:** {result.grade.value}")
    lines.append("")

    if not result.remediation_items:
        lines.append("No remediation items - repository is agent-ready!")
        return "\n".join(lines)

    lines.append("## Ordered Fix List")
    lines.append("")
    lines.append("Items are ordered by impact (higher-weighted domains first).")
    lines.append("")

    for i, item in enumerate(result.remediation_items, 1):
        lines.append(f"{i}. {item}")

    lines.append("")

    # Add domain-specific sections
    lines.append("## Domain Breakdown")
    lines.append("")

    for domain_name, domain_score in result.domain_scores.items():
        if domain_score.score < 100 and domain_score.red_flags:
            lines.append(
                f"### {domain_name.replace('_', ' ').title()} ({domain_score.score:.0f}%)"
            )
            lines.append("")
            for flag in domain_score.red_flags[:5]:
                lines.append(f"- {flag}")
            lines.append("")

    return "\n".join(lines)
