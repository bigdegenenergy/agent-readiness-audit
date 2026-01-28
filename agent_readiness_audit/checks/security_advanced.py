"""Advanced security checks for ARA v3 specification.

These checks evaluate whether a repository is safe for autonomous agent operation:
- No plaintext secrets in repo
- Secrets loaded via environment or secret managers
- Clear prod vs test boundaries
- Principle of least privilege
"""

from __future__ import annotations

import re
from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_exists,
    glob_files,
    read_file_safe,
)

# Patterns that might indicate hardcoded secrets
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\'][^"\']{10,}["\']', "API key"),
    (r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\'][^"\']{10,}["\']', "Secret key"),
    (r'(?i)(password|passwd)\s*[=:]\s*["\'][^"\']{4,}["\']', "Password"),
    (r'(?i)(token)\s*[=:]\s*["\'][^"\']{10,}["\']', "Token"),
    (
        r'(?i)(aws[_-]?access[_-]?key[_-]?id)\s*[=:]\s*["\'][A-Z0-9]{16,}["\']',
        "AWS key",
    ),
    (r"sk-[a-zA-Z0-9]{32,}", "OpenAI API key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub personal access token"),
    (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth token"),
]

# Files that should never be committed
SENSITIVE_FILES = [
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "service-account.json",
    "secrets.yaml",
    "secrets.yml",
    ".netrc",
    "id_rsa",
    "id_ed25519",
]


@check(
    name="no_hardcoded_secrets",
    category="security_and_governance",
    description="Check for absence of hardcoded secrets in code",
    domain="security",
)
def check_no_hardcoded_secrets(repo_path: Path) -> CheckResult:
    """Scan codebase for hardcoded secrets.

    Immediate rejection if:
    - Hardcoded API keys
    - Hardcoded passwords
    - Hardcoded tokens
    """
    findings: list[str] = []

    # Scan Python, JS, TS, and config files
    patterns_to_scan = ["**/*.py", "**/*.js", "**/*.ts", "**/*.yaml", "**/*.yml"]
    files_scanned = 0

    for pattern in patterns_to_scan:
        for file_path in glob_files(repo_path, pattern)[:30]:
            # Skip test files and fixtures
            if "test" in str(file_path).lower() or "fixture" in str(file_path).lower():
                continue

            content = read_file_safe(file_path)
            if not content:
                continue

            files_scanned += 1

            for secret_pattern, secret_type in SECRET_PATTERNS:
                matches = re.findall(secret_pattern, content)
                if matches:
                    rel_path = file_path.relative_to(repo_path)
                    findings.append(f"{rel_path}: potential {secret_type}")

            if len(findings) >= 5:
                break

        if len(findings) >= 5:
            break

    if findings:
        return CheckResult(
            passed=False,
            evidence=f"Found {len(findings)} potential secrets: {', '.join(findings[:3])}",
            suggestion="Remove hardcoded secrets and use environment variables or a secret manager.",
        )

    return CheckResult(
        passed=True,
        evidence=f"Scanned {files_scanned} files, no hardcoded secrets detected",
    )


@check(
    name="sensitive_files_gitignored",
    category="security_and_governance",
    description="Check that sensitive files are in .gitignore",
    domain="security",
)
def check_sensitive_files_gitignored(repo_path: Path) -> CheckResult:
    """Check that .gitignore includes common sensitive file patterns."""
    gitignore = repo_path / ".gitignore"

    if not gitignore.exists():
        return CheckResult(
            passed=False,
            evidence="No .gitignore file found",
            suggestion="Add a .gitignore file with patterns for .env, credentials, and keys.",
        )

    content = read_file_safe(gitignore)
    if not content:
        return CheckResult(
            passed=False,
            evidence=".gitignore exists but is empty or unreadable",
            suggestion="Add patterns for sensitive files (.env, *.pem, credentials.json).",
        )

    # Check for common patterns
    required_patterns = [".env", "*.pem", "*.key"]
    found_patterns = []
    missing_patterns = []

    for pattern in required_patterns:
        # Normalize pattern check
        if pattern in content or pattern.replace("*", "") in content:
            found_patterns.append(pattern)
        else:
            missing_patterns.append(pattern)

    if len(found_patterns) >= 2:
        return CheckResult(
            passed=True,
            evidence=f".gitignore includes sensitive patterns: {', '.join(found_patterns)}",
        )

    if found_patterns:
        return CheckResult(
            passed=True,
            partial=True,
            evidence=f".gitignore has some patterns ({', '.join(found_patterns)}) but missing {', '.join(missing_patterns)}",
        )

    return CheckResult(
        passed=False,
        evidence=".gitignore missing common sensitive file patterns",
        suggestion="Add .env, *.pem, *.key patterns to .gitignore.",
    )


@check(
    name="env_example_exists",
    category="security_and_governance",
    description="Check for .env.example or documentation of required environment variables",
    domain="security",
)
def check_env_example_exists(repo_path: Path) -> CheckResult:
    """Check for documentation of required environment variables."""
    # Check for .env.example or similar
    env_examples = [
        ".env.example",
        ".env.sample",
        ".env.template",
        "env.example",
        ".env.development.example",
    ]

    for env_file in env_examples:
        if file_exists(repo_path, env_file):
            return CheckResult(
                passed=True,
                evidence=f"Found environment template: {env_file}",
            )

    # Check README for environment variable documentation
    readme_files = ["README.md", "README.rst", "README.txt", "README"]
    for readme in readme_files:
        readme_path = repo_path / readme
        if readme_path.exists():
            content = read_file_safe(readme_path)
            if content and any(
                pattern in content.upper()
                for pattern in [
                    "ENVIRONMENT VARIABLE",
                    "ENV VAR",
                    ".ENV",
                    "CONFIGURATION",
                ]
            ):
                return CheckResult(
                    passed=True,
                    evidence="README documents environment configuration",
                )

    # Check for docs/configuration or similar
    config_docs = glob_files(repo_path, "docs/**/config*.md")
    if config_docs:
        return CheckResult(
            passed=True,
            evidence=f"Found configuration docs: {config_docs[0].name}",
        )

    return CheckResult(
        passed=False,
        evidence="No .env.example or environment documentation found",
        suggestion="Create .env.example documenting required environment variables.",
    )


@check(
    name="prod_test_boundary",
    category="security_and_governance",
    description="Check for clear separation between production and test configurations",
    domain="security",
)
def check_prod_test_boundary(repo_path: Path) -> CheckResult:
    """Check for clear prod/test environment separation.

    Looks for:
    - Separate config files for environments
    - Environment-based configuration loading
    - Test fixtures that don't touch prod resources
    """
    # Check for environment-specific configs
    env_configs = [
        "config/production.py",
        "config/development.py",
        "config/test.py",
        "settings/production.py",
        "settings/test.py",
        ".env.production",
        ".env.test",
        "config.production.yaml",
        "config.test.yaml",
    ]

    found_configs = []
    for config in env_configs:
        if file_exists(repo_path, config):
            found_configs.append(config)

    if len(found_configs) >= 2:
        return CheckResult(
            passed=True,
            evidence=f"Found environment-specific configs: {', '.join(found_configs[:3])}",
        )

    # Check for environment variable based config loading
    py_files = glob_files(repo_path, "**/*.py")[:30]
    for py_file in py_files:
        content = read_file_safe(py_file)
        if content:
            env_patterns = [
                "os.getenv('ENV'",
                "os.environ.get('ENVIRONMENT'",
                "os.getenv('APP_ENV'",
                "os.environ['ENV']",
                "settings_module",
                "DJANGO_SETTINGS_MODULE",
            ]
            for pattern in env_patterns:
                if pattern in content:
                    return CheckResult(
                        passed=True,
                        evidence=f"Found environment-based config in {py_file.name}",
                    )

    return CheckResult(
        passed=False,
        evidence="No clear prod/test boundary detected",
        suggestion="Create separate configuration files or use environment variables for prod/test separation.",
    )


@check(
    name="no_sensitive_files_committed",
    category="security_and_governance",
    description="Check that sensitive files are not committed to the repository",
    domain="security",
)
def check_no_sensitive_files_committed(repo_path: Path) -> CheckResult:
    """Check that known sensitive files are not in the repository."""
    found_sensitive: list[str] = []

    for sensitive_file in SENSITIVE_FILES:
        if file_exists(repo_path, sensitive_file):
            found_sensitive.append(sensitive_file)

    if found_sensitive:
        return CheckResult(
            passed=False,
            evidence=f"Sensitive files committed: {', '.join(found_sensitive)}",
            suggestion=f"Remove sensitive files ({', '.join(found_sensitive)}) and add to .gitignore.",
        )

    return CheckResult(
        passed=True,
        evidence="No sensitive files found in repository",
    )
