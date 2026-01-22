"""Table report generation for Agent Readiness Audit."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from agent_readiness_audit.models import ReadinessLevel, RepoResult, ScanSummary


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


def render_table_report(summary: ScanSummary, console: Console) -> None:
    """Render scan summary as a Rich table.

    Args:
        summary: Scan summary to render.
        console: Rich console to output to.
    """
    # Summary header
    console.print()
    console.print(
        Panel.fit(
            f"[bold]Agent Readiness Audit[/bold]\n"
            f"Scanned {summary.total_repos} repository(ies) | "
            f"Average Score: {summary.average_score:.1f}/16",
            border_style="blue",
        )
    )
    console.print()

    # Main results table
    table = Table(
        title="Scan Results",
        show_header=True,
        header_style="bold",
        border_style="dim",
    )

    table.add_column("Repository", style="cyan", no_wrap=True)
    table.add_column("Score", justify="center")
    table.add_column("Level", justify="center")
    table.add_column("Top Issues", style="dim")

    for repo in summary.repos:
        score_color = get_score_color(repo.score_total)
        level_color = get_level_color(repo.level)

        # Format top issues
        top_issues = ", ".join(repo.fix_first[:2]) if repo.fix_first else "None"
        if len(top_issues) > 40:
            top_issues = top_issues[:37] + "..."

        table.add_row(
            repo.repo_name,
            Text(f"{repo.score_total:.1f}/16", style=score_color),
            Text(repo.level.value, style=level_color),
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
    # Category breakdown table
    cat_table = Table(
        title="Category Breakdown",
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
            Text(f"{cat_score.score:.1f}/{cat_score.max_points:.0f}", style=score_color),
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
