"""Reference solution for exercise 05."""

from ce import Guardrails


def unattended_guardrails() -> Guardrails:
    return Guardrails(
        max_iterations=25,        # hard cap, always present
        max_tokens=150_000,       # the cost ceiling — catches the runaway
        max_tool_errors=5,        # circuit breaker
        no_progress_after=3,      # catches the stuck loop IMMEDIATELY
    )
