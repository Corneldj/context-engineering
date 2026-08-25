# **Changelog**

## **2026 Edition**

The field reorganized between 2023 and 2026. This edition follows that reorganization rather than appending to the old structure.

### **The Structural Change**

**Retired: Context Window Architecture (CWA).** The previous edition closed with an 11-layer model prescribing the ideal ordering of a single prompt. That answered a 2023-shaped question. Agents don't have one prompt — they assemble context dozens of times per task, across sub-agents with separate windows, over sessions that outlive any single window.

**Added: Module 8, Agentic Engineering** — a full module in its place, covering the harness, loop engineering, structuring AI teams, and a six-plane **Agentic Architecture** that organizes every technique in the course.

CWA's surviving insight — that context assembly is a deliberate design act rather than string concatenation — is now the Context plane of that model, updated for prompt caching and agent loops.

### **New Lessons**

| Lesson | Why |
| :--- | :--- |
| **1.4 The Four Disciplines** | The course now has a spine — prompt → context → harness → loop — and learners need the map early |
| **3.5 Agentic Retrieval** | Grep-based agentic search displaced vector RAG for code in 2025–2026. Choosing between them is now a core skill |
| **4.4 Long-Horizon Context** | Compaction, structured note-taking, sub-agent isolation, and just-in-time retrieval — the techniques that keep hours-long agents coherent |
| **5.4 MCP and Agent Skills** | MCP became ubiquitous and went stateless; Agent Skills became an open standard with progressive disclosure |
| **8.1 The Harness** | `Agent = Model + Harness`. Most production failures are harness failures |
| **8.2 Loop Engineering** | The shift from prompting agents to building systems that prompt agents |
| **8.3 Structuring AI Teams** | Orchestration patterns, handoff contracts, and the human roles that appeared alongside them |
| **8.4 Agentic Architecture** | The unifying capstone that replaces CWA |

### **Substantially Revised**

*   **1.1** — Explicit prompt-engineering vs. context-engineering distinction; expanded context components (memory, task state, tool results).
*   **1.2** — Agent-scale token economics, prompt caching (including the stable-to-volatile ordering rule), and model routing. The napkin-math exercise now costs an agent run with and without caching.
*   **1.3** — Added **Altitude** as a fifth design principle; new exercise on fixing an over-specified prompt.
*   **2.1** — The system prompt as a trust boundary; what does *not* belong in a prompt; positive over negative instructions.
*   **2.2** — When examples hurt: reasoning models, output capping, and where a schema is strictly better.
*   **2.3** — Native reasoning vs. explicit CoT; the ceiling on self-critique; schema-enforced structured output replacing "JSON mode"; decomposition for localizability.
*   **3.1** — RAG positioned as one grounding strategy among several.
*   **3.2** — Added **contextual retrieval** and structure-aware chunking.
*   **3.3** — Hybrid search as the recommended default, with Reciprocal Rank Fusion.
*   **4.1** — The context-rot research (18 models), the attention-budget framing, effective context at 60–70% of nominal, edge-loading, and code-enforced token budgets.
*   **4.3** — Replaced the Focused Transformer section, which was both dated and inaccurately described, with contextual retrieval, query transformation (multi-query, HyDE), and late-interaction retrievers — plus an explicit priority order for where to spend effort.
*   **5.1** — Agent vs. workflow ("if you can draw the flowchart, build the flowchart"); ReAct's weak stopping condition named.
*   **5.2** — Tool-set bloat and its diagnostic; actionable error design; token-efficient tool results; tool descriptions as prompt surface.
*   **5.3** — Current framework landscape; plan-act-replan; a minimal agent loop written out; how to adopt a framework without marrying it.
*   **6.1** — Trajectory evaluation across six dimensions; LLM-judge calibration and bias; eval set sizing.
*   **6.2** — OpenTelemetry GenAI conventions; the four agent failure patterns visible in a trace; the divergence-point debugging procedure.
*   **6.3** — Rewritten around **indirect** prompt injection and the **lethal trifecta**, separating defenses that reduce likelihood from those that contain damage. Red-team evals in CI.
*   **7.1** — Extended to computer-using agents and the security cost of visual context.
*   **7.2** — Rewritten: the reliability race, the four-standard interoperability stack, agentic search, meta-agents, and portable observability.
*   **7.3** — Extended from generation ethics to **autonomy ethics**: named accountability, meaningful versus rubber-stamped oversight, error at scale, and displacement.

### **Corrections**

*   **Focused Transformer (FoT)** was described as a contrastive method for improving embeddings. That mischaracterized the technique, and it was never widely adopted in production RAG. Removed.
*   **"Needle in a haystack"** was presented as the state of the art in long-context evaluation. It is now understood as a weak test — passing it does not imply reliable reasoning over long context. Reframed, with the real degradation research in its place.
*   **JSON mode** was presented as guaranteeing valid JSON. Superseded by schema-enforced structured output, which is a categorical improvement rather than an incremental one.
*   **Autogen** was listed as a current multi-agent framework. It was absorbed into the Microsoft Agent Framework.
*   **Delimiters as an injection defense** were presented without the caveat that prompt-level defenses fail against adaptive attackers. Corrected in 1.3 and 6.3.

### **New Supporting Files**

*   **REFERENCES.md** — primary sources, with a note on which figures to trust and which to treat as directional.
*   **CHANGELOG.md** — this file.
*   **GLOSSARY.md** — substantially expanded; superseded terms retained and marked *(historical)* so older material stays readable.

---

## **2026 Edition, revision 2 — Making the Course Runnable**

The taught material was sound but unverifiable: 40 illustrative code snippets and nothing you could execute. A course about **engineering** should let you run the thing it describes and watch it fail when you break it.

### **`code/` — a dependency-free reference harness**

Standard library only, Python 3.10+, no API key. `MockModel` makes the whole package deterministic and offline — not for convenience, but because *a harness you can only observe by spending money on a live API is a harness you cannot test*.

| Module | Implements |
| :--- | :--- |
| `context.py` | Budgeted, cache-aware assembly; cross-call prefix audit; edge-loading |
| `tools.py` | Schemas as prompt surface, actionable errors, result sizing |
| `loop.py` | The agent loop and its five guardrails |
| `compaction.py` | Compaction policy and prompt; stale tool-result clearing |
| `workspace.py` | File-backed structured note-taking |
| `verify.py` | Verification tiers; refusal to build a self-report loop |
| `trace.py` | OTel-shaped spans, cost accounting, thrashing detection |
| `evals.py` | Trajectory scoring, eval-set sizing, judge calibration |

**57 tests.** Each guardrail claim in Module 8 has a test that fails if the guardrail is removed — the test suite is the course's argument in falsifiable form.

**Six runnable examples**, including `03_agent_loop.py` (the same model under two harnesses: victory declaration bias, then verified success) and `06_security.py` (one injection, five capability configurations).

### **Three things the code found wrong in the prose**

Writing the implementation falsified three claims the lessons implied:

*   **A cache-order guard that could never fire.** The lessons frame the cache bug as "don't put volatile content above stable content" — which sorting trivially fixes, so the guard was dead code. The bug that *actually* happens is a volatile value **mislabelled** as stable, which ordering cannot detect. `ContextAssembler` now audits the prefix across calls and notices it is no longer byte-identical. Module 4's guidance is sharper as a result.
*   **Thrashing detection keyed on the wrong thing.** Keying on tool *arguments* misses the real case — three rephrasings of a query are three genuinely different calls returning the same result. Keying on the tool *name* over-fires on an agent legitimately reading ten files. Keying on **tool-plus-result** is correct. Corrected in Module 6, Lesson 2.
*   **Half-reported argument errors.** A typo like `e_mail` for `email` is simultaneously a missing argument and an unknown one; reporting only the first makes the agent add `email` while still sending `e_mail`. Two turns wasted on one typo. `ToolRegistry` reports both, and Module 5, Lesson 2 now says so.

### **Practitioner references**

*   **CHEATSHEET.md** — every decision the course asks you to make, on one page, plus the numbers worth remembering.
*   **ANTI_PATTERNS.md** — a diagnostic reference organized by **symptom** rather than topic, because when something is wrong you know what you're seeing, not what chapter it's in. Fourteen failure modes, each with the fix that works and the fix people reach for first that doesn't.
*   **INDEX.md** — concept → lesson → implementation.
*   **templates/** — architecture spec, eval set, red-team cases, tool spec, compaction prompt, and AGENTS.md skeleton.

### **Course logistics**

*   Every module README now states **learning outcomes**, a **time estimate** (28–35 hours total), and a **Check yourself** set with section references.
*   README gained **prerequisites** and three **learning paths** — building, debugging, or learning the field properly.

### **Accessibility**

*   All 19 Mermaid diagrams carry `accTitle` and `accDescr`, so screen readers get a real description rather than silence. Validated against the Mermaid parser.
*   Fixed a pre-existing diagram in Module 5, Lesson 1 that failed to parse (unquoted `"Cupertino, CA"` in a node label), and quoted several node labels containing parentheses.

---

## **2026 Edition, revision 3 — Module 9**

Added **Module 9: Graph Engineering and Autonomous Meta-Harness Systems**, and rewrote the Final Project to cover the full nine-module course.

### **The through-line**

The two halves of Module 9 look unrelated and are not. The bridge is one sentence: **a system can only safely rewrite what is explicit.** Graphs are how structure — knowledge, memory, control flow — becomes inspectable. Meta-harness systems are what inspects and edits it. A control flow buried in a `while` loop cannot be meaningfully improved by anything, human or otherwise.

### **Lessons**

| Lesson | Covers |
| :--- | :--- |
| **9.1 Graph Engineering** | The three distinct things called "graph engineering"; typed edges; when a graph earns its cost; the *p*ⁿ arithmetic that kills graph projects |
| **9.2 Knowledge and Memory Graphs** | GraphRAG vs vector RAG by hop count; the nine-stage pipeline; bi-temporal validity and its four timestamps; routing across three retrieval primitives |
| **9.3 Execution Graphs** | Nodes, typed state, routing as a pure function; durable execution; the four task-graph patterns; the stop rule |
| **9.4 Autonomous Meta-Harness Systems** | The three tiers; the optimization ladder; propose-evaluate-accept; the held-out gate; Pareto frontiers; what the published results actually show |
| **9.5 Governing Self-Modifying Systems** | **Harness updating is not harness benefit**; reward hacking, diversity collapse, catastrophic forgetting; the frozen set; the maturity ladder |

Lesson 5 is the sceptical one and the most important. There is substantial 2026 work showing that most self-improvement gains do not survive contact with an evaluator the system did not optimize against — and a system reporting its own improvement will do so sincerely, because your evaluator is its entire definition of "better."

### **New runnable code**

| Module | Implements |
| :--- | :--- |
| `ce/graph.py` | Typed edges with a closed vocabulary, ontology enforcement as a quality gate, bi-temporal validity (`supersede`, `correct`, invalidate-never-delete), confidence-decaying traversal, absence queries |
| `ce/execgraph.py` | Nodes, typed state, declared routing, checkpointing, interrupts that genuinely suspend, and a **durable idempotency ledger** |
| `ce/metaharness.py` | Weakness mining by mechanism, bounded edits, the held-out acceptance gate, frozen surfaces enforced at runtime, a diversity-tracking archive, Pareto frontier |

**52 new tests** (109 total), and three new examples. As before, the tests are mostly about the *failure* modes, because the success path is easy and the pathologies are quiet.

### **Four bugs the code found**

Writing the implementation falsified four things — three in my own code, one in a claim I had written into a test:

*   **A checkpoint aliasing bug.** `Checkpointer.save` stored the live `completed` list rather than a copy, so later mutations retroactively edited an already-written checkpoint. The in-memory checkpointer silently lied about history, and a simulated crash appeared to have saved work it never saved. This is a realistic bug — the disk path was safe only because `json.dumps` serializes.
*   **The idempotency fence was in the wrong place.** It lived in the checkpoint — but the dangerous window for a duplicate side effect is precisely when the process died *before* the checkpoint wrote. The fence needs its own durable store. `examples/08` now demonstrates the same crash charging a card twice without the ledger and once with it.
*   **`resume` discarded caller state**, so a resume after fixing an environment problem failed identically forever. Saved state is now the base and caller-supplied keys override it.
*   **A false claim in a test.** I wrote "three steps at 92% beats nine steps at 98%." It does not — 0.92³ = 0.779 < 0.98⁹ = 0.834. The test caught my own overclaim, and the lesson now says topology is powerful, not magic.

A fifth, smaller one: `Graph.missing()` originally checked only outgoing edges, so "which services have no owner?" — an *incoming* `owns` edge — could not be expressed. My first test worked around the API instead of exercising it, which is its own warning sign.

### **Rewritten Final Project**

Restructured from five parts to seven, covering the whole course: architecture spec → agent → **graph** → **execution graph and durability** → evaluation → security → **bounded optimizer**.

Three deliberate choices:

*   **A justified decision *not* to build a graph scores as well as building one.** Part 3 requires you to measure the fraction of real query traffic that needs multi-hop reasoning *before* building, and an honest negative result is a pass.
*   **A negative result in Part 7 scores higher than an unexamined positive one.** If held-out gains don't survive on the sealed set, saying so with evidence demonstrates the central lesson of Lesson 5.
*   **Graph poisoning** joins the red-team set — a false edge is worse than a false document, because a graph *reuses* it on every future query.

The agent working is worth 5% of the grade. That is deliberate, and it is the summary of the course.

### **Supporting material**

CHEATSHEET, ANTI_PATTERNS (four new failure modes: deep-query confidence collapse, the graph that became an expensive vector index, vanishing self-improvement gains, and the unexplained optimizer plateau), GLOSSARY, INDEX, and REFERENCES all extended.

### **Revision 3 review fixes**

A correctness review of Module 9 found and fixed five issues — reported here because the repo's own doctrine is that failures become recorded cases:

*   **The Lesson 3 illustrative graph merged the PR *before* the approval gate** — contradicting the course's own rule that human gates precede irreversible actions — and routed to an `escalate` node it never defined, which `StateGraph.validate()` itself would reject. The snippet now gates before merging and defines every target.
*   **The acceptance gate's default contradicted Module 6's eval-sizing math.** `min_gain=0.005` on a 200-case held-out split is *one flipped case*; a loop querying that gate for hundreds of rounds accumulates noise as improvement — the Lesson 5 pathology, enabled by a default. Added `HeldOutGate.for_split()`, which denominates the threshold in net flipped cases (≥3), plus the paired-vs-unpaired statistics note in Lesson 4 and the solutions.
*   **`Graph.correct()` could only correct when a fact *began*,** but real corrections — including the module's own Lesson 2 exercise — usually also move when it *ended*. It now accepts either or both clocks, and a stale-edge reference fails with an instructive error instead of `list.index`.
*   **`Graph.transitive()` returned duplicate targets on diamond-shaped graphs.** It now returns one path per reachable node, keeping the most trustworthy — which also encodes the redundant-paths nuance the *p*ⁿ caveat describes.
*   **The Lesson 2 routing diagram had a vacuous decision node** (both branches led to graph traversal). Restructured so the time/absence/themes check sits on the single-hop side, where it does real work — those questions need the graph *regardless* of hop count.

Also added: the *p*ⁿ independence caveat in Lesson 1 (correlated hub errors, redundant paths), a note on the token cost of the optimization loop itself in Lesson 4, and a forward pointer from Module 3, Lesson 5 to the third retrieval primitive.

---

## **2026 Edition, revision 4 — Continuous Vector Memory Graphs, the Setup Guide, and the Doing Layer**

### **Module 9 grows to seven lessons**

Two new lessons, with the meta-harness pair renumbered to Lessons 6–7 (all cross-references updated; CHANGELOG history left describing the repo as it was):

*   **Lesson 3: Continuous Vector Memory Graphs.** The entry problem — a traversal starts from a node, users give you fuzz — and the 2026 hybrid-memory consensus answer: one store where nodes and facts carry embeddings maintained continuously. Retrieval as **entry → expand → filter → rank**, and the two subtleties that separate working systems from naive ones: **an embedding outlives the truth of its fact** (keep + filter by validity; deleting breaks as-of, not filtering pollutes now), and **node embeddings rot when their neighbourhood changes** (refresh at the mutation point, including the endpoint a fact leaves). "Continuous" is treated as a cost claim: embed-on-write is O(neighbourhood) per write vs O(corpus) batch rebuilds. The lesson is explicit that the *name* is newer than its parts and cites the parts.
*   **Lesson 5: Standing Up the Four Graphs.** The practical setup guide: one recipe (justify → schema first → smallest storage → gated writes → tools as the read path → measure → classic mistake) applied to all four graph types, storage ladders with promotion conditions (Postgres as the underrated middle rung), read paths as Module-5-disciplined tools, durability proven by drills, and the stable-node-id integration contract. Includes the legal caveat that invalidate-never-delete needs a designed purge path where erasure law applies.

### **New runnable code**

`ce/vectorgraph.py` — `VectorMemoryGraph` wrapping the bi-temporal `Graph` with a deterministic, dependency-free hash embedder (crc32, not Python's salted `hash()`), embed-on-write with a cost meter, mutation-point node refresh, and `recall()` implementing the full pipeline. **13 new tests (130 total)** and `examples/10_vector_memory_graph.py`, whose centerpiece is a query sharing zero vocabulary with its answer — unreachable by pure vector search, found through entry + expansion with the path as provenance.

Two bugs the tests caught before they shipped: the first embedder used Python's `hash()`, which is salted per process — "deterministic" would have been quietly false across runs — and the first zero-overlap test query overlapped its answer on the stopword "for."

---

## **2026 Edition, revision 5 — The Doing Layer (Tier 1)**

Three additions closing the gap between reading the course and being able to do it, plus the repo finally practicing its own doctrine.

### **1. Ten auto-graded exercises** — `code/exercises/`

Skeletons the learner implements, graded by the same tests CI runs against reference solutions. `python3 exercises/check.py` reports pass / fail / not-started per exercise.

| | Implements | Lesson |
| :--- | :--- | :--- |
| `ex01` | Cache-aware Section list | M1 L2 · M4 L1 · M8 L4 |
| `ex02` | Actionable tool errors | M5 L2 |
| `ex03` | The pruned 4-tool registry | M5 L2 |
| `ex04` | A loop that checks the world, not the transcript | M8 L1–L2 |
| `ex05` | Guardrails for unattended runs | M8 L2 |
| `ex06` | Compaction preserving dead ends and identifiers | M4 L4 |
| `ex07` | A binary, verifiable judge rubric | M6 L1 |
| `ex08` | Ontology as a gate | M9 L1–L2 |
| `ex09` | Bi-temporal transfer and correction | M9 L2 |
| `ex10` | Held-out gate and editable surfaces | M9 L6–L7 |

CI enforces **both** directions: solutions must pass 10/10 (every exercise is solvable) **and** skeletons must fail (no exercise is vacuous).

### **2. The validator moved into the repo** — `tools/validate_course.py` + CI

Previously these checks lived in an agent scratchpad and died with it — the next editor inherited nothing. Now `python3 tools/validate_course.py` runs nine checks (library tests, examples, links, task alignment, prose code blocks, exercise solvability, exercise non-vacuousness, lab syntax, diagrams) and a GitHub Actions workflow runs them on every push. The course preaches "run the evals on every harness change"; its own repo now does.

Mermaid validation moved to `tools/mermaid/` with a committed `package.json`.

### **3. Six live-model labs** — `code/labs/` + `ce/adapters.py`

What `MockModel` deliberately hides: real non-determinism (`lab01`), the cache counter going to zero when a timestamp is prepended (`lab02`), the Module 8 harness driving a live model in a sandbox (`lab03`), judge calibration with measured kappa across two rubrics (`lab04`), a live model under injection with and without the capability to act (`lab05`), and a pass rate wandering across identical eval runs (`lab06`). Under $1 total; each exits cleanly with no API key. `ce.adapters` is the only networked file and is deliberately **not** imported by `import ce`.

### **Safety fixes made while writing this**

*   **`Workspace.path()` used string-prefix containment** — `/tmp/ws` string-prefixes `/tmp/ws-evil`, so a sibling directory could be reached. Now uses `Path.is_relative_to`, with tests for deep traversal, absolute paths, and the sibling-prefix case.
*   **`lab03` originally passed model-supplied filenames straight to `workdir / name`** — a path-traversal hole in a lab demonstrating agent safety. Containment is now the lab's teaching point, verified against `../`, deep traversal, absolute paths, and prefix-sibling attacks. The lab also carries a real `max_cost_usd` ceiling and deletes its sandbox.
*   `lab05` performs a genuine injection attempt against a live model but exposes no real secret — the tool returns a refusal and records the attempt locally.
*   `exercises/_loader.py` used Python's salted `str.__hash__` for module naming; now a stable SHA-256 digest.

### **One library bug the exercises found**

`ContextAssembler` sorted **all** tiers by descending value, which put a high-value task *above* a low-value timestamp inside the volatile zone — backwards, since the volatile zone is the recency zone and the task belongs last. `ex01` failed against its own reference solution and exposed it. Fixed: stable tiers sort importance early (primacy), the volatile tier sorts importance late (recency), with a library test pinning the rule.
