# Contributing to Agent Readiness Audit

First off, thank you for considering contributing to Agent Readiness Audit! It's people like you that make this tool better for everyone.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, please include as many details as possible using our bug report template.

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce (be specific!)
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or things you tried that didn't work)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- A clear and descriptive title
- A detailed description of the proposed enhancement
- Examples of how the enhancement would be used
- Why this enhancement would be useful to most users

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Getting Started

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/agent-readiness-audit.git
cd agent-readiness-audit

# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run ruff format --check .

# Run type checking
uv run mypy agent_readiness_audit
```

### Running the CLI Locally

```bash
# Run directly
uv run ara --help

# Or install in development mode
uv pip install -e .
ara --help
```

## Adding New Checks

One of the main ways to contribute is by adding new checks. Here's how:

1. Create a new file in `agent_readiness_audit/checks/` or add to an existing category file.

2. Implement your check function following this pattern:

```python
from agent_readiness_audit.checks.base import CheckResult, check

@check(
    name="my_new_check",
    category="discoverability",  # or another category
    description="Description of what this check verifies"
)
def check_my_new_thing(repo_path: Path) -> CheckResult:
    # Your check logic here
    return CheckResult(
        passed=True,  # or False
        evidence="What was found",
        suggestion="How to fix if failed"
    )
```

3. Register your check in the appropriate category's `__init__.py`.

4. Add tests for your check in `tests/`.

5. Update documentation if needed.

## Style Guide

### Python Style

- We use [ruff](https://github.com/astral-sh/ruff) for linting and formatting
- We use [mypy](https://mypy-lang.org/) for type checking
- All functions should have type hints
- All public functions should have docstrings

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Documentation Style

- Use Markdown for all documentation
- Include code examples where appropriate
- Keep explanations clear and concise

## Project Structure

```
agent-readiness-audit/
├── agent_readiness_audit/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── config.py           # Configuration handling
│   ├── scanner.py          # Main scanning logic
│   ├── scoring.py          # Scoring calculations
│   ├── checks/             # Check implementations
│   │   ├── __init__.py
│   │   ├── base.py         # Base check infrastructure
│   │   └── ...             # Category-specific checks
│   ├── reporting/          # Report generation
│   │   ├── __init__.py
│   │   ├── json_report.py
│   │   ├── markdown_report.py
│   │   └── table_report.py
│   └── utils/              # Utility functions
├── tests/
│   ├── fixtures/           # Test fixtures
│   └── ...
├── docs/
└── ...
```

## Release Process

Releases are automated via GitHub Actions when a tag is pushed:

1. Update `CHANGELOG.md` with the new version's changes
2. Update version in `pyproject.toml`
3. Create and push a tag: `git tag v0.1.0 && git push origin v0.1.0`
4. GitHub Actions will build and create a release

## Questions?

Feel free to open an issue with your question or reach out to the maintainers.

Thank you for contributing! 🎉
