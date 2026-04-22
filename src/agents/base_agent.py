"""Base class for all underwriting agents."""
from __future__ import annotations

import json
import os
from typing import Any

import anthropic

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-7")


class BaseAgent:
    """
    Wraps a Claude API call with a cached system prompt.
    Subclasses define their system prompt and use _call_structured() to
    force Claude to return data conforming to a tool schema.
    """

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = anthropic.Anthropic()

    def _call_structured(
        self,
        user_message: str,
        tool_name: str,
        tool_description: str,
        tool_schema: dict[str, Any],
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """
        Call Claude with a single forced tool to get structured output.
        The system prompt is cache_control-marked so it's cached after the
        first request to this agent within the TTL window.
        """
        tool_def = {
            "name": tool_name,
            "description": tool_description,
            "input_schema": tool_schema,
        }

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": self.system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[tool_def],
            tool_choice={"type": "tool", "name": tool_name},
            messages=[{"role": "user", "content": user_message}],
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                return block.input  # type: ignore[return-value]

        return {}

    def _format_currency(self, amount: float) -> str:
        return f"₹{amount:,.0f}"
