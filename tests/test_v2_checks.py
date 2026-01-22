"""Tests for v2 checks - type contracts, verification, docs, telemetry, evals."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks import (
    check_diataxis_structure,
    check_docstring_coverage_python,
    check_eval_framework_detect,
    check_fast_linter_python,
    check_flake_awareness_pytest,
    check_golden_dataset_present,
    check_machine_readable_coverage,
    check_mypy_strictness,
    check_opentelemetry_present,
    check_precommit_present,
    check_prompt_secret_scanning,
    check_promptfoo_present,
    check_python_type_hint_coverage,
    check_structured_logging_present,
    check_test_splitting,
)


class TestFastGuardrails:
    """Tests for fast guardrails v2 checks."""

    def test_fast_linter_python_ruff(self, python_repo: Path) -> None:
        result = check_fast_linter_python(python_repo)
        assert result.passed
        assert "ruff" in result.evidence.lower()

    def test_fast_linter_python_missing(self, minimal_repo: Path) -> None:
        result = check_fast_linter_python(minimal_repo)
        assert not result.passed

    def test_precommit_present(self, v2_optimized_repo: Path) -> None:
        result = check_precommit_present(v2_optimized_repo)
        assert result.passed
        assert (
            "ruff" in result.evidence.lower() or "pre-commit" in result.evidence.lower()
        )

    def test_precommit_missing(self, python_repo: Path) -> None:
        result = check_precommit_present(python_repo)
        # Python repo has CI but no pre-commit, so it's partial
        assert not result.passed or result.partial


class TestTypeContracts:
    """Tests for type contracts v2 checks."""

    def test_python_type_hint_coverage(self, v2_optimized_repo: Path) -> None:
        result = check_python_type_hint_coverage(v2_optimized_repo)
        # The v2_optimized_repo has type hints, should pass or be partial
        assert result.passed

    def test_python_type_hint_coverage_no_hints(self, python_repo: Path) -> None:
        result = check_python_type_hint_coverage(python_repo)
        # Basic python_repo doesn't have full type hints
        # Result depends on coverage percentage - just verify it runs
        assert result.evidence  # Has some evidence

    def test_mypy_strictness(self, v2_optimized_repo: Path) -> None:
        result = check_mypy_strictness(v2_optimized_repo)
        assert result.passed
        assert (
            "strict" in result.evidence.lower()
            or "disallow_untyped" in result.evidence.lower()
        )

    def test_mypy_strictness_missing(self, minimal_repo: Path) -> None:
        result = check_mypy_strictness(minimal_repo)
        assert not result.passed


class TestVerification:
    """Tests for verification v2 checks."""

    def test_flake_awareness_pytest(self, python_repo: Path) -> None:
        result = check_flake_awareness_pytest(python_repo)
        # Python repo doesn't have flaky test mitigation
        assert not result.passed

    def test_machine_readable_coverage(self, v2_optimized_repo: Path) -> None:
        result = check_machine_readable_coverage(v2_optimized_repo)
        assert result.passed
        assert "xml" in result.evidence.lower()

    def test_machine_readable_coverage_missing(self, python_repo: Path) -> None:
        result = check_machine_readable_coverage(python_repo)
        # Python repo doesn't have coverage xml configured
        assert not result.passed

    def test_test_splitting(self, v2_optimized_repo: Path) -> None:
        result = check_test_splitting(v2_optimized_repo)
        # v2_optimized has unit/integration markers and Makefile targets
        assert result.passed

    def test_test_splitting_missing(self, python_repo: Path) -> None:
        result = check_test_splitting(python_repo)
        # Basic python_repo doesn't have test splitting
        assert not result.passed


class TestDocumentation:
    """Tests for documentation v2 checks."""

    def test_diataxis_structure(self, v2_optimized_repo: Path) -> None:
        result = check_diataxis_structure(v2_optimized_repo)
        assert result.passed
        # Check for Diataxis categories in evidence
        evidence_lower = result.evidence.lower()
        assert any(
            cat in evidence_lower
            for cat in ["tutorial", "how-to", "reference", "explanation"]
        )

    def test_diataxis_structure_missing(self, python_repo: Path) -> None:
        result = check_diataxis_structure(python_repo)
        # Basic python_repo doesn't have docs directory
        assert not result.passed

    def test_docstring_coverage_python(self, v2_optimized_repo: Path) -> None:
        result = check_docstring_coverage_python(v2_optimized_repo)
        # v2_optimized has docstrings
        assert result.passed


class TestAgenticSecurity:
    """Tests for agentic security v2 checks."""

    def test_promptfoo_present(self, llm_project_repo: Path) -> None:
        result = check_promptfoo_present(llm_project_repo)
        assert result.passed
        assert "promptfoo" in result.evidence.lower()

    def test_promptfoo_missing(self, python_repo: Path) -> None:
        result = check_promptfoo_present(python_repo)
        assert not result.passed

    def test_prompt_secret_scanning(self, llm_project_repo: Path) -> None:
        result = check_prompt_secret_scanning(llm_project_repo)
        assert result.passed
        assert "gitleaks" in result.evidence.lower()

    def test_prompt_secret_scanning_partial(self, python_repo: Path) -> None:
        result = check_prompt_secret_scanning(python_repo)
        # No prompts dir, so it's partial pass
        assert result.passed and result.partial


class TestTelemetry:
    """Tests for telemetry v2 checks."""

    def test_opentelemetry_present(self, llm_project_repo: Path) -> None:
        result = check_opentelemetry_present(llm_project_repo)
        assert result.passed
        assert "opentelemetry" in result.evidence.lower()

    def test_opentelemetry_missing(self, python_repo: Path) -> None:
        result = check_opentelemetry_present(python_repo)
        assert not result.passed

    def test_structured_logging_present(self, llm_project_repo: Path) -> None:
        result = check_structured_logging_present(llm_project_repo)
        assert result.passed
        assert "structlog" in result.evidence.lower()

    def test_structured_logging_missing(self, minimal_repo: Path) -> None:
        result = check_structured_logging_present(minimal_repo)
        assert not result.passed


class TestEvalFrameworks:
    """Tests for eval framework v2 checks."""

    def test_eval_framework_detect(self, llm_project_repo: Path) -> None:
        result = check_eval_framework_detect(llm_project_repo)
        assert result.passed
        assert (
            "deepeval" in result.evidence.lower()
            or "promptfoo" in result.evidence.lower()
        )

    def test_eval_framework_missing(self, python_repo: Path) -> None:
        result = check_eval_framework_detect(python_repo)
        assert not result.passed

    def test_golden_dataset_present(self, llm_project_repo: Path) -> None:
        result = check_golden_dataset_present(llm_project_repo)
        assert result.passed
        assert "golden" in result.evidence.lower()

    def test_golden_dataset_missing(self, python_repo: Path) -> None:
        result = check_golden_dataset_present(python_repo)
        assert not result.passed
