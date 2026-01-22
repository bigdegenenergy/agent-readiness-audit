# Agent Readiness Audit - Specification

> **Authoritative Contract for v2 Agent-Native Readiness Certification**

This file is the definitive specification for ARA's check system. Every check, pillar, maturity level, and scoring rule is documented here. AI agents and human contributors MUST reference this file when adding or modifying checks.

## Table of Contents

1. [Mission](#mission)
2. [Quick Reference](#quick-reference)
3. [Maturity Model (v2)](#maturity-model-v2)
4. [Pillars](#pillars)
5. [Level Gates](#level-gates)
6. [Check Specifications](#check-specifications)
7. [Scoring Algorithm](#scoring-algorithm)
8. [Report Format](#report-format)
9. [Configuration](#configuration)
10. [Safety Principles](#safety-principles)
11. [Development Guide](#development-guide)

---

## Mission

**ARA certifies Technical Readiness for autonomous coding agents.**

The target repository is treated as a **deterministic API surface** for a **probabilistic entity** (the AI agent). ARA provides:

- **Unambiguous scoring**: Every check has explicit pass/fail criteria
- **Evidence-backed results**: Every result includes proof of what was found
- **Fix-first actions**: Every failure includes actionable remediation steps
- **Safe-by-default**: No untrusted code execution; no network calls unless explicitly enabled

### Non-Negotiables

1. **Do not weaken checks** to inflate scores or create ceremonial pass conditions
2. **Do not add fake docs/tests/configs**; improvements must be meaningful and verifiable
3. **Do not execute arbitrary code** in scanned repos by default
4. **No network calls** during scans unless explicitly gated with a flag
5. **Every check must be documented** in this file with intent, detection, and fix-first
6. **Scoring semantics must be stable**; breaking changes require version bump + migration notes
7. **Evidence must be recorded** for every pass/fail and appear in both Markdown and JSON outputs

---

## Quick Reference

```bash
# Install
uv tool install agent-readiness-audit

# Scan current directory
ara scan --repo .

# Scan with v2 maturity output
ara scan --repo . --format markdown

# Generate config
ara init-config

# Run tests
uv run pytest

# Lint and type check
uv run ruff check . && uv run mypy agent_readiness_audit
```

---

## Maturity Model (v2)

ARA v2 introduces a 5-level maturity model that maps check results to meaningful readiness tiers.

| Level | Name             | Description                                                                                    | Score Range |
| ----- | ---------------- | ---------------------------------------------------------------------------------------------- | ----------- |
| **1** | **Functional**   | Works for humans; agents fail due to ambiguity and missing automation                          | 0-5         |
| **2** | **Documented**   | Setup/run instructions exist; agents can attempt tasks but ambiguity remains                   | 6-9         |
| **3** | **Standardized** | CI, linting, basic tests, and deterministic deps exist; minimum viable for production agents   | 10-13       |
| **4** | **Optimized**    | Fast feedback loops; split test targets; strong local guardrails; predictable artifacts        | 14-15       |
| **5** | **Autonomous**   | Telemetry + evals + golden datasets; agentic security posture; environment behaves like an API | 16          |

### V1 Compatibility

The v2 model maintains backward compatibility with the v1 0-16 score:

| v1 Level            | v1 Score | v2 Level  | v2 Name              |
| ------------------- | -------- | --------- | -------------------- |
| Human-Only Repo     | 0-5      | Level 1   | Functional           |
| Assisted Agent      | 6-9      | Level 2   | Documented           |
| Semi-Autonomous     | 10-13    | Level 3   | Standardized         |
| Agent-Ready Factory | 14-16    | Level 4-5 | Optimized/Autonomous |

---

## Pillars

ARA v2 organizes checks into **15 pillars** grouped by domain. Each pillar contributes to one or more maturity levels.

### Environment & Determinism

| Pillar                      | ID                        | Description                                                 | Levels |
| --------------------------- | ------------------------- | ----------------------------------------------------------- | ------ |
| **Environment Determinism** | `environment_determinism` | Reproducible dependency management and runtime pinning      | 2-5    |
| **Fast Guardrails**         | `fast_guardrails`         | Sub-second local feedback (linters, formatters, pre-commit) | 3-5    |

### Type Safety & Contracts

| Pillar             | ID               | Description                                         | Levels |
| ------------------ | ---------------- | --------------------------------------------------- | ------ |
| **Type Contracts** | `type_contracts` | Static typing coverage and strictness configuration | 4-5    |

### Verification

| Pillar                 | ID                   | Description                                               | Levels |
| ---------------------- | -------------------- | --------------------------------------------------------- | ------ |
| **Verification Trust** | `verification_trust` | Test reliability, flakiness awareness, coverage artifacts | 3-5    |
| **Verification Speed** | `verification_speed` | Test splitting (unit vs integration), parallel execution  | 4-5    |

### Documentation

| Pillar                      | ID                        | Description                                           | Levels |
| --------------------------- | ------------------------- | ----------------------------------------------------- | ------ |
| **Documentation Structure** | `documentation_structure` | Diátaxis-aligned doc organization for agent retrieval | 3-5    |
| **Inline Documentation**    | `inline_documentation`    | Docstring coverage for local context                  | 4-5    |
| **Contribution Contract**   | `contribution_contract`   | CONTRIBUTING.md, PR templates, issue templates        | 3-5    |

### Security

| Pillar               | ID                 | Description                                                 | Levels |
| -------------------- | ------------------ | ----------------------------------------------------------- | ------ |
| **Agentic Security** | `agentic_security` | Prompt red-teaming (promptfoo), agent guardrails            | 5      |
| **Secret Hygiene**   | `secret_hygiene`   | No hardcoded secrets, proper .env patterns, secret scanning | 3-5    |

### Observability

| Pillar                  | ID                        | Description                                              | Levels |
| ----------------------- | ------------------------- | -------------------------------------------------------- | ------ |
| **Telemetry & Tracing** | `telemetry_tracing`       | OpenTelemetry instrumentation for agent behavior tracing | 5      |
| **Structured Logging**  | `structured_logging_cost` | JSON logs with standard fields (task_id, cost, tokens)   | 4-5    |

### Evaluation

| Pillar              | ID                | Description                                                 | Levels |
| ------------------- | ----------------- | ----------------------------------------------------------- | ------ |
| **Eval Frameworks** | `eval_frameworks` | DeepEval, Ragas, or equivalent for agentic behavior testing | 5      |
| **Golden Datasets** | `golden_datasets` | Test cases with expected outcomes for regression testing    | 5      |

### Distribution

| Pillar              | ID                | Description                                            | Levels |
| ------------------- | ----------------- | ------------------------------------------------------ | ------ |
| **Distribution DX** | `distribution_dx` | README quality, setup instructions, test documentation | 2-5    |

---

## Level Gates

A repository cannot achieve Level N unless it passes **all gate checks** for that level.

### Level 2 Gates (Documented)

| Gate                | Check                        | Criteria                             |
| ------------------- | ---------------------------- | ------------------------------------ |
| README exists       | `readme_exists`              | README.md or equivalent present      |
| Setup instructions  | `readme_has_setup_section`   | Installation/setup section in README |
| Dependency manifest | `dependency_manifest_exists` | pyproject.toml, package.json, etc.   |

### Level 3 Gates (Standardized)

| Gate              | Check                              | Criteria                         |
| ----------------- | ---------------------------------- | -------------------------------- |
| CI present        | `ci_workflow_present`              | GitHub Actions, GitLab CI, etc.  |
| Linter configured | `linter_config_present`            | Ruff, ESLint, or equivalent      |
| Tests exist       | `tests_directory_or_config_exists` | tests/ directory or test config  |
| Lockfile exists   | `lockfile_exists`                  | uv.lock, package-lock.json, etc. |
| Test instructions | `readme_has_test_instructions`     | How to run tests in README       |

### Level 4 Gates (Optimized)

| Gate                      | Check                       | Criteria                                  |
| ------------------------- | --------------------------- | ----------------------------------------- |
| Fast linter               | `fast_linter_python`        | Ruff (Python) or Biome (JS/TS) configured |
| Pre-commit hooks          | `precommit_present`         | .pre-commit-config.yaml exists            |
| Type hints                | `python_type_hint_coverage` | ≥70% function coverage                    |
| Test splitting            | `test_splitting`            | Unit/integration separation               |
| Machine-readable coverage | `machine_readable_coverage` | coverage.xml or coverage.json output      |

### Level 5 Gates (Autonomous)

| Gate               | Check                        | Criteria                           |
| ------------------ | ---------------------------- | ---------------------------------- |
| OpenTelemetry      | `opentelemetry_present`      | OTel SDK in dependencies           |
| Structured logging | `structured_logging_present` | structlog or JSON logging          |
| Eval framework     | `eval_framework_detect`      | DeepEval, Ragas, or equivalent     |
| Golden dataset     | `golden_dataset_present`     | Test cases with expected outcomes  |
| Prompt testing     | `promptfoo_present`          | promptfoo or equivalent configured |
| High type coverage | `python_type_hint_coverage`  | ≥85% function coverage             |

---

## Check Specifications

### Discoverability Checks

#### `readme_exists`

| Field         | Value                                                       |
| ------------- | ----------------------------------------------------------- |
| **Pillar**    | `distribution_dx`                                           |
| **Intent**    | Ensure basic discoverability for agents entering the repo   |
| **Detection** | Pass if README.md, README, or readme.md exists in repo root |
| **Evidence**  | Path to found README file                                   |
| **Fix-First** | Create README.md with project description                   |
| **Gate For**  | Level 2                                                     |

#### `readme_has_setup_section`

| Field         | Value                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------- |
| **Pillar**    | `distribution_dx`                                                                                 |
| **Intent**    | Agents need explicit setup instructions to bootstrap the environment                              |
| **Detection** | Pass if README contains "install", "setup", "getting started", or "quickstart" (case-insensitive) |
| **Evidence**  | Matched section header or keyword                                                                 |
| **Fix-First** | Add "## Installation" or "## Setup" section with step-by-step instructions                        |
| **Gate For**  | Level 2                                                                                           |

#### `readme_has_test_instructions`

| Field         | Value                                                                               |
| ------------- | ----------------------------------------------------------------------------------- |
| **Pillar**    | `distribution_dx`                                                                   |
| **Intent**    | Agents must know how to verify changes via tests                                    |
| **Detection** | Pass if README contains "test", "testing", "run tests", or "pytest/jest/cargo test" |
| **Evidence**  | Matched test-related keyword                                                        |
| **Fix-First** | Add "## Testing" section with exact commands                                        |
| **Gate For**  | Level 3                                                                             |

---

### Deterministic Setup Checks

#### `dependency_manifest_exists`

| Field         | Value                                                                       |
| ------------- | --------------------------------------------------------------------------- |
| **Pillar**    | `environment_determinism`                                                   |
| **Intent**    | Ensure dependencies are declared, not implicit                              |
| **Detection** | Pass if pyproject.toml, package.json, Cargo.toml, go.mod, or Gemfile exists |
| **Evidence**  | Path to manifest file                                                       |
| **Fix-First** | Create pyproject.toml (Python), package.json (JS), or equivalent            |
| **Gate For**  | Level 2                                                                     |

#### `lockfile_exists`

| Field         | Value                                                                                                                  |
| ------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **Pillar**    | `environment_determinism`                                                                                              |
| **Intent**    | Ensure reproducible installs via locked versions                                                                       |
| **Detection** | Pass if uv.lock, poetry.lock, package-lock.json, yarn.lock, pnpm-lock.yaml, Cargo.lock, go.sum, or Gemfile.lock exists |
| **Evidence**  | Path to lockfile                                                                                                       |
| **Fix-First** | Run `uv lock` (Python), `npm install` (JS), or equivalent to generate lockfile                                         |
| **Gate For**  | Level 3                                                                                                                |

#### `runtime_version_declared`

| Field         | Value                                                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Pillar**    | `environment_determinism`                                                                                                 |
| **Intent**    | Pin runtime version for reproducibility                                                                                   |
| **Detection** | Pass if .python-version, .nvmrc, .node-version, .tool-versions, rust-toolchain.toml, or requires-python in pyproject.toml |
| **Evidence**  | Path to version file and version value                                                                                    |
| **Fix-First** | Create .python-version with e.g. "3.11"                                                                                   |

---

### Build and Run Checks

#### `make_or_task_runner_exists`

| Field         | Value                                                                   |
| ------------- | ----------------------------------------------------------------------- |
| **Pillar**    | `fast_guardrails`                                                       |
| **Intent**    | Provide standard entry points for common tasks                          |
| **Detection** | Pass if Makefile, Taskfile.yml, justfile, tox.ini, or noxfile.py exists |
| **Evidence**  | Path to task runner config                                              |
| **Fix-First** | Create Makefile with test, lint, format targets                         |

#### `package_scripts_or_equivalent`

| Field         | Value                                                                                                                      |
| ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Pillar**    | `fast_guardrails`                                                                                                          |
| **Intent**    | Standard scripts for project tasks                                                                                         |
| **Detection** | Pass if package.json has scripts, pyproject.toml has [tool.poetry.scripts] or [project.scripts], or Cargo.toml has [[bin]] |
| **Evidence**  | List of defined scripts/commands                                                                                           |
| **Fix-First** | Add scripts to package.json or pyproject.toml                                                                              |

#### `documented_commands_present`

| Field         | Value                                                                                                             |
| ------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Pillar**    | `distribution_dx`                                                                                                 |
| **Intent**    | Commands must be documented, not just configured                                                                  |
| **Detection** | Pass if README contains commands like `make`, `npm run`, `pytest`, `cargo test`, or Makefile has standard targets |
| **Evidence**  | Matched commands in README                                                                                        |
| **Fix-First** | Add command reference table to README                                                                             |

---

### Test Feedback Loop Checks

#### `tests_directory_or_config_exists`

| Field         | Value                                                                                                                 |
| ------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Pillar**    | `verification_trust`                                                                                                  |
| **Intent**    | Tests must be present and discoverable                                                                                |
| **Detection** | Pass if tests/, test/, **tests**/ directory exists OR pytest.ini, pyproject.toml [tool.pytest], jest.config.\* exists |
| **Evidence**  | Path to test directory or config                                                                                      |
| **Fix-First** | Create tests/ directory with at least one test file                                                                   |
| **Gate For**  | Level 3                                                                                                               |

#### `test_command_detectable`

| Field         | Value                                                                                      |
| ------------- | ------------------------------------------------------------------------------------------ |
| **Pillar**    | `verification_trust`                                                                       |
| **Intent**    | Test command must be obvious                                                               |
| **Detection** | Pass if "test" script in package.json, pytest/pytest-cov in deps, Makefile has test target |
| **Evidence**  | Detected test command                                                                      |
| **Fix-First** | Add `make test` or `npm test` script                                                       |

#### `test_command_has_timeout`

| Field         | Value                                                                                |
| ------------- | ------------------------------------------------------------------------------------ |
| **Pillar**    | `verification_speed`                                                                 |
| **Intent**    | Prevent tests from hanging indefinitely                                              |
| **Detection** | Pass if pytest-timeout in deps, testTimeout in jest config, or timeout in pytest.ini |
| **Evidence**  | Timeout configuration found                                                          |
| **Fix-First** | Add pytest-timeout with 30s default                                                  |

---

### Static Guardrails Checks

#### `linter_config_present`

| Field         | Value                                                                                         |
| ------------- | --------------------------------------------------------------------------------------------- |
| **Pillar**    | `fast_guardrails`                                                                             |
| **Intent**    | Linters catch errors before runtime                                                           |
| **Detection** | Pass if ruff.toml, .ruff.toml, [tool.ruff] in pyproject.toml, .eslintrc.\*, biome.json exists |
| **Evidence**  | Path to linter config                                                                         |
| **Fix-First** | Add ruff to pyproject.toml with sensible defaults                                             |
| **Gate For**  | Level 3                                                                                       |

#### `formatter_config_present`

| Field         | Value                                                                        |
| ------------- | ---------------------------------------------------------------------------- |
| **Pillar**    | `fast_guardrails`                                                            |
| **Intent**    | Consistent formatting reduces diff noise                                     |
| **Detection** | Pass if [tool.ruff.format], .prettierrc, biome.json, or .editorconfig exists |
| **Evidence**  | Path to formatter config                                                     |
| **Fix-First** | Enable ruff format in pyproject.toml                                         |

#### `typecheck_config_present`

| Field         | Value                                                                                     |
| ------------- | ----------------------------------------------------------------------------------------- |
| **Pillar**    | `type_contracts`                                                                          |
| **Intent**    | Type checking catches errors statically                                                   |
| **Detection** | Pass if mypy.ini, [tool.mypy] in pyproject.toml, tsconfig.json, pyrightconfig.json exists |
| **Evidence**  | Path to type config                                                                       |
| **Fix-First** | Add mypy to pyproject.toml with strict=true                                               |

---

### Observability Checks

#### `logging_present`

| Field         | Value                                                                                                          |
| ------------- | -------------------------------------------------------------------------------------------------------------- |
| **Pillar**    | `structured_logging_cost`                                                                                      |
| **Intent**    | Logging provides visibility into behavior                                                                      |
| **Detection** | Scan .py files for `import logging`, `import structlog`, `from loguru`; scan .js/.ts for winston, pino, bunyan |
| **Evidence**  | Files with logging imports                                                                                     |
| **Fix-First** | Add structured logging with JSON output                                                                        |

#### `structured_errors_present`

| Field         | Value                                                                                    |
| ------------- | ---------------------------------------------------------------------------------------- |
| **Pillar**    | `structured_logging_cost`                                                                |
| **Intent**    | Custom exceptions improve debuggability                                                  |
| **Detection** | Pass if custom exception classes found (class \*Error(Exception)) or error module exists |
| **Evidence**  | Paths to files with custom exceptions                                                    |
| **Fix-First** | Create exceptions.py with domain-specific error classes                                  |

---

### CI Enforcement Checks

#### `ci_workflow_present`

| Field         | Value                                                                                                 |
| ------------- | ----------------------------------------------------------------------------------------------------- |
| **Pillar**    | `verification_trust`                                                                                  |
| **Intent**    | CI ensures quality gates are enforced                                                                 |
| **Detection** | Pass if .github/workflows/\*.yml, .gitlab-ci.yml, azure-pipelines.yml, or .circleci/config.yml exists |
| **Evidence**  | Path to CI config                                                                                     |
| **Fix-First** | Create .github/workflows/ci.yml with lint, test, typecheck                                            |
| **Gate For**  | Level 3                                                                                               |

#### `ci_runs_tests_or_lint`

| Field         | Value                                                                         |
| ------------- | ----------------------------------------------------------------------------- |
| **Pillar**    | `verification_trust`                                                          |
| **Intent**    | CI must actually validate changes                                             |
| **Detection** | Pass if CI workflow contains "pytest", "jest", "cargo test", "eslint", "ruff" |
| **Evidence**  | Commands found in CI                                                          |
| **Fix-First** | Add test and lint steps to CI workflow                                        |

---

### Security & Governance Checks

#### `gitignore_present`

| Field         | Value                                                |
| ------------- | ---------------------------------------------------- |
| **Pillar**    | `secret_hygiene`                                     |
| **Intent**    | Prevent accidental commits of secrets/artifacts      |
| **Detection** | Pass if .gitignore exists and is non-empty           |
| **Evidence**  | Path to .gitignore                                   |
| **Fix-First** | Create .gitignore with language-appropriate patterns |

#### `env_example_or_secrets_docs_present`

| Field         | Value                                                                               |
| ------------- | ----------------------------------------------------------------------------------- |
| **Pillar**    | `secret_hygiene`                                                                    |
| **Intent**    | Document required secrets without exposing them                                     |
| **Detection** | Pass if .env.example, .env.sample, docs/secrets.md, or docs/configuration.md exists |
| **Evidence**  | Path to secrets documentation                                                       |
| **Fix-First** | Create .env.example with placeholder values                                         |

#### `security_policy_present_or_baseline`

| Field         | Value                                                              |
| ------------- | ------------------------------------------------------------------ |
| **Pillar**    | `secret_hygiene`                                                   |
| **Intent**    | Security vulnerability reporting process                           |
| **Detection** | Pass if SECURITY.md, .github/SECURITY.md, or dependabot.yml exists |
| **Evidence**  | Path to security policy                                            |
| **Fix-First** | Create SECURITY.md with vulnerability reporting instructions       |

---

### Fast Guardrails Checks (v2)

#### `fast_linter_python`

| Field         | Value                                                                                               |
| ------------- | --------------------------------------------------------------------------------------------------- |
| **Pillar**    | `fast_guardrails`                                                                                   |
| **Intent**    | Prefer ruff for Python to enable sub-second feedback loops                                          |
| **Detection** | Pass if ruff configured via pyproject.toml, ruff.toml, or .ruff.toml. Partial if flake8/black-only. |
| **Evidence**  | Config file path and presence of [tool.ruff]                                                        |
| **Fix-First** | Add ruff with minimal strict config; add pre-commit hook                                            |
| **Gate For**  | Level 4                                                                                             |

#### `precommit_present`

| Field         | Value                                                                       |
| ------------- | --------------------------------------------------------------------------- |
| **Pillar**    | `fast_guardrails`                                                           |
| **Intent**    | Local fast feedback for agents before pushing                               |
| **Detection** | Pass if .pre-commit-config.yaml exists. Partial if only CI lint exists.     |
| **Evidence**  | Hook list presence                                                          |
| **Fix-First** | Add .pre-commit-config.yaml with ruff + mypy; document `pre-commit install` |
| **Gate For**  | Level 4                                                                     |

---

### Type Contracts Checks (v2)

#### `python_type_hint_coverage`

| Field         | Value                                                                                                                                                                 |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pillar**    | `type_contracts`                                                                                                                                                      |
| **Intent**    | Treat typing as agent-readable documentation                                                                                                                          |
| **Detection** | AST scan .py files (excluding tests/, migrations/, vendor/). Compute: % of function defs with any type annotation. Pass threshold: ≥70% for Level 4; ≥85% for Level 5 |
| **Evidence**  | Total functions, annotated functions, percentage, top 5 missing files                                                                                                 |
| **Fix-First** | Add type hints to top 10 most-called modules; add mypy with stricter rules                                                                                            |
| **Gate For**  | Level 4 (70%), Level 5 (85%)                                                                                                                                          |
| **Safety**    | No imports/exec; parse with ast only; skip generated/vendor directories                                                                                               |

#### `mypy_strictness`

| Field         | Value                                                                                 |
| ------------- | ------------------------------------------------------------------------------------- |
| **Pillar**    | `type_contracts`                                                                      |
| **Intent**    | Require explicit strictness to reduce guessing                                        |
| **Detection** | Pass if mypy.ini or pyproject.toml contains strict=true OR disallow_untyped_defs=true |
| **Evidence**  | Config snippet key names (no secret values)                                           |
| **Fix-First** | Enable disallow_untyped_defs gradually with per-module overrides                      |

---

### Verification Trust Checks (v2)

#### `flake_awareness_pytest`

| Field         | Value                                                                                                       |
| ------------- | ----------------------------------------------------------------------------------------------------------- |
| **Pillar**    | `verification_trust`                                                                                        |
| **Intent**    | Detect awareness/mitigation of flaky tests                                                                  |
| **Detection** | Pass if pytest-rerunfailures OR pytest-flaky in deps. Partial if pytest markers exist but no rerun tooling. |
| **Evidence**  | Dependency name or config keys                                                                              |
| **Fix-First** | Add flaky mitigation plugin; add test isolation guidelines                                                  |

#### `machine_readable_coverage`

| Field         | Value                                                                                  |
| ------------- | -------------------------------------------------------------------------------------- |
| **Pillar**    | `verification_trust`                                                                   |
| **Intent**    | Coverage artifacts must be machine-parsable for agents                                 |
| **Detection** | Pass if config generates coverage.xml or coverage.json. Partial if only HTML coverage. |
| **Evidence**  | Config keys and output filenames                                                       |
| **Fix-First** | Enable coverage.xml with branch coverage; write to ./coverage/coverage.xml             |
| **Gate For**  | Level 4                                                                                |

---

### Verification Speed Checks (v2)

#### `test_splitting`

| Field         | Value                                                                                                |
| ------------- | ---------------------------------------------------------------------------------------------------- |
| **Pillar**    | `verification_speed`                                                                                 |
| **Intent**    | Fast feedback loop: unit vs integration split                                                        |
| **Detection** | Pass if Makefile/tox/nox/pyproject defines unit AND integration targets OR pytest markers documented |
| **Evidence**  | Command targets or marker config                                                                     |
| **Fix-First** | Add `make test-unit` and `make test-integration` targets; add pytest markers                         |
| **Gate For**  | Level 4                                                                                              |

---

### Documentation Structure Checks (v2)

#### `diataxis_structure`

| Field         | Value                                                                                             |
| ------------- | ------------------------------------------------------------------------------------------------- |
| **Pillar**    | `documentation_structure`                                                                         |
| **Intent**    | Reduce context confusion by structuring docs for agent retrieval                                  |
| **Detection** | Pass if docs/ contains ≥3 of: tutorials/, how-to/, reference/, explanation/ (or equivalent files) |
| **Evidence**  | Discovered paths                                                                                  |
| **Fix-First** | Create docs/ with Diátaxis skeleton; add README links                                             |

#### `docstring_coverage_python`

| Field         | Value                                                                                                    |
| ------------- | -------------------------------------------------------------------------------------------------------- |
| **Pillar**    | `inline_documentation`                                                                                   |
| **Intent**    | Docstrings provide local context; agents rely on them                                                    |
| **Detection** | Pass if interrogate config present OR AST scan finds ≥50% docstring coverage on public functions/classes |
| **Evidence**  | Measured percentage and missing hotspots                                                                 |
| **Fix-First** | Add docstrings to public APIs; adopt Google or NumPy style                                               |
| **Safety**    | Prefer interrogate if configured; else safe AST scan                                                     |

---

### Agentic Security Checks (v2)

#### `promptfoo_present`

| Field         | Value                                                               |
| ------------- | ------------------------------------------------------------------- |
| **Pillar**    | `agentic_security`                                                  |
| **Intent**    | Deterministic prompt/agent red teaming                              |
| **Detection** | Pass if promptfooconfig.yaml, promptfoo.yaml, or .promptfoo/ exists |
| **Evidence**  | Config path                                                         |
| **Fix-First** | Add promptfoo with baseline eval suite; wire into CI                |
| **Gate For**  | Level 5                                                             |

#### `prompt_secret_scanning`

| Field         | Value                                                                                                                                                             |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pillar**    | `secret_hygiene`                                                                                                                                                  |
| **Intent**    | Prevent prompt leaks and hardcoded secrets in templates                                                                                                           |
| **Detection** | Scan prompt/template directories for high-entropy strings and common key patterns. Pass if no suspicious patterns OR scanning config exists (gitleaks/TruffleHog) |
| **Evidence**  | Redacted findings (never print full secrets)                                                                                                                      |
| **Fix-First** | Move secrets to env vars; add .env.example; add gitleaks                                                                                                          |
| **Safety**    | Never print full secrets; redact and hash; no upload/exfiltration                                                                                                 |

---

### Telemetry & Observability Checks (v2)

#### `opentelemetry_present`

| Field         | Value                                                                              |
| ------------- | ---------------------------------------------------------------------------------- |
| **Pillar**    | `telemetry_tracing`                                                                |
| **Intent**    | Trace agent behavior; logs alone are insufficient                                  |
| **Detection** | Pass if opentelemetry-sdk, opentelemetry-api, or @opentelemetry/\* in dependencies |
| **Evidence**  | Matched package names                                                              |
| **Fix-First** | Add OTel instrumentation; document exporter injection via env vars                 |
| **Gate For**  | Level 5                                                                            |

#### `structured_logging_present`

| Field         | Value                                                        |
| ------------- | ------------------------------------------------------------ |
| **Pillar**    | `structured_logging_cost`                                    |
| **Intent**    | Enable cost/perf/behavior aggregation via JSON logs          |
| **Detection** | Pass if structlog (Python) or JSON logging config detected   |
| **Evidence**  | Dependency or config keys                                    |
| **Fix-First** | Adopt structlog with JSON renderer; document standard fields |
| **Gate For**  | Level 5                                                      |

---

### Eval Framework Checks (v2)

#### `eval_framework_detect`

| Field         | Value                                                                                              |
| ------------- | -------------------------------------------------------------------------------------------------- |
| **Pillar**    | `eval_frameworks`                                                                                  |
| **Intent**    | Evals are unit tests for agentic behavior                                                          |
| **Detection** | Pass if deepeval, ragas, promptfoo, or langsmith in dependencies. Partial if evals/ folder exists. |
| **Evidence**  | Package name and config paths                                                                      |
| **Fix-First** | Add DeepEval or Ragas minimal suite; integrate into CI                                             |
| **Gate For**  | Level 5                                                                                            |

#### `golden_dataset_present`

| Field         | Value                                                                                                   |
| ------------- | ------------------------------------------------------------------------------------------------------- |
| **Pillar**    | `golden_datasets`                                                                                       |
| **Intent**    | Golden datasets enable regression testing                                                               |
| **Detection** | Pass if tests/data/golden*.json, tests/data/golden*.csv, evals/test_cases._, or fixtures/golden_ exists |
| **Evidence**  | Path and record count (if safely parsable)                                                              |
| **Fix-First** | Create 10-25 golden test cases with expected outcomes; document update policy                           |
| **Gate For**  | Level 5                                                                                                 |

---

## Scoring Algorithm

### Category-to-Pillar Mapping

The v1 categories map to v2 pillars as follows:

| v1 Category             | v2 Pillar(s)                           |
| ----------------------- | -------------------------------------- |
| discoverability         | distribution_dx                        |
| deterministic_setup     | environment_determinism                |
| build_and_run           | fast_guardrails                        |
| test_feedback_loop      | verification_trust, verification_speed |
| static_guardrails       | fast_guardrails, type_contracts        |
| observability           | structured_logging_cost                |
| ci_enforcement          | verification_trust                     |
| security_and_governance | secret_hygiene                         |

### Score Calculation

1. **Check Score**: Each check returns PASSED (1.0), PARTIAL (0.5), or FAILED (0.0)
2. **Category Score**: `(sum of check scores / total checks) * max_points`
3. **Total Score**: Sum of all category scores (0-16)
4. **Maturity Level**: Determined by score AND gate requirements

```python
def calculate_maturity_level(score: float, gates: dict[int, list[str]], results: dict) -> int:
    """
    Level requires BOTH:
    1. Score >= threshold
    2. All gate checks for that level passed
    """
    for level in [5, 4, 3, 2]:
        threshold = {5: 16, 4: 14, 3: 10, 2: 6}[level]
        if score >= threshold:
            if all(results.get(gate, {}).get('passed') for gate in gates.get(level, [])):
                return level
    return 1  # Level 1: Functional
```

### Evidence Requirements

Every check result MUST include:

1. **status**: PASSED | PARTIAL | FAILED | UNKNOWN | SKIPPED
2. **evidence**: What was found (file path, config key, measured value)
3. **suggestion**: Actionable fix if not passed
4. **confidence**: HIGH | MEDIUM | LOW (optional, for heuristic checks)

---

## Report Format

### Markdown Report Structure

```markdown
# Agent Readiness Audit Report

## Summary

- **Repository**: {repo_name}
- **Score**: {score}/16
- **Maturity Level**: Level {N} - {level_name}
- **Scanned**: {timestamp}

## Maturity Level Details

{explanation of current level and what's needed for next level}

## Gate Status

| Level   | Status      | Blocking Checks                              |
| ------- | ----------- | -------------------------------------------- |
| Level 3 | PASSED      | -                                            |
| Level 4 | BLOCKED     | precommit_present, machine_readable_coverage |
| Level 5 | NOT REACHED | -                                            |

## Pillar Scores

| Pillar                  | Score | Status  |
| ----------------------- | ----- | ------- |
| Environment Determinism | 2/2   | PASSED  |
| Fast Guardrails         | 1.5/2 | PARTIAL |
| ...                     | ...   | ...     |

## Fix-First Recommendations

1. {highest-impact fix}
2. {second-impact fix}
   ...

## Category Details

### Discoverability (2/2)

- [x] readme_exists: Found README.md
- [x] readme_has_setup_section: Found "## Installation"
      ...

## Evidence Log

{detailed evidence for each check, path-based and redacted}
```

### JSON Report Structure

```json
{
  "version": "2.0.0",
  "generated_at": "2024-01-15T10:30:00Z",
  "repository": {
    "path": "/path/to/repo",
    "name": "repo-name"
  },
  "score": {
    "total": 14,
    "max": 16,
    "percentage": 87.5
  },
  "maturity": {
    "level": 4,
    "name": "Optimized",
    "description": "Fast feedback loops; split test targets; strong local guardrails"
  },
  "gates": {
    "level_3": {"passed": true, "blocking": []},
    "level_4": {"passed": true, "blocking": []},
    "level_5": {"passed": false, "blocking": ["opentelemetry_present", "eval_framework_detect"]}
  },
  "pillars": {
    "environment_determinism": {"score": 2.0, "max": 2.0, "checks": [...]},
    ...
  },
  "categories": {...},
  "checks": {
    "readme_exists": {
      "status": "passed",
      "evidence": "Found README.md",
      "suggestion": null,
      "pillar": "distribution_dx",
      "category": "discoverability",
      "gate_for": [2]
    },
    ...
  },
  "fix_first": [...],
  "config_used": {...},
  "ignore_policy": [...]
}
```

---

## Configuration

### Default Configuration

```toml
# .agent_readiness_audit.toml

[scoring]
scale_points_total = 16
minimum_passing_score = 10

# Score-to-level thresholds
[[scoring.levels]]
min = 0
max = 5
level = 1
name = "Functional"

[[scoring.levels]]
min = 6
max = 9
level = 2
name = "Documented"

[[scoring.levels]]
min = 10
max = 13
level = 3
name = "Standardized"

[[scoring.levels]]
min = 14
max = 15
level = 4
name = "Optimized"

[[scoring.levels]]
min = 16
max = 16
level = 5
name = "Autonomous"

[categories.discoverability]
enabled = true
max_points = 2
description = "Repo orientation and basic onboarding"

[categories.deterministic_setup]
enabled = true
max_points = 2
description = "Reproducible dependency and environment setup"

# ... more categories

[checks]
# Per-check configuration
readme_exists = { enabled = true, weight = 1.0 }
python_type_hint_coverage = { enabled = true, weight = 1.0, threshold_level_4 = 70, threshold_level_5 = 85 }

[detection]
# File pattern customization
readme_filenames = ["README.md", "README.MD", "README", "readme.md"]
lockfile_patterns = ["uv.lock", "poetry.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"]

[output]
default_format = "table"
include_recommendations = true
show_evidence = true
show_gates = true

[thresholds]
# Tunable thresholds for heuristic checks
type_hint_coverage_level_4 = 70
type_hint_coverage_level_5 = 85
docstring_coverage_minimum = 50
```

### Ignore Policy

Checks can be ignored via configuration:

```toml
[ignore]
# Ignore specific checks
checks = ["diataxis_structure"]

# Ignore entire pillars
pillars = ["agentic_security"]

# Ignore paths (for file-based checks)
paths = ["vendor/", "generated/", "migrations/"]
```

---

## Safety Principles

### Read-Only by Default

ARA MUST NOT:

- Execute code in the scanned repository
- Make network calls to fetch external data
- Modify any files in the scanned repository
- Import/eval any code from the scanned repository

ARA MAY (with explicit flags):

- `--exec-timing`: Run test timing checks (requires user consent)
- `--fetch-metadata`: Query package registries for version info

### Secret Handling

When scanning for secrets:

1. **Never log full secrets** - use redaction (first 4 chars + "...")
2. **Never include secrets in reports** - replace with "[REDACTED]"
3. **Use entropy detection** - high-entropy strings in likely secret locations
4. **Check for patterns** - API_KEY, PASSWORD, SECRET, TOKEN patterns

### Error Handling

Checks MUST:

- Catch all exceptions and return UNKNOWN status
- Include error message in evidence (sanitized)
- Never crash the entire scan for one check failure
- Log warnings for file permission issues

---

## Development Guide

### Adding a New Check

1. **Document first**: Add check specification to this file
2. **Identify pillar**: Assign to appropriate pillar
3. **Define gate level**: If this is a gate check, specify which level
4. **Implement check**:

```python
from pathlib import Path
from agent_readiness_audit.checks.base import CheckResult, check

@check(
    name="my_new_check",
    category="fast_guardrails",  # v1 category for backward compat
    pillar="fast_guardrails",    # v2 pillar
    description="Description of what this check verifies",
    gate_for=[4],                # Level 4 gate (optional)
)
def check_my_new_thing(repo_path: Path) -> CheckResult:
    """Check for new requirement.

    Intent: Why this matters for agent readiness.
    Detection: How we determine pass/fail.
    """
    config_path = repo_path / "config.toml"
    if config_path.exists():
        return CheckResult(
            passed=True,
            evidence=f"Found {config_path.name}",
        )
    return CheckResult(
        passed=False,
        evidence="config.toml not found",
        suggestion="Create config.toml with required settings.",
    )
```

5. **Add tests**:

```python
def test_my_new_check_passes(agent_ready_repo):
    result = check_my_new_thing(agent_ready_repo)
    assert result.passed
    assert "config.toml" in result.evidence

def test_my_new_check_fails(empty_repo):
    result = check_my_new_thing(empty_repo)
    assert not result.passed
    assert "Create config.toml" in result.suggestion
```

6. **Add fixture** if needed: Update `tests/conftest.py`
7. **Update CHANGELOG.md**

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=agent_readiness_audit --cov-report=term-missing

# Specific test file
uv run pytest tests/test_checks.py -v

# Watch mode (requires pytest-watch)
uv run ptw
```

### Code Quality

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy agent_readiness_audit

# All checks
uv run ruff check . && uv run ruff format --check . && uv run mypy agent_readiness_audit
```

---

## Changelog

### v2.0.0 (Unreleased)

- **Added**: 5-level maturity model (Functional → Autonomous)
- **Added**: 15 pillars replacing flat categories
- **Added**: Level gates for certification
- **Added**: New checks: fast_linter_python, precommit_present, python_type_hint_coverage, mypy_strictness, flake_awareness_pytest, machine_readable_coverage, test_splitting, diataxis_structure, docstring_coverage_python, promptfoo_present, prompt_secret_scanning, opentelemetry_present, structured_logging_present, eval_framework_detect, golden_dataset_present
- **Added**: Evidence requirements for all checks
- **Added**: JSON report v2 format with gates and pillars
- **Maintained**: Backward compatibility with v1 0-16 scoring

### v1.0.0

- Initial release with 8 categories and 24 checks
- 0-16 scoring scale
- Table, JSON, Markdown output formats
