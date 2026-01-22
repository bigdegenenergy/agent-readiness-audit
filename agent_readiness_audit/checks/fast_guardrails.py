"""Fast guardrails checks (v2) - fast linters and pre-commit hooks."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    check_dependency_present,
    file_contains,
    file_exists,
    read_toml_section,
)


@check(
    name="fast_linter_python",
    category="static_guardrails",
    description="Check for fast Python linter (ruff preferred)",
    pillar="fast_guardrails",
    weight=1.0,
    gate_for=[4],
)
def check_fast_linter_python(repo_path: Path) -> CheckResult:
    """Check if a fast linter like ruff is configured.

    Ruff provides sub-second feedback loops which is critical for agent workflows.
    """
    # Check for ruff configuration
    ruff_config = file_exists(repo_path, "ruff.toml", ".ruff.toml")
    if ruff_config:
        return CheckResult(
            passed=True,
            evidence=f"Fast linter (ruff) configured via {ruff_config.name}",
        )

    # Check pyproject.toml for ruff
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        ruff_section = read_toml_section(pyproject, "tool.ruff")
        if ruff_section:
            return CheckResult(
                passed=True,
                evidence="Fast linter (ruff) configured in pyproject.toml",
            )

    # Check if ruff is in dependencies
    has_ruff = check_dependency_present(repo_path, "ruff")
    if has_ruff:
        return CheckResult(
            passed=True,
            evidence="Ruff found in dependencies (fast linter available)",
        )

    # Check for biome (fast JS/TS linter)
    biome_config = file_exists(repo_path, "biome.json", ".biome.json")
    if biome_config:
        return CheckResult(
            passed=True,
            evidence=f"Fast linter (biome) configured via {biome_config.name}",
        )

    has_biome = check_dependency_present(repo_path, "@biomejs/biome", "biome")
    if has_biome:
        return CheckResult(
            passed=True,
            evidence="Biome found in dependencies (fast linter available)",
        )

    # Check for slower alternatives (partial pass)
    flake8_config = file_exists(repo_path, ".flake8", "setup.cfg")
    if flake8_config:
        content = flake8_config.read_text(encoding="utf-8", errors="ignore")
        if "[flake8]" in content:
            return CheckResult(
                passed=True,
                partial=True,
                evidence="Flake8 configured (slower than ruff)",
                suggestion="Consider migrating to ruff for faster feedback loops (ruff is a drop-in replacement for flake8).",
            )

    # Check for black (formatter only, not a linter)
    has_black = check_dependency_present(repo_path, "black")
    if has_black:
        return CheckResult(
            passed=True,
            partial=True,
            evidence="Black found (formatter only, no linter)",
            suggestion="Add ruff for linting. Ruff can replace both black and flake8 with better performance.",
        )

    # Check pyproject for flake8/pylint
    if pyproject.exists():
        if file_contains(pyproject, "[tool.flake8]"):
            return CheckResult(
                passed=True,
                partial=True,
                evidence="Flake8 configured in pyproject.toml (slower than ruff)",
                suggestion="Migrate to ruff for sub-second feedback loops.",
            )
        if file_contains(pyproject, "[tool.pylint]"):
            return CheckResult(
                passed=True,
                partial=True,
                evidence="Pylint configured (significantly slower than ruff)",
                suggestion="Migrate to ruff for faster agent-friendly feedback loops.",
            )

    # Check for eslint (JS/TS)
    eslint_config = file_exists(
        repo_path,
        ".eslintrc",
        ".eslintrc.js",
        ".eslintrc.json",
        ".eslintrc.yml",
        "eslint.config.js",
        "eslint.config.mjs",
    )
    if eslint_config:
        return CheckResult(
            passed=True,
            partial=True,
            evidence=f"ESLint configured via {eslint_config.name}",
            suggestion="Consider migrating to Biome for faster lint times.",
        )

    # Check if this is a Python project
    if pyproject.exists():
        return CheckResult(
            passed=False,
            evidence="Python project detected but no fast linter configured",
            suggestion="Add ruff to pyproject.toml: [tool.ruff] with sensible defaults.",
        )

    # Check if this is a JS/TS project
    package_json = repo_path / "package.json"
    if package_json.exists():
        return CheckResult(
            passed=False,
            evidence="JS/TS project detected but no fast linter configured",
            suggestion="Add biome or eslint for fast linting.",
        )

    return CheckResult(
        passed=False,
        evidence="No linter configuration detected",
        suggestion="Add a fast linter: ruff for Python, biome for JS/TS.",
    )


@check(
    name="precommit_present",
    category="static_guardrails",
    description="Check if pre-commit hooks are configured",
    pillar="fast_guardrails",
    weight=1.5,
    gate_for=[4],
)
def check_precommit_present(repo_path: Path) -> CheckResult:
    """Check if pre-commit hooks are configured for local feedback."""
    # Check for .pre-commit-config.yaml
    precommit_config = file_exists(
        repo_path, ".pre-commit-config.yaml", ".pre-commit-config.yml"
    )
    if precommit_config:
        # Check what hooks are configured
        content = precommit_config.read_text(encoding="utf-8", errors="ignore").lower()
        hooks_found: list[str] = []

        if "ruff" in content:
            hooks_found.append("ruff")
        if "black" in content:
            hooks_found.append("black")
        if "mypy" in content:
            hooks_found.append("mypy")
        if "eslint" in content:
            hooks_found.append("eslint")
        if "prettier" in content:
            hooks_found.append("prettier")
        if "biome" in content:
            hooks_found.append("biome")

        if hooks_found:
            return CheckResult(
                passed=True,
                evidence=f"Pre-commit configured with hooks: {', '.join(hooks_found)}",
            )
        return CheckResult(
            passed=True,
            evidence=f"Pre-commit configured via {precommit_config.name}",
        )

    # Check for husky (JS/TS pre-commit)
    husky_dir = repo_path / ".husky"
    if husky_dir.is_dir():
        return CheckResult(
            passed=True,
            evidence="Husky pre-commit hooks configured",
        )

    # Check package.json for husky config
    package_json = repo_path / "package.json"
    if package_json.exists():
        content = package_json.read_text(encoding="utf-8", errors="ignore")
        if '"husky"' in content or '"lint-staged"' in content:
            return CheckResult(
                passed=True,
                evidence="Husky/lint-staged configured in package.json",
            )

    # Check for lefthook
    lefthook_config = file_exists(
        repo_path, "lefthook.yml", "lefthook.yaml", ".lefthook.yml"
    )
    if lefthook_config:
        return CheckResult(
            passed=True,
            evidence=f"Lefthook pre-commit configured via {lefthook_config.name}",
        )

    # Check .git/hooks for manual hooks
    git_hooks = repo_path / ".git" / "hooks"
    if git_hooks.is_dir():
        precommit_hook = git_hooks / "pre-commit"
        if precommit_hook.exists() and precommit_hook.stat().st_size > 0:
            return CheckResult(
                passed=True,
                partial=True,
                evidence="Manual pre-commit hook found in .git/hooks",
                suggestion="Consider using pre-commit framework for easier hook management and sharing.",
            )

    # Check if CI exists (partial credit for lint in CI)
    ci_workflows = file_exists(
        repo_path,
        ".github/workflows/ci.yml",
        ".github/workflows/lint.yml",
        ".gitlab-ci.yml",
    )
    if ci_workflows:
        return CheckResult(
            passed=False,
            partial=True,
            evidence="CI workflows found but no local pre-commit hooks",
            suggestion="Add .pre-commit-config.yaml for fast local feedback before push.",
        )

    return CheckResult(
        passed=False,
        evidence="No pre-commit hooks configured",
        suggestion="Add .pre-commit-config.yaml with ruff and mypy hooks for local feedback.",
    )
