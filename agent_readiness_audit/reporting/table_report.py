"""Table report generation for Agent Readiness Audit."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from agent_readiness_audit.models import (
    AgentGrade,
    ReadinessLevel,
    RepoResult,
    ScanSummary,
)


def get_level_color(level: ReadinessLevel) -> str:
    """Get color for readiness level."""
    colors = {
        ReadinessLevel.HUMAN_ONLY: "red",
        ReadinessLevel.ASSISTED: "yellow",
        ReadinessLevel.SEMI_AUTONOMOUS: "cyan",
        ReadinessLevel.AGENT_READY: "green",
    }
    return colors.get(level, "white")


def get_score_color(score: float, max_score: float = 16.0) -> str:
    """Get color based on score percentage."""
    percentage = (score / max_score) * 100
    if percentage >= 87.5:  # 14+
        return "green"
    elif percentage >= 62.5:  # 10+
        return "cyan"
    elif percentage >= 37.5:  # 6+
        return "yellow"
    else:
        return "red"


def get_grade_color(grade: AgentGrade) -> str:
    """Get color for agent grade (v3)."""
    colors = {
        AgentGrade.AGENT_FIRST: "green",
        AgentGrade.AGENT_COMPATIBLE: "cyan",
        AgentGrade.HUMAN_FIRST_RISKY: "yellow",
        AgentGrade.AGENT_HOSTILE: "red",
    }
    return colors.get(grade, "white")


def get_domain_score_color(score: float) -> str:
    """Get color based on domain score (0-100)."""
    if score >= 90:
        return "green"
    elif score >= 75:
        return "cyan"
    elif score >= 60:
        return "yellow"
    else:
        return "red"


def render_table_report(summary: ScanSummary, console: Console) -> None:
    """Render scan summary as a Rich table.

    Args:
        summary: Scan summary to render.
        console: Rich console to output to.
    """
    # Summary header with v3 overall score
    console.print()
    console.print(
        Panel.fit(
            f"[bold]Agent Readiness Audit[/bold]\n"
            f"Scanned {summary.total_repos} repository(ies)\n"
            f"Average Score: {summary.average_overall_score:.0f}% | "
            f"Legacy Score: {summary.average_score:.1f}/16",
            border_style="blue",
        )
    )
    console.print()

    # Main results table with v3 grade
    table = Table(
        title="Scan Results",
        show_header=True,
        header_style="bold",
        border_style="dim",
    )

    table.add_column("Repository", style="cyan", no_wrap=True)
    table.add_column("Overall", justify="center")
    table.add_column("Grade", justify="center")
    table.add_column("Legacy", justify="center")
    table.add_column("Top Issues", style="dim")

    for repo in summary.repos:
        overall_color = get_domain_score_color(repo.overall_score)
        grade_color = get_grade_color(repo.grade)
        legacy_color = get_score_color(repo.score_total)

        # Format top issues
        top_issues = ", ".join(repo.fix_first[:2]) if repo.fix_first else "None"
        if len(top_issues) > 35:
            top_issues = top_issues[:32] + "..."

        table.add_row(
            repo.repo_name,
            Text(f"{repo.overall_score:.0f}%", style=overall_color),
            Text(repo.grade.value, style=grade_color),
            Text(f"{repo.score_total:.1f}", style=legacy_color),
            top_issues,
        )

    console.print(table)
    console.print()

    # Detailed view for single repo
    if len(summary.repos) == 1:
        render_detailed_repo(summary.repos[0], console)


def render_detailed_repo(result: RepoResult, console: Console) -> None:
    """Render detailed view for a single repository.

    Args:
        result: Repository result to render.
        console: Rich console to output to.
    """
    # v3 Domain scores table
    if result.domain_scores:
        domain_table = Table(
            title="Domain Scores (v3)",
            show_header=True,
            header_style="bold",
            border_style="dim",
        )

        domain_table.add_column("Domain", style="cyan")
        domain_table.add_column("Score", justify="center")
        domain_table.add_column("Weight", justify="center")
        domain_table.add_column("Weighted", justify="center")
        domain_table.add_column("Status", justify="center")

        for domain_name, domain_score in result.domain_scores.items():
            score_color = get_domain_score_color(domain_score.score)

            # Status indicator
            if domain_score.score >= 90:
                status = Text("✓", style="green")
            elif domain_score.score >= 60:
                status = Text("◐", style="yellow")
            else:
                status = Text("✗", style="red")

            domain_table.add_row(
                domain_name.replace("_", " ").title(),
                Text(f"{domain_score.score:.0f}%", style=score_color),
                f"{domain_score.weight * 100:.0f}%",
                f"{domain_score.weighted_score:.1f}",
                status,
            )

        console.print(domain_table)
        console.print()

    # Category breakdown table (legacy)
    cat_table = Table(
        title="Category Breakdown (Legacy)",
        show_header=True,
        header_style="bold",
        border_style="dim",
    )

    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Score", justify="center")
    cat_table.add_column("Checks", justify="center")
    cat_table.add_column("Status", justify="center")

    for cat_name, cat_score in result.category_scores.items():
        score_color = get_score_color(cat_score.score, cat_score.max_points)

        # Status indicator
        if cat_score.score >= cat_score.max_points:
            status = Text("✓", style="green")
        elif cat_score.score >= cat_score.max_points * 0.5:
            status = Text("◐", style="yellow")
        else:
            status = Text("✗", style="red")

        cat_table.add_row(
            cat_name.replace("_", " ").title(),
            Text(
                f"{cat_score.score:.1f}/{cat_score.max_points:.0f}", style=score_color
            ),
            f"{cat_score.passed_checks}/{cat_score.total_checks}",
            status,
        )

    console.print(cat_table)
    console.print()

    # Failed checks
    if result.failed_checks:
        console.print("[bold]Failed Checks:[/bold]")
        for check in result.failed_checks[:8]:
            console.print(f"  [red]✗[/red] [dim]{check.category}:[/dim] {check.name}")
            if check.suggestion:
                console.print(f"    [dim]→ {check.suggestion}[/dim]")
        if len(result.failed_checks) > 8:
            console.print(f"  [dim]... and {len(result.failed_checks) - 8} more[/dim]")
        console.print()

    # Fix-first recommendations
    if result.fix_first:
        console.print("[bold]Fix-First Recommendations:[/bold]")
        for i, rec in enumerate(result.fix_first[:5], 1):
            console.print(f"  {i}. {rec}")
        console.print()
