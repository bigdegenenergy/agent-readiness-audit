# Agent Readiness Audit

A CLI tool that audits repositories for agent-readiness and outputs human + machine-readable reports.

## Project Overview

**Purpose:** Help developers understand how well their repositories support autonomous AI agents by scoring them across 8 key dimensions and providing actionable recommendations.

**Architecture:** Python CLI built with Typer, using a plugin-based check system where each category has its own module.

## Tech Stack

- **Language:** Python 3.11+
- **CLI Framework:** Typer + Rich (for terminal output)
- **Data Validation:** Pydantic
- **Build Tool:** Hatch
- **Package Manager:** uv
- **Linting:** Ruff
- **Type Checking:** mypy
- **Testing:** pytest

## Project Structure

```
agent_readiness_audit/
├── cli.py              # Typer CLI entry point
├── scanner.py          # Repository scanning orchestration
├── config.py           # TOML configuration loading
├── models.py           # Pydantic models for results
├── checks/             # Check implementations by category
│   ├── base.py         # @check decorator and CheckResult
│   ├── discoverability.py
│   ├── deterministic_setup.py
│   ├── build_and_run.py
│   ├── test_feedback_loop.py
│   ├── static_guardrails.py
│   ├── observability.py
│   ├── ci_enforcement.py
│   └── security_governance.py
├── reporting/          # Output format renderers
│   ├── table_report.py
│   ├── json_report.py
│   └── markdown_report.py
└── utils/              # Shared utilities
```

## Development Commands

Use the Makefile for all standard operations:

```bash
make install    # Install dependencies with uv sync
make lint       # Run ruff linter
make format     # Run ruff formatter
make typecheck  # Run mypy
make test       # Run pytest
make test-cov   # Run pytest with coverage
make check      # Run all quality checks (lint, format, typecheck, test)
make build      # Build the package
make scan       # Run ara self-audit (dogfooding)
```

## Running the Tool

```bash
# Scan this repository
uv run ara scan --repo .

# Scan with JSON output
uv run ara scan --repo . --format json

# Scan multiple repositories
uv run ara scan --root ~/code --depth 2 --out ./reports

# Strict mode (exit non-zero if below threshold)
uv run ara scan --repo . --strict --min-score 10
```

## Adding New Checks

1. Create a function in the appropriate category module (e.g., `checks/discoverability.py`)
2. Decorate with `@check(name, category, description)`
3. Return a `CheckResult` with passed, evidence, and optional suggestion

```python
@check(
    name="my_check",
    category="discoverability",
    description="Check for something"
)
def check_my_thing(repo_path: Path) -> CheckResult:
    if (repo_path / "SOMETHING").exists():
        return CheckResult(passed=True, evidence="Found SOMETHING")
    return CheckResult(
        passed=False,
        evidence="SOMETHING not found",
        suggestion="Add SOMETHING to improve agent readiness."
    )
```

## Scoring Model

| Category              | Description                       | Max Points |
| --------------------- | --------------------------------- | ---------- |
| Discoverability       | README presence and clarity       | 2          |
| Deterministic Setup   | Reproducible dependencies         | 2          |
| Build and Run         | Standard build/test/lint commands | 2          |
| Test Feedback Loop    | Test infrastructure               | 2          |
| Static Guardrails     | Linting, formatting, types        | 2          |
| Observability         | Logging and error handling        | 2          |
| CI Enforcement        | CI configuration                  | 2          |
| Security & Governance | Security policies                 | 2          |

**Total: 16 points**

## Configuration

The tool reads `.agent_readiness_audit.toml` for customization:

- Enable/disable categories or individual checks
- Adjust check weights
- Set minimum passing score for strict mode
- Customize file detection patterns

## Quality Standards

Before committing:

1. **All checks must pass:** `make check`
2. **Type annotations required:** All functions must have type hints
3. **Tests required:** New checks need corresponding tests in `tests/`
4. **No `any` types:** Use proper typing throughout

## AI Dev Toolkit Configuration

This repository uses [AI Dev Toolkit](https://github.com/bigdegenenergy/ai-dev-toolkit) for Claude Code configuration. The `.claude/` directory contains:

- **17 Specialized Agents** for development tasks
- **11 Auto-Discovered Skills** for domain expertise
- **22 Slash Commands** for workflows
- **8 Automated Hooks** for quality gates

### Key Commands for This Project

```bash
/plan            # Plan before implementing
/qa              # Run tests and fix until green
/simplify        # Refactor for readability
/ship            # Commit, push, create PR

@python-pro      # Python expertise
@test-automator  # Create test suites
@code-reviewer   # Critical code review
```

### Workflow

1. **Plan:** Use `/plan` for complex features
2. **Implement:** Write code with type hints
3. **Test:** Run `make check` to validate
4. **Simplify:** Use `/simplify` to clean up
5. **Ship:** Use `/ship` to commit and PR

## Things Claude Should Do

- Run `make check` before committing
- Add type hints to all functions
- Write tests for new checks
- Follow existing patterns in `checks/` modules
- Use Pydantic models for structured data
- Keep check functions focused and single-purpose

## Things Claude Should NOT Do

- Skip type checking (`make typecheck`)
- Add checks without tests
- Use `any` type
- Commit with linting errors
- Force push without permission
