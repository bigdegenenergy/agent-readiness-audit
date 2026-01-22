"""Check implementations for Agent Readiness Audit."""

from agent_readiness_audit.checks.base import CheckResult, check, get_all_checks
from agent_readiness_audit.checks.discoverability import (
    check_readme_exists,
    check_readme_has_setup_section,
    check_readme_has_test_instructions,
)
from agent_readiness_audit.checks.deterministic_setup import (
    check_dependency_manifest_exists,
    check_lockfile_exists,
    check_runtime_version_declared,
)
from agent_readiness_audit.checks.build_and_run import (
    check_documented_commands_present,
    check_make_or_task_runner_exists,
    check_package_scripts_or_equivalent,
)
from agent_readiness_audit.checks.test_feedback_loop import (
    check_test_command_detectable,
    check_test_command_has_timeout,
    check_tests_directory_or_config_exists,
)
from agent_readiness_audit.checks.static_guardrails import (
    check_formatter_config_present,
    check_linter_config_present,
    check_typecheck_config_present,
)
from agent_readiness_audit.checks.observability import (
    check_logging_present,
    check_structured_errors_present,
)
from agent_readiness_audit.checks.ci_enforcement import (
    check_ci_runs_tests_or_lint,
    check_ci_workflow_present,
)
from agent_readiness_audit.checks.security_governance import (
    check_env_example_or_secrets_docs_present,
    check_gitignore_present,
    check_security_policy_present_or_baseline,
)

__all__ = [
    "CheckResult",
    "check",
    "get_all_checks",
    # Discoverability
    "check_readme_exists",
    "check_readme_has_setup_section",
    "check_readme_has_test_instructions",
    # Deterministic Setup
    "check_dependency_manifest_exists",
    "check_lockfile_exists",
    "check_runtime_version_declared",
    # Build and Run
    "check_make_or_task_runner_exists",
    "check_package_scripts_or_equivalent",
    "check_documented_commands_present",
    # Test Feedback Loop
    "check_tests_directory_or_config_exists",
    "check_test_command_detectable",
    "check_test_command_has_timeout",
    # Static Guardrails
    "check_linter_config_present",
    "check_formatter_config_present",
    "check_typecheck_config_present",
    # Observability
    "check_logging_present",
    "check_structured_errors_present",
    # CI Enforcement
    "check_ci_workflow_present",
    "check_ci_runs_tests_or_lint",
    # Security and Governance
    "check_gitignore_present",
    "check_env_example_or_secrets_docs_present",
    "check_security_policy_present_or_baseline",
]
