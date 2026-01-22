"""Tests for reporting module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_readiness_audit.config import load_config
from agent_readiness_audit.models import AuditConfig, ScanSummary
from agent_readiness_audit.reporting import (
    render_json_report,
    render_markdown_report,
    write_artifacts,
)
from agent_readiness_audit.scanner import scan_repo, scan_repos


class TestJSONReport:
    """Tests for JSON report generation."""

    def test_render_json_report(self, python_repo: Path) -> None:
        config = AuditConfig.default()
        summary = scan_repos([python_repo], config)

        json_output = render_json_report(summary)

        # Should be valid JSON
        data = json.loads(json_output)
        assert "generated_at" in data
        assert "repos" in data
        assert len(data["repos"]) == 1

    def test_json_contains_all_fields(self, python_repo: Path) -> None:
        config = AuditConfig.default()
        summary = scan_repos([python_repo], config)

        json_output = render_json_report(summary)
        data = json.loads(json_output)

        repo = data["repos"][0]
        assert "repo_path" in repo
        assert "repo_name" in repo
        assert "score_total" in repo
        assert "level" in repo
        assert "category_scores" in repo
        assert "failed_checks" in repo
        assert "fix_first" in repo


class TestMarkdownReport:
    """Tests for Markdown report generation."""

    def test_render_markdown_report(self, python_repo: Path) -> None:
        config = AuditConfig.default()
        summary = scan_repos([python_repo], config)

        md_output = render_markdown_report(summary)

        assert "# Agent Readiness Audit Report" in md_output
        assert "python-repo" in md_output
        assert "Score" in md_output

    def test_markdown_contains_sections(self, python_repo: Path) -> None:
        config = AuditConfig.default()
        summary = scan_repos([python_repo], config)

        md_output = render_markdown_report(summary)

        assert "## Repository Summary" in md_output
        assert "## Detailed Results" in md_output
        assert "### python-repo" in md_output


class TestArtifacts:
    """Tests for artifact writing."""

    def test_write_artifacts(self, python_repo: Path, temp_dir: Path) -> None:
        config = AuditConfig.default()
        summary = scan_repos([python_repo], config)

        output_dir = temp_dir / "artifacts"
        write_artifacts(summary, output_dir)

        assert output_dir.exists()
        assert (output_dir / "summary.json").exists()
        assert (output_dir / "summary.md").exists()
        assert (output_dir / "python-repo.json").exists()
        assert (output_dir / "python-repo.md").exists()

    def test_artifacts_are_valid(self, python_repo: Path, temp_dir: Path) -> None:
        config = AuditConfig.default()
        summary = scan_repos([python_repo], config)

        output_dir = temp_dir / "artifacts"
        write_artifacts(summary, output_dir)

        # JSON should be valid
        with open(output_dir / "summary.json") as f:
            data = json.load(f)
        assert "repos" in data

        # Markdown should have content
        md_content = (output_dir / "summary.md").read_text()
        assert len(md_content) > 100
