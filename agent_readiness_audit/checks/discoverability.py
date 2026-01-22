"""Discoverability checks - README presence and quality."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_contains,
    file_exists,
)

README_FILENAMES = ["README.md", "README.MD", "README", "readme.md", "Readme.md"]


@check(
    name="readme_exists",
    category="discoverability",
    description="Check if a README file exists in the repository root",
    pillar="distribution_dx",
    gate_for=[2],
)
def check_readme_exists(repo_path: Path) -> CheckResult:
    """Check if README exists."""
    readme = file_exists(repo_path, *README_FILENAMES)
    if readme:
        return CheckResult(
            passed=True,
            evidence=f"Found README at: {readme.name}",
        )
    return CheckResult(
        passed=False,
        evidence="No README file found in repository root",
        suggestion="Add a README.md file with project overview, setup instructions, and usage examples.",
    )


@check(
    name="readme_has_setup_section",
    category="discoverability",
    description="Check if README contains setup/installation instructions",
    pillar="distribution_dx",
    gate_for=[2],
)
def check_readme_has_setup_section(repo_path: Path) -> CheckResult:
    """Check if README has setup instructions."""
    readme = file_exists(repo_path, *README_FILENAMES)
    if not readme:
        return CheckResult(
            passed=False,
            evidence="No README file found",
            suggestion="Add a README.md file with setup instructions.",
        )

    setup_patterns = [
        "## installation",
        "## setup",
        "## getting started",
        "## quick start",
        "## quickstart",
        "### installation",
        "### setup",
        "### getting started",
        "# installation",
        "# setup",
        "pip install",
        "npm install",
        "yarn add",
        "pnpm add",
        "uv add",
        "cargo install",
        "go install",
        "brew install",
    ]

    found = file_contains(readme, *setup_patterns)
    if found:
        return CheckResult(
            passed=True,
            evidence=f"Found setup-related content: '{found}'",
        )

    return CheckResult(
        passed=False,
        evidence="No setup/installation section found in README",
        suggestion="Add an 'Installation' or 'Getting Started' section to your README.",
    )


@check(
    name="readme_has_test_instructions",
    category="discoverability",
    description="Check if README contains test running instructions",
    pillar="distribution_dx",
    gate_for=[3],
)
def check_readme_has_test_instructions(repo_path: Path) -> CheckResult:
    """Check if README has test instructions."""
    readme = file_exists(repo_path, *README_FILENAMES)
    if not readme:
        return CheckResult(
            passed=False,
            evidence="No README file found",
            suggestion="Add a README.md file with test instructions.",
        )

    test_patterns = [
        "## testing",
        "## tests",
        "## running tests",
        "### testing",
        "### tests",
        "### running tests",
        "# testing",
        "# tests",
        "pytest",
        "npm test",
        "yarn test",
        "pnpm test",
        "cargo test",
        "go test",
        "make test",
        "uv run pytest",
    ]

    found = file_contains(readme, *test_patterns)
    if found:
        return CheckResult(
            passed=True,
            evidence=f"Found test-related content: '{found}'",
        )

    return CheckResult(
        passed=False,
        evidence="No test instructions found in README",
        suggestion="Add a 'Testing' section to your README explaining how to run tests.",
    )
