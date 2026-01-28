"""Data models for Agent Readiness Audit."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    """Status of a check execution."""

    PASSED = "passed"
    FAILED = "failed"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"
    PARTIAL = "partial"  # v2: for checks with partial compliance


class ReadinessLevel(str, Enum):
    """Agent readiness level based on score (v1 compatibility)."""

    HUMAN_ONLY = "Human-Only Repo"
    ASSISTED = "Assisted Agent"
    SEMI_AUTONOMOUS = "Semi-Autonomous"
    AGENT_READY = "Agent-Ready Factory"


class AgentGrade(str, Enum):
    """Agent readiness grade based on weighted percentage score (v3 spec)."""

    AGENT_FIRST = "Agent-First"
    AGENT_COMPATIBLE = "Agent-Compatible"
    HUMAN_FIRST_RISKY = "Human-First, Agent-Risky"
    AGENT_HOSTILE = "Agent-Hostile"


AGENT_GRADE_DESCRIPTIONS: dict[str, str] = {
    "Agent-First": "Repo is optimized for autonomous agent operation. Agents can read, modify, and execute workflows safely.",
    "Agent-Compatible": "Repo supports agent operation with minor friction. Most agent tasks will succeed.",
    "Human-First, Agent-Risky": "Repo works for humans but has significant agent risks. Agents may fail due to ambiguity or missing guardrails.",
    "Agent-Hostile": "Repo is unsuitable for agent operation. Agents should not be trusted to work in this environment.",
}


class MaturityLevel(int, Enum):
    """Agent-native maturity level (v2)."""

    FUNCTIONAL = 1
    DOCUMENTED = 2
    STANDARDIZED = 3
    OPTIMIZED = 4
    AUTONOMOUS = 5


MATURITY_NAMES: dict[int, str] = {
    1: "Functional",
    2: "Documented",
    3: "Standardized",
    4: "Optimized",
    5: "Autonomous",
}

MATURITY_DESCRIPTIONS: dict[int, str] = {
    1: "Works for humans; agents fail due to ambiguity and missing automation.",
    2: "Setup/run instructions exist; agents can attempt tasks but ambiguity remains.",
    3: "CI, linting, basic tests, and deterministic deps exist; minimum viable for production agents.",
    4: "Fast feedback loops; split test targets; strong local guardrails; predictable artifacts.",
    5: "Telemetry + evals + golden datasets; agentic security posture; environment behaves like an API.",
}


class Pillar(str, Enum):
    """v2 Pillars for granular analysis."""

    ENVIRONMENT_DETERMINISM = "environment_determinism"
    FAST_GUARDRAILS = "fast_guardrails"
    TYPE_CONTRACTS = "type_contracts"
    VERIFICATION_TRUST = "verification_trust"
    VERIFICATION_SPEED = "verification_speed"
    DOCUMENTATION_STRUCTURE = "documentation_structure"
    INLINE_DOCUMENTATION = "inline_documentation"
    CONTRIBUTION_CONTRACT = "contribution_contract"
    AGENTIC_SECURITY = "agentic_security"
    SECRET_HYGIENE = "secret_hygiene"
    TELEMETRY_TRACING = "telemetry_tracing"
    STRUCTURED_LOGGING_COST = "structured_logging_cost"
    EVAL_FRAMEWORKS = "eval_frameworks"
    GOLDEN_DATASETS = "golden_datasets"
    DISTRIBUTION_DX = "distribution_dx"


class Domain(str, Enum):
    """v3 Domains for weighted scoring per ARA specification."""

    STRUCTURE = "structure"
    INTERFACES = "interfaces"
    DETERMINISM = "determinism"
    SECURITY = "security"
    TESTING = "testing"
    ERGONOMICS = "ergonomics"


# Domain weights per specification (must sum to 100%)
DOMAIN_WEIGHTS: dict[str, float] = {
    "structure": 0.15,  # Structure & Discoverability - 15%
    "interfaces": 0.20,  # Interfaces & Contracts - 20%
    "determinism": 0.20,  # Determinism & Side Effects - 20%
    "security": 0.20,  # Security & Blast Radius - 20%
    "testing": 0.15,  # Testing & Validation - 15%
    "ergonomics": 0.10,  # Agent Ergonomics - 10%
}

DOMAIN_DESCRIPTIONS: dict[str, str] = {
    "structure": "Can an agent quickly understand what this repo is and how it is organized?",
    "interfaces": "Are inputs, outputs, and side effects machine-verifiable?",
    "determinism": "Can an agent replay execution safely and get the same result?",
    "security": "Can an agent operate without leaking secrets or damaging external systems?",
    "testing": "Can an agent verify correctness autonomously?",
    "ergonomics": "Is the repo pleasant for an agent to work in?",
}

# Mapping from v1 categories to v3 domains
CATEGORY_TO_DOMAIN: dict[str, str] = {
    "discoverability": "structure",
    "deterministic_setup": "determinism",
    "build_and_run": "ergonomics",
    "test_feedback_loop": "testing",
    "static_guardrails": "interfaces",
    "observability": "ergonomics",
    "ci_enforcement": "ergonomics",
    "security_and_governance": "security",
}

# Mapping from v2 pillars to v3 domains
PILLAR_TO_DOMAIN: dict[str, str] = {
    "environment_determinism": "determinism",
    "fast_guardrails": "interfaces",
    "type_contracts": "interfaces",
    "verification_trust": "testing",
    "verification_speed": "testing",
    "documentation_structure": "structure",
    "inline_documentation": "structure",
    "contribution_contract": "ergonomics",
    "agentic_security": "security",
    "secret_hygiene": "security",
    "telemetry_tracing": "ergonomics",
    "structured_logging_cost": "ergonomics",
    "eval_frameworks": "testing",
    "golden_datasets": "testing",
    "distribution_dx": "ergonomics",
}


# Pillar to v1 category mapping for backward compatibility
PILLAR_TO_CATEGORY: dict[str, str] = {
    "environment_determinism": "deterministic_setup",
    "fast_guardrails": "build_and_run",
    "type_contracts": "static_guardrails",
    "verification_trust": "test_feedback_loop",
    "verification_speed": "test_feedback_loop",
    "documentation_structure": "discoverability",
    "inline_documentation": "discoverability",
    "contribution_contract": "security_and_governance",
    "agentic_security": "security_and_governance",
    "secret_hygiene": "security_and_governance",
    "telemetry_tracing": "observability",
    "structured_logging_cost": "observability",
    "eval_frameworks": "security_and_governance",
    "golden_datasets": "security_and_governance",
    "distribution_dx": "build_and_run",
}


# Gate checks for each maturity level
GATE_CHECKS: dict[int, list[str]] = {
    3: [  # Level 3 - Standardized
        "dependency_manifest_exists",
        "lockfile_exists",
        "ci_workflow_present",
        "linter_config_present",
        "tests_directory_or_config_exists",
        "readme_has_setup_section",
        "readme_has_test_instructions",
    ],
    4: [  # Level 4 - Optimized
        "precommit_present",
        "fast_linter_python",
        "machine_readable_coverage",
        "test_splitting",
        "python_type_hint_coverage",
        "mypy_strictness",
    ],
    5: [  # Level 5 - Autonomous
        "opentelemetry_present",
        "structured_logging_present",
        "eval_framework_detect",
        "golden_dataset_present",
        "promptfoo_present",
    ],
}


class CheckResult(BaseModel):
    """Result of a single check execution."""

    name: str
    category: str
    status: CheckStatus
    evidence: str = ""
    suggestion: str = ""
    weight: float = 1.0
    pillar: str = ""  # v2: pillar this check belongs to
    gate_level: int | None = None  # v2: if set, this is a gate for that level

    @property
    def passed(self) -> bool:
        """Return True if check passed."""
        return self.status == CheckStatus.PASSED


class PillarScore(BaseModel):
    """Score for a single v2 pillar."""

    name: str
    score: float = 0.0
    max_points: float = 2.0
    checks: list[str] = Field(default_factory=list)
    passed_checks: int = 0
    total_checks: int = 0

    @property
    def percentage(self) -> float:
        """Return score as percentage."""
        if self.max_points == 0:
            return 0.0
        return (self.score / self.max_points) * 100


class DomainScore(BaseModel):
    """Score for a single v3 domain (0-100 scale)."""

    name: str
    description: str = ""
    score: float = 0.0  # 0-100 scale
    weight: float = 0.0  # Percentage weight (0.0-1.0)
    weighted_score: float = 0.0  # score * weight
    checks: list[CheckResult] = Field(default_factory=list)
    passed_checks: int = 0
    total_checks: int = 0
    evidence: list[str] = Field(default_factory=list)  # Collected evidence
    red_flags: list[str] = Field(default_factory=list)  # Immediate failures

    @property
    def percentage(self) -> float:
        """Return score as percentage (same as score for domains)."""
        return self.score


class GateStatus(BaseModel):
    """Status of gate checks for a maturity level."""

    level: int
    passed: bool = True
    required_checks: list[str] = Field(default_factory=list)
    failed_checks: list[str] = Field(default_factory=list)


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
    level: ReadinessLevel = ReadinessLevel.HUMAN_ONLY  # v1 compatibility
    maturity_level: int = 1  # v2: 1-5 scale
    maturity_name: str = "Functional"  # v2: human-readable name
    category_scores: dict[str, CategoryScore] = Field(default_factory=dict)
    pillar_scores: dict[str, PillarScore] = Field(default_factory=dict)  # v2
    gates: dict[str, GateStatus] = Field(default_factory=dict)  # v2
    failed_checks: list[CheckResult] = Field(default_factory=list)
    passed_checks: list[CheckResult] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    fix_first: list[str] = Field(default_factory=list)
    scanned_at: datetime = Field(default_factory=datetime.now)

    # v3 domain-based scoring
    domain_scores: dict[str, DomainScore] = Field(default_factory=dict)
    overall_score: float = 0.0  # Weighted sum of domain scores (0-100)
    grade: AgentGrade = AgentGrade.AGENT_HOSTILE
    grade_description: str = ""
    remediation_items: list[str] = Field(default_factory=list)  # Ordered fix list

    @property
    def percentage(self) -> float:
        """Return total score as percentage."""
        if self.max_score == 0:
            return 0.0
        return (self.score_total / self.max_score) * 100

    @property
    def overall_percentage(self) -> float:
        """Return v3 overall score (already 0-100 scale)."""
        return self.overall_score


class ScanSummary(BaseModel):
    """Summary of a scan across multiple repositories."""

    generated_at: datetime = Field(default_factory=datetime.now)
    config_used: str = "default"
    total_repos: int = 0
    repos: list[RepoResult] = Field(default_factory=list)
    average_score: float = 0.0
    level_distribution: dict[str, int] = Field(default_factory=dict)
    maturity_distribution: dict[str, int] = Field(default_factory=dict)  # v2
    grade_distribution: dict[str, int] = Field(default_factory=dict)  # v3
    average_overall_score: float = 0.0  # v3: weighted average (0-100)

    def calculate_summary(self) -> None:
        """Calculate summary statistics from repo results."""
        if not self.repos:
            return

        self.total_repos = len(self.repos)
        self.average_score = sum(r.score_total for r in self.repos) / self.total_repos

        # Count level distribution (v1)
        self.level_distribution = {}
        for repo in self.repos:
            level = repo.level.value
            self.level_distribution[level] = self.level_distribution.get(level, 0) + 1

        # Count maturity distribution (v2)
        self.maturity_distribution = {}
        for repo in self.repos:
            name = repo.maturity_name
            self.maturity_distribution[name] = (
                self.maturity_distribution.get(name, 0) + 1
            )

        # Count grade distribution (v3)
        self.grade_distribution = {}
        for repo in self.repos:
            grade = repo.grade.value
            self.grade_distribution[grade] = self.grade_distribution.get(grade, 0) + 1

        # Calculate average overall score (v3)
        self.average_overall_score = (
            sum(r.overall_score for r in self.repos) / self.total_repos
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


class DomainConfig(BaseModel):
    """Configuration for a v3 scoring domain."""

    enabled: bool = True
    weight: float = 0.0  # Will be set from DOMAIN_WEIGHTS
    description: str = ""


class ThresholdConfig(BaseModel):
    """Configuration for v2 thresholds."""

    type_hint_coverage_pass: int = 70  # Percentage for Level 4
    type_hint_coverage_optimal: int = 85  # Percentage for Level 5
    docstring_coverage_pass: int = 60  # Percentage for pass
    docstring_coverage_partial: int = 30  # Percentage for partial


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


class AuditConfig(BaseModel):
    """Complete audit configuration."""

    scale_points_total: int = 16
    minimum_passing_score: int = 10
    minimum_overall_score: float = 60.0  # v3: minimum weighted score for pass
    categories: dict[str, CategoryConfig] = Field(default_factory=dict)
    domains: dict[str, DomainConfig] = Field(default_factory=dict)  # v3
    checks: dict[str, CheckConfig] = Field(default_factory=dict)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)  # v2
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
            },
            domains={
                "structure": DomainConfig(
                    weight=DOMAIN_WEIGHTS["structure"],
                    description=DOMAIN_DESCRIPTIONS["structure"],
                ),
                "interfaces": DomainConfig(
                    weight=DOMAIN_WEIGHTS["interfaces"],
                    description=DOMAIN_DESCRIPTIONS["interfaces"],
                ),
                "determinism": DomainConfig(
                    weight=DOMAIN_WEIGHTS["determinism"],
                    description=DOMAIN_DESCRIPTIONS["determinism"],
                ),
                "security": DomainConfig(
                    weight=DOMAIN_WEIGHTS["security"],
                    description=DOMAIN_DESCRIPTIONS["security"],
                ),
                "testing": DomainConfig(
                    weight=DOMAIN_WEIGHTS["testing"],
                    description=DOMAIN_DESCRIPTIONS["testing"],
                ),
                "ergonomics": DomainConfig(
                    weight=DOMAIN_WEIGHTS["ergonomics"],
                    description=DOMAIN_DESCRIPTIONS["ergonomics"],
                ),
            },
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


def get_maturity_for_score(score: float) -> int:
    """Determine maturity level based on score (v2).

    Note: This is the score-based level; actual level may be lower
    if gate checks fail.
    """
    if score <= 4:
        return 1  # Functional
    elif score <= 7:
        return 2  # Documented
    elif score <= 11:
        return 3  # Standardized
    elif score <= 14:
        return 4  # Optimized
    else:
        return 5  # Autonomous


def calculate_maturity_with_gates(
    score_based_level: int, gates: dict[str, GateStatus]
) -> int:
    """Calculate final maturity level considering gate failures.

    The maturity level is the minimum of:
    - The score-based level
    - The highest level where all gates pass

    Args:
        score_based_level: Maturity level based on numeric score.
        gates: Gate status for each level.

    Returns:
        Final maturity level (1-5).
    """
    max_gate_level = score_based_level

    # Check gates from highest to lowest
    for level in range(score_based_level, 2, -1):  # 5, 4, 3 (skip 1, 2 - no gates)
        gate_key = f"level_{level}"
        if gate_key in gates and not gates[gate_key].passed:
            max_gate_level = level - 1

    return max(1, max_gate_level)


def get_maturity_name(level: int) -> str:
    """Get human-readable name for maturity level."""
    return MATURITY_NAMES.get(level, "Unknown")


def get_maturity_description(level: int) -> str:
    """Get description for maturity level."""
    return MATURITY_DESCRIPTIONS.get(level, "")


def get_grade_for_score(score: float) -> AgentGrade:
    """Determine agent grade based on weighted score (v3).

    Args:
        score: Overall weighted score (0-100).

    Returns:
        Agent grade based on score thresholds.
    """
    if score >= 90:
        return AgentGrade.AGENT_FIRST
    elif score >= 75:
        return AgentGrade.AGENT_COMPATIBLE
    elif score >= 60:
        return AgentGrade.HUMAN_FIRST_RISKY
    else:
        return AgentGrade.AGENT_HOSTILE


def get_grade_description(grade: AgentGrade) -> str:
    """Get description for agent grade.

    Args:
        grade: Agent grade enum value.

    Returns:
        Human-readable description of what the grade means.
    """
    return AGENT_GRADE_DESCRIPTIONS.get(grade.value, "")


def calculate_domain_score(passed: int, total: int) -> float:
    """Calculate domain score on 0-100 scale.

    Args:
        passed: Number of passed checks.
        total: Total number of checks.

    Returns:
        Score from 0 to 100.
    """
    if total == 0:
        return 0.0
    return (passed / total) * 100


def calculate_overall_score(domain_scores: dict[str, DomainScore]) -> float:
    """Calculate weighted overall score from domain scores.

    Args:
        domain_scores: Dictionary of domain name to DomainScore.

    Returns:
        Weighted overall score (0-100).
    """
    total = 0.0
    for domain_name, domain in domain_scores.items():
        weight = DOMAIN_WEIGHTS.get(domain_name, 0.0)
        domain.weighted_score = domain.score * weight
        total += domain.weighted_score
    return total
