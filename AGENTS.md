# Agent Readiness Audit - v2 Technical Specification

This document is the **authoritative contract** for AI agents working with ARA. It defines the v2 maturity model, pillars, checks, and scoring semantics.

## Table of Contents

- [Mission](#mission)
- [Maturity Model](#maturity-model)
- [Pillars](#pillars)
- [Gate Checks](#gate-checks)
- [Check Specifications](#check-specifications)
- [Scoring Engine](#scoring-engine)
- [Backward Compatibility](#backward-compatibility)
- [Development Guide](#development-guide)

---

## Mission

**ARA certifies Technical Readiness for autonomous coding agents.**

The tool treats the target repository as a **deterministic API surface** for a probabilistic entity (the AI agent). It provides:

- Unambiguous, explainable, evidence-backed scoring
- Fix-first actions prioritized by leverage
- Safe-by-default operation (no untrusted code execution; no network calls unless explicitly enabled)

### Non-Negotiables

1. **No score inflation**: Checks must be meaningful; do not weaken to create ceremonial pass conditions
2. **No fake artifacts**: Improvements must be verifiable, not ceremonial
3. **No arbitrary code execution**: Default scans use static analysis only
4. **No network calls by default**: Network access requires explicit `--network` flag
5. **Evidence required**: Every pass/fail must record evidence in Markdown + JSON outputs
6. **Stable semantics**: Breaking scoring changes require version bump and migration notes

---

## Maturity Model

ARA v2 uses a 5-level maturity model measuring how well a repository supports autonomous agents:

| Level | Name             | Description                                                                                    | Score Range |
| ----- | ---------------- | ---------------------------------------------------------------------------------------------- | ----------- |
| 1     | **Functional**   | Works for humans; agents fail due to ambiguity and missing automation                          | 0-4         |
| 2     | **Documented**   | Setup/run instructions exist; agents can attempt tasks but ambiguity remains                   | 5-7         |
| 3     | **Standardized** | CI, linting, basic tests, and deterministic deps exist; minimum viable for production agents   | 8-11        |
| 4     | **Optimized**    | Fast feedback loops; split test targets; strong local guardrails; predictable artifacts        | 12-14       |
| 5     | **Autonomous**   | Telemetry + evals + golden datasets; agentic security posture; environment behaves like an API | 15-16       |

### Level Requirements

Each level has **gate checks** that must pass. A repository cannot achieve Level N without passing all gates for levels 1 through N.

---

## Pillars

v2 organizes checks into 15 pillars (expanded from 8 categories):

| Pillar                      | Description                                             | Level Required |
| --------------------------- | ------------------------------------------------------- | -------------- |
| **environment_determinism** | Reproducible dependencies and pinned versions           | 3              |
| **fast_guardrails**         | Sub-second local feedback (ruff, pre-commit)            | 4              |
| **type_contracts**          | Type hints and strictness config                        | 4              |
| **verification_trust**      | Test reliability (flake mitigation, coverage artifacts) | 4              |
| **verification_speed**      | Fast feedback via test splitting                        | 4              |
| **documentation_structure** | Structured docs (Diataxis)                              | 3              |
| **inline_documentation**    | Docstring coverage                                      | 4              |
| **contribution_contract**   | CONTRIBUTING, code of conduct                           | 3              |
| **agentic_security**        | Prompt red-teaming (promptfoo)                          | 5              |
| **secret_hygiene**          | No hardcoded secrets, env documentation                 | 3              |
| **telemetry_tracing**       | OpenTelemetry instrumentation                           | 5              |
| **structured_logging_cost** | JSON logging for cost/perf tracking                     | 5              |
| **eval_frameworks**         | DeepEval/Ragas integration                              | 5              |
| **golden_datasets**         | Regression test datasets                                | 5              |
| **distribution_dx**         | Package distribution readiness                          | 3              |

### Pillar-to-Category Mapping (v1 Compatibility)

For backward compatibility, pillars map to v1 categories:

| v1 Category             | v2 Pillars                                              |
| ----------------------- | ------------------------------------------------------- |
| discoverability         | documentation_structure, inline_documentation           |
| deterministic_setup     | environment_determinism                                 |
| build_and_run           | fast_guardrails, distribution_dx                        |
| test_feedback_loop      | verification_trust, verification_speed                  |
| static_guardrails       | type_contracts, fast_guardrails                         |
| observability           | telemetry_tracing, structured_logging_cost              |
| ci_enforcement          | fast_guardrails, verification_speed                     |
| security_and_governance | agentic_security, secret_hygiene, contribution_contract |

---

## Gate Checks

Gates are mandatory checks for each maturity level. Failing a gate caps the maximum achievable level.

### Level 3 Gates (Standardized)

| Check                              | Pillar                  | Intent                  |
| ---------------------------------- | ----------------------- | ----------------------- |
| `dependency_manifest_exists`       | environment_determinism | Deterministic deps      |
| `lockfile_exists`                  | environment_determinism | Pinned versions         |
| `ci_workflow_present`              | fast_guardrails         | CI validates changes    |
| `linter_config_present`            | fast_guardrails         | Lint reduces ambiguity  |
| `tests_directory_or_config_exists` | verification_trust      | Tests exist             |
| `readme_has_setup_section`         | documentation_structure | Setup documented        |
| `readme_has_test_instructions`     | documentation_structure | Test running documented |

### Level 4 Gates (Optimized)

| Check                       | Pillar             | Intent                        |
| --------------------------- | ------------------ | ----------------------------- |
| `precommit_present`         | fast_guardrails    | Local fast feedback           |
| `fast_linter_python`        | fast_guardrails    | Sub-second linting (ruff)     |
| `machine_readable_coverage` | verification_trust | Coverage artifacts for agents |
| `test_splitting`            | verification_speed | Unit vs integration split     |
| `python_type_hint_coverage` | type_contracts     | >= 70% typed                  |
| `mypy_strictness`           | type_contracts     | Strict type checking          |

### Level 5 Gates (Autonomous)

| Check                        | Pillar                  | Intent                    |
| ---------------------------- | ----------------------- | ------------------------- |
| `opentelemetry_present`      | telemetry_tracing       | Trace agent behavior      |
| `structured_logging_present` | structured_logging_cost | JSON logs for aggregation |
| `eval_framework_detect`      | eval_frameworks         | Agent behavior tests      |
| `golden_dataset_present`     | golden_datasets         | Regression baselines      |
| `promptfoo_present`          | agentic_security        | Prompt red-teaming        |

---

## Check Specifications

Each check is specified with: intent, detection logic, evidence format, and fix-first recommendations.

### Environment Determinism

#### `dependency_manifest_exists`

- **Pillar**: environment_determinism
- **Intent**: Ensure dependencies are declared, not implicit
- **Detection**:
    - PASS: pyproject.toml, package.json, Cargo.toml, go.mod, or Gemfile exists
    - FAIL: No dependency manifest found
- **Evidence**: Path to manifest file
- **Fix-First**: "Add pyproject.toml (Python), package.json (Node), or equivalent for your ecosystem"

#### `lockfile_exists`

- **Pillar**: environment_determinism
- **Intent**: Pin exact dependency versions for reproducibility
- **Detection**:
    - PASS: uv.lock, poetry.lock, package-lock.json, yarn.lock, Cargo.lock, go.sum, or Gemfile.lock exists
    - FAIL: No lockfile found
- **Evidence**: Path to lockfile
- **Fix-First**: "Generate lockfile: uv lock (Python), npm install (Node), cargo build (Rust)"

#### `runtime_version_declared`

- **Pillar**: environment_determinism
- **Intent**: Declare runtime version for consistent execution
- **Detection**:
    - PASS: .python-version, .nvmrc, .node-version, requires-python in pyproject.toml, or engines in package.json
    - PARTIAL: Version in CI but not locally
    - FAIL: No runtime version declaration
- **Evidence**: Path and version string
- **Fix-First**: "Add .python-version or requires-python in pyproject.toml"

### Fast Guardrails

#### `fast_linter_python`

- **Pillar**: fast_guardrails
- **Intent**: Enable sub-second feedback loops with ruff
- **Detection**:
    - PASS: ruff configured via pyproject.toml [tool.ruff], ruff.toml, or .ruff.toml
    - PARTIAL: flake8/pylint only (recommend migrating to ruff)
    - FAIL: No linter configuration
- **Evidence**: Config file path and key section names
- **Fix-First**: "Add [tool.ruff] to pyproject.toml with minimal strict config"

#### `precommit_present`

- **Pillar**: fast_guardrails
- **Intent**: Ensure local fast feedback before push
- **Detection**:
    - PASS: .pre-commit-config.yaml exists
    - PARTIAL: CI lint only (no local hooks)
    - FAIL: No pre-commit configuration
- **Evidence**: Path to config, hook names if present
- **Fix-First**: "Add .pre-commit-config.yaml with ruff + mypy hooks"

#### `linter_config_present`

- **Pillar**: fast_guardrails
- **Intent**: Linting reduces ambiguity for agents
- **Detection**:
    - PASS: Any linter config found (ruff.toml, .eslintrc, [tool.ruff], etc.)
    - FAIL: No linter configuration
- **Evidence**: Config file path
- **Fix-First**: "Add ruff configuration for Python or eslint for JavaScript"

#### `formatter_config_present`

- **Pillar**: fast_guardrails
- **Intent**: Consistent formatting reduces diff noise
- **Detection**:
    - PASS: Formatter config found (prettierrc, [tool.ruff.format], .editorconfig, etc.)
    - FAIL: No formatter configuration
- **Evidence**: Config file path
- **Fix-First**: "Add [tool.ruff.format] or .prettierrc"

### Type Contracts

#### `python_type_hint_coverage`

- **Pillar**: type_contracts
- **Intent**: Type hints are agent-readable documentation
- **Detection**:
    - Static AST scan of .py files (excluding tests/, migrations/, vendor/)
    - Compute: percentage of function defs with any type annotation on params or return
    - PASS: >= 70% for Level 4, >= 85% for Level 5
    - PARTIAL: 40-69% coverage
    - FAIL: < 40% coverage
- **Evidence**: Total functions, typed functions, percentage, top 5 files needing types
- **Safety**: No imports/exec; parse with ast module only
- **Fix-First**: "Add type hints to top 10 most-called modules first"

#### `mypy_strictness`

- **Pillar**: type_contracts
- **Intent**: Explicit strictness reduces guessing
- **Detection**:
    - PASS: mypy.ini or pyproject.toml contains `strict = true` OR `disallow_untyped_defs = true`
    - PARTIAL: mypy configured without strict mode
    - FAIL: No mypy configuration
- **Evidence**: Config file path and strictness settings
- **Fix-First**: "Add `strict = true` to [tool.mypy] in pyproject.toml"

#### `typecheck_config_present`

- **Pillar**: type_contracts
- **Intent**: Type checking configured for the project
- **Detection**:
    - PASS: mypy.ini, pyproject.toml [tool.mypy], tsconfig.json, or pyrightconfig.json exists
    - FAIL: No type checking configuration
- **Evidence**: Config file path
- **Fix-First**: "Add [tool.mypy] configuration to pyproject.toml"

### Verification Trust

#### `tests_directory_or_config_exists`

- **Pillar**: verification_trust
- **Intent**: Tests must exist as a verification mechanism
- **Detection**:
    - PASS: tests/ directory or pytest.ini/conftest.py exists
    - FAIL: No test infrastructure found
- **Evidence**: Path to tests directory or config
- **Fix-First**: "Create tests/ directory with initial test file"

#### `test_command_detectable`

- **Pillar**: verification_trust
- **Intent**: Test command must be discoverable
- **Detection**:
    - PASS: `pytest` in pyproject.toml scripts, `make test` in Makefile, or `npm test` in package.json
    - FAIL: No test command found
- **Evidence**: Command and source file
- **Fix-First**: "Add `make test` target or pytest configuration"

#### `flake_awareness_pytest`

- **Pillar**: verification_trust
- **Intent**: Detect awareness/mitigation of flaky tests
- **Detection**:
    - PASS: pytest-rerunfailures or pytest-flaky in dependencies
    - PARTIAL: Test markers exist but no rerun tooling
    - FAIL: No flake mitigation detected
- **Evidence**: Dependency name or marker configuration
- **Fix-First**: "Add pytest-rerunfailures to handle transient failures"

#### `machine_readable_coverage`

- **Pillar**: verification_trust
- **Intent**: Coverage artifacts must be machine-parsable
- **Detection**:
    - PASS: Config generates coverage.xml or coverage.json
    - PARTIAL: HTML coverage only
    - FAIL: No coverage configuration
- **Evidence**: Config keys and output filename patterns
- **Fix-First**: "Enable coverage.xml in pytest-cov or coverage.py config"

### Verification Speed

#### `test_splitting`

- **Pillar**: verification_speed
- **Intent**: Fast feedback via unit vs integration split
- **Detection**:
    - PASS: Makefile/tox/nox defines `test-unit` and `test-integration` OR pytest markers documented
    - PARTIAL: Tests exist but no split
    - FAIL: No test organization
- **Evidence**: Target names or marker configuration
- **Fix-First**: "Add `make test-unit` and `make test-integration` targets"

#### `test_command_has_timeout`

- **Pillar**: verification_speed
- **Intent**: Prevent hung tests from blocking agents
- **Detection**:
    - PASS: pytest-timeout configured or jest testTimeout set
    - FAIL: No timeout configuration
- **Evidence**: Timeout value and config location
- **Fix-First**: "Add pytest-timeout with reasonable default (60s)"

### Documentation Structure

#### `readme_exists`

- **Pillar**: documentation_structure
- **Intent**: Entry point for understanding the repository
- **Detection**:
    - PASS: README.md, README, or readme.md exists
    - FAIL: No README found
- **Evidence**: Path to README
- **Fix-First**: "Add README.md with project overview"

#### `readme_has_setup_section`

- **Pillar**: documentation_structure
- **Intent**: Setup instructions must be discoverable
- **Detection**:
    - PASS: README contains "installation", "setup", "getting started", or "quickstart" section
    - FAIL: No setup section found
- **Evidence**: Section heading found
- **Fix-First**: "Add ## Installation or ## Getting Started section to README"

#### `readme_has_test_instructions`

- **Pillar**: documentation_structure
- **Intent**: Test running instructions must be documented
- **Detection**:
    - PASS: README contains "test", "testing", or "run tests" section/instructions
    - FAIL: No test instructions found
- **Evidence**: Section or command found
- **Fix-First**: "Add test running instructions to README"

#### `diataxis_structure`

- **Pillar**: documentation_structure
- **Intent**: Structured docs reduce agent context confusion
- **Detection**:
    - PASS: docs/ contains 3+ of: tutorials/, how-to/, reference/, explanation/ (or equivalent)
    - PARTIAL: docs/ exists but unstructured
    - FAIL: No docs/ directory
- **Evidence**: Discovered directory structure
- **Fix-First**: "Create docs/ with Diataxis skeleton: tutorials/, how-to/, reference/, explanation/"

### Inline Documentation

#### `docstring_coverage_python`

- **Pillar**: inline_documentation
- **Intent**: Docstrings provide local context for agents
- **Detection**:
    - PASS: interrogate config present OR AST scan finds >= 60% docstring coverage
    - PARTIAL: 30-59% coverage
    - FAIL: < 30% coverage
- **Evidence**: Measured percentage and top missing files
- **Safety**: AST scan only, no imports/exec
- **Fix-First**: "Add docstrings to public APIs first; adopt Google or NumPy style"

### Contribution Contract

#### `contributing_exists`

- **Pillar**: contribution_contract
- **Intent**: Contribution guidelines for agents and humans
- **Detection**:
    - PASS: CONTRIBUTING.md exists
    - FAIL: No contribution guidelines
- **Evidence**: Path to file
- **Fix-First**: "Add CONTRIBUTING.md with development workflow"

#### `security_policy_present`

- **Pillar**: contribution_contract
- **Intent**: Security reporting channel documented
- **Detection**:
    - PASS: SECURITY.md or .github/SECURITY.md exists
    - PARTIAL: Security section in README
    - FAIL: No security policy
- **Evidence**: Path to policy
- **Fix-First**: "Add SECURITY.md with vulnerability reporting process"

### Secret Hygiene

#### `gitignore_present`

- **Pillar**: secret_hygiene
- **Intent**: Prevent accidental secret commits
- **Detection**:
    - PASS: .gitignore exists and contains common patterns
    - FAIL: No .gitignore
- **Evidence**: Path to .gitignore
- **Fix-First**: "Add .gitignore with common patterns for your ecosystem"

#### `env_example_or_secrets_docs_present`

- **Pillar**: secret_hygiene
- **Intent**: Document required environment variables
- **Detection**:
    - PASS: .env.example, .env.sample, or docs/secrets.md exists
    - FAIL: No env documentation
- **Evidence**: Path to documentation
- **Fix-First**: "Add .env.example with required environment variables (no actual secrets)"

#### `prompt_secret_scanning`

- **Pillar**: secret_hygiene
- **Intent**: Prevent secrets in prompt templates
- **Detection**:
    - Scan prompt/, templates/, prompts/ for high-entropy strings and key patterns (API_KEY, SECRET, etc.)
    - PASS: No suspicious patterns OR gitleaks/trufflehog config exists
    - FAIL: Likely secrets found (redacted evidence)
- **Evidence**: Redacted pattern matches, file paths (never full secrets)
- **Safety**: Never print full secrets; hash and redact
- **Fix-First**: "Move secrets to environment variables; add .env.example"

### Agentic Security

#### `promptfoo_present`

- **Pillar**: agentic_security
- **Intent**: Deterministic prompt/agent red-teaming
- **Detection**:
    - PASS: promptfooconfig.yaml or promptfoo.yaml exists
    - PARTIAL: Security docs mention red-teaming but no config
    - FAIL: No promptfoo configuration
- **Evidence**: Config file path
- **Fix-First**: "Add promptfooconfig.yaml with baseline eval suite"

### Telemetry & Observability

#### `opentelemetry_present`

- **Pillar**: telemetry_tracing
- **Intent**: Trace agent behavior; logs alone are insufficient
- **Detection**:
    - PASS: opentelemetry-sdk or equivalent in dependencies
    - PARTIAL: Basic logging only
    - FAIL: No telemetry instrumentation
- **Evidence**: Matched package names
- **Fix-First**: "Add opentelemetry-sdk and configure basic tracing"

#### `structured_logging_present`

- **Pillar**: structured_logging_cost
- **Intent**: Enable cost/perf/behavior aggregation via JSON logs
- **Detection**:
    - PASS: structlog (Python) or JSON logging config detected
    - PARTIAL: Logging exists but unstructured
    - FAIL: No structured logging
- **Evidence**: Package name or config keys
- **Fix-First**: "Adopt structlog with JSON renderer; document standard fields"

#### `logging_present`

- **Pillar**: telemetry_tracing
- **Intent**: Basic logging infrastructure exists
- **Detection**:
    - PASS: `import logging`, structlog, or winston detected in source
    - FAIL: No logging imports found
- **Evidence**: Import statements found
- **Fix-First**: "Add logging infrastructure with structured output"

### Eval Frameworks

#### `eval_framework_detect`

- **Pillar**: eval_frameworks
- **Intent**: Evals are unit tests for agentic behavior
- **Detection**:
    - PASS: deepeval or ragas in dependencies
    - PARTIAL: evals/ directory exists without framework
    - FAIL: No eval framework detected
- **Evidence**: Package name and config paths
- **Fix-First**: "Add DeepEval or Ragas with minimal test suite"

#### `golden_dataset_present`

- **Pillar**: golden_datasets
- **Intent**: Golden datasets enable regression testing
- **Detection**:
    - PASS: tests/data/golden\*.json, evals/test_cases.json, or similar exists
    - PARTIAL: Example data exists but not labeled as golden
    - FAIL: No golden dataset found
- **Evidence**: Path and record count (if safely parsable)
- **Fix-First**: "Create golden dataset with 10-25 test cases and expected outcomes"

### Distribution DX

#### `make_or_task_runner_exists`

- **Pillar**: distribution_dx
- **Intent**: Standard entry point for common tasks
- **Detection**:
    - PASS: Makefile, Taskfile.yml, justfile, or tox.ini exists
    - FAIL: No task runner found
- **Evidence**: Path to task runner
- **Fix-First**: "Add Makefile with standard targets: install, lint, test, build"

#### `package_scripts_or_equivalent`

- **Pillar**: distribution_dx
- **Intent**: Package-manager-native scripts available
- **Detection**:
    - PASS: npm scripts in package.json or [project.scripts] in pyproject.toml
    - FAIL: No package scripts
- **Evidence**: Script names defined
- **Fix-First**: "Add scripts to package.json or [project.scripts] in pyproject.toml"

#### `ci_workflow_present`

- **Pillar**: distribution_dx
- **Intent**: CI validates changes automatically
- **Detection**:
    - PASS: .github/workflows/, .gitlab-ci.yml, or similar exists
    - FAIL: No CI configuration
- **Evidence**: Path to CI config
- **Fix-First**: "Add .github/workflows/ci.yml with lint, test, and type check steps"

#### `ci_runs_tests_or_lint`

- **Pillar**: distribution_dx
- **Intent**: CI must run quality checks
- **Detection**:
    - PASS: CI config contains pytest, npm test, ruff, eslint, or similar
    - FAIL: CI exists but no tests/lint
- **Evidence**: Commands found in CI config
- **Fix-First**: "Add test and lint steps to CI workflow"

---

## Scoring Engine

### Score Calculation

1. **Check Execution**: Each check returns `{status, evidence, suggestion}`
2. **Pillar Aggregation**: Checks grouped by pillar; pillar score = (passed / total) \* max_points
3. **Category Score** (v1 compat): Pillars map to v1 categories for backward compatibility
4. **Total Score**: Sum of category scores (0-16 scale preserved)
5. **Maturity Level**: Determined by score AND gate checks

### Gate Enforcement

```
Level = min(score_based_level, max_level_with_all_gates_passed)
```

Example: Score of 14 (Level 4 by score) but missing `precommit_present` gate caps at Level 3.

### Evidence Recording

Every check must record:

- **Passed**: Evidence of what was found (file paths, config keys)
- **Failed**: Evidence of what was searched for and not found
- **Suggestions**: Actionable fix-first recommendations

---

## Backward Compatibility

### v1 Score Preservation

- Total score remains 0-16
- Categories remain the same 8 names
- v2 pillars map to v1 categories
- New checks contribute to existing categories

### Migration Notes

When running v2:

1. Maturity level (1-5) is displayed alongside score
2. Gate failures are called out explicitly
3. New pillar breakdown available in JSON output
4. Legacy `--model v1` flag available if needed

---

## Development Guide

### Quick Start

```bash
uv sync                    # Install dependencies
uv run ara scan --repo .   # Scan a repository
uv run pytest              # Run tests
make check                 # Run all quality checks
```

### Adding a New Check

1. Create function in appropriate module under `agent_readiness_audit/checks/`
2. Use `@check` decorator with pillar (maps to category for v1 compat)
3. Return `CheckResult(passed, evidence, suggestion)`
4. Add tests in `tests/test_checks.py`
5. Document in this file under Check Specifications

```python
@check(
    name="my_check",
    category="fast_guardrails",  # v1 category
    description="Check description",
    pillar="fast_guardrails",    # v2 pillar
    gate_level=4,                # Optional: makes this a gate for Level 4
)
def check_my_thing(repo_path: Path) -> CheckResult:
    if (repo_path / "TARGET").exists():
        return CheckResult(
            passed=True,
            evidence="Found TARGET"
        )
    return CheckResult(
        passed=False,
        evidence="TARGET not found",
        suggestion="Add TARGET to improve agent readiness."
    )
```

### Testing

```bash
uv run pytest tests/test_checks.py -v  # Test checks
uv run pytest --cov                     # Coverage report
```

### Before Committing

```bash
make check  # Runs: lint, format, typecheck, test
```

---

## Report Formats

### Markdown Report Must Include

- Maturity level (1-5) with explanation
- Numeric score (0-16 for v1 compatibility)
- Pillar table with pass/partial/fail counts
- Gate failures called out explicitly
- Fix-first plan grouped by highest leverage
- Evidence section (redacted, path-based)

### JSON Report Must Include

```json
{
  "maturity_level": 4,
  "maturity_name": "Optimized",
  "score_total": 13.5,
  "max_score": 16,
  "pillars": {
    "fast_guardrails": {"score": 2.0, "max": 2.0, "checks": [...]}
  },
  "gates": {
    "level_3": {"passed": true, "failed_checks": []},
    "level_4": {"passed": false, "failed_checks": ["precommit_present"]}
  },
  "checks": [...],
  "config_used": "default",
  "ignore_policy": []
}
```

---

## Links

- [README](README.md) - Project overview
- [CLAUDE.md](CLAUDE.md) - AI development instructions
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
