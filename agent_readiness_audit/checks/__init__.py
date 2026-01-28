"""Check implementations for Agent Readiness Audit."""

# v3 domain-specific checks
from agent_readiness_audit.checks.agent_ergonomics import (
    check_agent_manifest_present,
    check_clear_error_messages,
    check_command_reproducibility,
    check_contribution_rules_explicit,
    check_deterministic_commands,
    check_machine_readable_configs,
)
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
from agent_readiness_audit.checks.determinism_advanced import (
    check_network_mockable,
    check_no_global_state_mutation,
    check_random_seed_injectable,
    check_time_abstraction,
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
from agent_readiness_audit.checks.interfaces_contracts import (
    check_api_schema_defined,
    check_cli_typed_args,
    check_contract_versioning,
    check_no_implicit_dict_schemas,
    check_return_types_documented,
    check_typed_interfaces,
)
from agent_readiness_audit.checks.observability import (
    check_logging_present,
    check_structured_errors_present,
)
from agent_readiness_audit.checks.security_advanced import (
    check_env_example_exists,
    check_no_hardcoded_secrets,
    check_no_sensitive_files_committed,
    check_prod_test_boundary,
    check_sensitive_files_gitignored,
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
from agent_readiness_audit.checks.structure_discoverability import (
    check_entrypoint_clear,
    check_file_tree_organized,
    check_no_hidden_critical_logic,
    check_predictable_layout,
    check_readme_answers_how,
    check_readme_answers_what,
)
from agent_readiness_audit.checks.test_feedback_loop import (
    check_test_command_detectable,
    check_test_command_has_timeout,
    check_tests_directory_or_config_exists,
)
from agent_readiness_audit.checks.testing_validation import (
    check_ci_enforces_tests,
    check_golden_fixtures_present,
    check_test_coverage_tracked,
    check_test_ordering_independent,
    check_tests_isolated,
    check_tests_no_network_required,
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
    # v3: Structure & Discoverability
    "check_readme_answers_what",
    "check_readme_answers_how",
    "check_predictable_layout",
    "check_entrypoint_clear",
    "check_no_hidden_critical_logic",
    "check_file_tree_organized",
    # v3: Interfaces & Contracts
    "check_typed_interfaces",
    "check_api_schema_defined",
    "check_cli_typed_args",
    "check_return_types_documented",
    "check_no_implicit_dict_schemas",
    "check_contract_versioning",
    # v3: Determinism & Side Effects
    "check_random_seed_injectable",
    "check_time_abstraction",
    "check_network_mockable",
    "check_no_global_state_mutation",
    # v3: Security & Blast Radius
    "check_no_hardcoded_secrets",
    "check_sensitive_files_gitignored",
    "check_env_example_exists",
    "check_prod_test_boundary",
    "check_no_sensitive_files_committed",
    # v3: Testing & Validation
    "check_tests_isolated",
    "check_tests_no_network_required",
    "check_golden_fixtures_present",
    "check_test_ordering_independent",
    "check_ci_enforces_tests",
    "check_test_coverage_tracked",
    # v3: Agent Ergonomics
    "check_machine_readable_configs",
    "check_deterministic_commands",
    "check_clear_error_messages",
    "check_contribution_rules_explicit",
    "check_agent_manifest_present",
    "check_command_reproducibility",
]
