"""Testing and validation checks for ARA v3 specification.

These checks evaluate whether an agent can verify correctness autonomously:
- Tests runnable in isolation
- No network required for unit tests
- Golden fixtures or snapshots
- CI enforces test execution
"""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    dir_exists,
    file_exists,
    glob_files,
    read_file_safe,
)


@check(
    name="tests_isolated",
    category="test_feedback_loop",
    description="Check if tests can run in isolation without external dependencies",
    domain="testing",
)
def check_tests_isolated(repo_path: Path) -> CheckResult:
    """Check if tests are designed for isolated execution.

    Looks for:
    - Fixtures in conftest.py
    - Mock usage in tests
    - No database URLs in test files (unless mocked)
    """
    # Check for conftest.py (fixture isolation)
    conftest_files = glob_files(repo_path, "**/conftest.py")
    if conftest_files:
        has_fixtures = False
        for conftest in conftest_files[:5]:
            content = read_file_safe(conftest)
            if content and "@pytest.fixture" in content:
                has_fixtures = True
                break

        if has_fixtures:
            return CheckResult(
                passed=True,
                evidence=f"Found pytest fixtures in {len(conftest_files)} conftest.py files",
            )

    # Check for mock usage in tests
    test_files = glob_files(repo_path, "tests/**/*.py")[:20]
    for test_file in test_files:
        content = read_file_safe(test_file)
        if content and any(
            pattern in content
            for pattern in [
                "from unittest.mock",
                "from unittest import mock",
                "@patch",
                "MagicMock",
                "mocker.",
            ]
        ):
            return CheckResult(
                passed=True,
                evidence="Mock patterns found in test files",
            )

    # Check if tests directory exists
    tests_dir = dir_exists(repo_path, "tests", "test", "spec")
    if not tests_dir:
        return CheckResult(
            passed=False,
            evidence="No tests directory found",
            suggestion="Create a tests/ directory with isolated unit tests.",
        )

    return CheckResult(
        passed=False,
        evidence="Tests found but no isolation patterns detected",
        suggestion="Add pytest fixtures (conftest.py) and mocks for test isolation.",
    )


@check(
    name="tests_no_network_required",
    category="test_feedback_loop",
    description="Check that unit tests don't require network access",
    domain="testing",
)
def check_tests_no_network_required(repo_path: Path) -> CheckResult:
    """Check that tests are designed to run offline.

    Looks for:
    - Network blocking in pytest config
    - VCR/cassettes usage
    - No direct HTTP calls in test files
    """
    # Check pytest.ini or pyproject.toml for network blocking
    pytest_ini = repo_path / "pytest.ini"
    pyproject = repo_path / "pyproject.toml"

    for config_file in [pytest_ini, pyproject]:
        if config_file.exists():
            content = read_file_safe(config_file)
            if content and any(
                pattern in content
                for pattern in ["socket", "network", "disable_socket", "block_network"]
            ):
                return CheckResult(
                    passed=True,
                    evidence=f"Network blocking configured in {config_file.name}",
                )

    # Check for VCR/cassettes
    cassettes_dir = dir_exists(
        repo_path, "tests/cassettes", "cassettes", "fixtures/cassettes"
    )
    if cassettes_dir:
        return CheckResult(
            passed=True,
            evidence="VCR cassettes found for network request recording",
        )

    # Check for pytest-vcr or socket mocking
    if pyproject.exists():
        content = read_file_safe(pyproject)
        if content and any(
            lib in content
            for lib in ["pytest-vcr", "pytest-socket", "responses", "httpretty"]
        ):
            return CheckResult(
                passed=True,
                evidence="Network mocking library in dependencies",
            )

    # Check if tests make network calls
    test_files = glob_files(repo_path, "tests/**/*.py")[:20]
    makes_network_calls = False
    network_patterns = [
        "requests.get",
        "requests.post",
        "httpx.",
        "aiohttp.",
        "urllib.request",
    ]
    mock_patterns = ["@responses", "@httpretty", "vcr", "mock"]
    for test_file in test_files:
        content = read_file_safe(test_file)
        has_network = content and any(
            pattern in content for pattern in network_patterns
        )
        has_mocking = content and any(mock in content for mock in mock_patterns)
        # Flag as network call if uses network but doesn't mock
        if has_network and not has_mocking:
            makes_network_calls = True
            break

    if makes_network_calls:
        return CheckResult(
            passed=False,
            evidence="Tests appear to make unmocked network calls",
            suggestion="Use VCR, responses, or pytest-socket to ensure tests run offline.",
        )

    return CheckResult(
        passed=True,
        evidence="No unmocked network calls detected in tests",
    )


@check(
    name="golden_fixtures_present",
    category="test_feedback_loop",
    description="Check for golden fixtures or snapshot testing",
    domain="testing",
)
def check_golden_fixtures_present(repo_path: Path) -> CheckResult:
    """Check for golden fixtures or snapshot testing.

    Looks for:
    - fixtures/ or golden/ directories
    - Snapshot testing libraries (syrupy, pytest-snapshot)
    - .snap files
    """
    # Check for fixture directories
    fixture_dirs = ["fixtures", "golden", "snapshots", "__snapshots__", "test_data"]
    for fix_dir in fixture_dirs:
        found = dir_exists(repo_path, f"tests/{fix_dir}", fix_dir)
        if found:
            return CheckResult(
                passed=True,
                evidence=f"Found fixture directory: {found}",
            )

    # Check for snapshot files
    snap_files = glob_files(repo_path, "**/*.snap")
    if snap_files:
        return CheckResult(
            passed=True,
            evidence=f"Found {len(snap_files)} snapshot files",
        )

    # Check for snapshot libraries
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = read_file_safe(pyproject)
        if content and any(
            lib in content for lib in ["syrupy", "pytest-snapshot", "snapshottest"]
        ):
            return CheckResult(
                passed=True,
                evidence="Snapshot testing library detected",
            )

    # Check for JSON/YAML fixtures in tests
    fixture_files = glob_files(repo_path, "tests/**/*.{json,yaml,yml}")
    if len(fixture_files) >= 2:
        return CheckResult(
            passed=True,
            evidence=f"Found {len(fixture_files)} data fixtures in tests",
        )

    return CheckResult(
        passed=False,
        evidence="No golden fixtures or snapshots detected",
        suggestion="Add test fixtures in tests/fixtures/ or use snapshot testing (syrupy).",
    )


@check(
    name="test_ordering_independent",
    category="test_feedback_loop",
    description="Check that tests don't depend on execution order",
    domain="testing",
)
def check_test_ordering_independent(repo_path: Path) -> CheckResult:
    """Check for patterns that indicate order-dependent tests.

    Red flags:
    - Global state modification between tests
    - Tests named test_1, test_2 (sequential naming)
    - Shared mutable fixtures without cleanup
    """
    test_files = glob_files(repo_path, "tests/**/*.py")[:20]

    red_flags: list[str] = []

    for test_file in test_files:
        content = read_file_safe(test_file)
        if not content:
            continue

        # Check for sequential test naming
        import re

        sequential_pattern = r"def test_\d+\("
        if re.search(sequential_pattern, content):
            red_flags.append(
                f"{test_file.name}: sequential test naming (test_1, test_2)"
            )

        # Check for global state modification
        if "global " in content:
            red_flags.append(f"{test_file.name}: global keyword in tests")

    if red_flags:
        return CheckResult(
            passed=False,
            evidence=f"Order-dependent patterns: {', '.join(red_flags[:3])}",
            suggestion="Remove sequential test naming and avoid global state in tests.",
        )

    # Check for pytest-randomly or pytest-random-order
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = read_file_safe(pyproject)
        if content and any(
            lib in content for lib in ["pytest-randomly", "pytest-random-order"]
        ):
            return CheckResult(
                passed=True,
                evidence="Test randomization plugin detected",
            )

    return CheckResult(
        passed=True,
        evidence="No order-dependent test patterns detected",
    )


@check(
    name="ci_enforces_tests",
    category="test_feedback_loop",
    description="Check that CI runs tests on every change",
    domain="testing",
)
def check_ci_enforces_tests(repo_path: Path) -> CheckResult:
    """Check that CI configuration includes test execution."""
    # GitHub Actions
    workflows = glob_files(repo_path, ".github/workflows/*.{yml,yaml}")
    for workflow in workflows:
        content = read_file_safe(workflow)
        if content and any(
            pattern in content
            for pattern in [
                "pytest",
                "npm test",
                "cargo test",
                "go test",
                "make test",
                "npm run test",
            ]
        ):
            return CheckResult(
                passed=True,
                evidence=f"Tests enforced in {workflow.name}",
            )

    # GitLab CI
    gitlab_ci = file_exists(repo_path, ".gitlab-ci.yml")
    if gitlab_ci:
        content = read_file_safe(gitlab_ci)
        if content and "test" in content.lower():
            return CheckResult(
                passed=True,
                evidence="Tests found in .gitlab-ci.yml",
            )

    # Check for Makefile test target
    makefile = file_exists(repo_path, "Makefile")
    if makefile:
        content = read_file_safe(makefile)
        if content and "test:" in content:
            # Partial - Makefile has tests but not enforced in CI
            return CheckResult(
                passed=True,
                partial=True,
                evidence="Makefile has test target but CI enforcement unclear",
            )

    return CheckResult(
        passed=False,
        evidence="No CI test enforcement detected",
        suggestion="Add test execution to CI workflow (e.g., pytest in GitHub Actions).",
    )


@check(
    name="test_coverage_tracked",
    category="test_feedback_loop",
    description="Check if test coverage is tracked",
    domain="testing",
)
def check_test_coverage_tracked(repo_path: Path) -> CheckResult:
    """Check for test coverage configuration or reports."""
    # Check for coverage configuration
    coverage_configs = [
        ".coveragerc",
        "coverage.xml",
        "htmlcov",
        ".nyc_output",
        "lcov.info",
    ]

    for config in coverage_configs:
        if file_exists(repo_path, config):
            return CheckResult(
                passed=True,
                evidence=f"Coverage configuration found: {config}",
            )

    # Check pyproject.toml for coverage config
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = read_file_safe(pyproject)
        if content and any(
            pattern in content
            for pattern in ["[tool.coverage", "pytest-cov", "coverage"]
        ):
            return CheckResult(
                passed=True,
                evidence="Coverage configuration in pyproject.toml",
            )

    # Check CI for coverage
    workflows = glob_files(repo_path, ".github/workflows/*.{yml,yaml}")
    for workflow in workflows:
        content = read_file_safe(workflow)
        if content and "coverage" in content.lower():
            return CheckResult(
                passed=True,
                evidence=f"Coverage tracked in CI: {workflow.name}",
            )

    return CheckResult(
        passed=False,
        evidence="No test coverage tracking detected",
        suggestion="Add pytest-cov or coverage.py for test coverage tracking.",
    )
