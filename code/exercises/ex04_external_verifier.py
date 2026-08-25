"""Exercise 04 — The loop must not take the model's word for it.

Lesson: Module 8 Lesson 2 §4 · Module 8 Lesson 1 §2 (victory declaration bias).

You get a world (a dict), a registry whose `deploy` tool mutates it, and a
model. Implement `make_loop` so the ONLY way the loop reports success is the
world actually changing:

  * a Deterministic verifier that checks `world["deployed"]` — not the transcript,
  * guardrails that stop a non-acting model quickly (≤5 iterations),
    with no_progress detection doing the stopping.

The test runs two models against your loop: one that confidently claims
"Deployed!" without ever calling the tool, and one that does the work. Your
configuration must tell them apart.

Grade with:  python3 exercises/check.py ex04
"""

from ce import AgentLoop, ToolRegistry


def make_loop(model, registry: ToolRegistry, world: dict) -> AgentLoop:
    raise NotImplementedError("a Deterministic verifier over `world`, plus tight guardrails")
