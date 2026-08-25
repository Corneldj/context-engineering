# **`ce` — A Runnable Reference Harness**

A small, **dependency-free** implementation of the techniques this course teaches. Standard library only, Python 3.10+. No API key, no install, no network.

```bash
cd code
python3 -m unittest discover -s tests -t .    # 134 tests
python3 examples/03_agent_loop.py             # any example
```

---

## **Why this exists**

A course about engineering harnesses, illustrated only by snippets, asks you to take its claims on faith. This package makes them **executable and falsifiable**.

Every guardrail in Module 8 has a test that fails if the guardrail is removed. The test suite *is* the course's argument, in a form that can be wrong:

| Claim | Test |
| :--- | :--- |
| A loop must not terminate on the model's self-report | `test_the_model_saying_it_is_done_is_not_enough` |
| Building such a loop should be refused outright | `test_building_a_self_report_loop_is_refused_at_construction` |
| Tool errors must never raise into the loop | `test_tool_failure_never_raises_out_of_the_loop` |
| A stuck loop must stop immediately, not eventually | `test_a_stuck_loop_stops_immediately_not_eventually` |
| Injection is a capability amplifier | `test_injected_instructions_cannot_amplify_absent_capability` |
| Context must be dropped by value, not by age | `test_drops_by_value_not_by_age` |
| A mislabelled-stable value silently kills your cache | `test_a_timestamp_mislabelled_static_is_caught_across_turns` |
| Externalized state survives compaction | `test_externalized_state_survives_compaction` |
| A 20-case eval set cannot detect a 10% change | `test_small_eval_sets_announce_their_own_uselessness` |
| 80% judge agreement can mean zero signal | `test_a_judge_that_always_says_pass_scores_zero_despite_looking_accurate` |
| An undeclared edge type must be refused, not coerced | `test_undeclared_edge_type_is_refused` |
| Superseding a fact must not destroy history | `test_supersede_preserves_history` |
| A correction moves the world clock, not the belief clock | `test_correction_changes_the_world_clock_not_the_belief_clock` |
| A side effect must not repeat when the checkpoint never wrote | `test_effect_does_not_repeat_when_the_checkpoint_never_wrote` |
| A held-out gate catches an optimizer fitting your evaluator | `test_fitting_the_held_in_split_is_caught` |
| Catastrophic forgetting hides behind an improving mean | `test_catastrophic_forgetting_hides_behind_the_mean` |
| A frozen-surface proposal never reaches evaluation | `test_a_frozen_proposal_never_reaches_evaluation` |
| A fact sharing no vocabulary with the query is reachable only through the graph | `test_recall_reaches_it_through_the_graph` |
| A superseded fact's vector must be kept and filtered, not deleted | `test_as_of_queries_still_find_the_superseded_fact` |
| Write cost must not grow with corpus size | `test_write_cost_is_independent_of_corpus_size` |

---

## **Running offline**

`MockModel` is scriptable and deterministic, so the whole package runs with no API key:

```python
from ce import AgentLoop, MockModel, ToolRegistry, Deterministic, Guardrails, call, say

model = MockModel(script=[call("run_tests"), say("fixed it")])
loop  = AgentLoop(
    model=model,
    tools=my_tools,
    verifier=Deterministic(lambda s: tests_pass(), "test suite passes"),
    guardrails=Guardrails(max_iterations=10, max_tokens=200_000),
)
outcome = loop.run("Fix the failing test.")
print(outcome, outcome.trace.render())
```

This is not a convenience. **A harness you can only observe by spending money on a live API is a harness you cannot test** — and an untested harness is where the failures in Module 8, Lesson 1 come from. To use a real model, implement the three-method `Model` protocol in `ce/model.py`.

---

## **Map**

| Module | Implements | Course reference |
| :--- | :--- | :--- |
| `tokens.py` | Token counting; pluggable tokenizer | M1 L2, M4 L1 |
| `model.py` | `Model` protocol, deterministic `MockModel` | — |
| `context.py` | Budgeted, cache-aware assembly; cross-call prefix audit; edge-loading | M1 L2, M4 L1, M8 L4 |
| `tools.py` | Schemas as prompt surface, actionable errors, result sizing | M5 L2 |
| `compaction.py` | Compaction policy and prompt; stale tool-result clearing | M4 L4 |
| `workspace.py` | File-backed structured note-taking | M4 L4 |
| `verify.py` | Verification tiers; refusal to trust self-report | M8 L2 |
| `loop.py` | The agent loop and its five guardrails | M8 L1, L2 |
| `trace.py` | OTel-shaped spans, token/cost accounting, thrashing detection | M6 L2 |
| `evals.py` | Trajectory scoring, eval-set sizing, judge calibration | M6 L1 |
| `graph.py` | Typed edges, ontology gate, bi-temporal validity, confidence decay | M9 L1–L2 |
| `execgraph.py` | Nodes, typed state, routing, checkpointing, interrupts, idempotency | M9 L4 |
| `vectorgraph.py` | Continuous vector memory graph: hash embedder, entry→expand→filter→rank, invalidation-aware recall, mutation-point refresh | M9 L3 |
| `metaharness.py` | Weakness mining, bounded edits, held-out gate, frozen surfaces, archive | M9 L6–L7 |

---

## **Examples**

| File | Shows |
| :--- | :--- |
| `01_context_and_cache.py` | Stable→volatile ordering; a mislabelled timestamp killing the cache; dropping by value; edge-loading |
| `02_tools_and_errors.py` | A useless error vs. an actionable one; loud truncation; what a tool set costs per turn |
| `03_agent_loop.py` | **The same model, two harnesses** — victory declaration bias, then verified success; all three guardrails firing |
| `04_long_horizon.py` | Clearing stale tool results; compaction preserving dead ends; surviving a crash at file 300 |
| `05_evaluation.py` | Two trajectories with identical answers scoring differently; eval-set sizing; 80% agreement at zero kappa |
| `06_security.py` | The lethal trifecta — same injection, five capability configurations |
| `07_graphs.py` | The ontology gate; bi-temporal correction; absence queries; the *p*ⁿ table |
| `08_execution_graph.py` | A human gate that suspends for days; **a duplicate charge, with and without the ledger**; the stop rule |
| `09_meta_harness.py` | Weakness mining by mechanism; a **reward hack caught by per-category tracking**; diversity collapse |
| `10_vector_memory_graph.py` | Pure vector vs entry+expand on a zero-overlap query; **vectors outliving truth**; the embed-on-write cost table |

---

## **Exercises and labs**

| Directory | What it is |
| :--- | :--- |
| [`exercises/`](./exercises/) | **Ten auto-graded exercises.** Skeletons you implement; `python3 exercises/check.py` grades them with the same tests CI runs against the reference solutions. CI also asserts the *skeletons* fail — no exercise is vacuous. |
| [`labs/`](./labs/) | **Six optional live-model labs.** What `MockModel` deliberately hides: real non-determinism, real cache counters, a live model under injection. Needs an API key; exits cleanly without one. |
| [`../tools/validate_course.py`](../tools/validate_course.py) | Every check that gates a change to this repo, in one command. |

---

## **Honest limitations**

This is a teaching implementation. It is deliberately small, and you should know where it stops:

* **Token counting is an estimate** (~4 chars/token). Install a real tokenizer via `tokens.set_counter()` before making cost decisions.
* **Cache accounting is modelled, not measured.** Real providers report cache reads in the API response; use those numbers.
* **The context assembler has no retrieval.** Retrieval strategy is a Module 3 concern and deliberately out of scope here.
* **No async, no streaming, no concurrency.** Sub-agents (Module 8, Lesson 3) are not implemented, and `StateGraph` runs nodes sequentially — real parallel fan-out is a good exercise.
* **The graph is in-memory and unindexed.** Traversal is a depth-first walk over a list of edges. Fine for teaching and for a few thousand edges; use a real graph store beyond that.
* **Entity resolution is not implemented at all.** `Graph` assumes you hand it resolved node ids — which is convenient, and is also precisely the step that dominates real accuracy (Module 9, Lesson 1). The confidence machinery lets you *model* imperfect resolution; it does not perform it.
* **`ce.adapters` is the one networked file**, and it is deliberately not imported by `import ce` — the package stays offline and dependency-free. The labs import it explicitly.
* **`MetaHarness` does not propose edits.** You supply the proposer. The package implements the *governance* — the gate, the frozen set, the archive — because that is the part the lesson argues people skip.
* **`ContextAssembler` enforces *declared* stability.** It catches a mislabelled section by noticing the prefix changed between turns, which requires at least two turns. It cannot know on turn one that you lied.
* **Trajectory scoring is heuristic.** Cheap deterministic signals only, no model judge. `result_utilization` is deliberately left `None` — it genuinely needs a judge or a human.

If you extend it, extend the tests first. That is the habit the course is really teaching.
