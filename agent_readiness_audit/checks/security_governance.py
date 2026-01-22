"""Security and governance checks - security policies and hygiene."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_contains,
    file_exists,
)


@check(
    name="gitignore_present",
    category="security_and_governance",
    description="Check if .gitignore file exists",
)
def check_gitignore_present(repo_path: Path) -> CheckResult:
    """Check if .gitignore exists."""
    gitignore = repo_path / ".gitignore"
    if gitignore.exists():
        # Check if it has meaningful content
        content = gitignore.read_text(encoding="utf-8", errors="ignore")
        non_empty_lines = [
            line for line in content.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if non_empty_lines:
            return CheckResult(
                passed=True,
                evidence=f"Found .gitignore with {len(non_empty_lines)} pattern(s)",
            )
        return CheckResult(
            passed=True,
            evidence="Found .gitignore (appears to be empty or only comments)",
        )

    return CheckResult(
        passed=False,
        evidence="No .gitignore file found",
        suggestion="Add a .gitignore file to exclude build artifacts, dependencies, and sensitive files.",
    )


@check(
    name="env_example_or_secrets_docs_present",
    category="security_and_governance",
    description="Check if environment variable documentation exists",
)
def check_env_example_or_secrets_docs_present(repo_path: Path) -> CheckResult:
    """Check if env example or secrets documentation exists."""
    # Check for .env.example files
    env_examples = [
        ".env.example",
        ".env.sample",
        ".env.template",
        "env.example",
        ".env.local.example",
    ]
    env_file = file_exists(repo_path, *env_examples)
    if env_file:
        return CheckResult(
            passed=True,
            evidence=f"Found environment template: {env_file.name}",
        )

    # Check for secrets documentation
    secrets_docs = [
        "docs/secrets.md",
        "docs/configuration.md",
        "docs/environment.md",
        "docs/env.md",
        "SECRETS.md",
        "CONFIGURATION.md",
    ]
    doc_file = file_exists(repo_path, *secrets_docs)
    if doc_file:
        return CheckResult(
            passed=True,
            evidence=f"Found configuration documentation: {doc_file}",
        )

    # Check README for environment variable documentation
    readme_files = ["README.md", "README.MD", "README", "readme.md"]
    for readme_name in readme_files:
        readme = repo_path / readme_name
        if readme.exists():
            env_patterns = [
                "environment variable",
                "env var",
                ".env",
                "configuration",
                "API_KEY",
                "SECRET",
            ]
            found = file_contains(readme, *env_patterns)
            if found:
                return CheckResult(
                    passed=True,
                    evidence=f"Found environment documentation in README: '{found}'",
                )

    # Check if project likely needs env vars
    has_env_usage = False
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        if file_contains(pyproject, "python-dotenv", "environs", "pydantic-settings"):
            has_env_usage = True

    package_json = repo_path / "package.json"
    if package_json.exists():
        if file_contains(package_json, "dotenv", "env"):
            has_env_usage = True

    if has_env_usage:
        return CheckResult(
            passed=False,
            evidence="Project uses environment variables but no .env.example found",
            suggestion="Add a .env.example file documenting required environment variables.",
        )

    # Pass if project doesn't seem to use env vars
    return CheckResult(
        passed=True,
        evidence="No environment variable usage detected (or documentation not required)",
    )


@check(
    name="security_policy_present_or_baseline",
    category="security_and_governance",
    description="Check if security policy or baseline documentation exists",
)
def check_security_policy_present_or_baseline(repo_path: Path) -> CheckResult:
    """Check if security policy exists."""
    # Check for SECURITY.md
    security_files = [
        "SECURITY.md",
        "security.md",
        ".github/SECURITY.md",
        "docs/SECURITY.md",
        "docs/security.md",
    ]
    security_file = file_exists(repo_path, *security_files)
    if security_file:
        return CheckResult(
            passed=True,
            evidence=f"Found security policy: {security_file}",
        )

    # Check for security-related content in other files
    contributing = repo_path / "CONTRIBUTING.md"
    if contributing.exists():
        if file_contains(contributing, "security", "vulnerability", "responsible disclosure"):
            return CheckResult(
                passed=True,
                evidence="Found security guidance in CONTRIBUTING.md",
            )

    # Check README for security section
    readme_files = ["README.md", "README.MD", "README", "readme.md"]
    for readme_name in readme_files:
        readme = repo_path / readme_name
        if readme.exists():
            if file_contains(readme, "## security", "### security", "# security"):
                return CheckResult(
                    passed=True,
                    evidence="Found security section in README",
                )

    # Check for GitHub security features
    github_dir = repo_path / ".github"
    if github_dir.is_dir():
        # Check for dependabot
        dependabot = file_exists(
            github_dir,
            "dependabot.yml",
            "dependabot.yaml",
        )
        if dependabot:
            return CheckResult(
                passed=True,
                evidence="Found Dependabot configuration (security baseline)",
            )

    return CheckResult(
        passed=False,
        evidence="No security policy or baseline documentation found",
        suggestion="Add a SECURITY.md file with vulnerability reporting instructions.",
    )
