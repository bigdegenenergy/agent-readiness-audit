# Agent Readiness Audit

[![CI](https://github.com/bigdegenenergy/agent-readiness-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/bigdegenenergy/agent-readiness-audit/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/agent-readiness-audit.svg)](https://badge.fury.io/py/agent-readiness-audit)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

**A CLI tool that audits repositories for agent-readiness and outputs human + machine-readable reports.**

Agent Readiness Audit (`ara`) helps you understand how well your repositories are prepared for AI agents to work with them autonomously. It analyzes your codebase across 8 key dimensions and provides actionable recommendations to improve agent compatibility.

## What is Agent Readiness?

Agent readiness measures how well a repository supports autonomous AI agents in performing development tasks. A highly agent-ready repository has clear documentation, reproducible builds, comprehensive tests, and strong guardrails that help agents understand, modify, and validate code changes safely.

The concept recognizes that AI agents work differently from human developers. They benefit from explicit instructions, deterministic environments, fast feedback loops, and clear boundaries. A repository optimized for agent readiness enables AI to contribute more effectively while reducing the risk of errors.

## Why This Exists

As AI agents become more capable of writing and modifying code, the quality of your repository's "developer experience" directly impacts how effectively agents can work with it. This tool helps you identify gaps and prioritize improvements that will make your codebase more accessible to both human and AI contributors.

Key benefits include faster agent onboarding, more reliable automated changes, reduced need for human intervention, and better overall code quality through improved documentation and testing practices.

## Installation

### Using uv (recommended)

```bash
uv tool install agent-readiness-audit
```

### Using pip

```bash
pip install agent-readiness-audit
```

### From source

```bash
git clone https://github.com/bigdegenenergy/agent-readiness-audit.git
cd agent-readiness-audit
uv sync
```

## Quickstart

Scan a single repository:

```bash
ara scan --repo .
```

Scan multiple repositories:

```bash
ara scan --root ~/code --depth 2 --out ./out
```

Generate a configuration file:

```bash
ara init-config --out ./.agent_readiness_audit.toml
```

## Configuration

Agent Readiness Audit can be customized via a TOML configuration file. By default, it looks for `.agent_readiness_audit.toml` in the current directory or parent directories.

Generate a starter configuration:

```bash
ara init-config
```

The configuration allows you to customize scoring weights, enable/disable specific checks, adjust detection patterns, and set minimum passing scores for strict mode.

Example configuration:

```toml
[scoring]
scale_points_total = 16
minimum_passing_score = 10

[categories.discoverability]
enabled = true
max_points = 2

[checks]
readme_exists = { enabled = true, weight = 1.0 }
```

## Scoring Model

Repositories are scored on a 0-16 point scale across 8 categories, each worth up to 2 points.

| Category | Description | Max Points |
|----------|-------------|------------|
| Discoverability | README presence and onboarding clarity | 2 |
| Deterministic Setup | Reproducible dependency management | 2 |
| Build and Run | Standard commands for build/test/lint | 2 |
| Test Feedback Loop | Test infrastructure and runnability | 2 |
| Static Guardrails | Linting, formatting, type checking | 2 |
| Observability | Logging and error handling | 2 |
| CI Enforcement | Continuous integration configuration | 2 |
| Security & Governance | Security policies and hygiene | 2 |

Scores map to readiness levels:

| Score Range | Level | Description |
|-------------|-------|-------------|
| 0-5 | Human-Only Repo | Requires significant human guidance |
| 6-9 | Assisted Agent | Agents can help with supervision |
| 10-13 | Semi-Autonomous | Agents can work with minimal oversight |
| 14-16 | Agent-Ready Factory | Fully optimized for autonomous agents |

## Adding Checks (Plugin Model)

New checks can be added by creating a function decorated with `@check`:

```python
from pathlib import Path
from agent_readiness_audit.checks.base import CheckResult, check

@check(
    name="my_custom_check",
    category="discoverability",
    description="Check for custom requirement"
)
def check_my_custom_thing(repo_path: Path) -> CheckResult:
    # Your check logic here
    if (repo_path / "CUSTOM_FILE.md").exists():
        return CheckResult(
            passed=True,
            evidence="Found CUSTOM_FILE.md"
        )
    return CheckResult(
        passed=False,
        evidence="CUSTOM_FILE.md not found",
        suggestion="Add a CUSTOM_FILE.md to document custom requirements."
    )
```

Register your check in the appropriate category's `__init__.py` and it will be automatically included in scans.

## Output Formats

Agent Readiness Audit supports multiple output formats.

### Table (default)

Human-readable terminal output with colors and formatting:

```bash
ara scan --repo . --format table
```

### JSON

Machine-readable JSON for integration with other tools:

```bash
ara scan --repo . --format json
```

### Markdown

Documentation-ready Markdown reports:

```bash
ara scan --repo . --format markdown
```

### Artifacts

Write all formats to an output directory:

```bash
ara scan --repo . --out ./reports
# Creates: summary.json, summary.md, {repo-name}.json, {repo-name}.md
```

## CLI Reference

### `ara scan`

Scan one or more repositories for agent readiness.

```
Options:
  --repo, -r PATH       Path to a single repository
  --root PATH           Path containing multiple repositories
  --depth, -d INT       Max search depth under --root (default: 2)
  --include, -i TEXT    Glob pattern to include repos
  --exclude, -e TEXT    Glob pattern to exclude repos
  --config, -c PATH     Path to config TOML file
  --format, -f FORMAT   Output format: table, json, markdown
  --out, -o PATH        Output directory for artifacts
  --strict, -s          Exit non-zero if below minimum score
  --min-score INT       Override minimum passing score (0-16)
```

### `ara report`

Render a report from previously saved JSON results.

```
Options:
  --input, -i PATH      Input JSON file from scan
  --format, -f FORMAT   Output format: table, markdown
```

### `ara init-config`

Generate a starter configuration file.

```
Options:
  --out, -o PATH        Output path (default: ./.agent_readiness_audit.toml)
```

## Roadmap

The following features are planned for future releases:

- Additional language-specific checks (Go, Rust, Java)
- Integration with popular CI/CD platforms
- Web dashboard for visualizing results over time
- GitHub Action for automated PR checks
- VS Code extension for real-time feedback
- Custom check plugin system with external packages

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/bigdegenenergy/agent-readiness-audit.git
cd agent-readiness-audit

# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run mypy agent_readiness_audit
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
