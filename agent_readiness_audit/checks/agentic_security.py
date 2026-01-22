"""Agentic security checks - prompt testing and secret scanning."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    dir_exists,
    file_exists,
)


@check(
    name="promptfoo_present",
    category="security_and_governance",
    description="Check if promptfoo or equivalent prompt testing is configured",
    pillar="agentic_security",
    weight=2.0,
    gate_for=[5],
)
def check_promptfoo_present(repo_path: Path) -> CheckResult:
    """Check if prompt red-teaming/testing is configured."""
    # Check for promptfoo configuration
    promptfoo_configs = [
        "promptfooconfig.yaml",
        "promptfooconfig.yml",
        "promptfoo.yaml",
        "promptfoo.yml",
        ".promptfoo.yaml",
        ".promptfoo.yml",
    ]

    for config in promptfoo_configs:
        if (repo_path / config).exists():
            return CheckResult(
                passed=True,
                evidence=f"Found promptfoo configuration: {config}",
            )

    # Check for .promptfoo directory
    promptfoo_dir = repo_path / ".promptfoo"
    if promptfoo_dir.is_dir():
        return CheckResult(
            passed=True,
            evidence="Found .promptfoo/ directory",
        )

    # Check package.json for promptfoo
    package_json = repo_path / "package.json"
    if package_json.exists():
        content = package_json.read_text(encoding="utf-8", errors="ignore").lower()
        if "promptfoo" in content:
            return CheckResult(
                passed=True,
                evidence="Found promptfoo in package.json dependencies",
            )

    # Check pyproject.toml for promptfoo
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore").lower()
        if "promptfoo" in content:
            return CheckResult(
                passed=True,
                evidence="Found promptfoo in pyproject.toml dependencies",
            )

    # Check for alternative prompt testing tools
    # giskard for ML testing
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore").lower()
        if "giskard" in content:
            return CheckResult(
                passed=True,
                evidence="Found giskard (ML testing) in dependencies",
            )

    return CheckResult(
        passed=False,
        evidence="No prompt testing configuration found",
        suggestion="Add promptfoo for prompt red-teaming: npm i -g promptfoo && promptfoo init",
    )


@check(
    name="prompt_secret_scanning",
    category="security_and_governance",
    description="Check for secret scanning configuration in prompt/template directories",
    pillar="secret_hygiene",
    weight=1.0,
)
def check_prompt_secret_scanning(repo_path: Path) -> CheckResult:
    """Check for secret scanning on prompt templates."""
    # Check for gitleaks configuration
    gitleaks_config = file_exists(
        repo_path, ".gitleaks.toml", "gitleaks.toml", ".gitleaks.yaml"
    )
    if gitleaks_config:
        return CheckResult(
            passed=True,
            evidence=f"Found gitleaks configuration: {gitleaks_config.name}",
        )

    # Check for TruffleHog configuration
    trufflehog_config = file_exists(repo_path, ".trufflehog.yml", "trufflehog.yaml")
    if trufflehog_config:
        return CheckResult(
            passed=True,
            evidence=f"Found TruffleHog configuration: {trufflehog_config.name}",
        )

    # Check for detect-secrets configuration
    detect_secrets_config = file_exists(repo_path, ".secrets.baseline")
    if detect_secrets_config:
        return CheckResult(
            passed=True,
            evidence="Found detect-secrets baseline",
        )

    # Check GitHub Actions for secret scanning
    gh_workflows = repo_path / ".github" / "workflows"
    if gh_workflows.is_dir():
        for workflow in gh_workflows.glob("*.yml"):
            content = workflow.read_text(encoding="utf-8", errors="ignore").lower()
            if any(
                tool in content
                for tool in ["gitleaks", "trufflehog", "detect-secrets", "secret"]
            ):
                return CheckResult(
                    passed=True,
                    evidence=f"Found secret scanning in CI: {workflow.name}",
                )
        for workflow in gh_workflows.glob("*.yaml"):
            content = workflow.read_text(encoding="utf-8", errors="ignore").lower()
            if any(
                tool in content
                for tool in ["gitleaks", "trufflehog", "detect-secrets", "secret"]
            ):
                return CheckResult(
                    passed=True,
                    evidence=f"Found secret scanning in CI: {workflow.name}",
                )

    # Check pre-commit for secret scanning
    precommit = file_exists(
        repo_path, ".pre-commit-config.yaml", ".pre-commit-config.yml"
    )
    if precommit:
        content = precommit.read_text(encoding="utf-8", errors="ignore").lower()
        if any(
            tool in content
            for tool in ["gitleaks", "trufflehog", "detect-secrets", "secret"]
        ):
            return CheckResult(
                passed=True,
                evidence="Found secret scanning in pre-commit hooks",
            )

    # Check if prompts directory exists (more important to have scanning then)
    prompts_dir = dir_exists(repo_path, "prompts", "templates", "prompt_templates")
    if prompts_dir:
        return CheckResult(
            passed=False,
            evidence=f"Found prompts directory ({prompts_dir.name}) but no secret scanning configured",
            suggestion="Add gitleaks or TruffleHog to scan prompts for hardcoded secrets.",
        )

    # No prompts dir and no secret scanning - partial pass
    return CheckResult(
        passed=True,
        partial=True,
        evidence="No prompts directory found (secret scanning recommended but not critical)",
        suggestion="Consider adding gitleaks for secret scanning as a best practice.",
    )
