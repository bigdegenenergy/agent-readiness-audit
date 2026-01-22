"""Agentic security and telemetry checks for v2 agent readiness."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_exists,
    glob_files,
    read_file_safe,
)


@check(
    name="promptfoo_present",
    category="security_and_governance",
    description="Check for promptfoo prompt red-teaming configuration",
    pillar="agentic_security",
    gate_level=5,
)
def check_promptfoo_present(repo_path: Path) -> CheckResult:
    """Check if promptfoo is configured for prompt/agent testing.

    Promptfoo enables deterministic testing of prompts and agent behavior.
    """
    # Check for promptfoo config files
    promptfoo_configs = [
        "promptfooconfig.yaml",
        "promptfooconfig.yml",
        "promptfoo.yaml",
        "promptfoo.yml",
        ".promptfoo.yaml",
        ".promptfoo.yml",
    ]

    for config_name in promptfoo_configs:
        if (repo_path / config_name).exists():
            return CheckResult(
                passed=True,
                evidence=f"promptfoo configured via {config_name}",
            )

    # Check for promptfoo in package.json
    package_json = file_exists(repo_path, "package.json")
    if package_json:
        content = read_file_safe(package_json)
        if content and "promptfoo" in content:
            return CheckResult(
                passed=True,
                evidence="promptfoo referenced in package.json",
            )

    # Check for security docs mentioning red-teaming (partial)
    security_md = file_exists(repo_path, "SECURITY.md", ".github/SECURITY.md")
    if security_md:
        content = read_file_safe(security_md)
        if content and (
            "red team" in content.lower() or "prompt test" in content.lower()
        ):
            return CheckResult(
                passed=False,
                partial=True,
                evidence="Security docs mention red-teaming but no promptfoo config",
                suggestion="Add promptfooconfig.yaml for automated prompt testing.",
            )

    return CheckResult(
        passed=False,
        evidence="No promptfoo configuration found",
        suggestion="Add promptfooconfig.yaml with baseline prompt eval suite.",
    )


@check(
    name="prompt_secret_scanning",
    category="security_and_governance",
    description="Check for secrets in prompt templates",
    pillar="secret_hygiene",
)
def check_prompt_secret_scanning(repo_path: Path) -> CheckResult:
    """Check for hardcoded secrets in prompt templates.

    Scans prompt/, templates/, prompts/ directories for patterns that
    look like secrets (API keys, tokens, etc.).

    IMPORTANT: Never prints full secrets - only redacted hashes.
    """
    # Check if secret scanning tools are configured
    if file_exists(repo_path, ".gitleaks.toml", "gitleaks.toml"):
        return CheckResult(
            passed=True,
            evidence="gitleaks configured for secret scanning",
        )

    if file_exists(repo_path, ".trufflehog.yml", "trufflehog.yml"):
        return CheckResult(
            passed=True,
            evidence="trufflehog configured for secret scanning",
        )

    # Directories to scan for prompts
    prompt_dirs = ["prompt", "prompts", "templates", "prompt_templates"]

    # Patterns that indicate potential secrets
    secret_patterns = [
        r'api[_-]?key\s*[=:]\s*["\']?[a-zA-Z0-9_-]{20,}',
        r'secret[_-]?key\s*[=:]\s*["\']?[a-zA-Z0-9_-]{20,}',
        r'password\s*[=:]\s*["\']?[^\s"\']{8,}',
        r'token\s*[=:]\s*["\']?[a-zA-Z0-9_-]{20,}',
        r"sk-[a-zA-Z0-9]{32,}",  # OpenAI key pattern
        r"xox[baprs]-[a-zA-Z0-9-]+",  # Slack token pattern
        r"ghp_[a-zA-Z0-9]{36}",  # GitHub PAT pattern
        r"gho_[a-zA-Z0-9]{36}",  # GitHub OAuth token pattern
    ]

    suspicious_findings: list[tuple[str, str]] = []

    for dir_name in prompt_dirs:
        prompt_dir = repo_path / dir_name
        if not prompt_dir.is_dir():
            continue

        # Scan files in prompt directories
        for file_path in prompt_dir.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix in [".pyc", ".pyo", ".so", ".dll"]:
                continue

            content = read_file_safe(file_path, max_size=100_000)
            if not content:
                continue

            for pattern in secret_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Never store actual secret - only hash for evidence
                    redacted_hash = hashlib.sha256(match.encode()).hexdigest()[:8]
                    rel_path = str(file_path.relative_to(repo_path))
                    suspicious_findings.append(
                        (rel_path, f"[REDACTED:{redacted_hash}]")
                    )

    if not suspicious_findings:
        # Also check if no prompt dirs exist (not applicable)
        has_prompt_dirs = any((repo_path / d).is_dir() for d in prompt_dirs)
        if not has_prompt_dirs:
            return CheckResult(
                passed=True,
                evidence="No prompt template directories found; secret scan not applicable.",
            )
        return CheckResult(
            passed=True,
            evidence="No suspicious patterns found in prompt templates.",
        )

    # Limit findings in evidence (redacted)
    evidence_parts = [f"{len(suspicious_findings)} potential secrets detected"]
    files_with_issues = list({f[0] for f in suspicious_findings})[:3]
    evidence_parts.append(f"in files: {', '.join(files_with_issues)}")

    return CheckResult(
        passed=False,
        evidence=" ".join(evidence_parts),
        suggestion="Move secrets to environment variables; add .env.example for documentation.",
    )


@check(
    name="opentelemetry_present",
    category="observability",
    description="Check for OpenTelemetry instrumentation",
    pillar="telemetry_tracing",
    gate_level=5,
)
def check_opentelemetry_present(repo_path: Path) -> CheckResult:
    """Check if OpenTelemetry is configured for tracing.

    Tracing is essential for understanding agent behavior; logs alone are insufficient.
    """
    # Check pyproject.toml dependencies
    pyproject = file_exists(repo_path, "pyproject.toml")
    if pyproject:
        content = read_file_safe(pyproject)
        if content and "opentelemetry" in content.lower():
            return CheckResult(
                passed=True,
                evidence="OpenTelemetry packages found in pyproject.toml",
            )

    # Check requirements files
    for req_file in ["requirements.txt", "requirements-dev.txt"]:
        req_path = repo_path / req_file
        if req_path.exists():
            content = read_file_safe(req_path)
            if content and "opentelemetry" in content.lower():
                return CheckResult(
                    passed=True,
                    evidence=f"OpenTelemetry packages in {req_file}",
                )

    # Check package.json for JavaScript projects
    package_json = file_exists(repo_path, "package.json")
    if package_json:
        content = read_file_safe(package_json)
        if content and "@opentelemetry" in content:
            return CheckResult(
                passed=True,
                evidence="OpenTelemetry packages in package.json",
            )

    # Check for existing OTel config files
    otel_configs = [
        "otel-collector-config.yaml",
        "opentelemetry.yaml",
        "tracing.yaml",
    ]
    for config in otel_configs:
        if (repo_path / config).exists():
            return CheckResult(
                passed=True,
                evidence=f"OpenTelemetry config found: {config}",
            )

    # Check if basic logging exists (partial)
    py_files = glob_files(repo_path, "**/*.py")[:20]  # Sample
    for py_file in py_files:
        content = read_file_safe(py_file)
        if content and "import logging" in content:
            return CheckResult(
                passed=False,
                partial=True,
                evidence="Basic logging found but no OpenTelemetry",
                suggestion="Add opentelemetry-sdk for distributed tracing.",
            )

    return CheckResult(
        passed=False,
        evidence="No OpenTelemetry instrumentation found",
        suggestion="Add opentelemetry-sdk and configure basic tracing.",
    )


@check(
    name="structured_logging_present",
    category="observability",
    description="Check for structured (JSON) logging",
    pillar="structured_logging_cost",
    gate_level=5,
)
def check_structured_logging_present(repo_path: Path) -> CheckResult:
    """Check if structured logging is configured.

    JSON logging enables cost/perf/behavior aggregation for agent monitoring.
    """
    # Check for structlog in Python projects
    pyproject = file_exists(repo_path, "pyproject.toml")
    if pyproject:
        content = read_file_safe(pyproject)
        if content and "structlog" in content:
            return CheckResult(
                passed=True,
                evidence="structlog configured in pyproject.toml",
            )

    # Check requirements files
    for req_file in ["requirements.txt", "requirements-dev.txt"]:
        req_path = repo_path / req_file
        if req_path.exists():
            content = read_file_safe(req_path)
            if content and "structlog" in content:
                return CheckResult(
                    passed=True,
                    evidence=f"structlog in {req_file}",
                )

    # Check for python-json-logger
    if pyproject:
        content = read_file_safe(pyproject)
        if content and "python-json-logger" in content:
            return CheckResult(
                passed=True,
                evidence="python-json-logger configured for JSON logging",
            )

    # Check for logging config with JSON formatter
    logging_configs = ["logging.yaml", "logging.json", "logging_config.py"]
    for config in logging_configs:
        config_path = repo_path / config
        if config_path.exists():
            content = read_file_safe(config_path)
            if content and "json" in content.lower():
                return CheckResult(
                    passed=True,
                    evidence=f"JSON logging configured in {config}",
                )

    # Check package.json for pino or winston JSON logging
    package_json = file_exists(repo_path, "package.json")
    if package_json:
        content = read_file_safe(package_json)
        if content and ("pino" in content or "winston" in content):
            return CheckResult(
                passed=True,
                evidence="Structured logging library in package.json",
            )

    # Check if basic logging exists (partial)
    py_files = glob_files(repo_path, "**/*.py")[:10]
    for py_file in py_files:
        content = read_file_safe(py_file)
        if content and "import logging" in content:
            return CheckResult(
                passed=False,
                partial=True,
                evidence="Basic logging found but not structured/JSON",
                suggestion="Use structlog with JSON renderer for structured logging.",
            )

    return CheckResult(
        passed=False,
        evidence="No structured logging configuration found",
        suggestion="Add structlog with JSON renderer; document standard log fields.",
    )


@check(
    name="eval_framework_detect",
    category="security_and_governance",
    description="Check for LLM evaluation framework",
    pillar="eval_frameworks",
    gate_level=5,
)
def check_eval_framework_detect(repo_path: Path) -> CheckResult:
    """Check if an LLM evaluation framework is configured.

    Evals are unit tests for agentic behavior.
    """
    # Check for DeepEval
    pyproject = file_exists(repo_path, "pyproject.toml")
    if pyproject:
        content = read_file_safe(pyproject)
        if content:
            if "deepeval" in content.lower():
                return CheckResult(
                    passed=True,
                    evidence="DeepEval configured in pyproject.toml",
                )
            if "ragas" in content.lower():
                return CheckResult(
                    passed=True,
                    evidence="Ragas configured in pyproject.toml",
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
                if "deepeval" in content.lower():
                    return CheckResult(
                        passed=True,
                        evidence=f"DeepEval in {req_file}",
                    )
                if "ragas" in content.lower():
                    return CheckResult(
                        passed=True,
                        evidence=f"Ragas in {req_file}",
                    )

    # Check for evals directory (partial)
    if (repo_path / "evals").is_dir() or (repo_path / "evaluations").is_dir():
        return CheckResult(
            passed=False,
            partial=True,
            evidence="evals/ directory exists but no framework detected",
            suggestion="Add DeepEval or Ragas for structured LLM evaluation.",
        )

    return CheckResult(
        passed=False,
        evidence="No LLM evaluation framework detected",
        suggestion="Add DeepEval or Ragas with minimal test suite for agent behavior testing.",
    )


@check(
    name="golden_dataset_present",
    category="security_and_governance",
    description="Check for golden dataset for regression testing",
    pillar="golden_datasets",
    gate_level=5,
)
def check_golden_dataset_present(repo_path: Path) -> CheckResult:
    """Check if golden datasets exist for regression testing.

    Golden datasets enable consistent testing of agent outputs.
    """
    # Patterns for golden datasets
    golden_patterns = [
        "tests/data/golden*.json",
        "tests/data/golden*.csv",
        "tests/fixtures/golden*.json",
        "evals/test_cases*.json",
        "evals/golden*.json",
        "test_data/golden*.json",
        "fixtures/golden*.json",
    ]

    for pattern in golden_patterns:
        matches = glob_files(repo_path, pattern)
        if matches:
            # Try to count records in the file
            first_match = matches[0]
            content = read_file_safe(first_match, max_size=500_000)
            record_info = ""
            if content and first_match.suffix == ".json":
                try:
                    import json

                    data = json.loads(content)
                    if isinstance(data, list):
                        record_info = f" ({len(data)} records)"
                except (json.JSONDecodeError, ValueError):
                    pass

            rel_path = str(first_match.relative_to(repo_path))
            return CheckResult(
                passed=True,
                evidence=f"Golden dataset found: {rel_path}{record_info}",
            )

    # Check for test_cases.json or similar
    test_case_files = ["test_cases.json", "test_cases.yaml", "test_cases.yml"]
    for tc_file in test_case_files:
        tc_path = repo_path / "evals" / tc_file
        if tc_path.exists():
            return CheckResult(
                passed=True,
                evidence=f"Test cases found: evals/{tc_file}",
            )
        tc_path = repo_path / "tests" / "data" / tc_file
        if tc_path.exists():
            return CheckResult(
                passed=True,
                evidence=f"Test cases found: tests/data/{tc_file}",
            )

    # Check for examples that could be promoted (partial)
    example_files = glob_files(repo_path, "examples/*.json")
    if example_files:
        return CheckResult(
            passed=False,
            partial=True,
            evidence="Example data exists but not labeled as golden dataset",
            suggestion="Create tests/data/golden_dataset.json with expected outcomes.",
        )

    return CheckResult(
        passed=False,
        evidence="No golden dataset found",
        suggestion="Create golden dataset with 10-25 test cases and expected outcomes.",
    )
