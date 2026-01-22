"""Build and run checks - task runners and standard commands."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_contains,
    file_exists,
)

TASK_RUNNERS = [
    "Makefile",
    "makefile",
    "GNUmakefile",
    "Taskfile.yml",
    "Taskfile.yaml",
    "justfile",
    "Justfile",
    "magefile.go",
    "tox.ini",
    "noxfile.py",
    "invoke.yaml",
    "tasks.py",
    "Rakefile",
    "build.gradle",
    "build.gradle.kts",
    "pom.xml",
]


@check(
    name="make_or_task_runner_exists",
    category="build_and_run",
    description="Check if a task runner (Makefile, Taskfile, etc.) exists",
    pillar="fast_guardrails",
)
def check_make_or_task_runner_exists(repo_path: Path) -> CheckResult:
    """Check if task runner exists."""
    runner = file_exists(repo_path, *TASK_RUNNERS)
    if runner:
        return CheckResult(
            passed=True,
            evidence=f"Found task runner: {runner.name}",
        )
    return CheckResult(
        passed=False,
        evidence="No task runner found",
        suggestion="Add a Makefile, Taskfile.yml, or justfile with common tasks (build, test, lint, format).",
    )


@check(
    name="package_scripts_or_equivalent",
    category="build_and_run",
    description="Check if package scripts or equivalent automation exists",
    pillar="fast_guardrails",
)
def check_package_scripts_or_equivalent(repo_path: Path) -> CheckResult:
    """Check if package scripts exist."""
    # Check package.json scripts
    package_json = repo_path / "package.json"
    if package_json.exists() and file_contains(package_json, '"scripts"'):
        return CheckResult(
            passed=True,
            evidence="Found scripts section in package.json",
        )

    # Check pyproject.toml scripts
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists() and file_contains(
        pyproject, "[project.scripts]", "[tool.poetry.scripts]", "[tool.hatch.envs"
    ):
        return CheckResult(
            passed=True,
            evidence="Found scripts/commands in pyproject.toml",
        )

    # Check Cargo.toml for binaries
    cargo_toml = repo_path / "Cargo.toml"
    if cargo_toml.exists() and file_contains(cargo_toml, "[[bin]]", "[package]"):
        return CheckResult(
            passed=True,
            evidence="Found binary/package definition in Cargo.toml",
        )

    # Check for task runner as fallback
    runner = file_exists(repo_path, *TASK_RUNNERS)
    if runner:
        return CheckResult(
            passed=True,
            evidence=f"Found task runner as alternative: {runner.name}",
        )

    return CheckResult(
        passed=False,
        evidence="No package scripts or task runner found",
        suggestion="Add scripts to your package manifest or create a task runner file.",
    )


@check(
    name="documented_commands_present",
    category="build_and_run",
    description="Check if common commands are documented or discoverable",
    pillar="distribution_dx",
)
def check_documented_commands_present(repo_path: Path) -> CheckResult:
    """Check if commands are documented."""
    # Check README for command documentation
    readme_files = ["README.md", "README.MD", "README", "readme.md"]
    for readme_name in readme_files:
        readme = repo_path / readme_name
        if readme.exists():
            command_patterns = [
                "make ",
                "npm run",
                "yarn ",
                "pnpm ",
                "cargo ",
                "go ",
                "pytest",
                "python ",
                "uv run",
                "./",
                "task ",
                "just ",
            ]
            found = file_contains(readme, *command_patterns)
            if found:
                return CheckResult(
                    passed=True,
                    evidence=f"Found command documentation in README: '{found}'",
                )

    # Check for Makefile with help target
    makefile = file_exists(repo_path, "Makefile", "makefile", "GNUmakefile")
    if makefile and file_contains(makefile, ".PHONY", "help:"):
        return CheckResult(
            passed=True,
            evidence="Found Makefile with targets (likely self-documenting)",
        )

    # Check for CONTRIBUTING.md with commands
    contributing = repo_path / "CONTRIBUTING.md"
    if contributing.exists():
        command_patterns = ["make ", "npm ", "pytest", "cargo ", "go "]
        found = file_contains(contributing, *command_patterns)
        if found:
            return CheckResult(
                passed=True,
                evidence=f"Found command documentation in CONTRIBUTING.md: '{found}'",
            )

    return CheckResult(
        passed=False,
        evidence="No documented commands found",
        suggestion="Document common commands (build, test, lint) in README or add a Makefile with help target.",
    )
