"""OpenAI Structured Outputs compatible JSON Schema conversion."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from climate_cascade.domain import BaselineActionResponse, ResponseSupervisorActionResponse


def baseline_response_schema() -> dict[str, Any]:
    """Require every object property and encode optional values as explicit nulls."""

    schema = deepcopy(BaselineActionResponse.model_json_schema())
    _make_strict(schema)
    return schema


def response_supervisor_response_schema() -> dict[str, Any]:
    """Schema for cited drafts that may abstain but cannot claim numeric life-safety values."""

    schema = deepcopy(ResponseSupervisorActionResponse.model_json_schema())
    _make_strict(schema)
    return schema


def _make_strict(node: object) -> None:
    if isinstance(node, list):
        for item in node:
            _make_strict(item)
        return
    if not isinstance(node, dict):
        return

    node.pop("default", None)
    properties = node.get("properties")
    if isinstance(properties, dict):
        node["required"] = list(properties)
    for value in node.values():
        _make_strict(value)
