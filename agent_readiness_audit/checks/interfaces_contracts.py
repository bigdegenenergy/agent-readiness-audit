"""Interface and contract checks for ARA v3 specification.

These checks evaluate whether inputs, outputs, and side effects are machine-verifiable:
- Typed interfaces (TypeScript, pydantic, dataclasses, JSON schema)
- Explicit input/output schemas for APIs, CLIs, data artifacts
- Versioned contracts
- Contract validation hooks
"""

from __future__ import annotations

from pathlib import Path

from agent_readiness_audit.checks.base import (
    CheckResult,
    check,
    glob_files,
    read_file_safe,
)


@check(
    name="typed_interfaces",
    category="static_guardrails",
    description="Check for typed interface definitions (Pydantic, dataclasses, TypedDict)",
    domain="interfaces",
)
def check_typed_interfaces(repo_path: Path) -> CheckResult:
    """Check for typed data interfaces.

    Looks for:
    - Pydantic models
    - dataclasses
    - TypedDict
    - NamedTuple
    - attrs classes
    """
    py_files = glob_files(repo_path, "**/*.py")[:50]

    interface_patterns = [
        ("from pydantic import", "Pydantic models"),
        ("from pydantic import BaseModel", "Pydantic BaseModel"),
        ("@dataclass", "dataclasses"),
        ("from dataclasses import", "dataclasses"),
        ("TypedDict", "TypedDict"),
        ("NamedTuple", "NamedTuple"),
        ("import attrs", "attrs classes"),
        ("@attr.s", "attrs classes"),
    ]

    found_interfaces: list[str] = []

    for py_file in py_files:
        content = read_file_safe(py_file)
        if not content:
            continue

        for pattern, desc in interface_patterns:
            if pattern in content and desc not in found_interfaces:
                found_interfaces.append(desc)

    if found_interfaces:
        return CheckResult(
            passed=True,
            evidence=f"Found typed interfaces: {', '.join(found_interfaces)}",
        )

    return CheckResult(
        passed=False,
        evidence="No typed interface definitions found",
        suggestion="Use Pydantic, dataclasses, or TypedDict for structured data interfaces.",
    )


@check(
    name="api_schema_defined",
    category="static_guardrails",
    description="Check for API schema definitions (OpenAPI, JSON Schema, GraphQL)",
    domain="interfaces",
)
def check_api_schema_defined(repo_path: Path) -> CheckResult:
    """Check for API schema definitions.

    Looks for:
    - OpenAPI/Swagger specs
    - JSON Schema files
    - GraphQL schemas
    - FastAPI/Flask automatic schema generation
    """
    # Check for schema files
    schema_patterns = [
        "openapi.yaml",
        "openapi.yml",
        "openapi.json",
        "swagger.yaml",
        "swagger.yml",
        "swagger.json",
        "schema.graphql",
        "*.graphql",
        "schema.json",
        "api-schema.json",
    ]

    for pattern in schema_patterns:
        matches = glob_files(repo_path, f"**/{pattern}")
        if matches:
            return CheckResult(
                passed=True,
                evidence=f"Found API schema: {matches[0].name}",
            )

    # Check for FastAPI (auto-generates OpenAPI)
    py_files = glob_files(repo_path, "**/*.py")[:30]
    for py_file in py_files:
        content = read_file_safe(py_file)
        if content and "from fastapi import" in content:
            return CheckResult(
                passed=True,
                evidence="FastAPI detected (auto-generates OpenAPI schema)",
            )

    # Check pyproject.toml for API frameworks
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = read_file_safe(pyproject)
        if content:
            api_frameworks = ["fastapi", "flask-openapi", "connexion", "strawberry"]
            for framework in api_frameworks:
                if framework in content.lower():
                    return CheckResult(
                        passed=True,
                        evidence=f"API framework with schema support detected: {framework}",
                    )

    # Check if there are any API endpoints
    has_api = False
    for py_file in py_files:
        content = read_file_safe(py_file)
        if content and any(
            pattern in content
            for pattern in ["@app.route", "@router.", "def get(", "def post("]
        ):
            has_api = True
            break

    if not has_api:
        return CheckResult(
            passed=True,
            evidence="No API endpoints detected",
        )

    return CheckResult(
        passed=False,
        evidence="API endpoints found but no schema definition",
        suggestion="Add OpenAPI, JSON Schema, or GraphQL schema for API documentation.",
    )


@check(
    name="cli_typed_args",
    category="static_guardrails",
    description="Check if CLI arguments are typed (Typer, Click with types, argparse)",
    domain="interfaces",
)
def check_cli_typed_args(repo_path: Path) -> CheckResult:
    """Check if CLI has typed arguments.

    Prefers:
    - Typer (fully typed)
    - Click with type annotations
    - argparse with type= specified
    """
    py_files = glob_files(repo_path, "**/*.py")[:40]

    for py_file in py_files:
        content = read_file_safe(py_file)
        if not content:
            continue

        # Best: Typer (fully typed)
        if "import typer" in content or "from typer import" in content:
            return CheckResult(
                passed=True,
                evidence=f"Typer CLI detected in {py_file.name} (fully typed)",
            )

        # Good: Click with type annotations
        has_click = "@click.command" in content or "@click.group" in content
        has_type_hints = ": " in content  # Basic check for type annotations
        if has_click and has_type_hints:
            return CheckResult(
                passed=True,
                evidence=f"Click CLI with type hints in {py_file.name}",
            )

        # Acceptable: argparse with type=
        if "argparse" in content and "type=" in content:
            return CheckResult(
                passed=True,
                evidence=f"argparse with typed arguments in {py_file.name}",
            )

    # Check if there's a CLI at all
    for py_file in py_files:
        content = read_file_safe(py_file)
        if content and any(
            pattern in content
            for pattern in ["argparse", "click", "if __name__", "def main("]
        ):
            return CheckResult(
                passed=False,
                evidence="CLI detected but arguments may not be typed",
                suggestion="Use Typer or add type annotations to Click/argparse arguments.",
            )

    return CheckResult(
        passed=True,
        evidence="No CLI detected",
    )


@check(
    name="return_types_documented",
    category="static_guardrails",
    description="Check for return type annotations on functions",
    domain="interfaces",
)
def check_return_types_documented(repo_path: Path) -> CheckResult:
    """Check that functions have return type annotations.

    Samples functions and checks for -> annotation.
    """
    py_files = glob_files(repo_path, "**/*.py")[:30]

    # Skip test files for this check
    py_files = [f for f in py_files if "test" not in str(f).lower()]

    functions_checked = 0
    functions_with_return_type = 0

    for py_file in py_files:
        content = read_file_safe(py_file)
        if not content:
            continue

        lines = content.split("\n")
        for line in lines:
            if line.strip().startswith("def "):
                functions_checked += 1
                if " -> " in line:
                    functions_with_return_type += 1

    if functions_checked == 0:
        return CheckResult(
            passed=True,
            evidence="No function definitions found",
        )

    coverage = (functions_with_return_type / functions_checked) * 100

    if coverage >= 70:
        return CheckResult(
            passed=True,
            evidence=f"Return type coverage: {coverage:.0f}% ({functions_with_return_type}/{functions_checked})",
        )
    elif coverage >= 40:
        return CheckResult(
            passed=True,
            partial=True,
            evidence=f"Partial return type coverage: {coverage:.0f}%",
        )

    return CheckResult(
        passed=False,
        evidence=f"Low return type coverage: {coverage:.0f}%",
        suggestion="Add return type annotations (-> Type) to functions for better agent understanding.",
    )


@check(
    name="no_implicit_dict_schemas",
    category="static_guardrails",
    description="Check for avoidance of dicts as implicit schemas",
    domain="interfaces",
)
def check_no_implicit_dict_schemas(repo_path: Path) -> CheckResult:
    """Check that dicts aren't used as implicit schemas.

    Red flags:
    - Dict[str, Any] return types
    - -> dict without type parameters
    - Functions returning {'key': value} patterns
    """
    py_files = glob_files(repo_path, "**/*.py")[:30]
    py_files = [f for f in py_files if "test" not in str(f).lower()]

    red_flags: list[str] = []

    for py_file in py_files:
        content = read_file_safe(py_file)
        if not content:
            continue

        lines = content.split("\n")
        for i, line in enumerate(lines):
            # Check for Dict[str, Any] - too loose
            if "Dict[str, Any]" in line or "dict[str, Any]" in line:
                red_flags.append(f"{py_file.name}:{i + 1}: Dict[str, Any]")

            # Check for untyped dict returns
            if "-> dict" in line and "-> dict[" not in line:
                red_flags.append(f"{py_file.name}:{i + 1}: untyped dict return")

        if len(red_flags) >= 5:
            break

    if red_flags:
        return CheckResult(
            passed=False,
            evidence=f"Found {len(red_flags)} implicit dict schemas: {', '.join(red_flags[:3])}",
            suggestion="Replace Dict[str, Any] with typed dataclasses, Pydantic models, or TypedDict.",
        )

    return CheckResult(
        passed=True,
        evidence="No implicit dict schema patterns detected",
    )


@check(
    name="contract_versioning",
    category="static_guardrails",
    description="Check for API/contract versioning strategy",
    domain="interfaces",
)
def check_contract_versioning(repo_path: Path) -> CheckResult:
    """Check for versioning in API contracts.

    Looks for:
    - API version in URL patterns (/v1/, /api/v2/)
    - Version field in schemas
    - Semantic versioning in package
    """
    # Check for URL versioning
    py_files = glob_files(repo_path, "**/*.py")[:30]
    for py_file in py_files:
        content = read_file_safe(py_file)
        if content and any(
            pattern in content for pattern in ["/v1/", "/v2/", "/api/v", "api_version"]
        ):
            return CheckResult(
                passed=True,
                evidence=f"API versioning detected in {py_file.name}",
            )

    # Check OpenAPI for version
    schema_files = glob_files(repo_path, "**/openapi*.{yaml,yml,json}")
    for schema in schema_files:
        content = read_file_safe(schema)
        if content and "version" in content.lower():
            return CheckResult(
                passed=True,
                evidence=f"Version specified in {schema.name}",
            )

    # Check pyproject.toml for semantic versioning
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        content = read_file_safe(pyproject)
        if content and 'version = "' in content:
            return CheckResult(
                passed=True,
                evidence="Package versioning in pyproject.toml",
            )

    # Check package.json
    package_json = repo_path / "package.json"
    if package_json.exists():
        content = read_file_safe(package_json)
        if content and '"version"' in content:
            return CheckResult(
                passed=True,
                evidence="Package versioning in package.json",
            )

    return CheckResult(
        passed=False,
        evidence="No contract versioning strategy detected",
        suggestion="Add API versioning (URL prefix like /v1/) or package version for contract stability.",
    )
