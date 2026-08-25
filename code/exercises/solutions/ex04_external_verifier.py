"""Reference solution for exercise 04."""

from ce import AgentLoop, Deterministic, Guardrails, ToolRegistry


def make_loop(model, registry: ToolRegistry, world: dict) -> AgentLoop:
    return AgentLoop(
        model=model,
        tools=registry,
        # The verifier checks the WORLD. The model's opinion of its own work
        # is never consulted.
        verifier=Deterministic(lambda s: world.get("deployed", False),
                               "deployment observed in the world"),
        guardrails=Guardrails(
            max_iterations=5,
            no_progress_after=2,     # a talker changes nothing; stop it fast
            max_tool_errors=3,
        ),
    )
