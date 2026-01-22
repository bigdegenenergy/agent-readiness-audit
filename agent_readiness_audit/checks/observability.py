"""Observability checks - logging and error handling."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_contains,
    glob_files,
)


@check(
    name="logging_present",
    category="observability",
    description="Check if logging infrastructure is present",
    pillar="structured_logging_cost",
)
def check_logging_present(repo_path: Path) -> CheckResult:
    """Check if logging is configured."""
    # Check Python files for logging
    py_files = glob_files(repo_path, "**/*.py")
    for py_file in py_files[:50]:  # Limit search to avoid slowdown
        if file_contains(
            py_file, "import logging", "from logging", "getLogger", "structlog"
        ):
            return CheckResult(
                passed=True,
                evidence=f"Found logging usage in {py_file.relative_to(repo_path)}",
            )

    # Check for logging configuration files
    logging_configs = [
        "logging.conf",
        "logging.ini",
        "logging.yaml",
        "logging.yml",
        "log_config.py",
    ]
    for config in logging_configs:
        if (repo_path / config).exists():
            return CheckResult(
                passed=True,
                evidence=f"Found logging configuration: {config}",
            )

    # Check pyproject.toml for structlog or loguru
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists() and file_contains(
        pyproject, "structlog", "loguru", "logging"
    ):
        return CheckResult(
            passed=True,
            evidence="Found logging dependency in pyproject.toml",
        )

    # Check requirements for logging libraries
    requirements = repo_path / "requirements.txt"
    if requirements.exists() and file_contains(
        requirements, "structlog", "loguru", "python-json-logger"
    ):
        return CheckResult(
            passed=True,
            evidence="Found logging library in requirements.txt",
        )

    # Check JavaScript/TypeScript for logging
    js_files = glob_files(repo_path, "**/*.js") + glob_files(repo_path, "**/*.ts")
    for js_file in js_files[:50]:
        if file_contains(js_file, "console.log", "winston", "pino", "bunyan", "log4js"):
            return CheckResult(
                passed=True,
                evidence=f"Found logging usage in {js_file.relative_to(repo_path)}",
            )

    # Check package.json for logging libraries
    package_json = repo_path / "package.json"
    if package_json.exists() and file_contains(
        package_json, "winston", "pino", "bunyan", "log4js"
    ):
        return CheckResult(
            passed=True,
            evidence="Found logging library in package.json",
        )

    return CheckResult(
        passed=False,
        evidence="No logging infrastructure found",
        suggestion="Add logging to your application (e.g., Python logging, structlog, winston for Node.js).",
    )


@check(
    name="structured_errors_present",
    category="observability",
    description="Check if structured error handling is present",
    pillar="structured_logging_cost",
)
def check_structured_errors_present(repo_path: Path) -> CheckResult:
    """Check if structured error handling exists."""
    # Check Python files for custom exceptions or error handling
    py_files = glob_files(repo_path, "**/*.py")
    for py_file in py_files[:50]:
        if file_contains(
            py_file,
            "(Exception)",  # Class inheriting from Exception
            "(Error)",  # Class inheriting from Error
            "raise ",  # Raise statements
            "except ",  # Exception handling
            "@dataclass",
            "pydantic",
        ):
            return CheckResult(
                passed=True,
                evidence=f"Found structured error handling in {py_file.relative_to(repo_path)}",
            )

    # Check for dedicated error/exception modules
    error_modules = [
        "errors.py",
        "exceptions.py",
        "error.py",
        "exception.py",
        "errors/__init__.py",
        "exceptions/__init__.py",
    ]
    for module in error_modules:
        if (repo_path / module).exists():
            return CheckResult(
                passed=True,
                evidence=f"Found error module: {module}",
            )

    # Check src directory
    src_dir = repo_path / "src"
    if src_dir.exists():
        for module in error_modules:
            if (src_dir / module).exists():
                return CheckResult(
                    passed=True,
                    evidence=f"Found error module: src/{module}",
                )

    # Check TypeScript for custom error classes
    ts_files = glob_files(repo_path, "**/*.ts")
    for ts_file in ts_files[:50]:
        if file_contains(ts_file, "extends Error", "Error {", "Error<"):
            return CheckResult(
                passed=True,
                evidence=f"Found structured error handling in {ts_file.relative_to(repo_path)}",
            )

    # Check for Result types (Rust-style error handling)
    if (
        file_contains(repo_path / "Cargo.toml", "thiserror", "anyhow")
        if (repo_path / "Cargo.toml").exists()
        else False
    ):
        return CheckResult(
            passed=True,
            evidence="Found Rust error handling libraries (thiserror/anyhow)",
        )

    # Check Go for error handling patterns
    go_files = glob_files(repo_path, "**/*.go")
    for go_file in go_files[:50]:
        if file_contains(go_file, "errors.New", "fmt.Errorf", "type.*error"):
            return CheckResult(
                passed=True,
                evidence=f"Found error handling in {go_file.relative_to(repo_path)}",
            )

    return CheckResult(
        passed=False,
        evidence="No structured error handling found",
        suggestion="Add custom exception classes or structured error types for better error handling.",
    )
