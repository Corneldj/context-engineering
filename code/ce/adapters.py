"""Live-model adapters — the only file in `ce` that touches a network.

Everything else in this package runs offline against `MockModel`, deliberately:
a harness you can only observe by spending money is a harness you cannot test.
This adapter is the documented bridge to reality for the labs in `code/labs/`.

Requires the optional dependency:  pip install anthropic
and an ANTHROPIC_API_KEY in the environment.

Design notes:
* `AnthropicModel` implements the same three-argument `Model` protocol the
  whole package is built on, so `AgentLoop`, `JudgeModel`, and the eval harness
  run unchanged against a live model.
* Our tool schemas ({name, description, input_schema}) are already the wire
  format, so tools pass through untouched.
* `last_usage` keeps the raw usage block from the most recent call — the labs
  read real cache_creation/cache_read token counts from it, which is the only
  honest way to verify the cache-ordering claims from Module 1, Lesson 2.
"""

from __future__ import annotations

import os
from typing import Any, Sequence

from .model import ModelResponse, ToolCall

DEFAULT_MODEL = os.environ.get("CE_LAB_MODEL", "claude-haiku-4-5-20251001")


class AnthropicModel:
    """The `Model` protocol, backed by the Anthropic API."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        max_tokens: int = 1024,
        temperature: float | None = None,
        cache_system_prompt: bool = True,
    ) -> None:
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError(
                "The live labs need the optional dependency: pip install anthropic"
            ) from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not set — see code/labs/README.md")
        self.client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.cache_system_prompt = cache_system_prompt
        self.last_usage: Any = None
        self.calls = 0

    def generate(
        self,
        *,
        system: str,
        messages: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]] = (),
    ) -> ModelResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": list(messages),
        }
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        if system:
            if self.cache_system_prompt:
                # A cache breakpoint after the stable system prompt — the
                # ordering discipline from Module 1, Lesson 2 §4, on the wire.
                kwargs["system"] = [{
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }]
            else:
                kwargs["system"] = system
        if tools:
            kwargs["tools"] = list(tools)

        response = self.client.messages.create(**kwargs)
        self.last_usage = response.usage
        self.calls += 1

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(id=block.id, name=block.name,
                                           arguments=dict(block.input)))

        return ModelResponse(
            text="".join(text_parts),
            tool_calls=tuple(tool_calls),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            stop_reason=response.stop_reason or "end_turn",
        )

    # -- lab conveniences ---------------------------------------------------

    def cache_report(self) -> str:
        """The real cache meter, from the last call's usage block."""
        u = self.last_usage
        if u is None:
            return "no calls yet"
        created = getattr(u, "cache_creation_input_tokens", 0) or 0
        read = getattr(u, "cache_read_input_tokens", 0) or 0
        return (f"input={u.input_tokens} cache_write={created} "
                f"cache_read={read} output={u.output_tokens}")


def require_key_or_exit(lab_name: str, est_cost: str) -> None:
    """Preflight for every lab: no key means a clean, zero-cost exit."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        print(f"[{lab_name}] model={DEFAULT_MODEL}  estimated cost: {est_cost}\n")
        return
    print(
        f"[{lab_name}] ANTHROPIC_API_KEY is not set.\n"
        f"  This lab calls a live model (estimated cost {est_cost}).\n"
        f"  export ANTHROPIC_API_KEY=... and re-run. See code/labs/README.md."
    )
    raise SystemExit(0)
