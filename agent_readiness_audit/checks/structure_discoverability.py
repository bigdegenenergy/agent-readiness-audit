"""Structure and discoverability checks for ARA v3 specification.

These checks evaluate whether an agent can quickly understand the repo:
- Root README exists and answers key questions
- Predictable directory layout
- No critical logic hidden in scripts/notebooks/CI-only paths
- Clear entrypoints
"""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    file_exists,
    glob_files,
    read_file_safe,
)


@check(
    name="readme_answers_what",
    category="discoverability",
    description="Check if README explains what the repo does",
    domain="structure",
)
def check_readme_answers_what(repo_path: Path) -> CheckResult:
    """Check if README answers 'What does this repo do?'

    Looks for purpose/overview section or description in first paragraphs.
    """
    readme = file_exists(repo_path, "README.md", "README.rst", "README.txt", "README")
    if not readme:
        return CheckResult(
            passed=False,
            evidence="No README found",
            suggestion="Add a README.md explaining what this repository does.",
        )

    content = read_file_safe(readme)
    if not content:
        return CheckResult(
            passed=False,
            evidence="README exists but is empty or unreadable",
            suggestion="Add content to README explaining the project purpose.",
        )

    # Check for purpose indicators
    purpose_patterns = [
        "## what",
        "## about",
        "## overview",
        "## description",
        "## purpose",
        "## introduction",
        "# about",
        "a tool",
        "a library",
        "a framework",
        "a cli",
        "an application",
        "this project",
        "this repo",
    ]

    content_lower = content.lower()
    for pattern in purpose_patterns:
        if pattern in content_lower:
            return CheckResult(
                passed=True,
                evidence=f"README contains purpose indicator: '{pattern}'",
            )

    # Check first 500 chars for any descriptive content
    first_section = content[:500]
    if len(first_section.split()) > 20:  # At least some content
        return CheckResult(
            passed=True,
            partial=True,
            evidence="README has content but purpose section not clearly marked",
        )

    return CheckResult(
        passed=False,
        evidence="README doesn't clearly explain what the repo does",
        suggestion="Add a clear description of the project's purpose in the README.",
    )


@check(
    name="readme_answers_how",
    category="discoverability",
    description="Check if README explains how to run the repo",
    domain="structure",
)
def check_readme_answers_how(repo_path: Path) -> CheckResult:
    """Check if README answers 'How is it executed?'

    Looks for installation/setup/usage sections.
    """
    readme = file_exists(repo_path, "README.md", "README.rst", "README.txt", "README")
    if not readme:
        return CheckResult(
            passed=False,
            evidence="No README found",
            suggestion="Add a README.md with installation and usage instructions.",
        )

    content = read_file_safe(readme)
    if not content:
        return CheckResult(
            passed=False,
            evidence="README exists but is empty",
            suggestion="Add installation and usage instructions to README.",
        )

    # Check for execution/usage sections
    execution_patterns = [
        "## install",
        "## setup",
        "## usage",
        "## getting started",
        "## quick start",
        "## quickstart",
        "## running",
        "## how to use",
        "pip install",
        "npm install",
        "cargo install",
        "go install",
    ]

    content_lower = content.lower()
    for pattern in execution_patterns:
        if pattern in content_lower:
            return CheckResult(
                passed=True,
                evidence=f"README contains execution instructions: '{pattern}'",
            )

    return CheckResult(
        passed=False,
        evidence="README doesn't explain how to run/install",
        suggestion="Add Installation and Usage sections to README.",
    )


@check(
    name="predictable_layout",
    category="discoverability",
    description="Check for predictable directory structure",
    domain="structure",
)
def check_predictable_layout(repo_path: Path) -> CheckResult:
    """Check for standard directory layout.

    Expects common patterns:
    - src/ or package_name/ for source
    - tests/ for tests
    - docs/ for documentation (optional)
    """
    # Check for source directory patterns
    has_src = False
    src_patterns = ["src", "lib", "app"]

    for pattern in src_patterns:
        if (repo_path / pattern).is_dir():
            has_src = True
            break

    # Check for package-style layout (package_name/)
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = read_file_safe(pyproject)
        if content and 'name = "' in content:
            # Extract package name and check if dir exists
            import re

            match = re.search(r'name\s*=\s*"([^"]+)"', content)
            if match:
                pkg_name = match.group(1).replace("-", "_")
                if (repo_path / pkg_name).is_dir():
                    has_src = True

    # Check for tests directory
    has_tests = (repo_path / "tests").is_dir() or (repo_path / "test").is_dir()

    if has_src and has_tests:
        return CheckResult(
            passed=True,
            evidence="Standard layout detected (source + tests directories)",
        )

    if has_src:
        return CheckResult(
            passed=True,
            partial=True,
            evidence="Source directory found but tests directory missing",
        )

    # Check for flat layout with __init__.py
    init_files = glob_files(repo_path, "*/__init__.py")
    if init_files:
        return CheckResult(
            passed=True,
            evidence="Python package structure detected",
        )

    return CheckResult(
        passed=False,
        evidence="Non-standard directory layout",
        suggestion="Organize code into src/ or package_name/ with tests/ directory.",
    )


@check(
    name="entrypoint_clear",
    category="discoverability",
    description="Check for clear entry points (CLI, main module)",
    domain="structure",
)
def check_entrypoint_clear(repo_path: Path) -> CheckResult:
    """Check for clearly defined entry points.

    Looks for:
    - [project.scripts] in pyproject.toml
    - __main__.py
    - main.py
    - bin/ directory
    - "main" entry in package.json
    """
    # Check pyproject.toml for scripts
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = read_file_safe(pyproject)
        if content and "[project.scripts]" in content:
            return CheckResult(
                passed=True,
                evidence="CLI entry point defined in pyproject.toml [project.scripts]",
            )

    # Check for __main__.py
    main_files = glob_files(repo_path, "**/__main__.py")
    if main_files:
        return CheckResult(
            passed=True,
            evidence=f"Entry point: {main_files[0].relative_to(repo_path)}",
        )

    # Check for main.py at root or in src
    if file_exists(repo_path, "main.py", "src/main.py", "app/main.py"):
        return CheckResult(
            passed=True,
            evidence="Entry point: main.py",
        )

    # Check package.json
    package_json = repo_path / "package.json"
    if package_json.exists():
        content = read_file_safe(package_json)
        if content and ('"main"' in content or '"bin"' in content):
            return CheckResult(
                passed=True,
                evidence="Entry point defined in package.json",
            )

    # Check for Makefile with run target
    makefile = file_exists(repo_path, "Makefile")
    if makefile:
        content = read_file_safe(makefile)
        if content and ("run:" in content or "start:" in content):
            return CheckResult(
                passed=True,
                evidence="Entry point via Makefile run/start target",
            )

    return CheckResult(
        passed=False,
        evidence="No clear entry point found",
        suggestion="Define entry points in pyproject.toml [project.scripts] or add __main__.py.",
    )


@check(
    name="no_hidden_critical_logic",
    category="discoverability",
    description="Check that critical logic isn't hidden in scripts/notebooks/CI",
    domain="structure",
)
def check_no_hidden_critical_logic(repo_path: Path) -> CheckResult:
    """Check that critical logic is in main source, not hidden locations.

    Red flags:
    - Large scripts/ directory
    - Jupyter notebooks with significant logic
    - CI files with build/deployment logic
    """
    red_flags: list[str] = []

    # Check for scripts directory with significant code
    scripts_dir = repo_path / "scripts"
    if scripts_dir.is_dir():
        scripts = list(scripts_dir.glob("*.py")) + list(scripts_dir.glob("*.sh"))
        if len(scripts) > 5:
            red_flags.append(f"Large scripts/ directory ({len(scripts)} files)")

    # Check for notebooks with significant code
    notebooks = glob_files(repo_path, "**/*.ipynb")
    if len(notebooks) > 3:
        red_flags.append(f"Multiple notebooks ({len(notebooks)}) may contain logic")

    # Check CI for complex logic (only flag very large files that likely contain
    # embedded scripts or significant business logic, not normal workflow configs)
    ci_files = glob_files(repo_path, ".github/workflows/*.yml")
    for ci_file in ci_files:
        content = read_file_safe(ci_file)
        # 15000 chars threshold (~300+ lines) to avoid false positives on
        # standard multi-job workflows while catching embedded bash scripts
        if content and len(content) > 15000:
            red_flags.append(f"Very large CI file: {ci_file.name}")

    if red_flags:
        return CheckResult(
            passed=False,
            evidence=f"Potential hidden logic: {', '.join(red_flags)}",
            suggestion="Move critical logic from scripts/notebooks/CI into main source code.",
        )

    return CheckResult(
        passed=True,
        evidence="No significant hidden logic detected",
    )


@check(
    name="file_tree_organized",
    category="discoverability",
    description="Check for organized file tree (low entropy)",
    domain="structure",
)
def check_file_tree_organized(repo_path: Path) -> CheckResult:
    """Check that the file tree is well-organized.

    Measures:
    - Not too many files at root level
    - Logical grouping in directories
    """
    # Count files at root level (excluding hidden)
    root_files = [
        f for f in repo_path.iterdir() if f.is_file() and not f.name.startswith(".")
    ]

    # Standard root files to exclude from count
    standard_files = {
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "pyproject.toml",
        "package.json",
        "Makefile",
        "Dockerfile",
        ".gitignore",
        "setup.py",
        "setup.cfg",
    }

    extra_root_files = [f for f in root_files if f.name not in standard_files]

    if len(extra_root_files) > 10:
        return CheckResult(
            passed=False,
            evidence=f"Too many files at root level ({len(extra_root_files)} non-standard files)",
            suggestion="Organize files into subdirectories (src/, docs/, etc.).",
        )

    # Count total directories at root
    root_dirs = [
        d for d in repo_path.iterdir() if d.is_dir() and not d.name.startswith(".")
    ]

    if len(root_dirs) > 15:
        return CheckResult(
            passed=False,
            evidence=f"Too many directories at root ({len(root_dirs)})",
            suggestion="Consolidate related directories for cleaner structure.",
        )

    return CheckResult(
        passed=True,
        evidence=f"Organized structure: {len(root_files)} root files, {len(root_dirs)} directories",
    )
