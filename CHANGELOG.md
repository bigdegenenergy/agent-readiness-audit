# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Agent Readiness Audit CLI
- `ara scan` command for scanning single repos or directories of repos
- `ara report` command for rendering reports from saved JSON
- `ara init-config` command for generating starter configuration
- 8 scoring categories with 24 total checks:
  - Discoverability (README presence and quality)
  - Deterministic Setup (dependency management)
  - Build and Run (task runners and scripts)
  - Test Feedback Loop (test infrastructure)
  - Static Guardrails (linting, formatting, type checking)
  - Observability (logging and error handling)
  - CI Enforcement (continuous integration)
  - Security and Governance (security policies and hygiene)
- Multiple output formats: table, JSON, Markdown
- Configurable scoring via TOML configuration files
- Fix-first recommendations for improving readiness scores
- Cross-platform support (macOS, Linux, Windows)

### Security
- Safe-by-default design: no code execution, no network calls
- Read-only scanning operations

## [0.1.0] - Unreleased

Initial public release.

[Unreleased]: https://github.com/bigdegenenergy/agent-readiness-audit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/bigdegenenergy/agent-readiness-audit/releases/tag/v0.1.0
