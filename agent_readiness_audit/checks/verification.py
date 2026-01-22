"""Verification checks - test reliability, coverage artifacts, and test splitting."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    check_dependency_present,
    dir_exists,
    file_contains,
    file_exists,
    read_toml_section,
)


@check(
    name="flake_awareness_pytest",
    category="test_feedback_loop",
    description="Check for flaky test awareness and mitigation",
    pillar="verification_trust",
    weight=1.0,
)
def check_flake_awareness_pytest(repo_path: Path) -> CheckResult:
    """Check if flaky test mitigation is configured."""
    # Check for pytest-rerunfailures or pytest-flaky
    rerun_pkg = check_dependency_present(
        repo_path, "pytest-rerunfailures", "pytest-flaky"
    )
    if rerun_pkg:
        return CheckResult(
            passed=True,
            evidence=f"Flaky test mitigation found: {rerun_pkg}",
        )

    # Check for flaky markers in pytest config
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        pytest_section = read_toml_section(pyproject, "tool.pytest.ini_options")
        if pytest_section:
            markers = pytest_section.get("markers", [])
            if isinstance(markers, list):
                for marker in markers:
                    if "flaky" in str(marker).lower():
                        return CheckResult(
                            passed=True,
                            partial=True,
                            evidence="Flaky marker configured in pytest, but no rerun tooling",
                            suggestion="Add pytest-rerunfailures for automatic flaky test retries.",
                        )

    # Check pytest.ini for flaky markers
    pytest_ini = repo_path / "pytest.ini"
    if pytest_ini.exists() and file_contains(pytest_ini, "flaky"):
        return CheckResult(
            passed=True,
            partial=True,
            evidence="Flaky marker configured in pytest.ini, but no rerun tooling",
            suggestion="Add pytest-rerunfailures for automatic flaky test retries.",
        )

    # Check if tests exist
    test_dir = dir_exists(repo_path, "tests", "test")
    if not test_dir:
        return CheckResult(
            passed=True,
            evidence="No test directory found (flaky test mitigation not applicable)",
            confidence="MEDIUM",
        )

    return CheckResult(
        passed=False,
        evidence="No flaky test mitigation found",
        suggestion="Add pytest-rerunfailures or pytest-flaky for flaky test handling.",
    )


@check(
    name="machine_readable_coverage",
    category="test_feedback_loop",
    description="Check if coverage outputs machine-readable format",
    pillar="verification_trust",
    weight=1.5,
    gate_for=[4],
)
def check_machine_readable_coverage(repo_path: Path) -> CheckResult:
    """Check if coverage is configured to output XML or JSON."""
    # Check pyproject.toml for coverage config
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        cov_section = read_toml_section(pyproject, "tool.coverage.report")
        if cov_section and (cov_section.get("xml") or "xml" in str(cov_section)):
            return CheckResult(
                passed=True,
                evidence="Coverage XML output configured in pyproject.toml",
            )

        # Check tool.coverage.xml section
        xml_section = read_toml_section(pyproject, "tool.coverage.xml")
        if xml_section:
            return CheckResult(
                passed=True,
                evidence="Coverage XML configuration found in pyproject.toml",
            )

        # Check for pytest-cov with xml
        pytest_section = read_toml_section(pyproject, "tool.pytest.ini_options")
        if pytest_section:
            addopts = pytest_section.get("addopts", "")
            if "--cov-report=xml" in str(addopts) or "--cov-report xml" in str(addopts):
                return CheckResult(
                    passed=True,
                    evidence="Coverage XML output configured in pytest addopts",
                )
            if "--cov-report=html" in str(addopts) and "--cov-report=xml" not in str(
                addopts
            ):
                return CheckResult(
                    passed=False,
                    partial=True,
                    evidence="HTML coverage configured but not XML",
                    suggestion="Add --cov-report=xml to pytest addopts for machine-readable coverage.",
                )

    # Check .coveragerc
    coveragerc = repo_path / ".coveragerc"
    if coveragerc.exists():
        if file_contains(coveragerc, "[xml]", "xml"):
            return CheckResult(
                passed=True,
                evidence="Coverage XML configuration found in .coveragerc",
            )
        if file_contains(coveragerc, "[html]"):
            return CheckResult(
                passed=False,
                partial=True,
                evidence="HTML coverage configured in .coveragerc but not XML",
                suggestion="Add [xml] section to .coveragerc for machine-readable output.",
            )

    # Check setup.cfg
    setup_cfg = repo_path / "setup.cfg"
    if (
        setup_cfg.exists()
        and file_contains(setup_cfg, "[coverage:")
        and file_contains(setup_cfg, "xml", "[coverage:xml]")
    ):
        return CheckResult(
            passed=True,
            evidence="Coverage XML configuration found in setup.cfg",
        )

    # Check for existing coverage files (indicates it's configured somewhere)
    coverage_xml = file_exists(repo_path, "coverage.xml", "coverage/coverage.xml")
    if coverage_xml:
        return CheckResult(
            passed=True,
            evidence=f"Coverage XML file found: {coverage_xml.relative_to(repo_path)}",
        )

    # Check package.json for coverage config (JS)
    package_json = repo_path / "package.json"
    if package_json.exists() and file_contains(
        package_json, '"lcov"', '"json"', '"cobertura"'
    ):
        return CheckResult(
            passed=True,
            evidence="Machine-readable coverage format configured in package.json",
        )

    # Check if coverage is even in use
    has_coverage = check_dependency_present(
        repo_path, "pytest-cov", "coverage", "nyc", "c8"
    )
    if has_coverage:
        return CheckResult(
            passed=False,
            evidence=f"Coverage tool ({has_coverage}) found but XML/JSON output not configured",
            suggestion="Add --cov-report=xml to pytest config or configure coverage.xml output.",
        )

    # Check if tests exist
    test_dir = dir_exists(repo_path, "tests", "test")
    if not test_dir:
        return CheckResult(
            passed=False,
            evidence="No tests or coverage configuration found",
            suggestion="Add tests with coverage reporting (pytest-cov with --cov-report=xml).",
        )

    return CheckResult(
        passed=False,
        evidence="No machine-readable coverage configuration found",
        suggestion="Add pytest-cov with --cov-report=xml for machine-readable coverage artifacts.",
    )


@check(
    name="test_splitting",
    category="test_feedback_loop",
    description="Check if tests are split into unit and integration",
    pillar="verification_speed",
    weight=1.5,
    gate_for=[4],
)
def check_test_splitting(repo_path: Path) -> CheckResult:
    """Check if tests are split for faster feedback loops."""
    found_markers: list[str] = []

    # Check Makefile for test-unit, test-integration targets
    makefile = file_exists(repo_path, "Makefile", "makefile", "GNUmakefile")
    if makefile:
        content = makefile.read_text(encoding="utf-8", errors="ignore").lower()
        if "test-unit" in content or "test_unit" in content or "unittest" in content:
            found_markers.append("Makefile:test-unit")
        if (
            "test-integration" in content
            or "test_integration" in content
            or "test-int" in content
        ):
            found_markers.append("Makefile:test-integration")

    # Check pyproject.toml for pytest markers
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        pytest_section = read_toml_section(pyproject, "tool.pytest.ini_options")
        if pytest_section:
            markers = pytest_section.get("markers", [])
            if isinstance(markers, list):
                marker_str = " ".join(str(m) for m in markers).lower()
                if "unit" in marker_str:
                    found_markers.append("pytest:unit marker")
                if "integration" in marker_str or "integ" in marker_str:
                    found_markers.append("pytest:integration marker")
                if "slow" in marker_str:
                    found_markers.append("pytest:slow marker")

    # Check for tox.ini with multiple test envs
    tox_ini = repo_path / "tox.ini"
    if tox_ini.exists():
        content = tox_ini.read_text(encoding="utf-8", errors="ignore").lower()
        if "unit" in content and ("integration" in content or "integ" in content):
            found_markers.append("tox:multiple envs")

    # Check for noxfile.py with separate sessions
    noxfile = repo_path / "noxfile.py"
    if noxfile.exists():
        content = noxfile.read_text(encoding="utf-8", errors="ignore").lower()
        if "unit" in content and ("integration" in content or "integ" in content):
            found_markers.append("nox:multiple sessions")

    # Check for separate test directories
    tests_dir = repo_path / "tests"
    if tests_dir.is_dir():
        subdirs = [d.name for d in tests_dir.iterdir() if d.is_dir()]
        if "unit" in subdirs:
            found_markers.append("tests/unit/")
        if "integration" in subdirs or "e2e" in subdirs:
            found_markers.append("tests/integration/ or tests/e2e/")

    # Check package.json for multiple test scripts
    package_json = repo_path / "package.json"
    if package_json.exists():
        content = package_json.read_text(encoding="utf-8", errors="ignore").lower()
        if '"test:unit"' in content or '"test-unit"' in content:
            found_markers.append("npm:test:unit")
        if (
            '"test:integration"' in content
            or '"test:e2e"' in content
            or '"test-integration"' in content
        ):
            found_markers.append("npm:test:integration")

    # Evaluate results
    if len(found_markers) >= 2:
        return CheckResult(
            passed=True,
            evidence=f"Test splitting configured: {', '.join(found_markers)}",
        )
    elif len(found_markers) == 1:
        return CheckResult(
            passed=True,
            partial=True,
            evidence=f"Partial test splitting: {found_markers[0]}",
            suggestion="Add both unit and integration test targets for complete splitting.",
        )

    # Check if tests exist at all
    test_dir = dir_exists(repo_path, "tests", "test", "__tests__")
    if not test_dir:
        return CheckResult(
            passed=False,
            evidence="No test directory found",
            suggestion="Create tests/ with separate unit/ and integration/ subdirectories.",
        )

    return CheckResult(
        passed=False,
        evidence="No test splitting configuration found",
        suggestion="Add 'make test-unit' and 'make test-integration' targets, or use pytest markers.",
    )
