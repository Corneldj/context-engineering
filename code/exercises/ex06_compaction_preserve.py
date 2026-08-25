"""Exercise 06 — Shrink a trajectory without losing what matters.

Lesson: Module 4 Lesson 4 §2–§3.

Implement `shrink(messages, budget)` -> a smaller message list where:

  1. the FIRST user message (the goal) survives verbatim,
  2. every message containing a dead end ("TRIED:") survives,
  3. every message containing an incident id (INC-<digits>) survives —
     exact identifiers must never be paraphrased away,
  4. stale tool results are cleared first — `ce.clear_stale_tool_results`
     exists precisely for this; keep the 2 most recent,
  5. if still over budget, plain assistant chatter goes, oldest first,
  6. total tokens (ce.tokens.count over contents) end up <= budget.

The order matters: do the free, lossless step (4) before dropping anything.

Grade with:  python3 exercises/check.py ex06
"""


def shrink(messages: list[dict], budget: int) -> list[dict]:
    raise NotImplementedError("clear stale tool results first, then drop by value")
