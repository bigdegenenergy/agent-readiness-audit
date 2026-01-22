"""Pytest configuration and fixtures."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator

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
    (repo_path / "README.md").write_text("# Minimal Repo\n\n## Installation\n\npip install minimal\n")
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
