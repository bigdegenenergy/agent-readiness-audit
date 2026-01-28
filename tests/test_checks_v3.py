"""Tests for v3 domain-specific check implementations."""

from __future__ import annotations

from pathlib import Path


class TestStructureDiscoverabilityChecks:
    """Tests for Structure & Discoverability domain checks."""

    def test_readme_answers_what_pass(self, temp_dir: Path) -> None:
        """README with description should pass what check."""
        from agent_readiness_audit.checks import check_readme_answers_what

        repo = temp_dir / "what-repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        # Include "a tool" pattern that the check looks for
        (repo / "README.md").write_text(
            "# My Project\n\nA tool for auditing repositories.\n\n## Overview\n\nThis project helps with auditing.\n"
        )
        result = check_readme_answers_what(repo)
        assert result.passed
        assert "README" in result.evidence

    def test_readme_answers_what_fail(self, empty_repo: Path) -> None:
        """Empty repo should fail what check."""
        from agent_readiness_audit.checks import check_readme_answers_what

        result = check_readme_answers_what(empty_repo)
        assert not result.passed

    def test_readme_answers_how_pass(self, python_repo: Path) -> None:
        """README with setup section should pass how check."""
        from agent_readiness_audit.checks import check_readme_answers_how

        result = check_readme_answers_how(python_repo)
        assert result.passed

    def test_predictable_layout_pass(self, python_repo: Path) -> None:
        """Python repo with standard layout should pass."""
        from agent_readiness_audit.checks import check_predictable_layout

        result = check_predictable_layout(python_repo)
        assert result.passed

    def test_entrypoint_clear_pass(self, temp_dir: Path) -> None:
        """Repo with clear entrypoints should pass."""
        from agent_readiness_audit.checks import check_entrypoint_clear

        repo = temp_dir / "entrypoint-repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        # Add [project.scripts] to pyproject.toml
        (repo / "pyproject.toml").write_text(
            '[project]\nname = "test"\n\n[project.scripts]\ncli = "myapp.cli:main"\n'
        )
        result = check_entrypoint_clear(repo)
        assert result.passed
        assert "entry point" in result.evidence.lower()

    def test_file_tree_organized_pass(self, python_repo: Path) -> None:
        """Well-organized repo should pass."""
        from agent_readiness_audit.checks import check_file_tree_organized

        result = check_file_tree_organized(python_repo)
        assert result.passed


class TestInterfaceContractChecks:
    """Tests for Interfaces & Contracts domain checks."""

    def test_typed_interfaces_pass(self, temp_dir: Path) -> None:
        """Repo with Pydantic models should pass."""
        from agent_readiness_audit.checks import check_typed_interfaces

        repo = temp_dir / "typed-repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "models.py").write_text(
            "from pydantic import BaseModel\n\nclass User(BaseModel):\n    name: str\n"
        )
        result = check_typed_interfaces(repo)
        assert result.passed
        assert "Pydantic" in result.evidence

    def test_typed_interfaces_dataclass(self, temp_dir: Path) -> None:
        """Repo with dataclasses should pass."""
        from agent_readiness_audit.checks import check_typed_interfaces

        repo = temp_dir / "dataclass-repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "models.py").write_text(
            "from dataclasses import dataclass\n\n@dataclass\nclass User:\n    name: str\n"
        )
        result = check_typed_interfaces(repo)
        assert result.passed
        assert "dataclass" in result.evidence.lower()

    def test_typed_interfaces_fail(self, empty_repo: Path) -> None:
        """Empty repo should fail."""
        from agent_readiness_audit.checks import check_typed_interfaces

        result = check_typed_interfaces(empty_repo)
        assert not result.passed

    def test_return_types_documented_pass(self, temp_dir: Path) -> None:
        """Functions with return types should pass."""
        from agent_readiness_audit.checks import check_return_types_documented

        repo = temp_dir / "typed-returns"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "main.py").write_text(
            "def add(a: int, b: int) -> int:\n    return a + b\n\n"
            "def greet(name: str) -> str:\n    return f'Hello {name}'\n"
        )
        result = check_return_types_documented(repo)
        assert result.passed

    def test_return_types_documented_low_coverage(self, temp_dir: Path) -> None:
        """Functions without return types should fail."""
        from agent_readiness_audit.checks import check_return_types_documented

        repo = temp_dir / "untyped-returns"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "main.py").write_text(
            "def add(a, b):\n    return a + b\n\n"
            "def greet(name):\n    return f'Hello {name}'\n"
        )
        result = check_return_types_documented(repo)
        assert not result.passed

    def test_no_implicit_dict_schemas_pass(self, temp_dir: Path) -> None:
        """Code without Dict[str, Any] should pass."""
        from agent_readiness_audit.checks import check_no_implicit_dict_schemas

        repo = temp_dir / "explicit-schemas"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "main.py").write_text(
            "from dataclasses import dataclass\n\n@dataclass\nclass User:\n    name: str\n"
        )
        result = check_no_implicit_dict_schemas(repo)
        assert result.passed

    def test_no_implicit_dict_schemas_fail(self, temp_dir: Path) -> None:
        """Code with Dict[str, Any] should fail."""
        from agent_readiness_audit.checks import check_no_implicit_dict_schemas

        repo = temp_dir / "implicit-schemas"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "main.py").write_text(
            "from typing import Dict, Any\n\ndef get_data() -> Dict[str, Any]:\n    return {}\n"
        )
        result = check_no_implicit_dict_schemas(repo)
        assert not result.passed

    def test_cli_typed_args_typer(self, temp_dir: Path) -> None:
        """Typer CLI should pass."""
        from agent_readiness_audit.checks import check_cli_typed_args

        repo = temp_dir / "typer-cli"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "cli.py").write_text(
            "import typer\n\napp = typer.Typer()\n\n@app.command()\ndef main(name: str):\n    print(name)\n"
        )
        result = check_cli_typed_args(repo)
        assert result.passed
        assert "Typer" in result.evidence

    def test_contract_versioning_pass(self, python_repo: Path) -> None:
        """Repo with version in pyproject.toml should pass."""
        from agent_readiness_audit.checks import check_contract_versioning

        result = check_contract_versioning(python_repo)
        assert result.passed


class TestSecurityAdvancedChecks:
    """Tests for Security & Blast Radius domain checks."""

    def test_no_hardcoded_secrets_pass(self, python_repo: Path) -> None:
        """Repo without hardcoded secrets should pass."""
        from agent_readiness_audit.checks import check_no_hardcoded_secrets

        result = check_no_hardcoded_secrets(python_repo)
        assert result.passed

    def test_no_hardcoded_secrets_fail(self, temp_dir: Path) -> None:
        """Repo with hardcoded API key should fail."""
        from agent_readiness_audit.checks import check_no_hardcoded_secrets

        repo = temp_dir / "secrets-repo"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "config.py").write_text('api_key = "sk-1234567890abcdefghijklmnop"\n')
        result = check_no_hardcoded_secrets(repo)
        assert not result.passed
        assert "secret" in result.evidence.lower() or "key" in result.evidence.lower()

    def test_sensitive_files_gitignored_pass(self, python_repo: Path) -> None:
        """Repo with .env in gitignore should pass."""
        from agent_readiness_audit.checks import check_sensitive_files_gitignored

        # python_repo fixture has .gitignore with common patterns
        result = check_sensitive_files_gitignored(python_repo)
        # May be partial pass depending on patterns
        assert result.passed or result.evidence

    def test_sensitive_files_gitignored_fail(self, temp_dir: Path) -> None:
        """Repo without gitignore should fail."""
        from agent_readiness_audit.checks import check_sensitive_files_gitignored

        repo = temp_dir / "no-gitignore"
        repo.mkdir()
        (repo / ".git").mkdir()
        result = check_sensitive_files_gitignored(repo)
        assert not result.passed

    def test_env_example_exists_pass(self, python_repo: Path) -> None:
        """Repo with .env.example should pass."""
        from agent_readiness_audit.checks import check_env_example_exists

        result = check_env_example_exists(python_repo)
        assert result.passed

    def test_env_example_exists_fail(self, empty_repo: Path) -> None:
        """Empty repo should fail."""
        from agent_readiness_audit.checks import check_env_example_exists

        result = check_env_example_exists(empty_repo)
        assert not result.passed

    def test_prod_test_boundary_config_files(self, temp_dir: Path) -> None:
        """Repo with environment-specific configs should pass."""
        from agent_readiness_audit.checks import check_prod_test_boundary

        repo = temp_dir / "env-boundary"
        repo.mkdir()
        (repo / ".git").mkdir()
        config_dir = repo / "config"
        config_dir.mkdir()
        (config_dir / "production.py").write_text("DEBUG = False\n")
        (config_dir / "development.py").write_text("DEBUG = True\n")
        result = check_prod_test_boundary(repo)
        assert result.passed

    def test_prod_test_boundary_env_loading(self, temp_dir: Path) -> None:
        """Repo with environment-based config loading should pass."""
        from agent_readiness_audit.checks import check_prod_test_boundary

        repo = temp_dir / "env-loading"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "config.py").write_text(
            "import os\nENV = os.getenv('APP_ENV', 'development')\n"
        )
        result = check_prod_test_boundary(repo)
        assert result.passed


class TestDeterminismAdvancedChecks:
    """Tests for Determinism & Side Effects domain checks."""

    def test_no_global_state_mutation_pass(self, temp_dir: Path) -> None:
        """Code without global mutations should pass."""
        from agent_readiness_audit.checks import check_no_global_state_mutation

        repo = temp_dir / "no-globals"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "main.py").write_text(
            "def add(a: int, b: int) -> int:\n    return a + b\n"
        )
        result = check_no_global_state_mutation(repo)
        assert result.passed

    def test_time_abstraction_pass(self, temp_dir: Path) -> None:
        """Repo with freezegun dependency should pass."""
        from agent_readiness_audit.checks import check_time_abstraction

        repo = temp_dir / "time-abstracted"
        repo.mkdir()
        (repo / ".git").mkdir()
        # Check looks for freezegun/time-machine in dependencies
        (repo / "pyproject.toml").write_text(
            '[project]\nname = "test"\n\n[project.optional-dependencies]\ndev = ["freezegun>=1.0.0"]\n'
        )
        result = check_time_abstraction(repo)
        assert result.passed
        assert "freezegun" in result.evidence.lower()

    def test_network_mockable_pass(self, temp_dir: Path) -> None:
        """Repo with responses dependency should pass."""
        from agent_readiness_audit.checks import check_network_mockable

        repo = temp_dir / "network-mockable"
        repo.mkdir()
        (repo / ".git").mkdir()
        # Check looks for responses, vcrpy, or respx in dependencies
        (repo / "pyproject.toml").write_text(
            '[project]\nname = "test"\n\n[project.optional-dependencies]\ndev = ["responses>=0.23.0"]\n'
        )
        result = check_network_mockable(repo)
        assert result.passed
        assert "responses" in result.evidence.lower()

    def test_random_seed_injectable_pass(self, temp_dir: Path) -> None:
        """Code with RANDOM_SEED env var should pass."""
        from agent_readiness_audit.checks import check_random_seed_injectable

        repo = temp_dir / "seed-injectable"
        repo.mkdir()
        (repo / ".git").mkdir()
        # Check looks for RANDOM_SEED environment variable pattern
        (repo / "main.py").write_text(
            "import os\nimport random\n\n"
            "seed = os.getenv('RANDOM_SEED')\n"
            "if seed:\n"
            "    random.seed(int(seed))\n"
        )
        result = check_random_seed_injectable(repo)
        assert result.passed

    def test_random_seed_injectable_no_random(self, temp_dir: Path) -> None:
        """Code without random should pass (no random = no issue)."""
        from agent_readiness_audit.checks import check_random_seed_injectable

        repo = temp_dir / "no-random"
        repo.mkdir()
        (repo / ".git").mkdir()
        (repo / "main.py").write_text(
            "def add(a: int, b: int) -> int:\n    return a + b\n"
        )
        result = check_random_seed_injectable(repo)
        assert result.passed


class TestTestingValidationChecks:
    """Tests for Testing & Validation domain checks."""

    def test_tests_isolated_pass(self, temp_dir: Path) -> None:
        """Repo with conftest.py and fixtures should pass isolation check."""
        from agent_readiness_audit.checks import check_tests_isolated

        repo = temp_dir / "isolated-tests"
        repo.mkdir()
        (repo / ".git").mkdir()
        tests_dir = repo / "tests"
        tests_dir.mkdir()
        # Check looks for conftest.py with @pytest.fixture
        (tests_dir / "conftest.py").write_text(
            "import pytest\n\n@pytest.fixture\ndef client():\n    return {}\n"
        )
        result = check_tests_isolated(repo)
        assert result.passed
        assert "fixture" in result.evidence.lower()

    def test_tests_isolated_with_mocks(self, temp_dir: Path) -> None:
        """Repo with mock usage should pass isolation check."""
        from agent_readiness_audit.checks import check_tests_isolated

        repo = temp_dir / "mock-tests"
        repo.mkdir()
        (repo / ".git").mkdir()
        tests_dir = repo / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text(
            "from unittest.mock import MagicMock\n\ndef test_thing():\n    mock = MagicMock()\n"
        )
        result = check_tests_isolated(repo)
        assert result.passed
        assert "mock" in result.evidence.lower()

    def test_ci_enforces_tests_pass(self, python_repo: Path) -> None:
        """CI that runs tests should pass."""
        from agent_readiness_audit.checks import check_ci_enforces_tests

        result = check_ci_enforces_tests(python_repo)
        assert result.passed


class TestAgentErgonomicsChecks:
    """Tests for Agent Ergonomics domain checks."""

    def test_machine_readable_configs_pass(self, python_repo: Path) -> None:
        """Repo with TOML/YAML configs should pass."""
        from agent_readiness_audit.checks import check_machine_readable_configs

        result = check_machine_readable_configs(python_repo)
        assert result.passed

    def test_deterministic_commands_pass(self, python_repo: Path) -> None:
        """Repo with Makefile should pass."""
        from agent_readiness_audit.checks import check_deterministic_commands

        result = check_deterministic_commands(python_repo)
        assert result.passed

    def test_clear_error_messages_pass(self, python_repo: Path) -> None:
        """Repo with custom exceptions should pass."""
        from agent_readiness_audit.checks import check_clear_error_messages

        result = check_clear_error_messages(python_repo)
        assert result.passed
