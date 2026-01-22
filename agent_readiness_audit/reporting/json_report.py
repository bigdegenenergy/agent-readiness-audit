"""JSON report generation for Agent Readiness Audit."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from agent_readiness_audit.models import RepoResult, ScanSummary


def serialize_datetime(obj: Any) -> Any:
    """JSON serializer for datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def render_json_report(summary: ScanSummary) -> str:
    """Render scan summary as JSON.

    Args:
        summary: Scan summary to render.

    Returns:
        JSON string representation.
    """
    data = summary.model_dump(mode="json")
    return json.dumps(data, indent=2, default=serialize_datetime)


def render_repo_json(result: RepoResult) -> str:
    """Render single repo result as JSON.

    Args:
        result: Repository result to render.

    Returns:
        JSON string representation.
    """
    data = result.model_dump(mode="json")
    return json.dumps(data, indent=2, default=serialize_datetime)
