"""Agent ergonomics checks for ARA v3 specification.

These checks evaluate whether the repo is pleasant for an agent to work in:
- Machine-readable config files
- Deterministic commands
- Clear failure messages
- Explicit contribution rules
- Agent-readiness manifests
"""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_exists,
    glob_files,
    read_file_safe,
)


@check(
    name="machine_readable_configs",
    category="observability",
    description="Check for machine-readable configuration files",
    domain="ergonomics",
)
def check_machine_readable_configs(repo_path: Path) -> CheckResult:
    """Check for structured, machine-readable configuration.

    Prefers: TOML, YAML, JSON over ad-hoc formats.
    """
    config_patterns = [
        "*.toml",
        "*.yaml",
        "*.yml",
        "*.json",
    ]

    found_configs: list[str] = []

    # Check for pyproject.toml (best for Python)
    if file_exists(repo_path, "pyproject.toml"):
        found_configs.append("pyproject.toml")

    # Check for other machine-readable configs
    for pattern in config_patterns:
        matches = glob_files(repo_path, pattern)
        # Filter to actual config files (not data)
        for match in matches[:5]:
            if "config" in match.name.lower() or match.name in [
                "settings.yaml",
                "config.yaml",
                "app.yaml",
                "tsconfig.json",
                "package.json",
            ]:
                found_configs.append(match.name)

    if found_configs:
        return CheckResult(
            passed=True,
            evidence=f"Machine-readable configs: {', '.join(found_configs[:3])}",
        )

    # Check for .env files (less ideal but acceptable)
    if file_exists(repo_path, ".env.example", ".env.sample"):
        return CheckResult(
            passed=True,
            partial=True,
            evidence="Environment variable configuration only",
        )

    return CheckResult(
        passed=False,
        evidence="No machine-readable configuration files found",
        suggestion="Use TOML, YAML, or JSON for configuration instead of ad-hoc formats.",
    )


@check(
    name="deterministic_commands",
    category="build_and_run",
    description="Check for deterministic build/test commands",
    domain="ergonomics",
)
def check_deterministic_commands(repo_path: Path) -> CheckResult:
    """Check that build/test commands are deterministic and documented.

    Looks for:
    - Makefile with standard targets
    - npm scripts
    - Task runner configuration
    """
    # Check Makefile
    makefile = file_exists(repo_path, "Makefile")
    if makefile:
        content = read_file_safe(makefile)
        if content:
            targets = []
            for target in ["build", "test", "lint", "format", "install"]:
                if f"{target}:" in content:
                    targets.append(target)
            if len(targets) >= 2:
                return CheckResult(
                    passed=True,
                    evidence=f"Makefile with targets: {', '.join(targets)}",
                )

    # Check package.json scripts
    package_json = repo_path / "package.json"
    if package_json.exists():
        content = read_file_safe(package_json)
        if content and '"scripts"' in content:
            return CheckResult(
                passed=True,
                evidence="package.json with npm scripts",
            )

    # Check for task runners
    task_runners = [
        "Taskfile.yml",
        "justfile",
        "tox.ini",
        "noxfile.py",
    ]
    for runner in task_runners:
        if file_exists(repo_path, runner):
            return CheckResult(
                passed=True,
                evidence=f"Task runner found: {runner}",
            )

    # Check pyproject.toml for scripts
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = read_file_safe(pyproject)
        if content and "[tool.hatch" in content:
            return CheckResult(
                passed=True,
                evidence="Hatch task runner configured",
            )

    return CheckResult(
        passed=False,
        evidence="No deterministic command interface found",
        suggestion="Add a Makefile or task runner with build, test, lint targets.",
    )


@check(
    name="clear_error_messages",
    category="observability",
    description="Check for structured error handling with clear messages",
    domain="ergonomics",
)
def check_clear_error_messages(repo_path: Path) -> CheckResult:
    """Check for structured error handling.

    Looks for:
    - Custom exception classes
    - Logging configuration
    - Error message patterns
    """
    py_files = glob_files(repo_path, "**/*.py")[:30]
    py_files = [f for f in py_files if "test" not in str(f).lower()]

    has_custom_exceptions = False
    has_logging = False
    has_structured_errors = False

    for py_file in py_files:
        content = read_file_safe(py_file)
        if not content:
            continue

        # Check for custom exception classes
        if "class " in content and "Exception" in content:
            has_custom_exceptions = True

        # Check for logging
        if "import logging" in content or "from loguru" in content:
            has_logging = True

        # Check for structured error handling
        if "raise " in content and ('f"' in content or "f'" in content):
            has_structured_errors = True

    findings = []
    if has_custom_exceptions:
        findings.append("custom exceptions")
    if has_logging:
        findings.append("logging")
    if has_structured_errors:
        findings.append("formatted error messages")

    if len(findings) >= 2:
        return CheckResult(
            passed=True,
            evidence=f"Good error handling: {', '.join(findings)}",
        )
    elif findings:
        return CheckResult(
            passed=True,
            partial=True,
            evidence=f"Partial error handling: {', '.join(findings)}",
        )

    return CheckResult(
        passed=False,
        evidence="No structured error handling detected",
        suggestion="Add custom exceptions and logging for clear error messages.",
    )


@check(
    name="contribution_rules_explicit",
    category="security_and_governance",
    description="Check for explicit contribution guidelines",
    domain="ergonomics",
)
def check_contribution_rules_explicit(repo_path: Path) -> CheckResult:
    """Check for contribution documentation.

    Looks for:
    - CONTRIBUTING.md
    - Development section in README
    - PR templates
    """
    # Check for CONTRIBUTING.md
    if file_exists(
        repo_path, "CONTRIBUTING.md", "CONTRIBUTING.rst", ".github/CONTRIBUTING.md"
    ):
        return CheckResult(
            passed=True,
            evidence="CONTRIBUTING.md found",
        )

    # Check for PR template
    if file_exists(
        repo_path,
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/pull_request_template.md",
    ):
        return CheckResult(
            passed=True,
            evidence="PR template found",
        )

    # Check README for development section
    readme = file_exists(repo_path, "README.md", "README.rst")
    if readme:
        content = read_file_safe(readme)
        if content and any(
            pattern in content.lower()
            for pattern in [
                "## contributing",
                "## development",
                "## developer",
                "how to contribute",
            ]
        ):
            return CheckResult(
                passed=True,
                evidence="README contains contribution guidelines",
            )

    return CheckResult(
        passed=False,
        evidence="No contribution guidelines found",
        suggestion="Add CONTRIBUTING.md or a Contributing section in README.",
    )


@check(
    name="agent_manifest_present",
    category="observability",
    description="Check for agent-readiness manifest (CLAUDE.md, .cursorrules, etc.)",
    domain="ergonomics",
)
def check_agent_manifest_present(repo_path: Path) -> CheckResult:
    """Check for agent-specific configuration or manifests.

    Looks for:
    - CLAUDE.md (Claude Code)
    - .cursorrules (Cursor)
    - .github/copilot-instructions.md
    - .aider (Aider)
    - AGENTS.md
    """
    agent_files = [
        "CLAUDE.md",
        ".claude",
        ".cursorrules",
        ".cursor",
        ".github/copilot-instructions.md",
        ".aider",
        "AGENTS.md",
        ".ai",
        "ai-instructions.md",
    ]

    for agent_file in agent_files:
        if file_exists(repo_path, agent_file):
            return CheckResult(
                passed=True,
                evidence=f"Agent manifest found: {agent_file}",
            )

    # Check for .claude directory
    if (repo_path / ".claude").is_dir():
        return CheckResult(
            passed=True,
            evidence="Claude configuration directory found",
        )

    return CheckResult(
        passed=False,
        evidence="No agent-readiness manifest found",
        suggestion="Add CLAUDE.md or similar agent instructions file for better agent compatibility.",
    )


@check(
    name="command_reproducibility",
    category="build_and_run",
    description="Check that commands produce reproducible results",
    domain="ergonomics",
)
def check_command_reproducibility(repo_path: Path) -> CheckResult:
    """Check for reproducibility markers in build commands.

    Looks for:
    - Lock files (checked elsewhere, but referenced here)
    - Deterministic flags in configs
    - CI runs same commands as local
    """
    # Check for CI that mirrors local commands
    workflows = glob_files(repo_path, ".github/workflows/*.yml")
    makefile = file_exists(repo_path, "Makefile")

    if makefile and workflows:
        makefile_content = read_file_safe(makefile)
        for workflow in workflows:
            ci_content = read_file_safe(workflow)
            # Check if CI uses make commands
            if makefile_content and ci_content and "make " in ci_content:
                return CheckResult(
                    passed=True,
                    evidence="CI uses same Makefile commands as local development",
                )

    # Check for docker/containers (reproducible by design)
    if file_exists(
        repo_path, "Dockerfile", "docker-compose.yml", "docker-compose.yaml"
    ):
        return CheckResult(
            passed=True,
            evidence="Docker configuration ensures reproducible environment",
        )

    # Check for devcontainer
    if file_exists(repo_path, ".devcontainer/devcontainer.json", ".devcontainer.json"):
        return CheckResult(
            passed=True,
            evidence="Dev container ensures reproducible environment",
        )

    # Check for Nix
    if file_exists(repo_path, "flake.nix", "shell.nix", "default.nix"):
        return CheckResult(
            passed=True,
            evidence="Nix configuration ensures reproducible builds",
        )

    # Partial pass if lockfiles exist (handled elsewhere but good signal)
    lock_files = ["uv.lock", "poetry.lock", "package-lock.json", "Cargo.lock"]
    for lock in lock_files:
        if file_exists(repo_path, lock):
            return CheckResult(
                passed=True,
                partial=True,
                evidence=f"Lock file ({lock}) provides partial reproducibility",
            )

    return CheckResult(
        passed=False,
        evidence="No reproducibility guarantees detected",
        suggestion="Use Docker, devcontainer, or ensure CI mirrors local commands.",
    )
