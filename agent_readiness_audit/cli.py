"""CLI entry point for Agent Readiness Audit."""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from agent_readiness_audit import __version__
from agent_readiness_audit.config import generate_default_config, load_config
from agent_readiness_audit.reporting import (
    render_json_report,
    render_markdown_report,
    render_table_report,
    write_artifacts,
)
from agent_readiness_audit.scanner import find_repos, is_git_repo, scan_repo, scan_repos

app = typer.Typer(
    name="ara",
    help="Agent Readiness Audit - CLI tool for auditing repository agent-readiness.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()
err_console = Console(stderr=True)


class OutputFormat(str, Enum):
    """Output format options."""

    TABLE = "table"
    JSON = "json"
    MARKDOWN = "markdown"


class ReportFormat(str, Enum):
    """Report format options."""

    TABLE = "table"
    MARKDOWN = "markdown"


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"Agent Readiness Audit v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Agent Readiness Audit - Scan repositories for agent-readiness."""
    pass


@app.command()
def scan(
    repo: Annotated[
        Optional[Path],
        typer.Option(
            "--repo",
            "-r",
            help="Path to a single repo (defaults to current directory if not provided and --root not provided).",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
    root: Annotated[
        Optional[Path],
        typer.Option(
            "--root",
            help="Path containing multiple repos to scan.",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
    depth: Annotated[
        int,
        typer.Option(
            "--depth",
            "-d",
            help="Max directory depth to search for repos under --root.",
            min=1,
            max=10,
        ),
    ] = 2,
    include: Annotated[
        Optional[str],
        typer.Option(
            "--include",
            "-i",
            help="Glob pattern to include repo paths/names.",
        ),
    ] = None,
    exclude: Annotated[
        Optional[str],
        typer.Option(
            "--exclude",
            "-e",
            help="Glob pattern to exclude repo paths/names.",
        ),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            "-c",
            help="Path to audit config TOML.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = None,
    format: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            "-f",
            help="Primary output format to stdout.",
            case_sensitive=False,
        ),
    ] = OutputFormat.TABLE,
    out: Annotated[
        Optional[Path],
        typer.Option(
            "--out",
            "-o",
            help="Optional output directory to write artifacts (JSON + MD per repo + summary).",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            "-s",
            help="Exit non-zero if any repo is below configured minimum readiness.",
        ),
    ] = False,
    min_score: Annotated[
        Optional[int],
        typer.Option(
            "--min-score",
            help="Override minimum score required to pass (0-16).",
            min=0,
            max=16,
        ),
    ] = None,
) -> None:
    """Scan one repo or a directory of repos and produce audit results.

    Examples:
        ara scan --repo /path/to/repo
        ara scan --root /path/to/repos --depth 2
        ara scan --root /path/to/repos --include "*alpha*" --exclude "*archive*"
        ara scan --root /path/to/repos --format json --out ./out
        ara scan --repo . --strict
    """
    # Load configuration
    audit_config = load_config(config)

    # Determine repos to scan
    repos_to_scan: list[Path] = []

    if root:
        # Scan multiple repos under root
        repos_to_scan = find_repos(
            root,
            depth=depth,
            include_pattern=include,
            exclude_pattern=exclude,
        )
        if not repos_to_scan:
            err_console.print(f"[red]No repositories found under {root}[/red]")
            raise typer.Exit(1)
        console.print(f"[dim]Found {len(repos_to_scan)} repositories to scan[/dim]")
    elif repo:
        # Scan single repo
        if not is_git_repo(repo):
            err_console.print(f"[yellow]Warning: {repo} does not appear to be a git repository[/yellow]")
        repos_to_scan = [repo]
    else:
        # Default to current directory
        cwd = Path.cwd()
        if not is_git_repo(cwd):
            err_console.print("[yellow]Warning: Current directory does not appear to be a git repository[/yellow]")
        repos_to_scan = [cwd]

    # Perform scan
    summary = scan_repos(repos_to_scan, audit_config)

    # Output results
    if format == OutputFormat.TABLE:
        render_table_report(summary, console)
    elif format == OutputFormat.JSON:
        json_output = render_json_report(summary)
        console.print(json_output)
    elif format == OutputFormat.MARKDOWN:
        md_output = render_markdown_report(summary)
        console.print(md_output)

    # Write artifacts if output directory specified
    if out:
        out.mkdir(parents=True, exist_ok=True)
        write_artifacts(summary, out)
        console.print(f"\n[green]Artifacts written to {out}[/green]")

    # Check strict mode
    if strict:
        min_required = min_score if min_score is not None else audit_config.minimum_passing_score
        failing_repos = [r for r in summary.repos if r.score_total < min_required]
        if failing_repos:
            err_console.print(
                f"\n[red]Strict mode: {len(failing_repos)} repo(s) below minimum score of {min_required}[/red]"
            )
            raise typer.Exit(1)


@app.command()
def report(
    input: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            help="Input JSON file produced by scan.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ],
    format: Annotated[
        ReportFormat,
        typer.Option(
            "--format",
            "-f",
            help="Report rendering format.",
            case_sensitive=False,
        ),
    ] = ReportFormat.MARKDOWN,
) -> None:
    """Render a report from a previously saved JSON result.

    Examples:
        ara report --input ./out/summary.json --format markdown
        ara report --input ./out/summary.json --format table
    """
    import json

    from agent_readiness_audit.models import ScanSummary

    # Load JSON
    try:
        with open(input) as f:
            data = json.load(f)
        summary = ScanSummary.model_validate(data)
    except Exception as e:
        err_console.print(f"[red]Error loading JSON: {e}[/red]")
        raise typer.Exit(1)

    # Render report
    if format == ReportFormat.TABLE:
        render_table_report(summary, console)
    elif format == ReportFormat.MARKDOWN:
        md_output = render_markdown_report(summary)
        console.print(md_output)


@app.command("init-config")
def init_config(
    out: Annotated[
        Path,
        typer.Option(
            "--out",
            "-o",
            help="Where to write the starter config.",
            file_okay=True,
            dir_okay=False,
            resolve_path=True,
        ),
    ] = Path("./.agent_readiness_audit.toml"),
) -> None:
    """Generate a starter config TOML for customizing checks and scoring.

    Examples:
        ara init-config --out ./.agent_readiness_audit.toml
    """
    if out.exists():
        overwrite = typer.confirm(f"{out} already exists. Overwrite?")
        if not overwrite:
            console.print("[yellow]Aborted.[/yellow]")
            raise typer.Exit(0)

    config_content = generate_default_config()
    out.write_text(config_content)
    console.print(f"[green]Configuration written to {out}[/green]")


if __name__ == "__main__":
    app()
