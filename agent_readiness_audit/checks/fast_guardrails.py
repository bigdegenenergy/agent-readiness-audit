"""Fast guardrails checks for v2 agent readiness."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_exists,
    read_file_safe,
)


@check(
    name="fast_linter_python",
    category="static_guardrails",
    description="Check for fast Python linter (ruff preferred)",
    pillar="fast_guardrails",
    gate_level=4,
)
def check_fast_linter_python(repo_path: Path) -> CheckResult:
    """Check if ruff or equivalent fast linter is configured.

    Ruff is preferred for sub-second feedback loops.
    Pass if ruff is configured.
    Partial if flake8/pylint only.
    """
    # Check for ruff configuration
    ruff_toml = file_exists(repo_path, "ruff.toml", ".ruff.toml")
    if ruff_toml:
        return CheckResult(
            passed=True,
            evidence=f"ruff configured via {ruff_toml.name}",
        )

    # Check pyproject.toml for [tool.ruff]
    pyproject = file_exists(repo_path, "pyproject.toml")
    if pyproject:
        content = read_file_safe(pyproject)
        if content and "[tool.ruff]" in content:
            return CheckResult(
                passed=True,
                evidence="ruff configured in pyproject.toml [tool.ruff]",
            )

    # Check for other linters (partial pass)
    if file_exists(repo_path, ".flake8", "setup.cfg"):
        cfg = file_exists(repo_path, ".flake8", "setup.cfg")
        if cfg:
            content = read_file_safe(cfg)
            if content and ("[flake8]" in content or "flake8" in cfg.name):
                return CheckResult(
                    passed=False,
                    partial=True,
                    evidence=f"flake8 configured via {cfg.name}",
                    suggestion="Consider migrating to ruff for faster linting.",
                )

    if file_exists(repo_path, ".pylintrc", "pylintrc"):
        return CheckResult(
            passed=False,
            partial=True,
            evidence="pylint configured",
            suggestion="Consider adding ruff for faster feedback loops.",
        )

    # Check if not a Python project
    if not file_exists(repo_path, "pyproject.toml", "setup.py", "requirements.txt"):
        return CheckResult(
            passed=True,
            evidence="Not a Python project; fast linter check not applicable.",
        )

    return CheckResult(
        passed=False,
        evidence="No Python linter configuration found",
        suggestion="Add [tool.ruff] to pyproject.toml for sub-second linting.",
    )


@check(
    name="precommit_present",
    category="build_and_run",
    description="Check for pre-commit configuration",
    pillar="fast_guardrails",
    gate_level=4,
)
def check_precommit_present(repo_path: Path) -> CheckResult:
    """Check if pre-commit hooks are configured.

    Pre-commit provides local fast feedback before push.
    """
    precommit_config = file_exists(
        repo_path, ".pre-commit-config.yaml", ".pre-commit-config.yml"
    )
    if precommit_config:
        content = read_file_safe(precommit_config)
        hooks_mentioned: list[str] = []

        if content:
            if "ruff" in content.lower():
                hooks_mentioned.append("ruff")
            if "mypy" in content.lower():
                hooks_mentioned.append("mypy")
            if "black" in content.lower():
                hooks_mentioned.append("black")
            if "prettier" in content.lower():
                hooks_mentioned.append("prettier")
            if "eslint" in content.lower():
                hooks_mentioned.append("eslint")

        evidence = f"pre-commit configured: {precommit_config.name}"
        if hooks_mentioned:
            evidence += f" (hooks: {', '.join(hooks_mentioned)})"

        return CheckResult(
            passed=True,
            evidence=evidence,
        )

    # Check if there's CI linting but no pre-commit
    ci_dir = repo_path / ".github" / "workflows"
    if ci_dir.is_dir():
        for workflow in ci_dir.glob("*.yml"):
            content = read_file_safe(workflow)
            if content and ("ruff" in content or "lint" in content.lower()):
                return CheckResult(
                    passed=False,
                    partial=True,
                    evidence="CI linting configured but no local pre-commit hooks",
                    suggestion="Add .pre-commit-config.yaml for local fast feedback.",
                )

    return CheckResult(
        passed=False,
        evidence="No pre-commit configuration found",
        suggestion="Add .pre-commit-config.yaml with ruff, mypy, and format hooks.",
    )


@check(
    name="test_splitting",
    category="test_feedback_loop",
    description="Check for unit vs integration test splitting",
    pillar="verification_speed",
    gate_level=4,
)
def check_test_splitting(repo_path: Path) -> CheckResult:
    """Check if tests are split into unit and integration categories.

    Fast feedback requires running unit tests separately from integration tests.
    """
    # Check Makefile for test-unit and test-integration targets
    makefile = file_exists(repo_path, "Makefile")
    if makefile:
        content = read_file_safe(makefile)
        if content:
            has_unit = "test-unit" in content or "test_unit" in content
            has_integration = (
                "test-integration" in content or "test_integration" in content
            )
            if has_unit and has_integration:
                return CheckResult(
                    passed=True,
                    evidence="Makefile defines test-unit and test-integration targets",
                )
            if has_unit or has_integration:
                return CheckResult(
                    passed=False,
                    partial=True,
                    evidence="Makefile has partial test splitting",
                    suggestion="Add both 'make test-unit' and 'make test-integration' targets.",
                )

    # Check pyproject.toml for pytest markers
    pyproject = file_exists(repo_path, "pyproject.toml")
    if pyproject:
        content = read_file_safe(pyproject)
        if (
            content
            and "markers" in content
            and ("unit" in content or "integration" in content)
        ):
            return CheckResult(
                passed=True,
                evidence="pytest markers for test splitting defined in pyproject.toml",
            )

    # Check pytest.ini
    pytest_ini = file_exists(repo_path, "pytest.ini")
    if pytest_ini:
        content = read_file_safe(pytest_ini)
        if (
            content
            and "markers" in content
            and ("unit" in content or "integration" in content)
        ):
            return CheckResult(
                passed=True,
                evidence="pytest markers for test splitting defined in pytest.ini",
            )

    # Check tox.ini or noxfile.py
    tox_ini = file_exists(repo_path, "tox.ini")
    if tox_ini:
        content = read_file_safe(tox_ini)
        if content and ("unit" in content or "integration" in content):
            return CheckResult(
                passed=True,
                evidence="tox environments for test splitting detected",
            )

    noxfile = file_exists(repo_path, "noxfile.py")
    if noxfile:
        content = read_file_safe(noxfile)
        if content and ("unit" in content or "integration" in content):
            return CheckResult(
                passed=True,
                evidence="nox sessions for test splitting detected",
            )

    # Check if tests exist at all
    if not (repo_path / "tests").is_dir() and not (repo_path / "test").is_dir():
        return CheckResult(
            passed=False,
            evidence="No tests directory found",
            suggestion="Create tests/ with unit and integration test organization.",
        )

    return CheckResult(
        passed=False,
        evidence="No test splitting detected",
        suggestion="Add 'make test-unit' and 'make test-integration' targets or pytest markers.",
    )


@check(
    name="machine_readable_coverage",
    category="test_feedback_loop",
    description="Check for machine-readable coverage output",
    pillar="verification_trust",
    gate_level=4,
)
def check_machine_readable_coverage(repo_path: Path) -> CheckResult:
    """Check if coverage is configured to output machine-readable formats.

    Agents need coverage.xml or coverage.json for parsing.
    """
    # Check pyproject.toml for coverage config
    pyproject = file_exists(repo_path, "pyproject.toml")
    if pyproject:
        content = read_file_safe(pyproject)
        if content and "[tool.coverage" in content:
            if "xml" in content or "json" in content:
                return CheckResult(
                    passed=True,
                    evidence="coverage configured with XML/JSON output in pyproject.toml",
                )
            if "html" in content:
                return CheckResult(
                    passed=False,
                    partial=True,
                    evidence="coverage configured with HTML only",
                    suggestion="Add coverage.xml output for machine parsing.",
                )

    # Check .coveragerc
    coveragerc = file_exists(repo_path, ".coveragerc")
    if coveragerc:
        content = read_file_safe(coveragerc)
        if content:
            if "xml" in content or "json" in content:
                return CheckResult(
                    passed=True,
                    evidence="coverage configured with XML/JSON output in .coveragerc",
                )
            return CheckResult(
                passed=False,
                partial=True,
                evidence=".coveragerc exists but no XML/JSON output configured",
                suggestion="Add [xml] or [json] section to .coveragerc",
            )

    # Note: We intentionally don't check for coverage.xml/coverage.json artifact existence
    # because these are generated files that may not exist in fresh clones or CI.
    # Instead, we verify configuration that WILL generate these artifacts.

    # Check CI for coverage xml generation
    ci_dir = repo_path / ".github" / "workflows"
    if ci_dir.is_dir():
        for workflow in ci_dir.glob("*.yml"):
            content = read_file_safe(workflow)
            if content and ("coverage.xml" in content or "--cov-report=xml" in content):
                return CheckResult(
                    passed=True,
                    evidence="CI configured to generate coverage.xml",
                )

    # Check Makefile for coverage commands
    makefile = file_exists(repo_path, "Makefile")
    if makefile:
        content = read_file_safe(makefile)
        if content and ("coverage xml" in content or "--cov-report=xml" in content):
            return CheckResult(
                passed=True,
                evidence="Makefile configured to generate coverage.xml",
            )

    return CheckResult(
        passed=False,
        evidence="No machine-readable coverage configuration found",
        suggestion="Configure pytest-cov with --cov-report=xml for coverage.xml output.",
    )


@check(
    name="flake_awareness_pytest",
    category="test_feedback_loop",
    description="Check for flaky test awareness/mitigation",
    pillar="verification_trust",
)
def check_flake_awareness_pytest(repo_path: Path) -> CheckResult:
    """Check if flaky test mitigation tools are configured.

    Looks for pytest-rerunfailures, pytest-flaky, or documented flake policy.
    """
    # Check pyproject.toml dependencies
    pyproject = file_exists(repo_path, "pyproject.toml")
    if pyproject:
        content = read_file_safe(pyproject)
        if content:
            if "pytest-rerunfailures" in content:
                return CheckResult(
                    passed=True,
                    evidence="pytest-rerunfailures configured for flaky test mitigation",
                )
            if "pytest-flaky" in content:
                return CheckResult(
                    passed=True,
                    evidence="pytest-flaky configured for flaky test mitigation",
                )

    # Check requirements files
    for req_file in [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
    ]:
        req_path = repo_path / req_file
        if req_path.exists():
            content = read_file_safe(req_path)
            if content:
                if "pytest-rerunfailures" in content:
                    return CheckResult(
                        passed=True,
                        evidence=f"pytest-rerunfailures in {req_file}",
                    )
                if "pytest-flaky" in content:
                    return CheckResult(
                        passed=True,
                        evidence=f"pytest-flaky in {req_file}",
                    )

    # Check for pytest markers config (partial)
    if pyproject:
        content = read_file_safe(pyproject)
        if content and "flaky" in content.lower():
            return CheckResult(
                passed=False,
                partial=True,
                evidence="Flaky test markers mentioned but no rerun plugin",
                suggestion="Add pytest-rerunfailures for automatic flaky test retry.",
            )

    return CheckResult(
        passed=False,
        evidence="No flaky test mitigation detected",
        suggestion="Add pytest-rerunfailures to handle transient test failures.",
    )
