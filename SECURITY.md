# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability within Agent Readiness Audit, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via GitHub's private vulnerability reporting feature:

1. Go to the [Security tab](../../security) of this repository
2. Click "Report a vulnerability"
3. Fill out the form with details about the vulnerability

Alternatively, you can email the maintainers directly (if contact information is provided in the repository).

### What to Include

Please include the following information in your report:

- Type of vulnerability (e.g., path traversal, code injection, etc.)
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Initial Response**: Within 48 hours of receiving your report
- **Status Update**: Within 7 days with our assessment
- **Resolution**: We aim to resolve critical issues within 30 days

## Security Design Principles

Agent Readiness Audit is designed with security in mind:

### Safe by Default

- **No code execution**: The tool performs static analysis only and never executes code from scanned repositories
- **No network calls**: By default, no network requests are made during scanning
- **Read-only operations**: The tool only reads files; it never modifies scanned repositories

### Secret Handling

- **No secrets stored**: The tool does not store or transmit any secrets
- **Environment variables**: Configuration uses `.env.example` as a template; actual `.env` files are gitignored
- **Scan detection**: The tool can detect exposed secrets in scanned repos but does not log their values

### Dependency Security

We follow these practices for dependency management:

1. **Minimal dependencies**: We keep dependencies to a minimum
2. **Pinned versions**: All dependencies are version-pinned in `pyproject.toml`
3. **Regular updates**: Dependencies are regularly updated for security patches
4. **Automated scanning**: GitHub's Dependabot is enabled for vulnerability alerts

## Security Best Practices for Users

When using Agent Readiness Audit:

1. **Keep updated**: Always use the latest version
2. **Review output**: Be cautious when sharing scan results that might contain sensitive path information
3. **Trusted sources**: Only scan repositories you trust or have permission to analyze
4. **Output handling**: If writing reports to files, ensure the output directory has appropriate permissions

## Scope

This security policy applies to:

- The `agent-readiness-audit` Python package
- The `ara` CLI tool
- Official documentation and examples

It does not apply to:

- Third-party forks or modifications
- Repositories being scanned by the tool
- User-created plugins or extensions

## Acknowledgments

We appreciate the security research community's efforts in helping keep this project secure. Contributors who report valid security issues will be acknowledged (with their permission) in our release notes.
