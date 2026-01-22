"""Deterministic setup checks - dependency management and reproducibility."""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_contains,
    file_exists,
)

# Dependency manifest files by ecosystem
PYTHON_MANIFESTS = ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile"]
NODE_MANIFESTS = ["package.json"]
RUST_MANIFESTS = ["Cargo.toml"]
GO_MANIFESTS = ["go.mod"]
RUBY_MANIFESTS = ["Gemfile"]

ALL_MANIFESTS = PYTHON_MANIFESTS + NODE_MANIFESTS + RUST_MANIFESTS + GO_MANIFESTS + RUBY_MANIFESTS

# Lock files by ecosystem
PYTHON_LOCKFILES = [
    "uv.lock",
    "poetry.lock",
    "Pipfile.lock",
    "requirements.lock",
    "requirements-lock.txt",
    "pdm.lock",
]
NODE_LOCKFILES = ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb"]
RUST_LOCKFILES = ["Cargo.lock"]
GO_LOCKFILES = ["go.sum"]
RUBY_LOCKFILES = ["Gemfile.lock"]

ALL_LOCKFILES = (
    PYTHON_LOCKFILES + NODE_LOCKFILES + RUST_LOCKFILES + GO_LOCKFILES + RUBY_LOCKFILES
)


@check(
    name="dependency_manifest_exists",
    category="deterministic_setup",
    description="Check if a dependency manifest file exists",
)
def check_dependency_manifest_exists(repo_path: Path) -> CheckResult:
    """Check if dependency manifest exists."""
    manifest = file_exists(repo_path, *ALL_MANIFESTS)
    if manifest:
        return CheckResult(
            passed=True,
            evidence=f"Found dependency manifest: {manifest.name}",
        )
    return CheckResult(
        passed=False,
        evidence="No dependency manifest found",
        suggestion="Add a dependency manifest (e.g., pyproject.toml, package.json, Cargo.toml).",
    )


@check(
    name="lockfile_exists",
    category="deterministic_setup",
    description="Check if a dependency lock file exists for reproducible builds",
)
def check_lockfile_exists(repo_path: Path) -> CheckResult:
    """Check if lock file exists."""
    lockfile = file_exists(repo_path, *ALL_LOCKFILES)
    if lockfile:
        return CheckResult(
            passed=True,
            evidence=f"Found lock file: {lockfile.name}",
        )

    # Check if there's a manifest that should have a lockfile
    manifest = file_exists(repo_path, *ALL_MANIFESTS)
    if manifest:
        return CheckResult(
            passed=False,
            evidence=f"Found manifest ({manifest.name}) but no lock file",
            suggestion="Generate a lock file to ensure reproducible builds (e.g., uv lock, npm install, cargo build).",
        )

    return CheckResult(
        passed=False,
        evidence="No lock file found",
        suggestion="Add a lock file for reproducible dependency installation.",
    )


@check(
    name="runtime_version_declared",
    category="deterministic_setup",
    description="Check if runtime/language version is explicitly declared",
)
def check_runtime_version_declared(repo_path: Path) -> CheckResult:
    """Check if runtime version is declared."""
    # Python version files
    python_version_files = [".python-version", ".tool-versions"]
    for f in python_version_files:
        if file_exists(repo_path, f):
            return CheckResult(
                passed=True,
                evidence=f"Found version file: {f}",
            )

    # Check pyproject.toml for requires-python
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        if file_contains(pyproject, "requires-python", "python_requires"):
            return CheckResult(
                passed=True,
                evidence="Found Python version requirement in pyproject.toml",
            )

    # Check package.json for engines
    package_json = repo_path / "package.json"
    if package_json.exists():
        if file_contains(package_json, '"engines"', '"node"'):
            return CheckResult(
                passed=True,
                evidence="Found Node.js version requirement in package.json",
            )

    # Check .nvmrc for Node
    if file_exists(repo_path, ".nvmrc", ".node-version"):
        return CheckResult(
            passed=True,
            evidence="Found Node.js version file",
        )

    # Check rust-toolchain for Rust
    if file_exists(repo_path, "rust-toolchain", "rust-toolchain.toml"):
        return CheckResult(
            passed=True,
            evidence="Found Rust toolchain file",
        )

    # Check go.mod for Go version
    go_mod = repo_path / "go.mod"
    if go_mod.exists():
        if file_contains(go_mod, "go 1."):
            return CheckResult(
                passed=True,
                evidence="Found Go version in go.mod",
            )

    return CheckResult(
        passed=False,
        evidence="No runtime version declaration found",
        suggestion="Declare your runtime version (e.g., .python-version, .nvmrc, requires-python in pyproject.toml).",
    )
