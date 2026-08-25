# **Module 9: Solutions to Hands-On Tasks**

This document provides suggested solutions for the "Hands-On Tasks" in each lesson of Module 9.

Runnable versions of much of this live in [`code/examples/07_graphs.py`](../../code/examples/07_graphs.py), [`08_execution_graph.py`](../../code/examples/08_execution_graph.py), and [`09_meta_harness.py`](../../code/examples/09_meta_harness.py).

---

### **[Lesson 1: Graph Engineering](./Lesson1_Graph_Engineering.md)**

#### **Task: Does the Graph Earn Its Cost?**

#### **Example Solution — Part A: classify the graph**

1.  **Customer changed plans in March → memory graph.** The requirement is explicitly *"without losing the fact that they were on the old plan before that."* That is bi-temporal validity. A summary would carry "customer is on Plan B" and silently destroy the history you'll need when they dispute a February charge.

2.  **EU sub-processor compliance → knowledge graph.** Three hops: `Vendor → processes → DataCategory`, `→ via → SubProcessor`, `→ audited_by → Auditor`. No single document contains the answer; it's assembled across contracts, DPAs, and audit records. This is the canonical connected query.

3.  **Test → triage → retry twice → page → execution graph.** Branch, bounded cycle, terminal escalation. Nothing here is about *what is true*; it's about *what happens next*.

4.  **8,000 help articles, single-fact questions → none.** Single-hop factual lookups over unstructured prose is exactly vector RAG's home ground. Building a graph here spends the construction and maintenance budget to be worse.

5.  **"What else did the deploy that caused this incident touch?" → knowledge graph.** Two hops (`Incident → caused_by → Deploy → touched → Service`), and the value is high because the answer drives an operational decision. Note that two hops is a comfortable depth — see Part B.

#### **Example Solution — Part B: the arithmetic**

**1. At 88% per hop over three hops:** 0.88³ = **0.681**. About **68% of answers are trustworthy** — roughly one in three compliance answers is wrong. For a compliance system that is not a quality problem, it's a liability.

**2. Required per-hop for 95% over three hops:** p ≥ 0.95^(1/3) = **0.983**, i.e. **98.3% per hop**.

**3. Is that achievable with LLM extraction from contracts?** **No.** Contracts use inconsistent legal-entity names, subsidiaries, trading names, and defined terms ("the Processor" meaning something declared thirty pages earlier). 98.3% entity resolution on that corpus is not a tuning problem.

**Two design changes that get you there without improving the extractor:**

*   **Shorten the traversal by pre-materializing a hop.** Maintain a curated `Vendor → SubProcessor` mapping — from the vendor register the procurement team already keeps — turning three uncertain hops into one curated hop plus one extracted hop. Human-curated links are accurate by construction, which is the cheapest accuracy available anywhere in this module.
*   **Restrict the question.** Return *candidates with their confidence and the traversal path*, framed as "vendors to review," not "vendors in violation." A 68%-confident list of twelve vendors for a human to check is genuinely useful; a flat assertion is not. This reframes the system from *decider* to *triage*, which is often the correct answer for compliance anyway.

*(A third option worth naming: raise per-hop accuracy for the two worst hops only, by adding a human adjudication queue for low-confidence entity merges. You don't need 98.3% everywhere — you need it on the path.)*

#### **Example Solution — Part C: the edge vocabulary**

For the incident bot, seven types:

| Edge | Answers |
| :--- | :--- |
| `caused_by` (Incident → Deploy) | What triggered this? |
| `touched` (Deploy → Service) | What else did that deploy change? |
| `depends_on` (Service → Service) | What is downstream of the blast radius? |
| `owns` (Team → Service) *time-varying* | Who do I page? |
| `on_call_for` (Person → Team) *time-varying* | Who specifically, right now? |
| `mitigated_by` (Incident → Action) | What resolved it, for the postmortem? |
| `recurrence_of` (Incident → Incident) | Have we seen this before? |

**Rejected: `related_to` (Incident → Incident).** It carries one bit and duplicates what a vector search over incident descriptions already does — better, in fact, since embeddings capture graded similarity. Its real cost is that it's a magnet: an extractor with `related_to` available will use it for every relationship it can't confidently type, and the graph slowly fills with edges nobody can query. `recurrence_of` is the specific, useful version of the same intuition.

---

### **[Lesson 2: Knowledge and Memory Graphs](./Lesson2_Knowledge_and_Memory_Graphs.md)**

#### **Task: Build the Model Before the Graph**

#### **Example Solution — Part A: stages 1–3**

**1. Scope.**
*In:* Service, Team, Person, Incident, Deploy, Postmortem, Rotation.
*Out (deliberately):* individual commits (too granular; the deploy is the unit), customers (a different domain), and infrastructure hosts (the service is the abstraction the questions are asked at).

**2. Ontology.**

| Edge | Source → Target | Cardinality | Time-varying |
| :--- | :--- | :--- | :--- |
| `owns` | Team → Service | 1 team per service | **yes** |
| `member_of` | Person → Team | many | **yes** |
| `on_call_for` | Rotation → Team | 1 | **yes** |
| `covers` | Person → Rotation | many | **yes** |
| `depends_on` | Service → Service | many | **yes** |
| `caused_by` | Incident → Deploy | 0..1 | no |
| `touched` | Deploy → Service | many | no |
| `documents` | Postmortem → Incident | 1 | no |

Eight types. Note that everything about *organization* is time-varying and everything about *events* is not — a deploy touched what it touched, permanently.

**3. Traversals.**

| Question | Traversal |
| :--- | :--- |
| Who owns the service that caused Tuesday's incident? | `Incident --caused_by--> Deploy --touched--> Service <--owns-- Team` at `t=Tuesday` |
| What depends on `auth-lib`, transitively? | `transitive(auth-lib, depends_on, inbound)` |
| Which services have no on-call rotation? | `missing(Service, owns→Team→on_call_for)` — a **two-step absence** query |
| Who owned `payments-api` in January? | `Service <--owns-- Team` at `t=January` |
| Recurring themes across 200 postmortems? | Community detection over `Postmortem --documents--> Incident --caused_by--> Deploy` clusters |

**The schema fix the exercise is fishing for:** question three cannot be answered by the initial schema, because "has an on-call rotation" is a property of the *Team*, not the Service. You need either the two-step traversal above or a derived edge. Discovering that *before* extraction is exactly what stage 1 is for — discovering it after means re-extracting.

#### **Example Solution — Part B: temporality**

**1. Which edges need bi-temporal validity.**
`owns`, `member_of`, `on_call_for`, `covers`, `depends_on` — all organizational or architectural facts that change.

**Not** `caused_by`, `touched`, `documents`. These are **event records**: deploy-412 touched payments-api, and that will be true forever. Adding validity intervals to them costs storage and query complexity for a fact that cannot change. *(One nuance: if you later discover that `caused_by` was wrong — the incident had a different cause — that's a correction to a belief, so `t_created`/`t_expired` are useful even here. `t_valid`/`t_invalid` are not.)*

**2. Transfer on 3 March.**

```
BEFORE
  (Team A) --owns--> (payments-api)   t_valid=0    t_invalid=∞   t_created=0    t_expired=∞

AFTER
  (Team A) --owns--> (payments-api)   t_valid=0    t_invalid=MAR3 t_created=0   t_expired=MAR3
  (Team B) --owns--> (payments-api)   t_valid=MAR3 t_invalid=∞   t_created=MAR3 t_expired=∞
```
The first edge is **closed, not deleted**. "Who owned it in January?" still returns Team A.

**3. On 10 March you learn the transfer was actually 20 February.**

```
  (Team A) --owns--> (payments-api)   t_valid=0      t_invalid=MAR3  t_created=0     t_expired=MAR10
  (Team B) --owns--> (payments-api)   t_valid=MAR3   t_invalid=∞     t_created=MAR3  t_expired=MAR10
  (Team A) --owns--> (payments-api)   t_valid=0      t_invalid=FEB20 t_created=MAR10 t_expired=∞
  (Team B) --owns--> (payments-api)   t_valid=FEB20  t_invalid=∞     t_created=MAR10 t_expired=∞
```

**What changes:** the two original edges get `t_expired=MAR10` — we stopped believing them then. Two new edges carry the corrected world-clock with `t_created=MAR10`.

**What must not change:** the original edges' `t_valid`/`t_invalid`. Overwriting them would destroy the ability to answer *"what did we believe on 5 March, when we made that decision?"* — which is precisely the question an incident review will ask.

#### **Example Solution — Part C: routing and cost**

**1. Routing.**

| Question | Primitive | Why |
| :--- | :--- | :--- |
| Owner of the service that caused Tuesday's incident | **Graph** | Three hops, time-scoped |
| Transitive dependencies of `auth-lib` | **Graph** | Transitive closure; no other primitive does this |
| Services with no rotation | **Graph** | Absence |
| Owner of `payments-api` in January | **Graph** | Temporal point query |
| Themes across 200 postmortems | **Graph** (communities) **+ vector** | Community detection for structure; vector for reading the actual prose |

Note that this is a workload where the graph earns its keep — four of five questions need it. Compare a help-centre search where none would.

**2. Why no vector tuning answers question three.** Embeddings retrieve documents *similar to a query*. "Services with no rotation" describes a set defined by the **absence** of a record. There is no document to be similar to — the evidence is a gap, and a gap has no embedding. Better chunking, a better model, and a better reranker all improve retrieval of things that exist.

**3. At 91% over four hops:** 0.91⁴ = **0.686**. About a third of transitive-dependency answers are wrong.

**What to change: the question you let users ask** — and it's the right answer here rather than a cop-out. `depends_on` for a service graph should not be LLM-extracted at all. It is derivable **deterministically** from build manifests, lockfiles, and import graphs, at essentially 100% accuracy. The fix is to stop extracting a fact you can compute.

That generalizes into a rule worth keeping: **before improving extraction accuracy, check whether the fact is derivable from a system of record.** Ownership is in your service catalogue. Dependencies are in your build files. On-call is in PagerDuty. The graph's job is to *join* those, not to re-derive them from prose.

---

### **[Lesson 3: Continuous Vector Memory Graphs](./Lesson3_Continuous_Vector_Memory_Graphs.md)**

#### **Task: Design the Recall**

#### **Example Solution — Part A: tracing the pipeline**

**1. "What is Kim paying for these days" (now).**
*Entry:* the Kim node (strong name match). *Hop 1:* F1, F2, F3, F4 are all incident to Kim. *Filter (now):* **F1 is removed** — its validity closed in March. *Rank:* F2 first (a subscription fact, semantically closest to "paying for"), F3 second (billing is adjacent to paying). **Top-2: F2, F3.** Note that the filter, not the ranker, is what prevented the stale Starter answer — ranking a superseded fact well is exactly the failure mode.

**2. "What plan was Kim on when she opened the dispute" (about February).**
*Entry:* Kim, plus possibly Ticket 88 via "dispute". *Filter (at=February):* **F2 is removed** — not yet valid; F6 removed — April. F1 *survives*: valid Jan→Mar. **Top result: F1 (Starter).** Same pipeline as query 1, one parameter changed. This is the query that dies under any delete-on-supersede design.

**3. "Is the customer on ticket 88 entitled to priority support."**
*Why pure vector fails:* the answer requires a **join across three facts** — F4 (ticket 88 → Kim), F2 (Kim → Growth), F5 (Growth → priority support). Similarity will happily surface F4 and F5 individually, but no single fact connects the ticket to the entitlement; the connective tissue is the customer→plan hop, which lives in the *structure*, not in any text. *Pipeline:* enter through Ticket 88 → hop 1 reaches Kim via F4 → hop 2 reaches Growth via F2 (F1 filtered: not valid now) → hop 3 reaches F5. **Answer: yes — and the returned path F4 → F2 → F5 is the justification a support agent can actually show.**

#### **Example Solution — Part B: three failures of the naive design**

1.  **Delete-on-supersede amputates history from the vector side.** Exposed by query 2: "what plan was Kim on in February" — the graph still knows, but any retrieval that enters through the vector index finds nothing, and the agent answers from the current fact instead. The user sees a *confidently wrong* historical answer, which is worse than an error.
2.  **Nightly batch summaries make entry stale for a full day.** Kim upgrades at 10:00; at noon a "what is Kim paying for" query still enters through a summary that says Starter. Nothing errors — the entry just routes wrong until 02:00. The user sees yesterday's truth served with today's confidence.
3.  **Two stores joined by ids drift on partial failure.** The graph write commits; the vector delete fails (or the reverse). No error surfaces at query time — one index asserts a fact the other has closed, and *which answer you get depends on which index the query happens to enter through*. This is the silent-failure mode from §1, and no amount of retry logic at query time repairs state that diverged at write time.

*(Honourable mention: the nightly rebuild also costs more than every other failure combined — see Part C.)*

#### **Example Solution — Part C: the cost arithmetic**

**1. Per month.** Embed-on-write: 400 writes/day × 3 embeds (fact + 2 touched nodes) = **1,200/day ≈ 36,000/month**. Nightly full rebuild: ≥50,000 facts (plus node summaries) × 30 nights = **≥1,500,000/month** — a ~40× overhead, paid whether anything changed or not, *plus* a staleness window the width of a day.

**2. The embedder switch.** One full re-embed of the corpus — roughly 60–70k calls counting node summaries — done once, deliberately, with the version recorded on every vector. This is the single legitimate batch job in a continuous system, and the practical implication is: **keep the rebuild script written and tested even though you never schedule it.** It is the migration path, not the maintenance plan.

**3. The hot path.** Don't put the graph hop on it. Route: the <100 ms path gets vector-only lookup (or a precomputed/cached answer), and the graph serves the queries that need structure at interactive-but-not-hot latency. Lesson 2 §4 already answered this — vector is the cheap default; the graph is for the queries that need it. CVMG changes where the indexes live, not the routing discipline.

---

### **[Lesson 4: Execution Graphs](./Lesson4_Execution_Graphs.md)**

#### **Task: Model the Graph**

#### **Example Solution — Part A: the graph**

**State schema:**
```python
class ReviewState(TypedDict):
    quarter: str
    contract_ids: list[str]
    processed: dict[str, Finding]     # id -> finding, so resume knows what's done
    high_risk: list[str]
    approvals: dict[str, bool]
    report_path: str | None
```

**Nodes:** `fetch_contracts` → `extract_obligations` → `check_policy` → `assess_risk` → (conditional) → `await_review` / `record_finding` → `compile_report`.

**1. Fake edges.** The big one: `extract → check → assess` is drawn as a chain **per contract**, but the 200 contracts are independent of each other. The genuinely sequential part is *within* one contract; across contracts the whole pipeline is a fan-out. Teams routinely serialize the outer loop because that's how the requirements were written.

A second fake edge: `compile_report` is usually drawn as depending on *all* reviews completing, including human ones. It doesn't — it depends on all *automated* findings, plus whichever human reviews have returned. A report that includes 194 contracts and marks 6 as "pending review" is more useful, sooner, than one that blocks for four days.

**2. The diamond.** Split on contract (200 parallel branches), each branch running extract → check → assess with **its own verifier** — a per-contract schema check plus a policy-citation check confirming each flagged discrepancy references a real clause. Merge at `compile_report`, owned by a single node that reconciles and deduplicates.

The separate-verifier detail matters here: an aggregate check at the end ("does the report look right?") accepts individually wrong findings that are collectively plausible, which is exactly the failure a compliance report cannot have.

**3. The human gate** sits on the edge from `assess_risk` to `record_finding`, **only for the high-risk branch**. The officer sees: the contract clause verbatim, the specific policy it allegedly violates, the model's stated reasoning, its confidence, and the outcome of the same check on this vendor's previous contracts. Not a summary — evidence (Module 7, Lesson 3).

#### **Example Solution — Part B: durability**

**1. What must be checkpointed for a *correct* resume**, not merely a possible one:
*   `processed` — which contracts have completed findings, so work isn't redone.
*   The **contract list with a content hash each**, so a contract amended mid-run is detected rather than silently mixing versions.
*   Approval state, including which requests were *sent* — see below.
*   The `quarter` and policy version in force, so a resume after a policy update doesn't produce a report evaluated against two different policies.

That last one is the subtle one and the reason "correct" differs from "possible": a naive resume produces a report that is internally inconsistent in a way nothing flags.

**2. Posting a comment to the vendor system is dangerous on replay** because the crash window can fall *after* the comment posts and *before* the checkpoint records it. Resume then posts a duplicate. Vendors receive two contradictory compliance notices, which is worse than none.

**What makes it safe:** an idempotency key derived from `(contract_id, finding_hash)`, recorded in a **durable store separate from the checkpoint** — because the dangerous window is exactly when the checkpoint didn't write. Best of all, have the vendor system deduplicate on the key you send. *(This is demonstrated in `code/examples/08_execution_graph.py` §4: without the ledger the effect happens twice, with it once.)*

**3. Four days of waiting.**

*Under a graph runtime:* the run reaches `await_review`, checkpoints, and the process **exits**. Nothing is held open. When the officer approves — through a web form that writes to the approval store — a resume is triggered and execution continues from that node with the accumulated state intact. Cost during those four days: storage.

*Under the Module 8 loop:* either a process blocks for four days (holding memory, dying on any deploy, and losing everything if the host restarts), or you build state serialization, an external approval store, and a resumption path — which is most of a graph runtime, written under deadline. This is the clearest single case for adopting one.

#### **Example Solution — Part C: the stop rule**

**1. Nine sequential steps at 92%:** 0.92⁹ = **0.472**. Across 200 contracts, about **94 complete cleanly**; 106 need intervention. The pipeline generates more exception work than it removes.

**2. Restructured.**

```
   fetch (once, deterministic)
        │
        ├─► per contract:  extract ──► check_policy ──► assess_risk
        │                    (3 agent steps, with a validation gate between each)
        │
   compile_report (once, deterministic)
```

Changes made: `normalize` and `format` are **deterministic code**, not agent steps — they were only in the chain because everything was drafted as an agent. `draft_finding` and `review_finding` collapse into `assess_risk` with a structured output; they were two steps because two prompts existed, not because two decisions did.

Three agent steps at 92%: **0.92³ = 0.779**. Across 200 contracts, ~156 clean, ~44 needing attention — **less than half the exception load**, with no change to model or prompt quality.

**3. The change that helps for a reason other than parallelism: the validation gate between stages.**

The mechanism is different and worth stating precisely. Parallelism doesn't change per-item reliability at all — 200 contracts run concurrently still each face the same chain. What the inter-stage gate does is **stop errors propagating**: a malformed extraction is caught and retried at stage 1 instead of flowing into policy-checking and producing a confident, wrong finding. It converts a *silent cascade* into a *local retry*.

That's the deeper point of the stop rule. Long chains fail not only because *p*ⁿ shrinks, but because **a bad output at step 2 is indistinguishable from a good one at step 7** — by then it has been reformatted, summarized, and cited. Deterministic gates between stages restore locality, which is what makes the failures debuggable at all.

---

### **[Lesson 5: Standing Up the Four Graphs](./Lesson5_Standing_Up_the_Graphs.md)**

#### **Task: Write the Setup Plan**

*An example plan for the Final Project's recommended domain — a research agent over a codebase. Yours will differ; what is graded is the honesty of the justifications.*

#### **Example Solution — Part A: justify each graph**

| Graph | Verdict | Why |
| :--- | :--- | :--- |
| **Execution** | **Build.** | Runs unattended for hours, has a human gate, and has crashed twice — durable execution is the strongest single reason to adopt (Lesson 4 §5). |
| **Knowledge** | **Build, small.** | Real connected queries ("what depends transitively on X", "which modules have no tests" — an absence query), and the edges are **derivable** from imports and lockfiles at ~100% accuracy, sidestepping the entity-resolution tax entirely. |
| **Memory** | **Skip.** | Single-operator agent; the corpus's facts don't churn per-user, and Module 4's workspace files already carry cross-run state. None of Lesson 1's five conditions bind. |
| **CVMG** | **Skip.** | Entry into a codebase is *exact* — identifiers, paths, grep (Module 3, Lesson 5). Fuzzy entry is not the bottleneck, so the embedding layer would be cost without a query it serves. |

Two skips is not a lack of ambition; it is the assignment. A plan that builds all four is almost certainly solving problems it doesn't have.

#### **Example Solution — Part B: rungs and promotion conditions**

*   **Knowledge graph — rung 1, and deliberately ephemeral:** `ce.Graph` rebuilt from lockfiles and the import graph *per run*. Because every edge is derivable, persistence buys nothing — the source of truth is the repo itself. *Promotion condition:* cross-run reuse of expensive-to-derive edges (e.g., LLM-extracted doc links) or derivation time exceeding ~30 s → SQLite tables, same schema. *Cost of promoting:* a sync job, and with it the staleness questions the ephemeral design made impossible.
*   **Execution graph — rung 1.5:** `ce.StateGraph` with the file `Checkpointer` and a file-backed `IdempotencyLedger`. *Promotion condition:* concurrent runs, or needing runs to survive deploys → Postgres checkpointer. *Cost:* a database dependency and checkpoint-schema migrations.

#### **Example Solution — Part C: the read path**

```python
reg.register("code_neighbors",
    "Modules directly importing or imported by a module. Derived from the import "
    "graph at run start; confidence 1.0.",
    {"module": {"type": "string", "description": "Repo-relative path, e.g. 'src/auth/session.py'."},
     "direction": {"type": "string", "enum": ["imports", "imported_by", "both"]}},
    required=("module",),
    when_to_use="One-hop structure. Use code_dependents for transitive reach.")

reg.register("code_dependents",
    "Everything transitively depending on a module — the blast-radius query. "
    "Returns one path per dependent, deepest paths truncated at max_hops.",
    {"module": {"type": "string"}, "max_hops": {"type": "integer", "description": "Default 4."}},
    required=("module",), max_result_tokens=1_500)

reg.register("untested_modules",
    "Modules with no test file referencing them — the absence query.",
    {"path_prefix": {"type": "string", "description": "Limit scope, e.g. 'src/payments/'."}},
    required=())
```

**Deliberately not exposed:** raw graph mutation (edges are derived — an agent "fixing" the graph would be falsifying evidence), arbitrary query strings (the three tools *are* the query surface, which is what keeps results token-budgeted and confidence-annotated), and anything returning the whole graph.

#### **Example Solution — Part D: the drills**

*   **Knowledge graph:** the **absence-query gold check** — run `untested_modules` against five modules whose test status you verified by hand. Failing it means edge derivation is dropping links, and every other query is quietly incomplete in the same way.
*   **Execution graph, drill 1:** kill the run at file 140 of 200 and resume — nothing redone, nothing lost, report identical to an uninterrupted run. Failing it means the checkpoint schema is missing state (Lesson 4's "correct vs. merely possible" resume).
*   **Execution graph, drill 2:** crash *between* a side effect and its checkpoint; resume. One side effect, not two. Failing it means the ledger is in the wrong place — inside the checkpoint's failure domain instead of separate from it.

#### **Example Solution — Part E: the id map**

*   **Minted:** module id = repo-relative path at the current commit. Node ids for non-file entities (packages, services) are minted once in a small `ids.toml`, never derived from display names.
*   **Maps to:** package names (lockfile), test files (path convention), PR numbers (GitHub), service names (the catalogue, if promoted).
*   **When a system of record changes its key** — a file rename being the everyday case: **add a mapping, never rewrite history.** The old id keeps its edges with validity closed at the rename commit; the new id opens; a `renamed_to` edge joins them. Rewriting ids in place is deletion wearing a refactoring costume — it breaks every as-of question and every external reference simultaneously. (Git already models this correctly; follow it.)

---

### **[Lesson 6: Autonomous Meta-Harness Systems](./Lesson6_Autonomous_Meta_Harness.md)**

#### **Task: Design the Optimizer**

#### **Example Solution — Part A: the tier**

**Meta-harness (tier 2).** Justification against the constraints:

*   Volume (4,000/day) and six months of traces give the weakness miner real signal — tier 1 is bottlenecked on how many traces a human will read, and nobody reads 4,000.
*   A 600-case labeled eval set makes the acceptance gate possible. Without it, tier 2 is unsafe at any speed.
*   A mid-tier model is precisely where harness-benefit capability peaks — frontier models have less headroom, and this is where the reported gains are largest.
*   **Not tier 3**, because a self-modifying extraction agent has no separation between the thing being improved and the thing improving it; a bad edit degrades the editor, and there's no reason to accept that risk when a separate optimizer is available.

**The risk accepted:** the optimizer will find edits that fit the evaluation set. The 600 cases are a fixed, finite target, and 200 rounds of optimization against them is a lot of pressure. Mitigation is the held-out split plus periodic rotation onto fresh cases — but the risk is real and does not go to zero.

#### **Example Solution — Part B: surfaces**

**Editable:** system prompt · extraction field descriptions · few-shot examples · retry policy · page-selection workflow · confidence thresholds for routing to human review · tool descriptions.

**Frozen** — and the specific failure each prevents:

| Frozen | What goes wrong if editable |
| :--- | :--- |
| **The eval set and its labels** | The optimizer improves by relabelling hard cases. The score rises; nothing improves |
| **The output schema** | Loosening `total: number` to `total: number \| null` makes every failure a pass. Score up, product broken |
| **The human-review threshold's floor** | Raising the auto-accept threshold "improves throughput" by sending fewer cases to review — it moves errors downstream, invisibly |
| **Tool permissions / filesystem scope** | Self-improvement becomes privilege escalation |
| **Cost and iteration ceilings** | "Improvement" includes removing its own limits |
| **Logging and trace emission** | A system that can quiet its own observability is unauditable — and the traces are the optimizer's own input |
| **Rollback** | It must survive a bad edit to be worth having |

The three a naive design leaves open are typically **the output schema, the review threshold, and the eval labels** — all three are technically "just configuration," and all three let the system change what counts as success.

#### **Example Solution — Part C: mining a weakness**

**1. Four distinct mechanisms**, not one error:

| n | Mechanism | Editable surface |
| ---: | :--- | :--- |
| 14 | Total is rendered as an image, not text | `tool_implementations` — needs OCR on the region |
| 11 | Multi-page document; only page 1 was read | `workflow` — page-selection logic |
| 9 | Field label synonym ("Balance Due") unrecognized | `system_prompt` / field descriptions |
| 6 | No total exists on the document | **not a harness bug** |

**2. Failure signatures:**

```
terminal:  SchemaValidationError: total expected number, got null
behaviour: read all text on page 1, found no numeric field labelled "total"
mechanism: total present only as rendered pixels; text extraction cannot see it
surface:   tool_implementations
```
…and analogously for the other three, each naming the *causal behaviour* and the *abstract mechanism*, not just the error string.

**3. The cluster that must not be fixed by a harness edit: the six documents with genuinely no total.**

No prompt, workflow, or tool change makes a number appear that isn't there. Attempting to "fix" it is exactly how reward hacking starts — the cheapest edit that makes those six pass is to emit `0`, which satisfies the schema and is wrong.

**What should happen instead:** a schema change (allow `null` with a required `reason` field) and a routing rule sending those documents to human review. That is a **product decision made by a human**, not a harness edit — and it must be made *outside* the optimization loop, which is why the schema is on the frozen list.

#### **Example Solution — Part D: the gate**

**1. The split.** Of 600 cases: **300 held-in** (the proposer sees these traces and failures), **200 held-out** (used only for the accept/reject gate; the proposer never sees cases or per-case results), **100 sealed** (never used in the loop at all; reserved for periodic honest measurement, and rotated with fresh cases as they accumulate).

Three splits rather than two, because a held-out set that has gated a hundred decisions has been leaked to, one bit at a time.

**2. Acceptance criterion:**
```python
min_gain = 3 / 200          # three net flipped cases on the held-out split = 1.5%.
                            # NOT an arbitrary 0.5% — that is one case, a coin toss.
accept = (
    d_in  >= -tol and
    d_out >= -tol and
    max(d_in, d_out) >= min_gain and
    not any(per_category_drop > 0.05) and
    not (d_in >= 4 * d_out and d_out < 2 * min_gain)     # fitting the held-in split
)
```

The `min_gain` line matters more than it looks. Module 6 taught that a small eval set can't detect small changes; the same arithmetic binds this gate. With 200 held-out cases, a 0.5% delta is a single case flipping — and a loop that queries the gate two hundred times will find single lucky cases repeatedly. Denominate the threshold in **net flipped cases** (≥3), and note that the comparison is *paired* (same cases before and after), which is what makes even a 3-case threshold meaningful where an unpaired comparison would need ±7 points.

**3. Held-in +9.0, held-out +0.2: reject.**

The ratio is the signal. A change that generalizes moves both splits roughly together; a 45× gap means the edit is keyed to properties of the 300 cases the proposer read. Most likely it encodes something specific about those documents — a vendor's layout, a date format — as if it were a general rule.

**What it tells you** is more useful than the reject: your held-in set is **not representative**, or the proposer is over-fitting to individual cases rather than abstracting mechanisms. Either way it's a signal about the *setup*, not just this candidate. If you see it repeatedly, re-stratify the splits.

**4. Plateau after twelve rounds — two explanations:**

*   **Benign:** the identified weaknesses have been addressed. Remaining failures are genuinely hard, or are the "no total exists" class that harness edits cannot fix. This is success.
*   **Broken:** **diversity collapse.** The proposer is generating variations on one surface — probably the system prompt, because it's the easiest to edit — and never exploring workflow or tool changes. The search died; the plateau is its shape.

**The distinguishing measurement: surface diversity across accepted and proposed candidates.** If every recent proposal targets one or two surfaces, it's collapse — fix it by sampling from the archive rather than only from the current best, and by requiring the proposer to address the *ranked* weakness list rather than choosing freely. If proposals are spread across surfaces and simply keep getting rejected on the held-out gate, the plateau is real.

*(A useful secondary check: the residual failure distribution. If the mechanism mix is unchanged from round 1, nothing is being fixed. If the large clusters shrank and what remains is a long tail, you're done.)*

---

### **[Lesson 7: Governing Systems That Rewrite Themselves](./Lesson7_Governing_Self_Modifying_Systems.md)**

#### **Task: Govern the Loop**

#### **Example Solution — Part A: auditing the claim**

*"61% to 79% over 200 autonomous rounds, no human intervention."*

| Question | Satisfying answer | Disqualifying answer |
| :--- | :--- | :--- |
| **1. Was 79% measured on data the optimizer never saw?** | "On a sealed set drawn after the run, never used for acceptance." | "On our benchmark" / "on the eval set" / an unclear answer |
| **2. What was frozen?** | A specific list including the eval set, schema, permissions, and budget | "The optimizer could modify the whole repository" |
| **3. Per-category results?** | Per-task-family scores across rounds, showing nothing collapsed | Only an aggregate — this is where catastrophic forgetting hides |
| **4. What is the verifier, and can it be gamed?** | A deterministic checker over a fixed spec, plus red-team probes for degenerate solutions | A model judge scoring "quality," uncalibrated |
| **5. Does the improvement transfer?** | Held on a different base model / different corpus | "We only measured on the configuration we optimized" |

**A sixth, if you get the chance:** *"show me the rejected candidates."* A loop with no rejections either has no gate or has a gate that never fires — both mean the acceptance criterion isn't doing work. A healthy archive is mostly rejections.

#### **Example Solution — Part B: the envelope**

**1. Frozen surfaces:** as in Lesson 6, Part B.

**2. The `total: 0` fallback — reject, and this is the important one.**

The candidate does not look like reward hacking. It improves **both** splits — held-in +6, held-out +5 — so the held-out gate alone would **accept** it. That is the point of the exercise: held-out validation catches *fitting your evaluator*, and it does **not** catch *a genuinely general way to satisfy a bad metric*.

What happened: returning `0` instead of raising converts every unparseable document from a validation error into a passing extraction. Both splits contain unparseable documents, so both improve. The system is now silently reporting zero-value invoices as successfully processed — a much worse outcome than a visible failure, because nothing downstream flags it.

**What catches it:** **per-category tracking.** Aggregate accuracy rises while the "documents with no extractable total" category collapses. And a **red-team probe** in the eval set: a case that explicitly asserts *an unparseable document must produce an error, not a default*. Encoding "what failure should look like" as a test case is the durable fix. *(Demonstrated in `code/examples/09_meta_harness.py` §3.)*

**3. The promotion gate.** The reviewer sees: the diff, held-in and held-out deltas, **per-category deltas**, the failure signature the edit targets, and **the candidates that were rejected this round** — that last one is the cheapest way to spot a loop optimizing in a strange direction. Batch to roughly weekly, not per-candidate, so it fires rarely enough to be read.

*Signals it has become a rubber stamp*: approval rate above ~90%; median review time under a minute; approval uncorrelated with per-category regressions; and — the best one — **rising post-promotion rollbacks**, which means bad edits are getting through and being caught downstream instead of at the gate.

#### **Example Solution — Part C: detecting the pathologies**

| Pathology | Metric / artifact that reveals it | Why aggregate success is blind |
| :--- | :--- | :--- |
| **Reward hacking** | Per-category scores + red-team probes asserting *what failure must look like*. Also: inspect what accepted edits actually did | The hack raises the aggregate — that's what makes it a hack |
| **Diversity collapse** | Surface diversity across proposals and accepts; entropy of the archive over rounds | The aggregate plateaus *smoothly*, which reads as convergence |
| **Catastrophic forgetting** | Per-category scores tracked **across rounds**, not just current | The mean holds while composition churns underneath |
| **Held-out contamination** | Divergence between held-out and a **sealed** set; also, held-out gains that arrive suspiciously smoothly | Both numbers rise. Only a third, untouched set disagrees |

The common thread: **every one of these is invisible to a single aggregate number, and visible in a decomposition.** That is the practical argument for per-category tracking — not rigour for its own sake, but that the aggregate is exactly the statistic these failures are shaped to preserve.

#### **Example Solution — Part D: placing yourself**

*Example answer, for a typical team:*

1.  **Rung 0, honestly** — traces exist, but nobody reads them systematically. Failures are noticed when a customer complains. The team *believes* it's at rung 1 because someone occasionally greps the logs.

2.  **Missing for rung 1: reliable failure signatures.** Not a model, not a pipeline — the ability to say *"these forty failures are four mechanisms"* deterministically. That means classifying terminal state, causal behaviour, and mechanism from traces, which requires traces that record enough to classify from. Usually the real gap is upstream: the traces don't capture the assembled context or the tool arguments.

3.  **The prerequisite check.** *"What change caused last month's regression, and what did we roll back to?"*

    If the honest answer is *"we think it was the prompt change, but it went in with three other things and we never rolled back — we just tuned forward until it seemed fine"* — then you cannot attribute a regression to a change in a **human-edited** harness. Automating the editing multiplies the number of changes by fifty and removes the human who at least remembered what they did.

    That answer means **rung 3 is off the table**, and the correct next step is not more automation but versioning the harness and running evals on every change. Which is Module 6, and Module 8's "treat harness changes like model changes" — the prerequisite for this entire module turns out to be a thing the course already told you to do.
