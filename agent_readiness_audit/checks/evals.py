"""Eval framework checks - agentic behavior testing and golden datasets."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    check_dependency_present,
    dir_exists,
    glob_files,
)


@check(
    name="eval_framework_detect",
    category="test_feedback_loop",
    description="Check if an eval framework for agentic testing is configured",
    pillar="eval_frameworks",
    weight=2.0,
    gate_for=[5],
)
def check_eval_framework_detect(repo_path: Path) -> CheckResult:
    """Check if an eval framework is configured for agent testing."""
    # Check for DeepEval
    has_deepeval = check_dependency_present(repo_path, "deepeval")
    if has_deepeval:
        return CheckResult(
            passed=True,
            evidence="Found DeepEval in dependencies (LLM evaluation framework)",
        )

    # Check for Ragas
    has_ragas = check_dependency_present(repo_path, "ragas")
    if has_ragas:
        return CheckResult(
            passed=True,
            evidence="Found Ragas in dependencies (RAG evaluation framework)",
        )

    # Check for LangSmith
    has_langsmith = check_dependency_present(repo_path, "langsmith")
    if has_langsmith:
        return CheckResult(
            passed=True,
            evidence="Found LangSmith in dependencies (LLM ops & evaluation)",
        )

    # Check for promptfoo (also works as eval framework)
    package_json = repo_path / "package.json"

    promptfoo_configs = [
        "promptfooconfig.yaml",
        "promptfooconfig.yml",
        "promptfoo.yaml",
    ]
    for config in promptfoo_configs:
        if (repo_path / config).exists():
            return CheckResult(
                passed=True,
                evidence=f"Found promptfoo configuration: {config}",
            )

    if package_json.exists():
        content = package_json.read_text(encoding="utf-8", errors="ignore")
        if "promptfoo" in content:
            return CheckResult(
                passed=True,
                evidence="Found promptfoo in package.json dependencies",
            )

    # Check for MLflow (model evaluation)
    has_mlflow = check_dependency_present(repo_path, "mlflow")
    if has_mlflow:
        return CheckResult(
            passed=True,
            partial=True,
            evidence="Found MLflow (model tracking, limited eval capabilities)",
            suggestion="Add DeepEval or Ragas for comprehensive LLM evaluation.",
        )

    # Check for Weights & Biases (W&B)
    has_wandb = check_dependency_present(repo_path, "wandb")
    if has_wandb:
        return CheckResult(
            passed=True,
            partial=True,
            evidence="Found W&B (experiment tracking, limited eval capabilities)",
            suggestion="Add DeepEval or Ragas for LLM-specific evaluation.",
        )

    # Check for evals directory
    evals_dir = dir_exists(repo_path, "evals", "eval", "evaluations")
    if evals_dir:
        return CheckResult(
            passed=True,
            partial=True,
            evidence=f"Found eval directory: {evals_dir.name}",
            suggestion="Add DeepEval or Ragas for standardized LLM evaluation metrics.",
        )

    # Check if this is an LLM project
    is_llm_project = check_dependency_present(
        repo_path,
        "langchain",
        "openai",
        "anthropic",
        "llama-index",
        "transformers",
        "huggingface-hub",
    )
    if is_llm_project:
        return CheckResult(
            passed=False,
            evidence=f"LLM project detected ({is_llm_project}) but no eval framework found",
            suggestion="Add DeepEval (pip install deepeval) or Ragas for agentic behavior testing.",
        )

    return CheckResult(
        passed=False,
        evidence="No eval framework detected",
        suggestion="Add an eval framework: DeepEval for LLM testing, Ragas for RAG evaluation.",
    )


@check(
    name="golden_dataset_present",
    category="test_feedback_loop",
    description="Check if golden test datasets exist for regression testing",
    pillar="golden_datasets",
    weight=2.0,
    gate_for=[5],
)
def check_golden_dataset_present(repo_path: Path) -> CheckResult:
    """Check if golden test datasets exist."""
    golden_patterns = [
        # Common golden dataset locations
        "tests/data/golden*.json",
        "tests/data/golden*.jsonl",
        "tests/data/golden*.csv",
        "tests/fixtures/golden*.json",
        "tests/fixtures/golden*.jsonl",
        "tests/fixtures/golden*.csv",
        "evals/test_cases*.json",
        "evals/test_cases*.jsonl",
        "evals/test_cases*.yaml",
        "evals/golden*.json",
        "evals/golden*.jsonl",
        "fixtures/golden*.json",
        "fixtures/golden*.jsonl",
        "data/golden*.json",
        "data/golden*.jsonl",
        # DeepEval convention
        "tests/test_cases.json",
        "tests/test_cases.jsonl",
        # Promptfoo convention
        "prompts/test_cases*.yaml",
        "prompts/evaluations*.yaml",
    ]

    found_files: list[str] = []
    for pattern in golden_patterns:
        matches = glob_files(repo_path, pattern, limit=5)
        for match in matches:
            found_files.append(str(match.relative_to(repo_path)))

    if found_files:
        return CheckResult(
            passed=True,
            evidence=f"Found golden dataset(s): {', '.join(found_files[:3])}",
        )

    # Check for test fixtures directories with JSON files
    fixture_dirs = ["tests/fixtures", "tests/data", "fixtures", "evals"]
    for fixture_dir in fixture_dirs:
        dir_path = repo_path / fixture_dir
        if dir_path.is_dir():
            json_files = list(dir_path.glob("*.json")) + list(dir_path.glob("*.jsonl"))
            if json_files:
                return CheckResult(
                    passed=True,
                    partial=True,
                    evidence=f"Found test data in {fixture_dir}/ ({len(json_files)} JSON files)",
                    suggestion="Consider naming files with 'golden' prefix for clarity.",
                )

    # Check for promptfoo evals
    promptfoo_configs = ["promptfooconfig.yaml", "promptfoo.yaml"]
    for config in promptfoo_configs:
        config_path = repo_path / config
        if config_path.exists():
            content = config_path.read_text(encoding="utf-8", errors="ignore").lower()
            if "tests:" in content or "test:" in content:
                return CheckResult(
                    passed=True,
                    partial=True,
                    evidence=f"Found test cases in {config}",
                    suggestion="Extract test cases to dedicated golden dataset files.",
                )

    # Check if evals exist but no golden datasets
    evals_dir = dir_exists(repo_path, "evals", "eval")
    if evals_dir:
        return CheckResult(
            passed=False,
            evidence="Found evals directory but no golden test datasets",
            suggestion="Add golden dataset files (e.g., tests/data/golden_cases.json) for regression testing.",
        )

    # Check if this is an LLM project
    is_llm_project = check_dependency_present(
        repo_path,
        "langchain",
        "openai",
        "anthropic",
        "llama-index",
        "deepeval",
        "ragas",
    )
    if is_llm_project:
        return CheckResult(
            passed=False,
            evidence=f"LLM project detected ({is_llm_project}) but no golden datasets found",
            suggestion="Create tests/data/golden_cases.json with expected inputs/outputs for regression testing.",
        )

    return CheckResult(
        passed=False,
        evidence="No golden test datasets found",
        suggestion="Add golden datasets (e.g., tests/data/golden_cases.json) with expected outcomes.",
    )
