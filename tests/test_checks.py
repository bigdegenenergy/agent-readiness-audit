"""Tests for check implementations."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks import (
    check_ci_runs_tests_or_lint,
    check_ci_workflow_present,
    check_dependency_manifest_exists,
    check_documented_commands_present,
    check_env_example_or_secrets_docs_present,
    check_formatter_config_present,
    check_gitignore_present,
    check_linter_config_present,
    check_lockfile_exists,
    check_logging_present,
    check_make_or_task_runner_exists,
    check_package_scripts_or_equivalent,
    check_readme_exists,
    check_readme_has_setup_section,
    check_readme_has_test_instructions,
    check_runtime_version_declared,
    check_security_policy_present_or_baseline,
    check_structured_errors_present,
    check_test_command_detectable,
    check_tests_directory_or_config_exists,
    check_typecheck_config_present,
)


class TestDiscoverabilityChecks:
    """Tests for discoverability checks."""

    def test_readme_exists_pass(self, minimal_repo: Path) -> None:
        result = check_readme_exists(minimal_repo)
        assert result.passed
        assert "README" in result.evidence

    def test_readme_exists_fail(self, empty_repo: Path) -> None:
        result = check_readme_exists(empty_repo)
        assert not result.passed
        assert result.suggestion

    def test_readme_has_setup_section_pass(self, minimal_repo: Path) -> None:
        result = check_readme_has_setup_section(minimal_repo)
        assert result.passed

    def test_readme_has_setup_section_fail(self, empty_repo: Path) -> None:
        (empty_repo / "README.md").write_text("# Empty\n\nNo setup here.")
        result = check_readme_has_setup_section(empty_repo)
        assert not result.passed

    def test_readme_has_test_instructions_pass(self, python_repo: Path) -> None:
        result = check_readme_has_test_instructions(python_repo)
        assert result.passed

    def test_readme_has_test_instructions_fail(self, minimal_repo: Path) -> None:
        result = check_readme_has_test_instructions(minimal_repo)
        assert not result.passed


class TestDeterministicSetupChecks:
    """Tests for deterministic setup checks."""

    def test_dependency_manifest_exists_pass(self, python_repo: Path) -> None:
        result = check_dependency_manifest_exists(python_repo)
        assert result.passed
        assert "pyproject.toml" in result.evidence

    def test_dependency_manifest_exists_fail(self, empty_repo: Path) -> None:
        result = check_dependency_manifest_exists(empty_repo)
        assert not result.passed

    def test_lockfile_exists_pass(self, node_repo: Path) -> None:
        result = check_lockfile_exists(node_repo)
        assert result.passed

    def test_lockfile_exists_fail(self, python_repo: Path) -> None:
        result = check_lockfile_exists(python_repo)
        assert not result.passed

    def test_runtime_version_declared_pass(self, python_repo: Path) -> None:
        result = check_runtime_version_declared(python_repo)
        assert result.passed

    def test_runtime_version_declared_fail(self, empty_repo: Path) -> None:
        result = check_runtime_version_declared(empty_repo)
        assert not result.passed


class TestBuildAndRunChecks:
    """Tests for build and run checks."""

    def test_task_runner_exists_pass(self, python_repo: Path) -> None:
        result = check_make_or_task_runner_exists(python_repo)
        assert result.passed
        assert "Makefile" in result.evidence

    def test_task_runner_exists_fail(self, minimal_repo: Path) -> None:
        result = check_make_or_task_runner_exists(minimal_repo)
        assert not result.passed

    def test_package_scripts_pass(self, node_repo: Path) -> None:
        result = check_package_scripts_or_equivalent(node_repo)
        assert result.passed

    def test_documented_commands_pass(self, python_repo: Path) -> None:
        result = check_documented_commands_present(python_repo)
        assert result.passed


class TestTestFeedbackLoopChecks:
    """Tests for test feedback loop checks."""

    def test_tests_directory_exists_pass(self, python_repo: Path) -> None:
        result = check_tests_directory_or_config_exists(python_repo)
        assert result.passed

    def test_tests_directory_exists_fail(self, minimal_repo: Path) -> None:
        result = check_tests_directory_or_config_exists(minimal_repo)
        assert not result.passed

    def test_test_command_detectable_pass(self, python_repo: Path) -> None:
        result = check_test_command_detectable(python_repo)
        assert result.passed


class TestStaticGuardrailsChecks:
    """Tests for static guardrails checks."""

    def test_linter_config_pass(self, python_repo: Path) -> None:
        result = check_linter_config_present(python_repo)
        assert result.passed

    def test_linter_config_fail(self, minimal_repo: Path) -> None:
        result = check_linter_config_present(minimal_repo)
        assert not result.passed

    def test_formatter_config_pass(self, python_repo: Path) -> None:
        result = check_formatter_config_present(python_repo)
        assert result.passed

    def test_typecheck_config_pass(self, python_repo: Path) -> None:
        result = check_typecheck_config_present(python_repo)
        assert result.passed


class TestObservabilityChecks:
    """Tests for observability checks."""

    def test_logging_present_pass(self, python_repo: Path) -> None:
        result = check_logging_present(python_repo)
        assert result.passed

    def test_logging_present_fail(self, minimal_repo: Path) -> None:
        result = check_logging_present(minimal_repo)
        assert not result.passed

    def test_structured_errors_pass(self, python_repo: Path) -> None:
        result = check_structured_errors_present(python_repo)
        assert result.passed


class TestCIEnforcementChecks:
    """Tests for CI enforcement checks."""

    def test_ci_workflow_present_pass(self, python_repo: Path) -> None:
        result = check_ci_workflow_present(python_repo)
        assert result.passed

    def test_ci_workflow_present_fail(self, minimal_repo: Path) -> None:
        result = check_ci_workflow_present(minimal_repo)
        assert not result.passed

    def test_ci_runs_tests_pass(self, python_repo: Path) -> None:
        result = check_ci_runs_tests_or_lint(python_repo)
        assert result.passed


class TestSecurityGovernanceChecks:
    """Tests for security and governance checks."""

    def test_gitignore_present_pass(self, minimal_repo: Path) -> None:
        result = check_gitignore_present(minimal_repo)
        assert result.passed

    def test_gitignore_present_fail(self, empty_repo: Path) -> None:
        result = check_gitignore_present(empty_repo)
        assert not result.passed

    def test_env_example_pass(self, python_repo: Path) -> None:
        result = check_env_example_or_secrets_docs_present(python_repo)
        assert result.passed

    def test_security_policy_pass(self, agent_ready_repo: Path) -> None:
        result = check_security_policy_present_or_baseline(agent_ready_repo)
        assert result.passed

    def test_security_policy_fail(self, minimal_repo: Path) -> None:
        result = check_security_policy_present_or_baseline(minimal_repo)
        assert not result.passed


class TestGateCheckIntegrity:
    """Tests for gate check ID integrity.

    Ensures all check IDs referenced in GATE_CHECKS exist in the check registry.
    """

    def test_gate_check_ids_exist_in_registry(self) -> None:
        """Verify all gate check IDs reference valid registered checks."""
        from agent_readiness_audit.checks.base import get_all_checks
        from agent_readiness_audit.models import GATE_CHECKS

        # Get all registered check names (get_all_checks returns dict[name, definition])
        registered_checks = set(get_all_checks().keys())

        # Verify all gate checks exist
        missing_checks = []
        for level, check_ids in GATE_CHECKS.items():
            for check_id in check_ids:
                if check_id not in registered_checks:
                    missing_checks.append((level, check_id))

        assert not missing_checks, (
            f"Gate checks reference non-existent check IDs: {missing_checks}. "
            f"Registered checks: {sorted(registered_checks)}"
        )
