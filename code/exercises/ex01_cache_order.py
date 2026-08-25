"""Exercise 01 — Cache-aware, budgeted context assembly.

Lessons: Module 1 Lesson 2 §4 · Module 4 Lesson 1 §4 · Module 8 Lesson 4 §2.

Implement `build_sections`, which turns one turn's raw materials into a list of
`ce.Section` objects ready for `ContextAssembler.assemble()`.

The materials, per turn:
    system_prompt: str      — never changes between turns
    tool_schemas:  str      — never changes between turns
    conventions:   str      — durable project memory, changes rarely
    documents:     str      — retrieved for THIS request
    chatter:       str      — low-value recent small talk
    goal:          str      — the user's original goal; must NEVER be dropped
    timestamp:     str      — changes every turn
    task:          str      — the immediate instruction

Get the stability tiers, values, and droppability right so that:
  * the stable prefix is byte-identical across turns (the timestamp must not
    poison it),
  * when the budget squeezes, chatter dies before anything else and the goal
    survives everything,
  * the task lands last.

Grade with:  python3 exercises/check.py ex01
"""

from ce import Section, Stability


def build_sections(
    *, system_prompt: str, tool_schemas: str, conventions: str,
    documents: str, chatter: str, goal: str, timestamp: str, task: str,
) -> list[Section]:
    raise NotImplementedError("build the Section list — see the docstring")
