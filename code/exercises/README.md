# **Exercises**

Ten auto-graded exercises. Each is a skeleton you complete; the tests that grade you are the same ones the course's CI runs against the reference solutions — **if it passes here, it passes.**

```bash
cd code
python3 exercises/check.py          # grade everything
python3 exercises/check.py ex04     # grade one
```

Work them after the lesson they belong to. The docstring at the top of each skeleton names the lesson and states the contract; the tests state it precisely.

| Exercise | You implement | Lesson | The point |
| :--- | :--- | :--- | :--- |
| `ex01_cache_order` | The Section list for one turn | M1 L2 · M4 L1 · M8 L4 | A timestamp above the stable prefix silently costs you the cache; the goal survives any budget; the task goes last |
| `ex02_actionable_errors` | A customer-lookup tool pair | M5 L2 | `"Not found"` teaches the agent nothing — return the near-miss and the fallback |
| `ex03_tool_schema` | The pruned 4-tool registry | M5 L2 | Cross-referencing descriptions, closed enums, exactly one destructive tool |
| `ex04_external_verifier` | A loop that checks the world | M8 L1–L2 | The liar model claims "Deployed!" — your verifier must not care what it *says* |
| `ex05_guardrails` | Guardrails for overnight runs | M8 L2 | Stuck, thrashing, and runaway models each hit a *different* stop |
| `ex06_compaction_preserve` | `shrink(messages, budget)` | M4 L4 | Clear stale tool results first (free); dead ends and exact identifiers never drop |
| `ex07_judge_rubric` | A 4-point grounding rubric | M6 L1 | Binary, textually verifiable checks — the difference between kappa 0.3 and a usable judge |
| `ex08_ontology` | Ontology + incident graph | M9 L1–L2 | Declare types first; the gate refuses junk; answer a traversal and an absence query |
| `ex09_bitemporal` | Transfer + correction | M9 L2 | Both clocks: what was true, and what we believed — nothing deleted, ever |
| `ex10_heldout_gate` | Gate + editable surfaces | M9 L6–L7 | Net-flipped-cases thresholds; the reward hack caught; the schema stays frozen |

**Stuck?** Reference solutions live in [`solutions/`](./solutions/) — the same deal as the lesson SOLUTIONS files: they teach most if you attempt first. `check.py` never looks at them; your grade comes from your files.

**How grading works** (it's the course practicing its own doctrine): tests import your code via `exercises/_loader.py`, which honors `EXERCISE_IMPL_DIR`. CI sets that to `solutions/` and requires 10/10 — proving every exercise is solvable — and separately requires that the *skeletons* do **not** pass, proving no exercise is vacuous.
