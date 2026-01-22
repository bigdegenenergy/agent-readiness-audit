"""Pytest configuration and fixtures."""

from __future__ import annotations

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def empty_repo(temp_dir: Path) -> Path:
    """Create an empty git repository."""
    repo_path = temp_dir / "empty-repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()
    return repo_path


@pytest.fixture
def minimal_repo(temp_dir: Path) -> Path:
    """Create a minimal repository with basic files."""
    repo_path = temp_dir / "minimal-repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()
    (repo_path / "README.md").write_text(
        "# Minimal Repo\n\n## Installation\n\npip install minimal\n"
    )
    (repo_path / ".gitignore").write_text("__pycache__/\n*.pyc\n")
    return repo_path


@pytest.fixture
def python_repo(temp_dir: Path) -> Path:
    """Create a Python repository with standard structure."""
    repo_path = temp_dir / "python-repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()

    # README
    (repo_path / "README.md").write_text(
        """# Python Repo

## Installation

```bash
pip install python-repo
```

## Testing

```bash
pytest
```
"""
    )

    # pyproject.toml
    (repo_path / "pyproject.toml").write_text(
        """[project]
name = "python-repo"
version = "0.1.0"
requires-python = ">=3.11"

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F"]

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
"""
    )

    # Source code
    src_dir = repo_path / "src" / "python_repo"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('"""Python repo package."""\n')
    (src_dir / "main.py").write_text(
        """import logging

logger = logging.getLogger(__name__)

class AppError(Exception):
    pass

def main():
    logger.info("Starting")
"""
    )

    # Tests
    tests_dir = repo_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_main.py").write_text(
        """def test_placeholder():
    assert True
"""
    )

    # Other files
    (repo_path / ".gitignore").write_text("__pycache__/\n*.pyc\n.venv/\n")
    (repo_path / ".env.example").write_text("API_KEY=your-key-here\n")
    (repo_path / "Makefile").write_text(
        """test:
\tpytest

lint:
\truff check .

format:
\truff format .
"""
    )

    # CI
    workflows_dir = repo_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "ci.yml").write_text(
        """name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pytest ruff mypy
      - run: ruff check .
      - run: mypy .
      - run: pytest
"""
    )

    return repo_path


@pytest.fixture
def node_repo(temp_dir: Path) -> Path:
    """Create a Node.js repository with standard structure."""
    repo_path = temp_dir / "node-repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()

    # README
    (repo_path / "README.md").write_text(
        """# Node Repo

## Installation

```bash
npm install
```

## Testing

```bash
npm test
```
"""
    )

    # package.json
    (repo_path / "package.json").write_text(
        """{
  "name": "node-repo",
  "version": "1.0.0",
  "scripts": {
    "test": "jest",
    "lint": "eslint ."
  },
  "engines": {
    "node": ">=18"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "eslint": "^8.0.0"
  }
}
"""
    )

    # Lock file
    (repo_path / "package-lock.json").write_text('{"lockfileVersion": 3}')

    # Source
    (repo_path / "index.js").write_text("console.log('Hello');\n")

    # Config files
    (repo_path / ".eslintrc.json").write_text('{"extends": "eslint:recommended"}')
    (repo_path / ".prettierrc").write_text('{"semi": true}')
    (repo_path / "tsconfig.json").write_text('{"compilerOptions": {"strict": true}}')

    # Other files
    (repo_path / ".gitignore").write_text("node_modules/\n")
    (repo_path / ".nvmrc").write_text("18\n")

    return repo_path


@pytest.fixture
def agent_ready_repo(python_repo: Path) -> Path:
    """Create a fully agent-ready repository."""
    # Add SECURITY.md
    (python_repo / "SECURITY.md").write_text(
        """# Security Policy

## Reporting Vulnerabilities

Please report security issues via GitHub's private vulnerability reporting.
"""
    )

    # Add CONTRIBUTING.md
    (python_repo / "CONTRIBUTING.md").write_text(
        """# Contributing

## Development Setup

1. Clone the repo
2. Run `pip install -e .`
3. Run tests with `pytest`
"""
    )

    return python_repo


@pytest.fixture
def v2_optimized_repo(agent_ready_repo: Path) -> Path:
    """Create a v2-optimized repository with all Level 4+ checks passing.

    This fixture extends agent_ready_repo with:
    - Pre-commit configuration
    - Type hints in source code
    - Machine-readable coverage configuration
    - Test splitting markers
    - Docstrings on all public functions
    """
    # Add pre-commit config
    (agent_ready_repo / ".pre-commit-config.yaml").write_text(
        """repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
"""
    )

    # Add uv.lock for lockfile
    (agent_ready_repo / "uv.lock").write_text("# Lockfile placeholder\n")

    # Update pyproject.toml with strict mypy and coverage xml
    pyproject = agent_ready_repo / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "python-repo"
version = "0.1.0"
requires-python = ">=3.11"

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.11"
strict = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: unit tests",
    "integration: integration tests",
]
addopts = "--cov=src --cov-report=xml --cov-report=term"

[tool.coverage.report]
xml = true

[tool.coverage.xml]
output = "coverage.xml"
"""
    )

    # Update source code with type hints and docstrings
    src_dir = agent_ready_repo / "src" / "python_repo"
    (src_dir / "main.py").write_text(
        '''"""Main module for the application."""

import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Application-specific error class."""

    pass


def main() -> None:
    """Start the application.

    This is the main entry point for the application.
    It initializes logging and performs startup tasks.
    """
    logger.info("Starting")


def add(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number.
        b: Second number.

    Returns:
        The sum of a and b.
    """
    return a + b
'''
    )

    # Update __init__.py with type hints
    (src_dir / "__init__.py").write_text(
        '''"""Python repo package."""

__version__: str = "0.1.0"
'''
    )

    # Add Makefile with test splitting
    (agent_ready_repo / "Makefile").write_text(
        """test:
\tpytest

test-unit:
\tpytest -m unit

test-integration:
\tpytest -m integration

lint:
\truff check .

format:
\truff format .

typecheck:
\tmypy src
"""
    )

    # Add docs directory with Diataxis structure
    docs_dir = agent_ready_repo / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "tutorials").mkdir(exist_ok=True)
    (docs_dir / "how-to").mkdir(exist_ok=True)
    (docs_dir / "reference").mkdir(exist_ok=True)
    (docs_dir / "explanation").mkdir(exist_ok=True)
    (docs_dir / "tutorials" / "quickstart.md").write_text("# Quickstart Tutorial\n")
    (docs_dir / "how-to" / "setup.md").write_text("# How to Set Up\n")
    (docs_dir / "reference" / "api.md").write_text("# API Reference\n")
    (docs_dir / "explanation" / "architecture.md").write_text("# Architecture\n")

    return agent_ready_repo


@pytest.fixture
def llm_project_repo(v2_optimized_repo: Path) -> Path:
    """Create an LLM/agent project repository.

    This fixture extends v2_optimized_repo with:
    - OpenTelemetry dependencies
    - Structured logging (structlog)
    - DeepEval for evaluation
    - Golden test datasets
    - Promptfoo configuration
    """
    # Update pyproject.toml with LLM dependencies
    pyproject = v2_optimized_repo / "pyproject.toml"
    content = pyproject.read_text()
    content = content.replace(
        'requires-python = ">=3.11"',
        """requires-python = ">=3.11"
dependencies = [
    "openai",
    "opentelemetry-sdk",
    "opentelemetry-api",
    "structlog",
    "deepeval",
]""",
    )
    pyproject.write_text(content)

    # Add promptfoo config
    (v2_optimized_repo / "promptfooconfig.yaml").write_text(
        """description: Prompt testing suite
prompts:
  - prompts/system.txt
providers:
  - openai:gpt-4
tests:
  - vars:
      input: "Hello"
    assert:
      - type: contains
        value: "Hello"
"""
    )

    # Add prompts directory
    prompts_dir = v2_optimized_repo / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    (prompts_dir / "system.txt").write_text("You are a helpful assistant.\n")

    # Add golden test datasets
    evals_dir = v2_optimized_repo / "evals"
    evals_dir.mkdir(exist_ok=True)
    (evals_dir / "golden_cases.json").write_text(
        """[
  {"input": "Hello", "expected_output": "Hi there!"},
  {"input": "What is 2+2?", "expected_output": "4"}
]
"""
    )

    # Add tests/data with golden datasets
    test_data = v2_optimized_repo / "tests" / "data"
    test_data.mkdir(exist_ok=True)
    (test_data / "golden_inputs.json").write_text(
        """[
  {"query": "What is Python?", "expected_contains": "programming language"}
]
"""
    )

    # Add gitleaks config for secret scanning
    (v2_optimized_repo / ".gitleaks.toml").write_text(
        """title = "Gitleaks config"
[rules]
"""
    )

    return v2_optimized_repo
