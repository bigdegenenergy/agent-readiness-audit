# Agent Instructions

This file provides guidance for AI agents working with the `agent-readiness-audit` repository.

## Project Overview

**agent-readiness-audit** (`ara`) is a CLI tool that audits repositories for agent-readiness and outputs human + machine-readable reports. It analyzes codebases across 8 dimensions and provides actionable recommendations.

## Quick Start

```bash
# Install dependencies
uv sync

# Run the CLI
uv run ara --help

# Scan a repository
uv run ara scan --repo /path/to/repo

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run ruff format --check .

# Run type checking
uv run mypy agent_readiness_audit
```

## Project Structure

```
agent-readiness-audit/
├── agent_readiness_audit/       # Main package
│   ├── __init__.py              # Version and package metadata
│   ├── cli.py                   # Typer CLI entry point (ara command)
│   ├── config.py                # Configuration loading and parsing
│   ├── models.py                # Pydantic data models
│   ├── scanner.py               # Main scanning logic
│   ├── checks/                  # Check implementations by category
│   │   ├── base.py              # Check framework and registry
│   │   ├── discoverability.py   # README, docs checks
│   │   ├── deterministic_setup.py
│   │   ├── build_and_run.py
│   │   ├── test_feedback_loop.py
│   │   ├── static_guardrails.py
│   │   ├── observability.py
│   │   ├── ci_enforcement.py
│   │   └── security_governance.py
│   ├── reporting/               # Output formatters
│   │   ├── json_report.py
│   │   ├── markdown_report.py
│   │   ├── table_report.py
│   │   └── artifacts.py
│   └── utils/                   # Utility functions
│       └── fs.py                # Filesystem helpers
├── tests/                       # Test suite
│   ├── conftest.py              # Pytest fixtures
│   ├── test_checks.py
│   ├── test_scanner.py
│   ├── test_cli.py
│   ├── test_config.py
│   └── test_reporting.py
├── .github/workflows/           # CI/CD
│   ├── ci.yml                   # Main CI pipeline
│   ├── release.yml              # Tag-based releases
│   └── oss-checks.yml           # Security scanning
└── pyproject.toml               # Project configuration
```

## Key Commands

| Task | Command |
|------|---------|
| Install deps | `uv sync` |
| Run CLI | `uv run ara <command>` |
| Run tests | `uv run pytest` |
| Run tests with coverage | `uv run pytest --cov=agent_readiness_audit` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type check | `uv run mypy agent_readiness_audit` |
| Build package | `uv build` |

## Adding a New Check

1. Identify the appropriate category in `agent_readiness_audit/checks/`
2. Create a check function using the `@check` decorator:

```python
from pathlib import Path
from agent_readiness_audit.checks.base import CheckResult, check

@check(
    name="my_new_check",
    category="discoverability",  # Must match category module
    description="Description of what this check verifies"
)
def check_my_new_thing(repo_path: Path) -> CheckResult:
    target_file = repo_path / "TARGET_FILE.md"
    if target_file.exists():
        return CheckResult(
            passed=True,
            evidence=f"Found {target_file.name}"
        )
    return CheckResult(
        passed=False,
        evidence="TARGET_FILE.md not found",
        suggestion="Add TARGET_FILE.md to improve agent readiness."
    )
```

3. Export the check in the category's `__init__.py`
4. Add tests in `tests/test_checks.py`

## Scoring Model

The tool scores repositories on a 0-16 scale across 8 categories (2 points each):

1. **Discoverability** - README, setup/test instructions
2. **Deterministic Setup** - Dependency manifests, lockfiles, runtime versions
3. **Build and Run** - Task runners, package scripts, documented commands
4. **Test Feedback Loop** - Test directory, test commands, test config
5. **Static Guardrails** - Linter, formatter, type checker configs
6. **Observability** - Logging, structured errors
7. **CI Enforcement** - CI workflows, test/lint gates
8. **Security & Governance** - .gitignore, .env.example, SECURITY.md, CONTRIBUTING.md

Score ranges map to readiness levels:
- 0-5: Human-Only Repo
- 6-9: Assisted Agent
- 10-13: Semi-Autonomous
- 14-16: Agent-Ready Factory

## Configuration

The tool reads `.agent_readiness_audit.toml` for customization:

```toml
[scoring]
scale_points_total = 16
minimum_passing_score = 10

[categories.discoverability]
enabled = true
max_points = 2

[checks.readme_exists]
enabled = true
weight = 1.0
```

## Testing Guidelines

- Use fixtures from `tests/conftest.py` for test repos
- Available fixtures: `empty_repo`, `minimal_repo`, `python_repo`, `node_repo`, `agent_ready_repo`
- Each check should have pass/fail test cases
- Run full suite before committing: `uv run pytest -v`

## Common Tasks for Agents

### Adding support for a new language/ecosystem

1. Add detection patterns to `agent_readiness_audit/config.py` (DetectionConfig)
2. Update relevant check functions to recognize new file patterns
3. Add test fixtures in `tests/conftest.py`
4. Add tests for new patterns

### Modifying scoring weights

1. Update defaults in `agent_readiness_audit/models.py` (AuditConfig.default())
2. Update `.agent_readiness_audit.toml` template in `config.py`
3. Update documentation in README.md

### Adding a new output format

1. Create new module in `agent_readiness_audit/reporting/`
2. Export from `agent_readiness_audit/reporting/__init__.py`
3. Add format option to CLI in `agent_readiness_audit/cli.py`
4. Add tests in `tests/test_reporting.py`

## Code Style

- Python 3.11+
- Ruff for linting and formatting
- Mypy for type checking (strict mode)
- Pydantic for data models
- Typer for CLI
- Rich for terminal output

## Before Committing

```bash
# Run all checks
uv run ruff check .
uv run ruff format .
uv run mypy agent_readiness_audit
uv run pytest -v

# Or use pre-commit
uv run pre-commit run --all-files
```

## CI/CD

- **ci.yml**: Runs on push/PR to main - lint, typecheck, test (Python 3.11-3.13)
- **release.yml**: Triggered by version tags (v*) - builds and creates GitHub release
- **oss-checks.yml**: Weekly OpenSSF Scorecard scan

## Useful Links

- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
