"""Exercise 10 — Gate a self-improvement loop so it cannot fool you.

Lessons: Module 9 Lesson 6 §3 · Lesson 7 §1–§3.

Implement two functions:

  make_gate(held_out_n)
      A HeldOutGate whose minimum gain is denominated in NET FLIPPED CASES
      (at least 3), not an optimistic percentage — 0.5% on a 200-case split is
      one lucky case. `HeldOutGate.for_split` exists for exactly this.

  editable_surfaces()
      The frozenset of surfaces your optimizer may touch for the
      document-extraction agent. It must include the genuinely useful ones
      (system_prompt, workflow, retry_policy) and must be constructible into a
      MetaHarness — meaning nothing from the frozen set (eval_data,
      permissions, budget, logging, ...) may appear in it. The test also
      checks you did NOT expose the output schema: loosening the spec until
      every failure passes is how reward hacking starts.

Grade with:  python3 exercises/check.py ex10
"""

from ce import HeldOutGate


def make_gate(held_out_n: int) -> HeldOutGate:
    raise NotImplementedError("denominate min_gain in net flipped cases")


def editable_surfaces() -> frozenset[str]:
    raise NotImplementedError("useful surfaces only; nothing the optimizer could cheat with")
