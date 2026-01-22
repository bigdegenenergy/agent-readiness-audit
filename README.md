# Agent Readiness Audit

[![CI](https://github.com/bigdegenenergy/agent-readiness-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/bigdegenenergy/agent-readiness-audit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

**Certify Technical Readiness for Autonomous Coding Agents**

Agent Readiness Audit (`ara`) analyzes repositories to determine how well they support AI agents working autonomously. It provides a **5-level maturity certification** with evidence-backed scoring and actionable fix-first recommendations.

## Why Agent Readiness Matters

AI coding agents work differently from human developers:

- They need **explicit instructions** rather than tribal knowledge
- They require **deterministic environments** with reproducible builds
- They benefit from **fast feedback loops** to validate changes quickly
- They rely on **typed contracts** and structured documentation

A repository optimized for agent readiness becomes a **deterministic API surface** that enables reliable autonomous development while reducing errors and human intervention.

## The 5-Level Maturity Model

| Level | Name             | Description                                                        |
| ----- | ---------------- | ------------------------------------------------------------------ |
| **1** | **Functional**   | Works for humans; agents fail due to ambiguity                     |
| **2** | **Documented**   | Setup/run instructions exist; agents can attempt tasks             |
| **3** | **Standardized** | CI, linting, tests, deterministic deps; minimum viable for agents  |
| **4** | **Optimized**    | Fast feedback loops; split tests; strong local guardrails          |
| **5** | **Autonomous**   | Telemetry + evals + golden datasets; full agent-native environment |

> **Note**: Level 3 is the minimum recommended for production agent workflows.

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

## Quick Start

```bash
# Scan current directory
ara scan --repo .

# Scan with detailed markdown output
ara scan --repo . --format markdown

# Scan multiple repositories
ara scan --root ~/projects --depth 2

# Generate output artifacts
ara scan --repo . --out ./reports

# Strict mode (fail if below threshold)
ara scan --repo . --strict --min-score 10

# Generate configuration file
ara init-config
```

## Example Output

```
Agent Readiness Audit Report

Repository: my-project
Score: 12/16 (75%)
Maturity Level: Level 3 - Standardized

Gate Status:
  Level 2: PASSED
  Level 3: PASSED
  Level 4: BLOCKED (precommit_present, machine_readable_coverage)
  Level 5: NOT REACHED

Fix-First Recommendations:
  1. Add .pre-commit-config.yaml with ruff + mypy hooks
  2. Enable coverage.xml output in pytest configuration
  3. Add test-unit and test-integration Makefile targets
```

## Scoring Pillars

ARA v2 evaluates repositories across **15 pillars** grouped into domains:

### Environment & Determinism

- **Environment Determinism**: Dependency manifests, lockfiles, runtime version pinning
- **Fast Guardrails**: Linters (ruff), formatters, pre-commit hooks

### Type Safety

- **Type Contracts**: Type hint coverage, mypy strictness configuration

### Verification

- **Verification Trust**: Test presence, CI enforcement, flakiness awareness
- **Verification Speed**: Test splitting, timeouts, parallel execution

### Documentation

- **Documentation Structure**: Diátaxis-aligned organization
- **Inline Documentation**: Docstring coverage
- **Contribution Contract**: CONTRIBUTING.md, templates

### Security

- **Agentic Security**: Prompt red-teaming (promptfoo)
- **Secret Hygiene**: .gitignore, .env patterns, secret scanning

### Observability

- **Telemetry & Tracing**: OpenTelemetry instrumentation
- **Structured Logging**: JSON logs, standard fields

### Evaluation

- **Eval Frameworks**: DeepEval, Ragas integration
- **Golden Datasets**: Test cases with expected outcomes

### Distribution

- **Distribution DX**: README quality, setup instructions

## Level Requirements (Gates)

Each maturity level requires passing specific "gate" checks:

### Level 3 (Standardized) - Minimum for Production Agents

- README with setup and test instructions
- Dependency manifest and lockfile
- CI workflow that runs tests and linting
- Linter configuration

### Level 4 (Optimized) - Fast Feedback Loops

- Pre-commit hooks configured
- Fast linter (ruff for Python)
- 70%+ type hint coverage
- Machine-readable coverage output
- Test splitting (unit/integration)

### Level 5 (Autonomous) - Full Agent-Native

- 85%+ type hint coverage
- OpenTelemetry instrumentation
- Structured logging (structlog/JSON)
- Eval framework integration
- Golden dataset for regression testing
- Prompt testing (promptfoo)

## Configuration

ARA can be customized via `.agent_readiness_audit.toml`:

```toml
[scoring]
scale_points_total = 16
minimum_passing_score = 10

[categories.discoverability]
enabled = true
max_points = 2

[checks]
readme_exists = { enabled = true, weight = 1.0 }
python_type_hint_coverage = { enabled = true, threshold_level_4 = 70, threshold_level_5 = 85 }

[output]
default_format = "table"
show_evidence = true
show_gates = true
```

Generate a starter config:

```bash
ara init-config
```

## Output Formats

### Table (default)

Human-readable terminal output with colors:

```bash
ara scan --repo . --format table
```

### JSON

Machine-readable for CI integration:

```bash
ara scan --repo . --format json
```

### Markdown

Documentation-ready reports:

```bash
ara scan --repo . --format markdown
```

### Artifacts

Write all formats to directory:

```bash
ara scan --repo . --out ./reports
# Creates: summary.json, summary.md, {repo-name}.json, {repo-name}.md
```

## CLI Reference

### `ara scan`

```
Options:
  --repo, -r PATH       Path to a single repository (default: CWD)
  --root PATH           Path containing multiple repositories
  --depth, -d INT       Max search depth under --root (default: 2)
  --include, -i TEXT    Glob pattern to include repos
  --exclude, -e TEXT    Glob pattern to exclude repos
  --config, -c PATH     Path to config TOML file
  --format, -f FORMAT   Output: table, json, markdown (default: table)
  --out, -o PATH        Output directory for artifacts
  --strict, -s          Exit non-zero if below minimum score
  --min-score INT       Override minimum passing score (0-16)
```

### `ara report`

Render from saved JSON:

```
Options:
  --input, -i PATH      Input JSON from previous scan
  --format, -f FORMAT   Output: table, markdown
```

### `ara init-config`

Generate configuration file:

```
Options:
  --out, -o PATH        Output path (default: ./.agent_readiness_audit.toml)
```

## No-Gaming Principles

ARA is designed to encourage meaningful improvements, not checkbox compliance:

1. **Checks verify actual readiness**, not just file presence
2. **Evidence is required** for every pass/fail determination
3. **Scores cannot be inflated** through ceremonial configs
4. **Gates enforce real requirements**, not superficial ones
5. **Fix recommendations are actionable**, not generic

If a check passes, your repository genuinely supports that capability for agents.

## Backward Compatibility

ARA v2 maintains full backward compatibility with v1:

- **Same 0-16 score scale**
- **Same CLI interface**
- **Same output formats**
- **V1 levels map to v2**: Human-Only (L1), Assisted (L2), Semi-Autonomous (L3), Agent-Ready (L4-5)

The v2 maturity model and pillars are additions, not replacements.

## Development

```bash
# Clone
git clone https://github.com/bigdegenenergy/agent-readiness-audit.git
cd agent-readiness-audit

# Install dependencies
uv sync

# Run tests
uv run pytest

# Lint and format
uv run ruff check . && uv run ruff format .

# Type check
uv run mypy agent_readiness_audit

# Run the tool
uv run ara scan --repo .
```

## Specification

For the complete check specifications, scoring algorithm, and contribution guidelines, see [AGENTS.md](AGENTS.md).

## Contributing

Contributions welcome! Please:

1. Read [AGENTS.md](AGENTS.md) for check specifications
2. Run tests: `uv run pytest`
3. Run linting: `uv run ruff check . && uv run ruff format --check .`
4. Run type checking: `uv run mypy agent_readiness_audit`

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
