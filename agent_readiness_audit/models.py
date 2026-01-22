"""Data models for Agent Readiness Audit."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    """Status of a check execution."""

    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"


class ReadinessLevel(str, Enum):
    """Agent readiness level based on score."""

    HUMAN_ONLY = "Human-Only Repo"
    ASSISTED = "Assisted Agent"
    SEMI_AUTONOMOUS = "Semi-Autonomous"
    AGENT_READY = "Agent-Ready Factory"


class CheckResult(BaseModel):
    """Result of a single check execution."""

    name: str
    category: str
    status: CheckStatus
    evidence: str = ""
    suggestion: str = ""
    weight: float = 1.0

    @property
    def passed(self) -> bool:
        """Return True if check passed."""
        return self.status == CheckStatus.PASSED


class CategoryScore(BaseModel):
    """Score for a single category."""

    name: str
    description: str
    score: float = 0.0
    max_points: float = 2.0
    checks: list[CheckResult] = Field(default_factory=list)
    passed_checks: int = 0
    total_checks: int = 0

    @property
    def percentage(self) -> float:
        """Return score as percentage."""
        if self.max_points == 0:
            return 0.0
        return (self.score / self.max_points) * 100


class RepoResult(BaseModel):
    """Complete audit result for a single repository."""

    repo_path: str
    repo_name: str
    score_total: float = 0.0
    max_score: float = 16.0
    level: ReadinessLevel = ReadinessLevel.HUMAN_ONLY
    category_scores: dict[str, CategoryScore] = Field(default_factory=dict)
    failed_checks: list[CheckResult] = Field(default_factory=list)
    passed_checks: list[CheckResult] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    fix_first: list[str] = Field(default_factory=list)
    scanned_at: datetime = Field(default_factory=datetime.now)

    @property
    def percentage(self) -> float:
        """Return total score as percentage."""
        if self.max_score == 0:
            return 0.0
        return (self.score_total / self.max_score) * 100


class ScanSummary(BaseModel):
    """Summary of a scan across multiple repositories."""

    generated_at: datetime = Field(default_factory=datetime.now)
    config_used: str = "default"
    total_repos: int = 0
    repos: list[RepoResult] = Field(default_factory=list)
    average_score: float = 0.0
    level_distribution: dict[str, int] = Field(default_factory=dict)

    def calculate_summary(self) -> None:
        """Calculate summary statistics from repo results."""
        if not self.repos:
            return

        self.total_repos = len(self.repos)
        self.average_score = sum(r.score_total for r in self.repos) / self.total_repos

        # Count level distribution
        self.level_distribution = {}
        for repo in self.repos:
            level = repo.level.value
            self.level_distribution[level] = self.level_distribution.get(level, 0) + 1


class ScoreLevelMapping(BaseModel):
    """Mapping from score range to readiness level."""

    min_score: int
    max_score: int
    level: ReadinessLevel


class CategoryConfig(BaseModel):
    """Configuration for a scoring category."""

    enabled: bool = True
    max_points: float = 2.0
    description: str = ""


class CheckConfig(BaseModel):
    """Configuration for a specific check."""

    enabled: bool = True
    weight: float = 1.0


class DetectionConfig(BaseModel):
    """Configuration for file detection patterns."""

    readme_filenames: list[str] = Field(
        default_factory=lambda: ["README.md", "README.MD", "README", "readme.md"]
    )
    ci_paths: list[str] = Field(
        default_factory=lambda: [
            ".github/workflows",
            ".gitlab-ci.yml",
            "azure-pipelines.yml",
            "bitbucket-pipelines.yml",
        ]
    )
    python_dependency_files: list[str] = Field(
        default_factory=lambda: [
            "pyproject.toml",
            "requirements.txt",
            "Pipfile",
            "poetry.lock",
            "requirements.lock",
        ]
    )
    node_dependency_files: list[str] = Field(
        default_factory=lambda: [
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
        ]
    )
    task_runners: list[str] = Field(
        default_factory=lambda: [
            "Makefile",
            "Taskfile.yml",
            "justfile",
            "magefile.go",
            "tox.ini",
            "noxfile.py",
        ]
    )
    python_lint_configs: list[str] = Field(
        default_factory=lambda: ["ruff.toml", ".ruff.toml", "setup.cfg", "pyproject.toml"]
    )
    python_format_configs: list[str] = Field(
        default_factory=lambda: ["pyproject.toml"]
    )
    python_type_configs: list[str] = Field(
        default_factory=lambda: ["mypy.ini", "pyproject.toml", "pyrightconfig.json"]
    )
    env_examples: list[str] = Field(
        default_factory=lambda: [
            ".env.example",
            ".env.sample",
            "env.example",
            "docs/secrets.md",
            "docs/configuration.md",
        ]
    )


class AuditConfig(BaseModel):
    """Complete audit configuration."""

    scale_points_total: int = 16
    minimum_passing_score: int = 10
    categories: dict[str, CategoryConfig] = Field(default_factory=dict)
    checks: dict[str, CheckConfig] = Field(default_factory=dict)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    default_format: str = "table"
    include_recommendations: bool = True
    show_evidence: bool = True

    @classmethod
    def default(cls) -> AuditConfig:
        """Create default configuration."""
        return cls(
            categories={
                "discoverability": CategoryConfig(
                    description="Repo orientation: README presence and basic onboarding clarity"
                ),
                "deterministic_setup": CategoryConfig(
                    description="Reproducible dependency setup and pinning"
                ),
                "build_and_run": CategoryConfig(
                    description="Standard commands exist for build/test/lint/format"
                ),
                "test_feedback_loop": CategoryConfig(
                    description="Tests exist and are runnable with reasonable defaults"
                ),
                "static_guardrails": CategoryConfig(
                    description="Linters/formatters/types reduce ambiguity for agents"
                ),
                "observability": CategoryConfig(
                    description="Logging/metrics help agents validate behavior changes"
                ),
                "ci_enforcement": CategoryConfig(
                    description="CI exists and validates changes"
                ),
                "security_and_governance": CategoryConfig(
                    description="Baseline hygiene around secrets and contribution policy"
                ),
            }
        )


def get_level_for_score(score: float) -> ReadinessLevel:
    """Determine readiness level based on score."""
    if score <= 5:
        return ReadinessLevel.HUMAN_ONLY
    elif score <= 9:
        return ReadinessLevel.ASSISTED
    elif score <= 13:
        return ReadinessLevel.SEMI_AUTONOMOUS
    else:
        return ReadinessLevel.AGENT_READY
