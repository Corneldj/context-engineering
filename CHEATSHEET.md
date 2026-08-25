# **Cheat Sheet**

Every decision this course asks you to make, on one page. Each entry links to where it's derived.

---

## **Numbers worth remembering**

| Number | What it means |
| :--- | :--- |
| **60–70%** | Effective context as a fraction of nominal. Plan against this, not the marketing figure |
| **~30%** | Mid-context recall loss at scale, across all 18 frontier models tested |
| **~70%** | Compact here — of the *effective* window, not the nominal one |
| **~90% / 1.25×** | Prompt cache: read discount / write premium. Prefix valid only to the first changed byte |
| **~60%** | Cache hit rate below which caching may cost more than not caching |
| **~100** | Minimum eval cases before aggregate metrics mean anything (20 cases → ±22% margin) |
| **300–500+** | Eval cases for metrics you can slice and act on |
| **~0.6** | Cohen's kappa floor for a usable judge. Below it, fix the *rubric* |
| **3–7** | Agents in a team. Below: you didn't need a team. Above: coordination eats specialization |
| **~N×, ~(N+1)×** | Cost of fan-out/pipeline, and of supervisor |
| **1.5k / 50k** | What a sub-agent returns vs. what it spends. The compression ratio nothing else matches |
| **0.85⁵ = 44%** | Five-hop graph traversal at "respectable" 85% entity resolution |
| **0.92⁹ = 47%** | Nine-step agent chain at 92% per-step reliability. See the stop rule |
| **~8** | Maximum edge types in a workable ontology. More means an extractor inventing synonyms |
| **<15%** | Enterprises with graph retrieval in production as of 2025 — the gap between compelling and shipped |

---

## **Which discipline is my problem?**

| Symptom | Discipline | Fix shape |
| :--- | :--- | :--- |
| Wrong format or tone | **Prompt** | Clearer instruction, one canonical example |
| Confidently wrong facts | **Context** | Grounding, retrieval quality, verified citations |
| Degrades in long sessions | **Context** | Compaction, restate constraints at the end |
| Wrong tool chosen | **Context** | Prune overlapping tools; sharpen descriptions |
| Claims success falsely | **Harness** | External verification gates termination |
| Costs 10× the estimate | **Context + Harness** | Cache order, model routing, budget caps |
| Exceeded its permissions | **Capability** | Scope permissions, sandbox, egress allow-list |
| Fine by hand, useless unattended | **Loop** | Trigger, verifiable goal, escalation |

> **If you're adding a sentence to a prompt to prevent a failure that has happened twice — you need structure, not words.**

---

## **Retrieval strategy**

```
Structured data?            -> Query it (SQL / API). Not retrieval.
Exact identifiers + links?  -> Agentic search (glob, grep, read, follow)
Fuzzy prose, large corpus?  -> Hybrid RAG (vector + BM25 + rerank)
Fuzzy prose, < ~50 docs?    -> Just include it. Retrieval is overhead.
Query has an exact token?   -> Keyword first, semantic as fallback
```

**Priority order for improving retrieval** (cheapest and highest-leverage first):

1. **Hybrid search** — never worse than pure vector; removes exact-identifier failures
2. **Contextual retrieval** — one-time index cost, zero per-query cost
3. **Re-ranking** — big gain, no re-indexing
4. **Query transformation** — multi-query, HyDE
5. **A new embedding model** — last; it means re-indexing everything

**Failure modes differ in kind:** vector RAG fails *silently and plausibly*; agentic search fails *loudly*. Where a confident wrong answer beats no answer, that asymmetry matters more than any benchmark.

*(Module 3 Lessons 3, 5 · Module 4 Lesson 3)*

---

## **Memory strategy**

| Strategy | Use when | Weakness |
| :--- | :--- | :--- |
| **Sliding window** | Only recent context matters | Forgets abruptly, including the goal |
| **Summarization** | Long conversation, early content stays relevant | Misremembers — confident, not blank |
| **Hybrid** | Almost always in production | More moving parts |
| **Compaction** | Agents, long trajectories | Lossy by construction |
| **Externalized files** | State whose loss is expensive | Must be written to be kept |

**The test for externalizing:** *if losing this would make the agent redo work or repeat a mistake, it goes in a file.* Otherwise let compaction handle it.

**Compaction must preserve:** goal (verbatim) · decisions + why · findings + sources · **dead ends** · open questions · **exact identifiers**. Tune for recall first, precision second.

*(Module 4 Lessons 1, 4)*

---

## **Context assembly order**

```
┌─ STABLE — cached; high primacy attention ──────────────┐
│  1. System instructions                                │
│  2. Tool + skill definitions                           │
│  3. Canonical examples                                 │
│  4. Durable memory / conventions                       │
├─ ◆ CACHE BREAKPOINT ───────────────────────────────────┤
│  5. Compacted history summary                          │
├─ ◆ CACHE BREAKPOINT ───────────────────────────────────┤
│  6. Retrieved documents (ranked, edge-loaded)          │
│  7. Recent turns and tool results                      │
├─ VOLATILE — never cached; high recency attention ──────┤
│  8. Task state / plan and progress                     │
│  9. The immediate instruction                          │
└────────────────────────────────────────────────────────┘
```

Three rules: **never put anything volatile above anything stable** · **the task goes last, always** · **the middle is the cheap seats** — restate anything critical at position 9.

Drop by **value**, not by age. Edge-load ranked documents: `[1, 3, 5, 4, 2]`.

*(Module 8 Lesson 4)*

---

## **Agent, workflow, or neither?**

| | Workflow | Agent |
| :--- | :--- | :--- |
| Control flow | You write it | The model decides it |
| Cost | Predictable | Variable |
| Debugging | It's just code | Traces and interpretation |

> **If you can draw the flowchart, build the flowchart.** The moment it needs a box saying "figure out what to do next," you have an agent.

Most production systems are **workflows with an agentic step or two inside them**.

*(Module 5 Lesson 1)*

---

## **Loop design**

**Five components, all required:** trigger · **goal as a verifiable end state** · actions · verification · memory.

**Verification tiers** — prefer the lowest available:

| Tier | What | Use |
| :--- | :--- | :--- |
| 1 | Deterministic (tests, schema, row count) | Always, if you can design for it |
| 2 | Separate judge model + rubric | Qualitative goals; calibrate it |
| 3 | Human checkpoint | Irreversible / outward-facing actions |
| 4 | Agent self-report | **Never sufficient alone** |

**Five guardrails, all required:** iteration cap · token budget · circuit breaker on tool errors · **no-progress detection** · escalation carrying real state.

> Cost caps stop a *runaway* loop eventually. No-progress detection stops a *stuck* loop immediately.

*(Module 8 Lesson 2 · `code/examples/03_agent_loop.py`)*

---

## **Orchestration pattern**

| Pattern | Use when | Cost | Signature failure |
| :--- | :--- | :--- | :--- |
| **Single agent** | Try this first | 1× | — |
| **Fan-out** | Genuinely independent tasks | ~N× | Unspecified partial-failure policy |
| **Pipeline** | Each stage needs the last | ~N× | Cascade poisoning |
| **Debate** | High-stakes, experts differ | ~1.2–2.5× | Judge prefers style over correctness |
| **Supervisor** | Cross-domain specialists. **2026 default** | ~(N+1)× | Over-delegation into unfinishable slices |
| **Swarm** | 50+ parallel, unpredictable | Unbounded | Population explosion |

**The only question that justifies multi-agent:** *which work generates a lot of tokens whose details the coordinator doesn't need?*

**Handoff contract:** narrow question in · schema out · **mandatory `gaps` field** · per-sub-agent permissions.

*(Module 8 Lesson 3)*

---

## **Capability packaging**

| Use | When |
| :--- | :--- |
| **Plain tool** | One function, your codebase, this agent |
| **MCP server** | An external *system*, especially if several agents need it |
| **Agent Skill** | A *procedure*, used sometimes, shouldn't cost context when unused |
| **AGENTS.md** | Ambient repo knowledge every agent needs |
| **System prompt** | Behavior applying to every turn of this agent |

**The deciding question:** *"If the agent never does this task, should I still pay for these tokens?"* If no → skill.

*(Module 5 Lesson 4)*

---

## **Security**

> **Read untrusted content · hold private data · act outward — pick two.**

**Reduces likelihood** (necessary, not sufficient): delimiters · instruction hardening · input classifiers · canaries.

**Contains damage** (this is where security lives): least privilege · **egress allow-list** · sandboxing · human gates on irreversible actions · separated trust domains with a **schema** boundary · behavioral monitoring · output filtering.

> **Injection is a capability amplifier. With no capability, there is nothing to amplify.**

Audit the **combination**, not each addition. Red-team cases belong in CI.

*(Module 6 Lesson 3 · `code/examples/06_security.py`)*

---

## **Evaluation**

**Trajectory dimensions**, scored separately — a single score says it got worse; six say *which part*:

`tool_selection` · `argument_extraction` · `result_utilization` · `error_recovery` · `plan_coherence` · `task_completion`

**Judge calibration:** label 50–100 by hand → run the judge → measure kappa → **fix the rubric** if low → recheck after any change. Design against **position**, **verbosity**, and **self-preference** bias.

> 80% raw agreement can mean **zero** signal — a judge that always says PASS scores 80% against 8-good/2-bad labels and catches nothing.

**Stratify** across easy / hard / edge / adversarial / every production failure to date.

*(Module 6 Lesson 1 · `code/examples/05_evaluation.py`)*

---

## **Autonomy levels**

| Level | Agent | Human |
| :--- | :--- | :--- |
| 1 | Proposes | Executes |
| 2 | Executes sandboxed | Approves before effect |
| 3 | Executes | Reviews after |
| 4 | Executes | Samples and audits |

**Promote on evidence** — first-pass success and escalation rates. **Demote willingly.** The honest promotion signal is *approval with no substantive edits*, not approval.

*(Module 8 Lesson 3)*

---

## **Which graph do I need?**

| Question shape | Graph |
| :--- | :--- |
| *"How do these things relate?"* | **Knowledge graph** — entities and typed relations |
| *"…and when did that change?"* | **Memory graph** — bi-temporal validity |
| *"And then, unless, retry, in parallel, wait for approval"* | **Execution graph** — nodes, edges, state |

**A graph earns its cost** on: connected queries (2+ hops) · relations that change over time · provenance requirements · shared world state across agents · knowledge compounding across sessions. **Two or more of these, or don't build it.**

**Skip it** for: one-off questions · answers in a single document · stable tabular data (that's a SQL join) · data too fresh to keep in sync.

**Typed edges are the point.** `supersedes`, `depends_on`, `caused_by`, `decided_by` — not `related_to`, which carries one bit and duplicates vector search.

**The arithmetic:** per-hop accuracy `p` gives `p`ⁿ over `n` hops.

| per-hop | 2 hops | 3 hops | 5 hops |
| ---: | ---: | ---: | ---: |
| 95% | 90% | 86% | 77% |
| 90% | 81% | 73% | 59% |
| 85% | 72% | 61% | **44%** |

Set a per-hop floor from your deepest traversal. **Prefer short high-confidence traversals**, track confidence, and **withhold below a floor** rather than asserting flatly. Human-curated links are accurate by construction — the cheapest good graph is one your organization already maintains.

**Before improving extraction, check whether the fact is derivable from a system of record.** Dependencies are in your build files; ownership is in your service catalogue.

**Continuous vector memory graph** — when a justified memory graph needs fuzzy entry: one store, embeddings on nodes *and* facts, retrieval = **entry → expand → filter → rank**, the path is the citation. Two rules: **keep superseded facts' vectors and filter by validity** (deleting breaks as-of; not filtering pollutes now), and **refresh node embeddings at the mutation point**, including the endpoint a fact leaves. **The embedder is schema — version-pin it.** *(Module 9 Lesson 3 · `code/examples/10_vector_memory_graph.py`)*

**Standing them up** — one recipe: justify → schema first → smallest storage → gated writes → **tools as the read path** → measure → know the classic mistake. **Postgres is the underrated middle rung for all four graphs**; promote per component, on measurement. Durability is proven by **drills** (kill-and-resume, crash-before-checkpoint, gate-across-deploy). **Stable node ids are the integration contract.** *(Module 9 Lesson 5)*

*(Module 9 Lessons 1–2 · `code/examples/07_graphs.py`)*

---

## **Retrieval, with three primitives**

```
Exact identifier?          -> keyword / BM25
2+ relationship hops?      -> graph traversal
Time, absence, or themes?  -> graph traversal
Single fact in one doc?    -> vector + rerank   (the cheap default)
Structured data?           -> query it. Not retrieval.
Unclear?                   -> run both, fuse with RRF
```

**Route on structure, not a model's opinion.** "Does this query name two entity types?" is a cheap deterministic check. **Return the traversal path as provenance** — it is the strongest citation available, because it shows the reasoning.

*(Module 9 Lesson 2 §4)*

---

## **Execution graph vs. loop**

| Stay with a loop | Move to a graph |
| :--- | :--- |
| "Keep going until verified" | **Long runs where crashing is expensive** |
| Runs finish in minutes | Human approval pauses that must survive days |
| One branch point | Real parallelism with a join |
| No human pause | Several branch points encoded in flags |
| | Topology you need to inspect or modify |

**Durable execution is the real payoff.** Watch for: **non-idempotent nodes on replay** (fence with a key in a store *separate from the checkpoint*) and **oversized state** (every transition is a write).

**Four patterns:** delete fake edges · the diamond (separate verifiers, single merge owner) · the stop rule · the human gate.

> **The stop rule:** long sequential chains fail at `p`ⁿ. **Shorten the chain; don't buy better agents.** Deterministic gates between stages also stop errors cascading — a bad output at step 2 is indistinguishable from a good one at step 7.

*(Module 9 Lesson 4 · `code/examples/08_execution_graph.py`)*

---

## **Meta-harness governance**

**Three tiers:** human harness engineering → **meta-harness** (separate optimizer — the sweet spot) → self-harness (self-referential, riskiest).

**The loop:** weakness mining (cluster by **mechanism**, not error code) → **bounded** proposal (one mechanism, one surface) → acceptance gated on **held-out** data.

**Split three ways:** held-in (proposer sees) · held-out (gates acceptance) · **sealed** (never touched — the headline number). A held-out set that has gated 100 decisions has been leaked to, one bit at a time. **Rotate it.**

**Frozen set — matters more than the editable set:**

| Frozen | Prevents |
| :--- | :--- |
| Eval harness + data | Optimizing by editing the exam |
| Output schema | Loosening the spec until every failure passes |
| Permissions, egress | Self-improvement becoming privilege escalation |
| Budgets | "Improvement" that removes its own limits |
| Rollback, logging | A system that can't be reverted or audited |

**Pathologies, and what reveals each** *(none are visible in an aggregate score)*:

| Pathology | Reveal with |
| :--- | :--- |
| Reward hacking | Per-category scores + red-team probes asserting what failure must look like |
| Diversity collapse | Surface diversity across proposals |
| Catastrophic forgetting | Per-category scores **across rounds** |
| Held-out contamination | Divergence between held-out and a sealed set |

> **Harness updating is not harness benefit.** Gains largely vanish on evaluators the system did not optimize against. **Meta-agents propose; humans and held-out evals dispose.**

**Maturity ladder:** 0 humans read traces → 1 **automated weakness mining** → 2 automated proposal → 3 automated accept into a candidate pool → 4 auto-promotion on low-risk surfaces → 5 autonomous code optimization in a frozen envelope.

**Rung 1 carries most of the value and almost none of the risk.** Prerequisite check before rung 3: *can you say what change caused your last regression and what you rolled back to?*

*(Module 9 Lessons 6–7 · `code/examples/09_meta_harness.py`)*

---

## **The four that don't change**

1. **Context is finite and degrades.**
2. **Verification must live outside the agent.**
3. **Capability must be scoped.**
4. **You can't improve what you can't measure.**
