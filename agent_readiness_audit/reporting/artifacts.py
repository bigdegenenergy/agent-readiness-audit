"""Artifact writing for Agent Readiness Audit."""

from __future__ import annotations

import re
from pathlib import Path

from agent_readiness_audit.models import RepoResult, ScanSummary
from agent_readiness_audit.reporting.json_report import (
    render_json_report,
    render_repo_json,
)
from agent_readiness_audit.reporting.markdown_report import (
    render_markdown_report,
    render_remediation_markdown,
    render_repo_markdown,
)


def slugify(name: str) -> str:
    """Convert a name to a safe filename slug.

    Args:
        name: Name to slugify.

    Returns:
        Safe filename string.
    """
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


def write_artifacts(summary: ScanSummary, output_dir: Path) -> None:
    """Write all artifacts to output directory.

    Args:
        summary: Scan summary to write.
        output_dir: Directory to write artifacts to.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write summary JSON
    summary_json = render_json_report(summary)
    (output_dir / "summary.json").write_text(summary_json)

    # Write summary Markdown
    summary_md = render_markdown_report(summary)
    (output_dir / "summary.md").write_text(summary_md)

    # Write per-repo artifacts
    for repo in summary.repos:
        write_repo_artifacts(repo, output_dir)


def write_repo_artifacts(result: RepoResult, output_dir: Path) -> None:
    """Write artifacts for a single repository.

    Per v3 specification, outputs:
    - audit.json (machine-readable results)
    - audit.md (human-readable summary)
    - remediation.md (ordered fix list)

    Args:
        result: Repository result to write.
        output_dir: Directory to write artifacts to.
    """
    slug = slugify(result.repo_name)

    # Write repo JSON (audit.json per v3 spec)
    repo_json = render_repo_json(result)
    (output_dir / f"{slug}.json").write_text(repo_json)

    # Write repo Markdown (audit.md per v3 spec)
    repo_md = render_repo_markdown(result)
    (output_dir / f"{slug}.md").write_text(repo_md)

    # Write remediation Markdown (remediation.md per v3 spec)
    remediation_md = render_remediation_markdown(result)
    (output_dir / f"{slug}-remediation.md").write_text(remediation_md)
