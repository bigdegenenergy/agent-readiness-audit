"""Telemetry and observability checks - OpenTelemetry and structured logging."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    check_dependency_present,
    file_contains,
    glob_files,
    read_toml_section,
)


@check(
    name="opentelemetry_present",
    category="observability",
    description="Check if OpenTelemetry instrumentation is configured",
    pillar="telemetry_tracing",
    weight=2.0,
    gate_for=[5],
)
def check_opentelemetry_present(repo_path: Path) -> CheckResult:
    """Check if OpenTelemetry is configured for tracing."""
    # Check Python dependencies
    otel_python = check_dependency_present(
        repo_path,
        "opentelemetry-sdk",
        "opentelemetry-api",
        "opentelemetry",
        "opentelemetry-instrumentation",
    )
    if otel_python:
        return CheckResult(
            passed=True,
            evidence=f"Found OpenTelemetry Python dependency: {otel_python}",
        )

    # Check JS/TS dependencies
    package_json = repo_path / "package.json"
    if package_json.exists():
        content = package_json.read_text(encoding="utf-8", errors="ignore")
        if "@opentelemetry/" in content or '"opentelemetry-' in content:
            return CheckResult(
                passed=True,
                evidence="Found OpenTelemetry JS/TS dependencies in package.json",
            )

    # Check for tracing configuration files
    otel_configs = [
        "otel-collector-config.yaml",
        "otel-collector-config.yml",
        "opentelemetry.yaml",
        "tracing.yaml",
    ]
    for config in otel_configs:
        if (repo_path / config).exists():
            return CheckResult(
                passed=True,
                evidence=f"Found OpenTelemetry configuration: {config}",
            )

    # Check pyproject.toml for OTel
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore").lower()
        if "opentelemetry" in content:
            return CheckResult(
                passed=True,
                evidence="Found OpenTelemetry in pyproject.toml",
            )

    # Check for Jaeger/Zipkin (indicates tracing infrastructure)
    if check_dependency_present(repo_path, "jaeger", "zipkin", "jaeger-client"):
        return CheckResult(
            passed=True,
            partial=True,
            evidence="Found alternative tracing (Jaeger/Zipkin), not OpenTelemetry",
            suggestion="Consider migrating to OpenTelemetry for vendor-neutral tracing.",
        )

    # Check for AWS X-Ray
    if check_dependency_present(repo_path, "aws-xray-sdk", "aws_xray_sdk"):
        return CheckResult(
            passed=True,
            partial=True,
            evidence="Found AWS X-Ray for tracing",
            suggestion="Consider adding OpenTelemetry for vendor-neutral tracing.",
        )

    # Check if this looks like an agent/LLM project
    is_llm_project = check_dependency_present(
        repo_path,
        "langchain",
        "openai",
        "anthropic",
        "llama-index",
        "transformers",
    )
    if is_llm_project:
        return CheckResult(
            passed=False,
            evidence=f"LLM project detected ({is_llm_project}) but no tracing configured",
            suggestion="Add OpenTelemetry for agent behavior tracing. See: https://opentelemetry.io/docs/",
        )

    return CheckResult(
        passed=False,
        evidence="No OpenTelemetry instrumentation found",
        suggestion="Add opentelemetry-sdk for distributed tracing of agent behavior.",
    )


@check(
    name="structured_logging_present",
    category="observability",
    description="Check if structured (JSON) logging is configured",
    pillar="structured_logging_cost",
    weight=1.5,
    gate_for=[5],
)
def check_structured_logging_present(repo_path: Path) -> CheckResult:
    """Check if structured logging is configured for JSON output."""
    # Check for structlog (Python)
    has_structlog = check_dependency_present(repo_path, "structlog")
    if has_structlog:
        return CheckResult(
            passed=True,
            evidence="Found structlog in dependencies (structured logging)",
        )

    # Check for python-json-logger
    has_json_logger = check_dependency_present(repo_path, "python-json-logger")
    if has_json_logger:
        return CheckResult(
            passed=True,
            evidence="Found python-json-logger in dependencies",
        )

    # Check pyproject.toml for structlog config
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        structlog_section = read_toml_section(pyproject, "tool.structlog")
        if structlog_section:
            return CheckResult(
                passed=True,
                evidence="Found structlog configuration in pyproject.toml",
            )

    # Check for pino/winston JSON mode (JS/TS)
    package_json = repo_path / "package.json"
    if package_json.exists():
        content = package_json.read_text(encoding="utf-8", errors="ignore")
        if '"pino"' in content:
            return CheckResult(
                passed=True,
                evidence="Found pino in dependencies (JSON logging by default)",
            )
        if '"winston"' in content:
            # Winston needs to check for JSON format config
            return CheckResult(
                passed=True,
                partial=True,
                evidence="Found winston (may need JSON transport configuration)",
                suggestion="Configure winston with JSON transport for structured logs.",
            )
        if '"bunyan"' in content:
            return CheckResult(
                passed=True,
                evidence="Found bunyan in dependencies (JSON logging)",
            )

    # Check for loguru with JSON
    has_loguru = check_dependency_present(repo_path, "loguru")
    if has_loguru:
        # Check if serialization is configured
        py_files = glob_files(repo_path, "**/*.py", limit=30)
        for py_file in py_files:
            if file_contains(py_file, "serialize=True", ".serialize"):
                return CheckResult(
                    passed=True,
                    evidence="Found loguru with serialization enabled",
                )
        return CheckResult(
            passed=True,
            partial=True,
            evidence="Found loguru (add serialize=True for JSON output)",
            suggestion="Enable serialize=True in loguru for structured JSON logs.",
        )

    # Check for logging config with JSON formatter
    logging_configs = ["logging.yaml", "logging.yml", "logging.conf", "logging.ini"]
    for config_name in logging_configs:
        config_path = repo_path / config_name
        if config_path.exists():
            content = config_path.read_text(encoding="utf-8", errors="ignore").lower()
            if "json" in content:
                return CheckResult(
                    passed=True,
                    evidence=f"Found JSON logging configuration in {config_name}",
                )

    # Check Python files for JSON logging setup
    py_files = glob_files(repo_path, "**/*.py", limit=30)
    for py_file in py_files:
        if file_contains(
            py_file,
            "JSONFormatter",
            "json_logger",
            "JsonFormatter",
            "structlog.processors.JSONRenderer",
        ):
            return CheckResult(
                passed=True,
                evidence=f"Found JSON logging setup in {py_file.relative_to(repo_path)}",
            )

    # Check for basic logging (partial)
    has_logging = check_dependency_present(repo_path, "logging", "loguru")
    if has_logging:
        return CheckResult(
            passed=False,
            evidence="Found logging library but no structured/JSON format configured",
            suggestion="Add structlog or configure JSON formatter for machine-parsable logs.",
        )

    return CheckResult(
        passed=False,
        evidence="No structured logging configuration found",
        suggestion="Add structlog (Python) or pino (Node.js) for JSON structured logging.",
    )
