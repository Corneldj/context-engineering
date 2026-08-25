"""Exercise 05 — Guardrails that make runaway impossible.

Lesson: Module 8 Lesson 2 §5.

Implement `unattended_guardrails()` for a loop that runs overnight with nobody
watching. The tests throw three pathological models at it:

  * a STUCK one (same non-answer forever)   -> stopped by no-progress, ≤6 iterations
  * a THRASHING one (same tool forever)     -> stopped well before 40 iterations
  * a RUNAWAY one (huge outputs)            -> stopped by the token budget
                                               before 200k total tokens

Remember the asymmetry: cost caps stop a runaway loop EVENTUALLY; no-progress
detection stops a stuck loop IMMEDIATELY. You need both.

Grade with:  python3 exercises/check.py ex05
"""

from ce import Guardrails


def unattended_guardrails() -> Guardrails:
    raise NotImplementedError("bound iterations, tokens, tool errors, and progress")
