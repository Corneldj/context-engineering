"""Exercise 09 — Invalidate, never delete. Correct without destroying history.

Lesson: Module 9 Lesson 2 §3.

The test hands you a graph where Team A has owned a service since t=0.
Implement two operations:

  record_transfer(g, service, from_team, to_team, at)
      The service changes hands at `at`. Close the old edge, open the new one.
      Afterwards ALL THREE questions must answer correctly:
        - what is true now
        - what was true before `at`
        - and nothing was deleted.

  correct_transfer(g, service, from_team, to_team, actual_at, discovered_at)
      Later you learn the transfer really happened at `actual_at`. Move the
      WORLD clock on both edges; the BELIEF clock must record that you only
      found out at `discovered_at` — "what did we believe before the
      correction?" must still be answerable.

Hints: `g.invalidate(...)` returns the closed edge (your old reference is
stale after mutation — Lesson 2's sharp edge), and `g.correct(...)` takes
`actual_t_valid` and/or `actual_t_invalid`.

Grade with:  python3 exercises/check.py ex09
"""

from ce import Graph


def record_transfer(g: Graph, service: str, from_team: str, to_team: str, at: int):
    raise NotImplementedError


def correct_transfer(g: Graph, service: str, from_team: str, to_team: str,
                     actual_at: int, discovered_at: int):
    raise NotImplementedError
