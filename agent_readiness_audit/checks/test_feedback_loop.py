"""Test feedback loop checks - test infrastructure and runnability."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    dir_exists,
    file_contains,
    file_exists,
    glob_files,
)

TEST_DIRECTORIES = ["tests", "test", "spec", "specs", "__tests__", "testing"]
TEST_CONFIG_FILES = [
    "pytest.ini",
    "pyproject.toml",
    "setup.cfg",
    "tox.ini",
    "noxfile.py",
    "jest.config.js",
    "jest.config.ts",
    "jest.config.mjs",
    "vitest.config.js",
    "vitest.config.ts",
    "karma.conf.js",
    "mocha.opts",
    ".mocharc.js",
    ".mocharc.json",
    "ava.config.js",
    "phpunit.xml",
    "phpunit.xml.dist",
]


@check(
    name="tests_directory_or_config_exists",
    category="test_feedback_loop",
    description="Check if tests directory or test configuration exists",
    pillar="verification_trust",
    gate_for=[3],
)
def check_tests_directory_or_config_exists(repo_path: Path) -> CheckResult:
    """Check if tests exist."""
    # Check for test directories
    test_dir = dir_exists(repo_path, *TEST_DIRECTORIES)
    if test_dir:
        # Verify it has test files
        test_files = (
            glob_files(test_dir, "test_*.py")
            + glob_files(test_dir, "*_test.py")
            + glob_files(test_dir, "*.test.js")
            + glob_files(test_dir, "*.test.ts")
            + glob_files(test_dir, "*.spec.js")
            + glob_files(test_dir, "*.spec.ts")
        )
        if test_files:
            return CheckResult(
                passed=True,
                evidence=f"Found test directory '{test_dir.name}' with {len(test_files)} test file(s)",
            )
        return CheckResult(
            passed=True,
            evidence=f"Found test directory '{test_dir.name}' (may need test files)",
        )

    # Check for test config files
    config = file_exists(repo_path, *TEST_CONFIG_FILES)
    if config:
        return CheckResult(
            passed=True,
            evidence=f"Found test configuration: {config.name}",
        )

    # Check pyproject.toml for pytest config
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists() and file_contains(pyproject, "[tool.pytest", "testpaths"):
        return CheckResult(
            passed=True,
            evidence="Found pytest configuration in pyproject.toml",
        )

    # Check package.json for test script
    package_json = repo_path / "package.json"
    if package_json.exists() and file_contains(package_json, '"test"'):
        return CheckResult(
            passed=True,
            evidence="Found test script in package.json",
        )

    return CheckResult(
        passed=False,
        evidence="No test directory or configuration found",
        suggestion="Create a 'tests/' directory and add test files, or configure a test framework.",
    )


@check(
    name="test_command_detectable",
    category="test_feedback_loop",
    description="Check if test command is easily detectable",
    pillar="verification_trust",
)
def check_test_command_detectable(repo_path: Path) -> CheckResult:
    """Check if test command is detectable."""
    # Check package.json test script
    package_json = repo_path / "package.json"
    if package_json.exists() and file_contains(package_json, '"test"'):
        return CheckResult(
            passed=True,
            evidence="Test command detectable via 'npm test' or 'yarn test'",
        )

    # Check Makefile for test target
    makefile = file_exists(repo_path, "Makefile", "makefile", "GNUmakefile")
    if makefile and file_contains(makefile, "test:", "tests:"):
        return CheckResult(
            passed=True,
            evidence="Test command detectable via 'make test'",
        )

    # Check for pytest configuration
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists() and file_contains(pyproject, "[tool.pytest"):
        return CheckResult(
            passed=True,
            evidence="Test command detectable via 'pytest' (configured in pyproject.toml)",
        )

    pytest_ini = repo_path / "pytest.ini"
    if pytest_ini.exists():
        return CheckResult(
            passed=True,
            evidence="Test command detectable via 'pytest' (pytest.ini present)",
        )

    # Check for test directory with standard naming
    test_dir = dir_exists(repo_path, "tests", "test")
    if test_dir:
        return CheckResult(
            passed=True,
            evidence=f"Test command likely 'pytest' or similar (found {test_dir.name}/ directory)",
        )

    # Check Cargo.toml (Rust)
    cargo_toml = repo_path / "Cargo.toml"
    if cargo_toml.exists():
        return CheckResult(
            passed=True,
            evidence="Test command detectable via 'cargo test'",
        )

    # Check go.mod (Go)
    go_mod = repo_path / "go.mod"
    if go_mod.exists():
        return CheckResult(
            passed=True,
            evidence="Test command detectable via 'go test ./...'",
        )

    return CheckResult(
        passed=False,
        evidence="Test command not easily detectable",
        suggestion="Add a 'test' script to package.json, a 'test' target to Makefile, or configure pytest.",
    )


@check(
    name="test_command_has_timeout",
    category="test_feedback_loop",
    description="Check if test configuration includes timeout settings",
    pillar="verification_speed",
)
def check_test_command_has_timeout(repo_path: Path) -> CheckResult:
    """Check if tests have timeout configuration."""
    # Check pytest configuration for timeout
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists() and file_contains(pyproject, "timeout", "pytest-timeout"):
        return CheckResult(
            passed=True,
            evidence="Found timeout configuration in pyproject.toml",
        )

    pytest_ini = repo_path / "pytest.ini"
    if pytest_ini.exists() and file_contains(pytest_ini, "timeout"):
        return CheckResult(
            passed=True,
            evidence="Found timeout configuration in pytest.ini",
        )

    # Check for pytest-timeout in dependencies
    requirements = file_exists(repo_path, "requirements.txt", "requirements-dev.txt")
    if requirements and file_contains(requirements, "pytest-timeout"):
        return CheckResult(
            passed=True,
            evidence="Found pytest-timeout in requirements",
        )

    # Check package.json for jest timeout
    package_json = repo_path / "package.json"
    if package_json.exists() and file_contains(package_json, "testTimeout", "timeout"):
        return CheckResult(
            passed=True,
            evidence="Found timeout configuration in package.json",
        )

    # Check jest config
    jest_configs = ["jest.config.js", "jest.config.ts", "jest.config.mjs"]
    for config_name in jest_configs:
        config = repo_path / config_name
        if config.exists() and file_contains(config, "testTimeout", "timeout"):
            return CheckResult(
                passed=True,
                evidence=f"Found timeout configuration in {config_name}",
            )

    # This is a softer requirement - pass with suggestion if tests exist
    test_dir = dir_exists(repo_path, *TEST_DIRECTORIES)
    if test_dir:
        return CheckResult(
            passed=False,
            evidence="Tests exist but no explicit timeout configuration found",
            suggestion="Add timeout configuration to prevent hanging tests (e.g., pytest-timeout, jest testTimeout).",
        )

    return CheckResult(
        passed=False,
        evidence="No test timeout configuration found",
        suggestion="Configure test timeouts to prevent infinite hangs during automated runs.",
    )
