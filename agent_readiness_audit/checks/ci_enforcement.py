"""CI enforcement checks - continuous integration configuration."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_contains,
    file_exists,
    glob_files,
)

CI_PATHS = [
    ".github/workflows",
    ".gitlab-ci.yml",
    ".gitlab-ci.yaml",
    "azure-pipelines.yml",
    "azure-pipelines.yaml",
    "bitbucket-pipelines.yml",
    ".circleci/config.yml",
    ".circleci/config.yaml",
    "Jenkinsfile",
    ".travis.yml",
    ".travis.yaml",
    "appveyor.yml",
    ".drone.yml",
    ".buildkite/pipeline.yml",
]


@check(
    name="ci_workflow_present",
    category="ci_enforcement",
    description="Check if CI workflow configuration exists",
    pillar="verification_trust",
    gate_for=[3],
)
def check_ci_workflow_present(repo_path: Path) -> CheckResult:
    """Check if CI is configured."""
    # Check for GitHub Actions
    gh_workflows = repo_path / ".github" / "workflows"
    if gh_workflows.is_dir():
        workflow_files = glob_files(gh_workflows, "*.yml") + glob_files(
            gh_workflows, "*.yaml"
        )
        if workflow_files:
            return CheckResult(
                passed=True,
                evidence=f"Found GitHub Actions workflows: {len(workflow_files)} file(s)",
            )

    # Check for other CI systems
    ci_configs = [
        ".gitlab-ci.yml",
        ".gitlab-ci.yaml",
        "azure-pipelines.yml",
        "azure-pipelines.yaml",
        "bitbucket-pipelines.yml",
        ".circleci/config.yml",
        ".circleci/config.yaml",
        "Jenkinsfile",
        ".travis.yml",
        ".travis.yaml",
        "appveyor.yml",
        ".drone.yml",
        ".buildkite/pipeline.yml",
    ]

    for ci_config in ci_configs:
        if (repo_path / ci_config).exists():
            return CheckResult(
                passed=True,
                evidence=f"Found CI configuration: {ci_config}",
            )

    return CheckResult(
        passed=False,
        evidence="No CI workflow configuration found",
        suggestion="Add CI configuration (e.g., .github/workflows/ci.yml for GitHub Actions).",
    )


@check(
    name="ci_runs_tests_or_lint",
    category="ci_enforcement",
    description="Check if CI runs tests or linting",
    pillar="verification_trust",
)
def check_ci_runs_tests_or_lint(repo_path: Path) -> CheckResult:
    """Check if CI runs tests or lint."""
    # Check GitHub Actions workflows
    gh_workflows = repo_path / ".github" / "workflows"
    if gh_workflows.is_dir():
        workflow_files = glob_files(gh_workflows, "*.yml") + glob_files(
            gh_workflows, "*.yaml"
        )
        for workflow in workflow_files:
            # Check for test/lint commands
            test_patterns = [
                "pytest",
                "npm test",
                "yarn test",
                "pnpm test",
                "cargo test",
                "go test",
                "make test",
                "uv run pytest",
                "ruff",
                "eslint",
                "mypy",
                "flake8",
                "black --check",
                "prettier --check",
                "lint",
                "typecheck",
            ]
            found = file_contains(workflow, *test_patterns)
            if found:
                return CheckResult(
                    passed=True,
                    evidence=f"Found test/lint command in {workflow.name}: '{found}'",
                )

    # Check GitLab CI
    gitlab_ci = file_exists(repo_path, ".gitlab-ci.yml", ".gitlab-ci.yaml")
    if gitlab_ci:
        test_patterns = ["pytest", "npm test", "cargo test", "go test", "lint", "test"]
        found = file_contains(gitlab_ci, *test_patterns)
        if found:
            return CheckResult(
                passed=True,
                evidence=f"Found test/lint command in GitLab CI: '{found}'",
            )

    # Check other CI configs
    other_ci_files = [
        "azure-pipelines.yml",
        "bitbucket-pipelines.yml",
        ".circleci/config.yml",
        ".travis.yml",
    ]
    for ci_file in other_ci_files:
        ci_path = repo_path / ci_file
        if ci_path.exists():
            test_patterns = ["test", "lint", "pytest", "npm test", "cargo test"]
            found = file_contains(ci_path, *test_patterns)
            if found:
                return CheckResult(
                    passed=True,
                    evidence=f"Found test/lint command in {ci_file}: '{found}'",
                )

    # Check if CI exists but no test/lint found
    ci_exists = check_ci_workflow_present(repo_path).passed
    if ci_exists:
        return CheckResult(
            passed=False,
            evidence="CI configuration exists but no test/lint commands detected",
            suggestion="Add test and lint steps to your CI workflow.",
        )

    return CheckResult(
        passed=False,
        evidence="No CI configuration with test/lint commands found",
        suggestion="Add CI configuration that runs tests and linting on PRs.",
    )
