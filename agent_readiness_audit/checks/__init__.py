"""Check implementations for Agent Readiness Audit."""

from agent_readiness_audit.checks.agentic_security import (
    check_eval_framework_detect,
    check_golden_dataset_present,
    check_opentelemetry_present,
    check_prompt_secret_scanning,
    check_promptfoo_present,
    check_structured_logging_present,
)
from agent_readiness_audit.checks.base import CheckResult, check, get_all_checks
from agent_readiness_audit.checks.build_and_run import (
    check_documented_commands_present,
    check_make_or_task_runner_exists,
    check_package_scripts_or_equivalent,
)
from agent_readiness_audit.checks.ci_enforcement import (
    check_ci_runs_tests_or_lint,
    check_ci_workflow_present,
)
from agent_readiness_audit.checks.deterministic_setup import (
    check_dependency_manifest_exists,
    check_lockfile_exists,
    check_runtime_version_declared,
)
from agent_readiness_audit.checks.discoverability import (
    check_readme_exists,
    check_readme_has_setup_section,
    check_readme_has_test_instructions,
)
from agent_readiness_audit.checks.documentation import (
    check_contributing_exists,
    check_diataxis_structure,
    check_docstring_coverage_python,
)
from agent_readiness_audit.checks.fast_guardrails import (
    check_fast_linter_python,
    check_flake_awareness_pytest,
    check_machine_readable_coverage,
    check_precommit_present,
    check_test_splitting,
)
from agent_readiness_audit.checks.observability import (
    check_logging_present,
    check_structured_errors_present,
)
from agent_readiness_audit.checks.security_governance import (
    check_env_example_or_secrets_docs_present,
    check_gitignore_present,
    check_security_policy_present_or_baseline,
)
from agent_readiness_audit.checks.static_guardrails import (
    check_formatter_config_present,
    check_linter_config_present,
    check_typecheck_config_present,
)
from agent_readiness_audit.checks.test_feedback_loop import (
    check_test_command_detectable,
    check_test_command_has_timeout,
    check_tests_directory_or_config_exists,
)

# v2 checks
from agent_readiness_audit.checks.type_contracts import (
    check_mypy_strictness,
    check_python_type_hint_coverage,
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
    # v2: Type Contracts
    "check_python_type_hint_coverage",
    "check_mypy_strictness",
    # v2: Documentation
    "check_diataxis_structure",
    "check_docstring_coverage_python",
    "check_contributing_exists",
    # v2: Fast Guardrails
    "check_fast_linter_python",
    "check_precommit_present",
    "check_test_splitting",
    "check_machine_readable_coverage",
    "check_flake_awareness_pytest",
    # v2: Agentic Security & Telemetry
    "check_promptfoo_present",
    "check_prompt_secret_scanning",
    "check_opentelemetry_present",
    "check_structured_logging_present",
    "check_eval_framework_detect",
    "check_golden_dataset_present",
]
