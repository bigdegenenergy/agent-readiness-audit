"""Configuration loading and management for Agent Readiness Audit."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from agent_readiness_audit.models import (
    AuditConfig,
    CategoryConfig,
    CheckConfig,
    DetectionConfig,
)

DEFAULT_CONFIG_FILENAME = ".agent_readiness_audit.toml"


def find_config_file(start_path: Path | None = None) -> Path | None:
    """Find configuration file by searching up the directory tree.

    Args:
        start_path: Starting directory for search. Defaults to current directory.

    Returns:
        Path to config file if found, None otherwise.
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    while current != current.parent:
        config_path = current / DEFAULT_CONFIG_FILENAME
        if config_path.exists():
            return config_path
        current = current.parent

    # Check home directory as last resort
    home_config = Path.home() / DEFAULT_CONFIG_FILENAME
    if home_config.exists():
        return home_config

    return None


def load_config(config_path: Path | None = None) -> AuditConfig:
    """Load configuration from TOML file.

    Args:
        config_path: Explicit path to config file. If None, searches for default.

    Returns:
        Loaded configuration, or default if no config found.
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None or not config_path.exists():
        return AuditConfig.default()

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    return parse_config(data)


def parse_config(data: dict[str, Any]) -> AuditConfig:
    """Parse configuration dictionary into AuditConfig.

    Args:
        data: Raw configuration dictionary from TOML.

    Returns:
        Parsed AuditConfig object.
    """
    config = AuditConfig.default()

    # Parse scoring section
    if "scoring" in data:
        scoring = data["scoring"]
        if "scale_points_total" in scoring:
            config.scale_points_total = scoring["scale_points_total"]
        if "minimum_passing_score" in scoring:
            config.minimum_passing_score = scoring["minimum_passing_score"]

    # Parse categories section
    if "categories" in data:
        for cat_name, cat_data in data["categories"].items():
            if isinstance(cat_data, dict):
                config.categories[cat_name] = CategoryConfig(
                    enabled=cat_data.get("enabled", True),
                    max_points=cat_data.get("max_points", 2.0),
                    description=cat_data.get("description", ""),
                )

    # Parse checks section
    if "checks" in data:
        for check_name, check_data in data["checks"].items():
            if isinstance(check_data, dict):
                config.checks[check_name] = CheckConfig(
                    enabled=check_data.get("enabled", True),
                    weight=check_data.get("weight", 1.0),
                )

    # Parse detection section
    if "detection" in data:
        detection = data["detection"]
        config.detection = DetectionConfig(
            readme_filenames=detection.get(
                "readme_filenames", config.detection.readme_filenames
            ),
            ci_paths=detection.get("ci_paths", config.detection.ci_paths),
            python_dependency_files=detection.get(
                "python_dependency_files", config.detection.python_dependency_files
            ),
            node_dependency_files=detection.get(
                "node_dependency_files", config.detection.node_dependency_files
            ),
            task_runners=detection.get("task_runners", config.detection.task_runners),
            python_lint_configs=detection.get(
                "python_lint_configs", config.detection.python_lint_configs
            ),
            python_format_configs=detection.get(
                "python_format_configs", config.detection.python_format_configs
            ),
            python_type_configs=detection.get(
                "python_type_configs", config.detection.python_type_configs
            ),
            env_examples=detection.get("env_examples", config.detection.env_examples),
        )

    # Parse output section
    if "output" in data:
        output = data["output"]
        if "default_format" in output:
            config.default_format = output["default_format"]
        if "include_recommendations" in output:
            config.include_recommendations = output["include_recommendations"]
        if "show_evidence" in output:
            config.show_evidence = output["show_evidence"]

    return config


def generate_default_config() -> str:
    """Generate default configuration TOML content.

    Returns:
        TOML string with default configuration and comments.
    """
    return """# Agent Readiness Audit Configuration
# This file customizes the scoring and check behavior

[scoring]
# Total points possible (sum of all category max_points)
scale_points_total = 16

# Minimum score to pass in strict mode (0-16)
minimum_passing_score = 10

# Score to level mapping
[[scoring.levels]]
min = 0
max = 5
level = "Human-Only Repo"

[[scoring.levels]]
min = 6
max = 9
level = "Assisted Agent"

[[scoring.levels]]
min = 10
max = 13
level = "Semi-Autonomous"

[[scoring.levels]]
min = 14
max = 16
level = "Agent-Ready Factory"

[categories]
# Enable/disable specific categories
# Each category contributes 0-2 points

[categories.discoverability]
enabled = true
max_points = 2
description = "Repo orientation: README presence and basic onboarding clarity"

[categories.deterministic_setup]
enabled = true
max_points = 2
description = "Reproducible dependency setup and pinning"

[categories.build_and_run]
enabled = true
max_points = 2
description = "Standard commands exist for build/test/lint/format"

[categories.test_feedback_loop]
enabled = true
max_points = 2
description = "Tests exist and are runnable with reasonable defaults"

[categories.static_guardrails]
enabled = true
max_points = 2
description = "Linters/formatters/types reduce ambiguity for agents"

[categories.observability]
enabled = true
max_points = 2
description = "Logging/metrics help agents validate behavior changes"

[categories.ci_enforcement]
enabled = true
max_points = 2
description = "CI exists and validates changes"

[categories.security_and_governance]
enabled = true
max_points = 2
description = "Baseline hygiene around secrets and contribution policy"

[checks]
# Override specific check weights or disable checks
# Format: check_name = { enabled = true, weight = 1.0 }

# Example: Disable a specific check
# readme_has_test_instructions = { enabled = false }

# Example: Increase weight of a check
# ci_workflow_present = { weight = 2.0 }

[detection]
# Customize file detection patterns

readme_filenames = ["README.md", "README.MD", "README", "readme.md"]

ci_paths = [
    ".github/workflows",
    ".gitlab-ci.yml",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml"
]

python_dependency_files = [
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "poetry.lock",
    "requirements.lock"
]

node_dependency_files = [
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock"
]

task_runners = [
    "Makefile",
    "Taskfile.yml",
    "justfile",
    "magefile.go",
    "tox.ini",
    "noxfile.py"
]

[output]
# Default output settings

# Default format for stdout
default_format = "table"

# Include fix-first recommendations
include_recommendations = true

# Show evidence details
show_evidence = true
"""
