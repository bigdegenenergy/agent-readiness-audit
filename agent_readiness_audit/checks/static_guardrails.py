"""Static guardrails checks - linting, formatting, type checking."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_contains,
    file_exists,
)

# Linter configuration files
PYTHON_LINTER_CONFIGS = [
    "ruff.toml",
    ".ruff.toml",
    ".flake8",
    "setup.cfg",
    ".pylintrc",
    "pylintrc",
]
JS_LINTER_CONFIGS = [
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.json",
    ".eslintrc.yml",
    ".eslintrc.yaml",
    "eslint.config.js",
    "eslint.config.mjs",
    ".biome.json",
    "biome.json",
]
RUST_LINTER_CONFIGS = ["clippy.toml", ".clippy.toml"]
GO_LINTER_CONFIGS = [".golangci.yml", ".golangci.yaml", "golangci.yml"]

ALL_LINTER_CONFIGS = (
    PYTHON_LINTER_CONFIGS + JS_LINTER_CONFIGS + RUST_LINTER_CONFIGS + GO_LINTER_CONFIGS
)

# Formatter configuration files
PYTHON_FORMATTER_CONFIGS = ["ruff.toml", ".ruff.toml", ".style.yapf", "pyproject.toml"]
JS_FORMATTER_CONFIGS = [
    ".prettierrc",
    ".prettierrc.js",
    ".prettierrc.json",
    ".prettierrc.yml",
    ".prettierrc.yaml",
    "prettier.config.js",
    ".biome.json",
    "biome.json",
]
RUST_FORMATTER_CONFIGS = ["rustfmt.toml", ".rustfmt.toml"]
GO_FORMATTER_CONFIGS: list[str] = []  # gofmt is built-in

ALL_FORMATTER_CONFIGS = (
    PYTHON_FORMATTER_CONFIGS + JS_FORMATTER_CONFIGS + RUST_FORMATTER_CONFIGS
)

# Type checker configuration files
PYTHON_TYPE_CONFIGS = [
    "mypy.ini",
    ".mypy.ini",
    "pyrightconfig.json",
    "pyright.json",
]
JS_TYPE_CONFIGS = ["tsconfig.json", "jsconfig.json"]


@check(
    name="linter_config_present",
    category="static_guardrails",
    description="Check if linter configuration exists",
    pillar="fast_guardrails",
    gate_for=[3],
)
def check_linter_config_present(repo_path: Path) -> CheckResult:
    """Check if linter is configured."""
    # Check dedicated linter config files
    config = file_exists(repo_path, *ALL_LINTER_CONFIGS)
    if config:
        return CheckResult(
            passed=True,
            evidence=f"Found linter configuration: {config.name}",
        )

    # Check pyproject.toml for linter config
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists() and file_contains(
        pyproject, "[tool.ruff", "[tool.flake8", "[tool.pylint"
    ):
        return CheckResult(
            passed=True,
            evidence="Found linter configuration in pyproject.toml",
        )

    # Check package.json for eslint
    package_json = repo_path / "package.json"
    if package_json.exists() and file_contains(
        package_json, '"eslint"', '"eslintConfig"', '"biome"'
    ):
        return CheckResult(
            passed=True,
            evidence="Found linter configuration in package.json",
        )

    return CheckResult(
        passed=False,
        evidence="No linter configuration found",
        suggestion="Add a linter configuration (e.g., ruff.toml, .eslintrc, [tool.ruff] in pyproject.toml).",
    )


@check(
    name="formatter_config_present",
    category="static_guardrails",
    description="Check if code formatter configuration exists",
    pillar="fast_guardrails",
)
def check_formatter_config_present(repo_path: Path) -> CheckResult:
    """Check if formatter is configured."""
    # Check dedicated formatter config files
    config = file_exists(repo_path, *ALL_FORMATTER_CONFIGS)
    if config:
        return CheckResult(
            passed=True,
            evidence=f"Found formatter configuration: {config.name}",
        )

    # Check pyproject.toml for formatter config
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists() and file_contains(
        pyproject,
        "[tool.ruff.format",
        "[tool.black",
        "[tool.yapf",
        "[tool.isort",
        "line-length",
    ):
        return CheckResult(
            passed=True,
            evidence="Found formatter configuration in pyproject.toml",
        )

    # Check package.json for prettier
    package_json = repo_path / "package.json"
    if package_json.exists() and file_contains(package_json, '"prettier"', '"biome"'):
        return CheckResult(
            passed=True,
            evidence="Found formatter configuration in package.json",
        )

    # Check .editorconfig as basic formatting
    editorconfig = repo_path / ".editorconfig"
    if editorconfig.exists():
        return CheckResult(
            passed=True,
            evidence="Found .editorconfig for basic formatting rules",
        )

    return CheckResult(
        passed=False,
        evidence="No formatter configuration found",
        suggestion="Add a formatter configuration (e.g., [tool.ruff.format] in pyproject.toml, .prettierrc).",
    )


@check(
    name="typecheck_config_present",
    category="static_guardrails",
    description="Check if type checking configuration exists",
    pillar="type_contracts",
)
def check_typecheck_config_present(repo_path: Path) -> CheckResult:
    """Check if type checker is configured."""
    # Check Python type checker configs
    config = file_exists(repo_path, *PYTHON_TYPE_CONFIGS)
    if config:
        return CheckResult(
            passed=True,
            evidence=f"Found type checker configuration: {config.name}",
        )

    # Check TypeScript/JavaScript configs
    ts_config = file_exists(repo_path, *JS_TYPE_CONFIGS)
    if ts_config:
        return CheckResult(
            passed=True,
            evidence=f"Found TypeScript configuration: {ts_config.name}",
        )

    # Check pyproject.toml for mypy config
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists() and file_contains(pyproject, "[tool.mypy", "[tool.pyright"):
        return CheckResult(
            passed=True,
            evidence="Found type checker configuration in pyproject.toml",
        )

    # Check setup.cfg for mypy
    setup_cfg = repo_path / "setup.cfg"
    if setup_cfg.exists() and file_contains(setup_cfg, "[mypy"):
        return CheckResult(
            passed=True,
            evidence="Found mypy configuration in setup.cfg",
        )

    # Rust has built-in type checking
    cargo_toml = repo_path / "Cargo.toml"
    if cargo_toml.exists():
        return CheckResult(
            passed=True,
            evidence="Rust has built-in type checking via the compiler",
        )

    # Go has built-in type checking
    go_mod = repo_path / "go.mod"
    if go_mod.exists():
        return CheckResult(
            passed=True,
            evidence="Go has built-in type checking via the compiler",
        )

    return CheckResult(
        passed=False,
        evidence="No type checking configuration found",
        suggestion="Add type checking (e.g., mypy.ini, [tool.mypy] in pyproject.toml, tsconfig.json).",
    )
