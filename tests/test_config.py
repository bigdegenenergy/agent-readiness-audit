"""Tests for configuration module."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_readiness_audit.config import (
    find_config_file,
    generate_default_config,
    load_config,
    parse_config,
)
from agent_readiness_audit.models import AuditConfig


class TestFindConfigFile:
    """Tests for find_config_file function."""

    def test_find_config_in_current_dir(self, temp_dir: Path) -> None:
        config_path = temp_dir / ".agent_readiness_audit.toml"
        config_path.write_text("[scoring]\nscale_points_total = 16\n")

        found = find_config_file(temp_dir)
        assert found == config_path

    def test_find_config_in_parent_dir(self, temp_dir: Path) -> None:
        config_path = temp_dir / ".agent_readiness_audit.toml"
        config_path.write_text("[scoring]\nscale_points_total = 16\n")

        child_dir = temp_dir / "subdir"
        child_dir.mkdir()

        found = find_config_file(child_dir)
        assert found == config_path

    def test_no_config_found(self, temp_dir: Path) -> None:
        found = find_config_file(temp_dir)
        # May find home config or None
        assert found is None or found.name == ".agent_readiness_audit.toml"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_default_config(self) -> None:
        config = load_config(None)
        assert isinstance(config, AuditConfig)
        assert config.scale_points_total == 16
        assert len(config.categories) == 8

    def test_load_custom_config(self, temp_dir: Path) -> None:
        config_path = temp_dir / "custom.toml"
        config_path.write_text(
            """
[scoring]
scale_points_total = 20
minimum_passing_score = 15

[categories.discoverability]
enabled = true
max_points = 3
"""
        )

        config = load_config(config_path)
        assert config.scale_points_total == 20
        assert config.minimum_passing_score == 15
        assert config.categories["discoverability"].max_points == 3


class TestParseConfig:
    """Tests for parse_config function."""

    def test_parse_empty_config(self) -> None:
        config = parse_config({})
        assert isinstance(config, AuditConfig)
        assert config.scale_points_total == 16

    def test_parse_scoring_section(self) -> None:
        data = {
            "scoring": {
                "scale_points_total": 24,
                "minimum_passing_score": 18,
            }
        }
        config = parse_config(data)
        assert config.scale_points_total == 24
        assert config.minimum_passing_score == 18

    def test_parse_categories_section(self) -> None:
        data = {
            "categories": {
                "discoverability": {
                    "enabled": False,
                    "max_points": 4,
                    "description": "Custom description",
                }
            }
        }
        config = parse_config(data)
        assert not config.categories["discoverability"].enabled
        assert config.categories["discoverability"].max_points == 4

    def test_parse_checks_section(self) -> None:
        data = {
            "checks": {
                "readme_exists": {
                    "enabled": False,
                    "weight": 2.0,
                }
            }
        }
        config = parse_config(data)
        assert not config.checks["readme_exists"].enabled
        assert config.checks["readme_exists"].weight == 2.0

    def test_parse_detection_section(self) -> None:
        data = {
            "detection": {
                "readme_filenames": ["README.md", "readme.txt"],
                "ci_paths": [".github/workflows"],
            }
        }
        config = parse_config(data)
        assert config.detection.readme_filenames == ["README.md", "readme.txt"]
        assert config.detection.ci_paths == [".github/workflows"]


class TestGenerateDefaultConfig:
    """Tests for generate_default_config function."""

    def test_generates_valid_toml(self) -> None:
        content = generate_default_config()
        assert "[scoring]" in content
        assert "[categories]" in content
        assert "[checks]" in content
        assert "[detection]" in content

    def test_config_is_parseable(self, temp_dir: Path) -> None:
        content = generate_default_config()
        config_path = temp_dir / "test.toml"
        config_path.write_text(content)

        config = load_config(config_path)
        assert isinstance(config, AuditConfig)
