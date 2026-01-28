"""Advanced determinism checks for ARA v3 specification.

These checks evaluate whether a repository supports deterministic execution
for autonomous agents, including:
- Random seed centralization and injection
- Wall-clock time abstraction
- Network access gating and mocking
- Global state detection
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
    name="random_seed_injectable",
    category="deterministic_setup",
    description="Check if random seeds are centralized and injectable",
    domain="determinism",
)
def check_random_seed_injectable(repo_path: Path) -> CheckResult:
    """Check if random operations use injectable seeds.

    Looks for patterns indicating seed centralization:
    - Environment variable for seeds (e.g., RANDOM_SEED)
    - Configuration-based seed injection
    - Fixtures or conftest with seed setup
    """
    # Check conftest.py for seed fixtures
    conftest_files = glob_files(repo_path, "**/conftest.py")
    for conftest in conftest_files:
        content = read_file_safe(conftest)
        if content and any(
            pattern in content.lower()
            for pattern in ["seed", "random_state", "np.random", "random.seed"]
        ):
            return CheckResult(
                passed=True,
                evidence=f"Found seed fixture in {conftest.relative_to(repo_path)}",
            )

    # Check for seed in environment/config patterns
    config_files = glob_files(repo_path, "**/*.{toml,yaml,yml,json}")[:20]
    for config in config_files:
        content = read_file_safe(config)
        if content and "seed" in content.lower():
            return CheckResult(
                passed=True,
                evidence=f"Found seed configuration in {config.relative_to(repo_path)}",
            )

    # Check Python files for seed patterns
    py_files = glob_files(repo_path, "**/*.py")[:50]
    for py_file in py_files:
        content = read_file_safe(py_file)
        # Look for seed injection via environment
        has_seed_ref = content and (
            "RANDOM_SEED" in content or "SEED" in content.upper()
        )
        has_env_access = content and ("os.environ" in content or "os.getenv" in content)
        if has_seed_ref and has_env_access:
            return CheckResult(
                passed=True,
                evidence=f"Found env-based seed in {py_file.relative_to(repo_path)}",
            )

    # Partial pass if random is used but no seed injection found
    for py_file in py_files:
        content = read_file_safe(py_file)
        if content and ("import random" in content or "numpy.random" in content):
            return CheckResult(
                passed=False,
                evidence="Random operations found but no seed injection detected",
                suggestion="Centralize random seeds via environment variable (e.g., RANDOM_SEED) for reproducibility.",
            )

    # No random usage detected - pass by default
    return CheckResult(
        passed=True,
        evidence="No random operations detected in codebase",
    )


@check(
    name="time_abstraction",
    category="deterministic_setup",
    description="Check if wall-clock time is abstracted and mockable",
    domain="determinism",
)
def check_time_abstraction(repo_path: Path) -> CheckResult:
    """Check if time operations are abstracted for testing.

    Looks for:
    - freezegun or time-machine in dependencies
    - Custom time providers/interfaces
    - Mockable time utilities
    """
    # Check for time mocking libraries in dependencies
    time_mock_libs = ["freezegun", "time-machine", "faketime", "libfaketime"]

    pyproject = repo_path / "pyproject.toml"
    requirements_files = glob_files(repo_path, "requirements*.txt")

    for dep_file in [pyproject, *requirements_files]:
        if dep_file.exists():
            content = read_file_safe(dep_file)
            if content:
                for lib in time_mock_libs:
                    if lib in content.lower():
                        return CheckResult(
                            passed=True,
                            evidence=f"Found time mocking library: {lib}",
                        )

    # Check for time abstraction patterns in code
    py_files = glob_files(repo_path, "**/*.py")[:50]
    time_patterns = [
        "from datetime import",
        "import datetime",
        "time.time()",
        "datetime.now()",
        "datetime.utcnow()",
    ]

    uses_time = False
    has_abstraction = False

    for py_file in py_files:
        content = read_file_safe(py_file)
        if not content:
            continue

        # Check if time is used
        for pattern in time_patterns:
            if pattern in content:
                uses_time = True
                break

        # Check for abstraction patterns
        abstraction_patterns = [
            "clock",
            "time_provider",
            "now_func",
            "get_current_time",
            "@freeze_time",
            "@time_machine",
        ]
        for pattern in abstraction_patterns:
            if pattern.lower() in content.lower():
                has_abstraction = True
                break

    if not uses_time:
        return CheckResult(
            passed=True,
            evidence="No wall-clock time usage detected",
        )

    if has_abstraction:
        return CheckResult(
            passed=True,
            evidence="Time abstraction patterns found in codebase",
        )

    return CheckResult(
        passed=False,
        evidence="Time operations used without abstraction",
        suggestion="Abstract wall-clock time using freezegun, time-machine, or a custom time provider.",
    )


@check(
    name="network_mockable",
    category="deterministic_setup",
    description="Check if network access is gated and mockable",
    domain="determinism",
)
def check_network_mockable(repo_path: Path) -> CheckResult:
    """Check if network operations can be mocked.

    Looks for:
    - responses, httpretty, vcrpy, respx in dependencies
    - pytest-httpserver, pytest-vcr usage
    - Fixtures for mocking HTTP calls
    """
    # Check for network mocking libraries
    network_mock_libs = [
        "responses",
        "httpretty",
        "vcrpy",
        "vcr",
        "respx",
        "pytest-httpserver",
        "pytest-vcr",
        "aioresponses",
        "requests-mock",
    ]

    pyproject = repo_path / "pyproject.toml"
    requirements_files = glob_files(repo_path, "requirements*.txt")

    for dep_file in [pyproject, *requirements_files]:
        if dep_file.exists():
            content = read_file_safe(dep_file)
            if content:
                for lib in network_mock_libs:
                    if lib in content.lower():
                        return CheckResult(
                            passed=True,
                            evidence=f"Found network mocking library: {lib}",
                        )

    # Check for cassettes directory (VCR pattern)
    cassettes = file_exists(
        repo_path, "tests/cassettes", "cassettes", "fixtures/cassettes"
    )
    if cassettes:
        return CheckResult(
            passed=True,
            evidence=f"Found VCR cassettes: {cassettes}",
        )

    # Check test files for mock patterns
    test_files = glob_files(repo_path, "tests/**/*.py")[:30]
    for test_file in test_files:
        content = read_file_safe(test_file)
        if content:
            mock_patterns = [
                "@responses.activate",
                "@httpretty.activate",
                "@vcr.use_cassette",
                "respx.mock",
                "requests_mock",
                "aioresponses",
            ]
            for pattern in mock_patterns:
                if pattern in content:
                    return CheckResult(
                        passed=True,
                        evidence=f"Found network mocking in {test_file.relative_to(repo_path)}",
                    )

    # Check if there's any HTTP client usage
    py_files = glob_files(repo_path, "**/*.py")[:50]
    uses_network = False
    for py_file in py_files:
        content = read_file_safe(py_file)
        if content and any(
            lib in content
            for lib in ["requests.", "httpx.", "aiohttp.", "urllib.request"]
        ):
            uses_network = True
            break

    if not uses_network:
        return CheckResult(
            passed=True,
            evidence="No HTTP client usage detected",
        )

    return CheckResult(
        passed=False,
        evidence="Network operations used without mocking infrastructure",
        suggestion="Add network mocking (e.g., responses, vcrpy, respx) for deterministic tests.",
    )


@check(
    name="no_global_state_mutation",
    category="deterministic_setup",
    description="Check for absence of hidden global state mutations",
    domain="determinism",
)
def check_no_global_state_mutation(repo_path: Path) -> CheckResult:
    """Check for patterns indicating global state mutation.

    Red flags:
    - Module-level mutable state (lists, dicts assigned at module level)
    - Singleton patterns without clear reset mechanisms
    - Global variables modified in functions
    """
    py_files = glob_files(repo_path, "**/*.py")[:50]
    red_flags: list[str] = []

    global_patterns = [
        # Module-level mutable defaults
        ("= []", "module-level list"),
        ("= {}", "module-level dict"),
        ("global ", "global keyword usage"),
    ]

    for py_file in py_files:
        # Skip test files and __init__.py
        if "test" in str(py_file).lower() or py_file.name == "__init__.py":
            continue

        content = read_file_safe(py_file)
        if not content:
            continue

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Skip inside functions/classes (simple heuristic: no leading whitespace)
            stripped = line.lstrip()
            if stripped != line:
                continue  # Inside a block

            for pattern, desc in global_patterns:
                if pattern in line and not line.strip().startswith("#"):
                    # Additional filter: skip type annotations
                    if ": list" in line or ": dict" in line:
                        continue
                    red_flags.append(f"{py_file.name}:{i + 1}: {desc}")

        if len(red_flags) >= 3:
            break

    if red_flags:
        return CheckResult(
            passed=False,
            evidence=f"Found {len(red_flags)} potential global state issues: {', '.join(red_flags[:3])}",
            suggestion="Avoid module-level mutable state. Use dependency injection or explicit state containers.",
        )

    return CheckResult(
        passed=True,
        evidence="No obvious global state mutation patterns detected",
    )
