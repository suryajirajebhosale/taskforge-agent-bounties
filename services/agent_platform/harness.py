"""Listing harness: process contract (tools/models) hashed onto jobs."""

from __future__ import annotations

import hashlib
import json

DEFAULT_HARNESS: dict = {
    "models_allow": ["gpt-4.1-mini", "claude-haiku"],
    "tools_allow": ["http.fetch", "hunter.email"],
    "tools_deny": ["browser.unrestricted", "db.write"],
    "memory": "none",
    "live_sample_rate": 0.05,
    "max_tool_calls": 8,
}


def merge_harness(override: dict | None = None) -> dict:
    merged = dict(DEFAULT_HARNESS)
    if override:
        merged.update(override)
    return merged


def harness_hash(harness: dict) -> str:
    blob = json.dumps(harness, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def check_trace(harness: dict, trace: dict | None) -> str:
    """Fail closed on Hire: undeclared or denied tools. Returns digest of the trace."""
    if not isinstance(trace, dict) or "tools_used" not in trace:
        raise ValueError("hire jobs require a trace with tools_used")
    tools = trace["tools_used"]
    if not isinstance(tools, list):
        raise ValueError("tools_used must be a list")
    deny = set(harness.get("tools_deny") or [])
    allow = set(harness.get("tools_allow") or [])
    max_calls = int(harness.get("max_tool_calls") or 8)
    if len(tools) > max_calls:
        raise ValueError(f"tool call cap {max_calls} exceeded")
    for tool in tools:
        if tool in deny or (allow and tool not in allow):
            raise ValueError(f"undeclared or denied tool: {tool}")
    return harness_hash(trace)
