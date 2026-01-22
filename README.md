# Agent Readiness Audit

[![CI](https://github.com/bigdegenenergy/agent-readiness-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/bigdegenenergy/agent-readiness-audit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

**A CLI tool that audits repositories for agent-readiness and outputs human + machine-readable reports.**

Agent Readiness Audit (`ara`) certifies how well repositories support autonomous AI agents. It treats your codebase as a **deterministic API surface** for probabilistic entities (AI agents), measuring readiness across 15 pillars and 5 maturity levels.

## What is Agent Readiness?

Agent readiness measures how well a repository supports autonomous AI agents in performing development tasks. Agent-native environments require:

- **Determinism**: Reproducible builds, pinned dependencies, consistent environments
- **Fast Feedback**: Sub-second linting, pre-commit hooks, split test targets
- **Type Contracts**: Type hints and strict checking as machine-readable documentation
- **Verification Trust**: Machine-readable coverage, flake mitigation, test isolation
- **Structured Documentation**: Diataxis-style docs, inline docstrings
- **Agentic Security**: Prompt red-teaming, secret hygiene, sandboxed execution
- **Telemetry**: OpenTelemetry tracing, structured JSON logging
- **Evaluation Frameworks**: Golden datasets, regression testing for agent behavior

## Maturity Model

ARA v2 uses a 5-level maturity model:

| Level | Name         | Description                                                 | Score |
| ----- | ------------ | ----------------------------------------------------------- | ----- |
| 1     | Functional   | Works for humans; agents fail due to ambiguity              | 0-4   |
| 2     | Documented   | Setup/run instructions exist; agents can attempt tasks      | 5-7   |
| 3     | Standardized | CI, linting, tests, deterministic deps; minimum for agents  | 8-11  |
| 4     | Optimized    | Fast feedback, test splitting, strong guardrails            | 12-14 |
| 5     | Autonomous   | Telemetry, evals, golden datasets, agentic security posture | 15-16 |

Each level has **gate checks** that must pass. A repository cannot achieve Level N without passing all gates for that level. See [AGENTS.md](AGENTS.md) for the complete specification.

## No-Gaming Principles

ARA is designed to prevent score inflation:

1. **No ceremonial artifacts**: Checks verify meaningful content, not just file presence
2. **Evidence required**: Every pass/fail records evidence in output
3. **Gate enforcement**: High scores require actual capabilities, not workarounds
4. **Safe by default**: No arbitrary code execution; network calls require explicit opt-in
5. **Stable semantics**: Scoring changes require version bumps and migration notes

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

Scan with JSON output:

```bash
ara scan --repo . --format json
```

Scan multiple repositories:

```bash
ara scan --root ~/code --depth 2 --out ./reports
```

Strict mode (exit non-zero if below threshold):

```bash
ara scan --repo . --strict --min-score 10
```

## Scoring Model

Repositories are scored on a 0-16 point scale across 8 categories (v1 compatibility), while also reporting the 5-level maturity model.

### Categories (v1 Compatible)

| Category              | Description                            | Max Points |
| --------------------- | -------------------------------------- | ---------- |
| Discoverability       | README presence and onboarding clarity | 2          |
| Deterministic Setup   | Reproducible dependency management     | 2          |
| Build and Run         | Standard commands for build/test/lint  | 2          |
| Test Feedback Loop    | Test infrastructure and runnability    | 2          |
| Static Guardrails     | Linting, formatting, type checking     | 2          |
| Observability         | Logging and error handling             | 2          |
| CI Enforcement        | Continuous integration configuration   | 2          |
| Security & Governance | Security policies and hygiene          | 2          |

### Pillars (v2)

v2 introduces 15 pillars for more granular analysis:

- **environment_determinism**: Reproducible dependencies and pinned versions
- **fast_guardrails**: Sub-second local feedback (ruff, pre-commit)
- **type_contracts**: Type hints and strictness config
- **verification_trust**: Test reliability (flake mitigation, coverage artifacts)
- **verification_speed**: Fast feedback via test splitting
- **documentation_structure**: Structured docs (Diataxis)
- **inline_documentation**: Docstring coverage
- **contribution_contract**: CONTRIBUTING, code of conduct
- **agentic_security**: Prompt red-teaming (promptfoo)
- **secret_hygiene**: No hardcoded secrets, env documentation
- **telemetry_tracing**: OpenTelemetry instrumentation
- **structured_logging_cost**: JSON logging for cost/perf tracking
- **eval_frameworks**: DeepEval/Ragas integration
- **golden_datasets**: Regression test datasets
- **distribution_dx**: Package distribution readiness

## Configuration

ARA can be customized via a TOML configuration file. By default, it looks for `.agent_readiness_audit.toml` in the current directory or parent directories.

Generate a starter configuration:

```bash
ara init-config
```

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
python_type_hint_coverage = { enabled = true, weight = 1.0 }

[thresholds]
type_hint_coverage_pass = 70    # Percentage for Level 4
type_hint_coverage_optimal = 85 # Percentage for Level 5
```

## Output Formats

### Table (default)

Human-readable terminal output with colors:

```bash
ara scan --repo . --format table
```

### JSON

Machine-readable JSON including maturity level, pillars, and gates:

```bash
ara scan --repo . --format json
```

```json
{
    "maturity_level": 4,
    "maturity_name": "Optimized",
    "score_total": 13.5,
    "max_score": 16,
    "gates": {
        "level_3": { "passed": true },
        "level_4": { "passed": true },
        "level_5": {
            "passed": false,
            "failed_checks": ["opentelemetry_present"]
        }
    }
}
```

### Markdown

Documentation-ready reports:

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

## Adding Custom Checks

New checks can be added by creating a function decorated with `@check`:

```python
from pathlib import Path
from agent_readiness_audit.checks.base import CheckResult, check

@check(
    name="my_custom_check",
    category="discoverability",
    description="Check for custom requirement",
    pillar="documentation_structure",
    gate_level=3,  # Optional: makes this a gate for Level 3
)
def check_my_custom_thing(repo_path: Path) -> CheckResult:
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

See [AGENTS.md](AGENTS.md) for the complete check specification contract.

## Documentation

- [AGENTS.md](AGENTS.md) - **Authoritative v2 specification**: maturity model, pillars, check contracts
- [CLAUDE.md](CLAUDE.md) - AI development instructions
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

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

# Run all quality checks
make check
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
