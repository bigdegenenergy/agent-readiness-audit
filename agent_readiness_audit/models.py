"""Data models for Agent Readiness Audit."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    """Status of a check execution."""

    PASSED = "passed"
    PARTIAL = "partial"
    FAILED = "failed"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"


class ReadinessLevel(str, Enum):
    """Agent readiness level based on score (v1 compatibility)."""

    HUMAN_ONLY = "Human-Only Repo"
    ASSISTED = "Assisted Agent"
    SEMI_AUTONOMOUS = "Semi-Autonomous"
    AGENT_READY = "Agent-Ready Factory"


class MaturityLevel(int, Enum):
    """V2 maturity levels for agent-native readiness certification."""

    FUNCTIONAL = 1
    DOCUMENTED = 2
    STANDARDIZED = 3
    OPTIMIZED = 4
    AUTONOMOUS = 5


# Maturity level metadata
MATURITY_LEVEL_INFO: dict[MaturityLevel, dict[str, str]] = {
    MaturityLevel.FUNCTIONAL: {
        "name": "Functional",
        "description": "Works for humans; agents fail due to ambiguity and missing automation",
    },
    MaturityLevel.DOCUMENTED: {
        "name": "Documented",
        "description": "Setup/run instructions exist; agents can attempt tasks but ambiguity remains",
    },
    MaturityLevel.STANDARDIZED: {
        "name": "Standardized",
        "description": "CI, linting, basic tests, and deterministic deps exist; minimum viable for production agents",
    },
    MaturityLevel.OPTIMIZED: {
        "name": "Optimized",
        "description": "Fast feedback loops; split test targets; strong local guardrails; predictable artifacts",
    },
    MaturityLevel.AUTONOMOUS: {
        "name": "Autonomous",
        "description": "Telemetry + evals + golden datasets; agentic security posture; environment behaves like an API",
    },
}


# Gate definitions: checks required for each maturity level
MATURITY_GATES: dict[MaturityLevel, list[str]] = {
    MaturityLevel.DOCUMENTED: [
        "readme_exists",
        "readme_has_setup_section",
        "dependency_manifest_exists",
    ],
    MaturityLevel.STANDARDIZED: [
        "ci_workflow_present",
        "linter_config_present",
        "tests_directory_or_config_exists",
        "lockfile_exists",
        "readme_has_test_instructions",
    ],
    MaturityLevel.OPTIMIZED: [
        "fast_linter_python",
        "precommit_present",
        "python_type_hint_coverage",
        "test_splitting",
        "machine_readable_coverage",
    ],
    MaturityLevel.AUTONOMOUS: [
        "opentelemetry_present",
        "structured_logging_present",
        "eval_framework_detect",
        "golden_dataset_present",
        "promptfoo_present",
    ],
}

# Score thresholds for each maturity level
MATURITY_SCORE_THRESHOLDS: dict[MaturityLevel, tuple[int, int]] = {
    MaturityLevel.FUNCTIONAL: (0, 5),
    MaturityLevel.DOCUMENTED: (6, 9),
    MaturityLevel.STANDARDIZED: (10, 13),
    MaturityLevel.OPTIMIZED: (14, 15),
    MaturityLevel.AUTONOMOUS: (16, 16),
}


class Pillar(str, Enum):
    """V2 pillars for organizing checks."""

    # Environment & Determinism
    ENVIRONMENT_DETERMINISM = "environment_determinism"
    FAST_GUARDRAILS = "fast_guardrails"

    # Type Safety
    TYPE_CONTRACTS = "type_contracts"

    # Verification
    VERIFICATION_TRUST = "verification_trust"
    VERIFICATION_SPEED = "verification_speed"

    # Documentation
    DOCUMENTATION_STRUCTURE = "documentation_structure"
    INLINE_DOCUMENTATION = "inline_documentation"
    CONTRIBUTION_CONTRACT = "contribution_contract"

    # Security
    AGENTIC_SECURITY = "agentic_security"
    SECRET_HYGIENE = "secret_hygiene"

    # Observability
    TELEMETRY_TRACING = "telemetry_tracing"
    STRUCTURED_LOGGING_COST = "structured_logging_cost"

    # Evaluation
    EVAL_FRAMEWORKS = "eval_frameworks"
    GOLDEN_DATASETS = "golden_datasets"

    # Distribution
    DISTRIBUTION_DX = "distribution_dx"


# Pillar metadata
PILLAR_INFO: dict[Pillar, dict[str, str]] = {
    Pillar.ENVIRONMENT_DETERMINISM: {
        "name": "Environment Determinism",
        "description": "Reproducible dependency management and runtime pinning",
    },
    Pillar.FAST_GUARDRAILS: {
        "name": "Fast Guardrails",
        "description": "Sub-second local feedback (linters, formatters, pre-commit)",
    },
    Pillar.TYPE_CONTRACTS: {
        "name": "Type Contracts",
        "description": "Static typing coverage and strictness configuration",
    },
    Pillar.VERIFICATION_TRUST: {
        "name": "Verification Trust",
        "description": "Test reliability, flakiness awareness, coverage artifacts",
    },
    Pillar.VERIFICATION_SPEED: {
        "name": "Verification Speed",
        "description": "Test splitting (unit vs integration), parallel execution",
    },
    Pillar.DOCUMENTATION_STRUCTURE: {
        "name": "Documentation Structure",
        "description": "Diátaxis-aligned doc organization for agent retrieval",
    },
    Pillar.INLINE_DOCUMENTATION: {
        "name": "Inline Documentation",
        "description": "Docstring coverage for local context",
    },
    Pillar.CONTRIBUTION_CONTRACT: {
        "name": "Contribution Contract",
        "description": "CONTRIBUTING.md, PR templates, issue templates",
    },
    Pillar.AGENTIC_SECURITY: {
        "name": "Agentic Security",
        "description": "Prompt red-teaming (promptfoo), agent guardrails",
    },
    Pillar.SECRET_HYGIENE: {
        "name": "Secret Hygiene",
        "description": "No hardcoded secrets, proper .env patterns, secret scanning",
    },
    Pillar.TELEMETRY_TRACING: {
        "name": "Telemetry & Tracing",
        "description": "OpenTelemetry instrumentation for agent behavior tracing",
    },
    Pillar.STRUCTURED_LOGGING_COST: {
        "name": "Structured Logging",
        "description": "JSON logs with standard fields (task_id, cost, tokens)",
    },
    Pillar.EVAL_FRAMEWORKS: {
        "name": "Eval Frameworks",
        "description": "DeepEval, Ragas, or equivalent for agentic behavior testing",
    },
    Pillar.GOLDEN_DATASETS: {
        "name": "Golden Datasets",
        "description": "Test cases with expected outcomes for regression testing",
    },
    Pillar.DISTRIBUTION_DX: {
        "name": "Distribution DX",
        "description": "README quality, setup instructions, test documentation",
    },
}


class GateStatus(BaseModel):
    """Status of a maturity level gate."""

    level: MaturityLevel
    passed: bool = False
    blocking_checks: list[str] = Field(default_factory=list)


class CheckResult(BaseModel):
    """Result of a single check execution."""

    name: str
    category: str
    pillar: str = ""
    status: CheckStatus
    evidence: str = ""
    suggestion: str = ""
    weight: float = 1.0
    gate_for: list[int] = Field(default_factory=list)
    confidence: str = "HIGH"  # HIGH, MEDIUM, LOW

    @property
    def passed(self) -> bool:
        """Return True if check passed."""
        return self.status == CheckStatus.PASSED

    @property
    def score(self) -> float:
        """Return numeric score based on status."""
        if self.status == CheckStatus.PASSED:
            return 1.0
        elif self.status == CheckStatus.PARTIAL:
            return 0.5
        return 0.0


class PillarScore(BaseModel):
    """Score for a single pillar (v2)."""

    pillar: str
    name: str
    description: str
    score: float = 0.0
    max_score: float = 2.0
    checks: list[str] = Field(default_factory=list)
    passed_checks: int = 0
    total_checks: int = 0

    @property
    def percentage(self) -> float:
        """Return score as percentage."""
        if self.max_score == 0:
            return 0.0
        return (self.score / self.max_score) * 100


class CategoryScore(BaseModel):
    """Score for a single category (v1 compatibility)."""

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


class MaturityInfo(BaseModel):
    """Information about the repository's maturity level."""

    level: int
    name: str
    description: str
    score_range: tuple[int, int] = (0, 0)


class RepoResult(BaseModel):
    """Complete audit result for a single repository."""

    repo_path: str
    repo_name: str
    score_total: float = 0.0
    max_score: float = 16.0

    # V1 compatibility
    level: ReadinessLevel = ReadinessLevel.HUMAN_ONLY

    # V2 maturity model
    maturity_level: int = 1
    maturity_info: MaturityInfo | None = None
    gates: dict[int, GateStatus] = Field(default_factory=dict)

    # Scores
    category_scores: dict[str, CategoryScore] = Field(default_factory=dict)
    pillar_scores: dict[str, PillarScore] = Field(default_factory=dict)

    # Check results
    failed_checks: list[CheckResult] = Field(default_factory=list)
    passed_checks: list[CheckResult] = Field(default_factory=list)
    all_checks: dict[str, CheckResult] = Field(default_factory=dict)

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
    maturity_distribution: dict[str, int] = Field(default_factory=dict)

    def calculate_summary(self) -> None:
        """Calculate summary statistics from repo results."""
        if not self.repos:
            return

        self.total_repos = len(self.repos)
        self.average_score = sum(r.score_total for r in self.repos) / self.total_repos

        # Count v1 level distribution
        self.level_distribution = {}
        for repo in self.repos:
            level = repo.level.value
            self.level_distribution[level] = self.level_distribution.get(level, 0) + 1

        # Count v2 maturity distribution
        self.maturity_distribution = {}
        for repo in self.repos:
            if repo.maturity_info:
                level_name = f"Level {repo.maturity_level} - {repo.maturity_info.name}"
            else:
                level_name = f"Level {repo.maturity_level}"
            self.maturity_distribution[level_name] = (
                self.maturity_distribution.get(level_name, 0) + 1
            )


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
    threshold_level_4: int | None = None  # For type coverage checks
    threshold_level_5: int | None = None  # For type coverage checks


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
        default_factory=lambda: [
            "ruff.toml",
            ".ruff.toml",
            "setup.cfg",
            "pyproject.toml",
        ]
    )
    python_format_configs: list[str] = Field(default_factory=lambda: ["pyproject.toml"])
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
    lockfile_patterns: list[str] = Field(
        default_factory=lambda: [
            "uv.lock",
            "poetry.lock",
            "Pipfile.lock",
            "requirements.lock",
            "pdm.lock",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "bun.lockb",
            "Cargo.lock",
            "go.sum",
            "Gemfile.lock",
        ]
    )


class ThresholdConfig(BaseModel):
    """Configuration for tunable thresholds."""

    type_hint_coverage_level_4: int = 70
    type_hint_coverage_level_5: int = 85
    docstring_coverage_minimum: int = 50


class IgnoreConfig(BaseModel):
    """Configuration for ignoring checks/pillars/paths."""

    checks: list[str] = Field(default_factory=list)
    pillars: list[str] = Field(default_factory=list)
    paths: list[str] = Field(
        default_factory=lambda: ["vendor/", "generated/", "migrations/", ".git/"]
    )


class OutputConfig(BaseModel):
    """Configuration for output options."""

    default_format: str = "table"
    include_recommendations: bool = True
    show_evidence: bool = True
    show_gates: bool = True


class AuditConfig(BaseModel):
    """Complete audit configuration."""

    scale_points_total: int = 16
    minimum_passing_score: int = 10
    categories: dict[str, CategoryConfig] = Field(default_factory=dict)
    checks: dict[str, CheckConfig] = Field(default_factory=dict)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
    ignore: IgnoreConfig = Field(default_factory=IgnoreConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    default_format: str = "table"  # Legacy compatibility
    include_recommendations: bool = True  # Legacy compatibility
    show_evidence: bool = True  # Legacy compatibility

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
    """Determine readiness level based on score (v1 compatibility)."""
    if score <= 5:
        return ReadinessLevel.HUMAN_ONLY
    elif score <= 9:
        return ReadinessLevel.ASSISTED
    elif score <= 13:
        return ReadinessLevel.SEMI_AUTONOMOUS
    else:
        return ReadinessLevel.AGENT_READY


def get_maturity_level_for_score(score: float) -> MaturityLevel:
    """Determine maturity level based on score only (gates checked separately)."""
    for level in reversed(list(MaturityLevel)):
        min_score, max_score = MATURITY_SCORE_THRESHOLDS[level]
        if min_score <= score <= max_score:
            return level
    return MaturityLevel.FUNCTIONAL


def calculate_maturity_level(
    score: float, check_results: dict[str, CheckResult]
) -> tuple[MaturityLevel, dict[int, GateStatus]]:
    """
    Calculate the actual maturity level based on score AND gate requirements.

    A repository cannot achieve Level N unless:
    1. Score >= threshold for that level
    2. All gate checks for that level (and below) pass

    Returns:
        Tuple of (achieved level, gate statuses for all levels)
    """
    gates: dict[int, GateStatus] = {}

    # Check gates for each level
    for level in MaturityLevel:
        if level == MaturityLevel.FUNCTIONAL:
            # Level 1 has no gates
            gates[level.value] = GateStatus(level=level, passed=True)
            continue

        gate_checks = MATURITY_GATES.get(level, [])
        blocking = []

        for check_name in gate_checks:
            result = check_results.get(check_name)
            if result is None or not result.passed:
                blocking.append(check_name)

        gates[level.value] = GateStatus(
            level=level,
            passed=len(blocking) == 0,
            blocking_checks=blocking,
        )

    # Determine the highest level where both score threshold and gates are met
    achieved_level = MaturityLevel.FUNCTIONAL

    for level in MaturityLevel:
        if level == MaturityLevel.FUNCTIONAL:
            continue

        min_score, _ = MATURITY_SCORE_THRESHOLDS[level]

        # Check if score meets threshold
        if score < min_score:
            break

        # Check if all gates up to this level pass
        all_gates_pass = all(
            gates[mat_level.value].passed
            for mat_level in MaturityLevel
            if mat_level.value <= level.value and mat_level != MaturityLevel.FUNCTIONAL
        )

        if all_gates_pass:
            achieved_level = level
        else:
            # Can't skip levels - if a lower level gate fails, we're blocked
            break

    return achieved_level, gates


def get_maturity_info(level: MaturityLevel) -> MaturityInfo:
    """Get maturity level information."""
    info = MATURITY_LEVEL_INFO[level]
    score_range = MATURITY_SCORE_THRESHOLDS[level]
    return MaturityInfo(
        level=level.value,
        name=info["name"],
        description=info["description"],
        score_range=score_range,
    )
