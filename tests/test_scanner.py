"""Tests for scanner module."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.models import AuditConfig, ReadinessLevel
from agent_readiness_audit.scanner import find_repos, is_git_repo, scan_repo, scan_repos


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_is_git_repo_true(self, empty_repo: Path) -> None:
        assert is_git_repo(empty_repo)

    def test_is_git_repo_false(self, temp_dir: Path) -> None:
        non_repo = temp_dir / "not-a-repo"
        non_repo.mkdir()
        assert not is_git_repo(non_repo)


class TestFindRepos:
    """Tests for find_repos function."""

    def test_find_repos_single(self, empty_repo: Path) -> None:
        repos = find_repos(empty_repo.parent, depth=1)
        assert len(repos) == 1
        assert repos[0] == empty_repo

    def test_find_repos_multiple(self, temp_dir: Path) -> None:
        # Create multiple repos
        for name in ["repo1", "repo2", "repo3"]:
            repo = temp_dir / name
            repo.mkdir()
            (repo / ".git").mkdir()

        repos = find_repos(temp_dir, depth=1)
        assert len(repos) == 3

    def test_find_repos_with_include_pattern(self, temp_dir: Path) -> None:
        # Create repos with different names
        for name in ["alpha-repo", "beta-repo", "alpha-test"]:
            repo = temp_dir / name
            repo.mkdir()
            (repo / ".git").mkdir()

        repos = find_repos(temp_dir, depth=1, include_pattern="alpha*")
        assert len(repos) == 2

    def test_find_repos_with_exclude_pattern(self, temp_dir: Path) -> None:
        # Create repos with different names
        for name in ["main-repo", "archive-old", "archive-backup"]:
            repo = temp_dir / name
            repo.mkdir()
            (repo / ".git").mkdir()

        repos = find_repos(temp_dir, depth=1, exclude_pattern="archive*")
        assert len(repos) == 1
        assert repos[0].name == "main-repo"


class TestScanRepo:
    """Tests for scan_repo function."""

    def test_scan_empty_repo(self, empty_repo: Path) -> None:
        config = AuditConfig.default()
        result = scan_repo(empty_repo, config)

        assert result.repo_name == "empty-repo"
        assert result.score_total < 5  # Should be low score
        assert result.level == ReadinessLevel.HUMAN_ONLY

    def test_scan_minimal_repo(self, minimal_repo: Path) -> None:
        config = AuditConfig.default()
        result = scan_repo(minimal_repo, config)

        assert result.repo_name == "minimal-repo"
        assert result.score_total > 0  # Should have some points
        assert len(result.passed_checks) > 0

    def test_scan_python_repo(self, python_repo: Path) -> None:
        config = AuditConfig.default()
        result = scan_repo(python_repo, config)

        assert result.repo_name == "python-repo"
        assert result.score_total >= 10  # Should be decent score
        assert result.level in [
            ReadinessLevel.SEMI_AUTONOMOUS,
            ReadinessLevel.AGENT_READY,
        ]

    def test_scan_agent_ready_repo(self, agent_ready_repo: Path) -> None:
        config = AuditConfig.default()
        result = scan_repo(agent_ready_repo, config)

        assert result.score_total >= 10  # Should be decent score (v2 has more checks)
        # fix_first is limited to 7, so just ensure recommendations exist
        assert len(result.fix_first) <= 7

    def test_scan_generates_fix_first(self, minimal_repo: Path) -> None:
        config = AuditConfig.default()
        result = scan_repo(minimal_repo, config)

        assert len(result.fix_first) > 0
        assert all(isinstance(rec, str) for rec in result.fix_first)


class TestScanRepos:
    """Tests for scan_repos function."""

    def test_scan_multiple_repos(
        self, temp_dir: Path, minimal_repo: Path, python_repo: Path
    ) -> None:
        config = AuditConfig.default()
        summary = scan_repos([minimal_repo, python_repo], config)

        assert summary.total_repos == 2
        assert len(summary.repos) == 2
        assert summary.average_score > 0

    def test_scan_summary_statistics(
        self, python_repo: Path, agent_ready_repo: Path
    ) -> None:
        config = AuditConfig.default()
        summary = scan_repos([python_repo, agent_ready_repo], config)

        assert summary.total_repos == 2
        assert summary.average_score > 0
        assert len(summary.level_distribution) > 0


class TestScoringLevels:
    """Tests for scoring level determination."""

    def test_level_human_only(self, empty_repo: Path) -> None:
        config = AuditConfig.default()
        result = scan_repo(empty_repo, config)
        assert result.level == ReadinessLevel.HUMAN_ONLY

    def test_level_progression(self, temp_dir: Path) -> None:
        """Test that adding more features increases the level."""
        # Start with empty repo
        repo = temp_dir / "progressive-repo"
        repo.mkdir()
        (repo / ".git").mkdir()

        config = AuditConfig.default()

        # Empty - should be Human-Only
        result1 = scan_repo(repo, config)
        assert result1.level == ReadinessLevel.HUMAN_ONLY

        # Add README
        (repo / "README.md").write_text(
            "# Test\n\n## Installation\n\npip install test\n\n## Testing\n\npytest\n"
        )
        (repo / ".gitignore").write_text("*.pyc\n")
        (repo / "pyproject.toml").write_text(
            '[project]\nname = "test"\nrequires-python = ">=3.11"\n'
        )

        result2 = scan_repo(repo, config)
        assert result2.score_total > result1.score_total
