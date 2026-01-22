"""Tests for CLI module."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from agent_readiness_audit.cli import app

runner = CliRunner()


class TestCLIBasics:
    """Basic CLI tests."""

    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Agent Readiness Audit" in result.stdout

    def test_version(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "Agent Readiness Audit" in result.stdout


class TestScanCommand:
    """Tests for scan command."""

    def test_scan_help(self) -> None:
        result = runner.invoke(app, ["scan", "--help"])
        assert result.exit_code == 0
        assert "--repo" in result.stdout
        assert "--root" in result.stdout
        assert "--format" in result.stdout

    def test_scan_single_repo(self, python_repo: Path) -> None:
        result = runner.invoke(app, ["scan", "--repo", str(python_repo)])
        assert result.exit_code == 0
        assert "python-repo" in result.stdout

    def test_scan_with_json_format(self, python_repo: Path) -> None:
        result = runner.invoke(
            app, ["scan", "--repo", str(python_repo), "--format", "json"]
        )
        assert result.exit_code == 0
        assert '"repo_name"' in result.stdout
        assert '"score_total"' in result.stdout

    def test_scan_with_markdown_format(self, python_repo: Path) -> None:
        result = runner.invoke(
            app, ["scan", "--repo", str(python_repo), "--format", "markdown"]
        )
        assert result.exit_code == 0
        assert "# Agent Readiness Audit Report" in result.stdout

    def test_scan_with_output_dir(self, python_repo: Path, temp_dir: Path) -> None:
        output_dir = temp_dir / "output"
        result = runner.invoke(
            app, ["scan", "--repo", str(python_repo), "--out", str(output_dir)]
        )
        assert result.exit_code == 0
        assert output_dir.exists()
        assert (output_dir / "summary.json").exists()
        assert (output_dir / "summary.md").exists()

    def test_scan_strict_mode_pass(self, agent_ready_repo: Path) -> None:
        result = runner.invoke(
            app,
            ["scan", "--repo", str(agent_ready_repo), "--strict", "--min-score", "10"],
        )
        assert result.exit_code == 0

    def test_scan_strict_mode_fail(self, empty_repo: Path) -> None:
        result = runner.invoke(
            app, ["scan", "--repo", str(empty_repo), "--strict", "--min-score", "10"]
        )
        assert result.exit_code == 1
        # Error message goes to stderr, but check combined output
        output = result.output if hasattr(result, "output") else result.stdout
        assert "below minimum score" in output


class TestReportCommand:
    """Tests for report command."""

    def test_report_help(self) -> None:
        result = runner.invoke(app, ["report", "--help"])
        assert result.exit_code == 0
        assert "--input" in result.stdout
        assert "--format" in result.stdout

    def test_report_from_json(self, python_repo: Path, temp_dir: Path) -> None:
        # First generate JSON
        output_dir = temp_dir / "output"
        runner.invoke(
            app, ["scan", "--repo", str(python_repo), "--out", str(output_dir)]
        )

        # Then render report
        result = runner.invoke(
            app,
            [
                "report",
                "--input",
                str(output_dir / "summary.json"),
                "--format",
                "table",
            ],
        )
        assert result.exit_code == 0


class TestInitConfigCommand:
    """Tests for init-config command."""

    def test_init_config_help(self) -> None:
        result = runner.invoke(app, ["init-config", "--help"])
        assert result.exit_code == 0
        assert "--out" in result.stdout

    def test_init_config_creates_file(self, temp_dir: Path) -> None:
        config_path = temp_dir / ".agent_readiness_audit.toml"
        result = runner.invoke(app, ["init-config", "--out", str(config_path)])
        assert result.exit_code == 0
        assert config_path.exists()

        content = config_path.read_text()
        assert "[scoring]" in content
        assert "[categories]" in content

    def test_init_config_overwrite_prompt(self, temp_dir: Path) -> None:
        config_path = temp_dir / ".agent_readiness_audit.toml"
        config_path.write_text("existing content")

        # Should prompt for overwrite
        result = runner.invoke(
            app, ["init-config", "--out", str(config_path)], input="n\n"
        )
        assert result.exit_code == 0
        assert "Aborted" in result.stdout
